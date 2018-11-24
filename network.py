from requests import get, post
from bitcoin import mktx, sign, encode_privkey, privtoaddr, sha256
from binascii import b2a_hex

## Pago a minero
base_fee = 0.000452
fee_per_input = 0.000296

## Cantidad de ceros decimales o llamados satoshis
COIN = 100000000

# Gen key
def getkeys(i, s):
	privkey = sha256(str(i) + s)
	addr = privtoaddr(privkey, 88)
	return addr, privkey

def getbalance(addr):
	unspent = get('https://explorer.cha.terahash.cl/api/addr/' + addr + '/utxo').json()

	confirmed = unconfirmed = 0

	inputs = []
	for i in unspent:
		if i['confirmations'] >= 1 and i['amount'] > 0.001:
			confirmed += i['amount']
			inputs_tx = {'output' : i['txid'] + ':' + str(i['vout']), 'value' : i['satoshis'], 'address' : i['address']}
			inputs.append(inputs_tx)
		else:
			unconfirmed += i['amount']

	return [confirmed, inputs, unconfirmed]


def OP_RETURN_payload(metadata):
	metadata_len = len(metadata)

	if metadata_len <= 75:
		payload = bytearray((metadata_len,)) + metadata
	elif metadata_len <= 256:
		payload = b"\x4c" + bytearray((metadata_len,)) + metadata
	else:
		payload = b"\x4d" + bytearray((metadata_len%256,)) + bytearray((int(metadata_len/256),)) + metadata

	return payload


def sendtx(key_info, op_return = ''):
	addr, privkey = key_info
	confirmed_balance, inputs, unconfirmed = getbalance(addr)
	amount = confirmed_balance

	if not confirmed_balance >= amount:
		msg = "Balance insuficiente"

	else:
		# Transformar valores a Chatoshis
		used_amount = int(amount*COIN)

		# Utilizar solo las unspent que se necesiten
		used_balance = 0
		used_inputs = []

		for i in inputs:
			used_balance += i['value']
			used_inputs.append(i)
			if used_balance > used_amount:
				break

		used_fee = int((base_fee + fee_per_input*len(inputs))*COIN)

		# Output
		outputs = []

		# Receptor
		if used_balance == used_amount:
			outputs.append({'address' : addr, 'value' : (used_amount - used_fee)})
		else:
			outputs.append({'address' : addr, 'value' : used_amount})

		# Change
		if used_balance > used_amount + used_fee:
			outputs.append({'address' : addr, 'value' : int(used_balance - used_amount - used_fee)})

		# OP_RETURN
		if len(op_return) > 0 and len(op_return) <= 255:
			payload = OP_RETURN_payload(op_return)
			script = '6a' + b2a_hex(payload).decode('utf-8', errors='ignore')
			outputs.append({'value' : 0, 'script' : script})

		# Transacción
		tx = mktx(used_inputs, outputs)

		# Firma
		for i in range(len(used_inputs)):
			tx = sign(tx, i, privkey)
		msg = tx

	return msg
