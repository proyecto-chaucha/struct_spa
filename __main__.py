from network import *
from pack import *
from bitcoin import deserialize, serialize
from requests import get, post
from binascii import a2b_hex


def main(rut):
    # Lectura JSON de la api del SII / contrato / blockchain
    json = get('http://25.7.155.170/hackaton/index.php/crear/get_datos').json()

    # Creación del packet cabecera
    packet_header = eS('header') + pL(rut) + \
                     sL(json['razon_social']) + eS(json['razon_social']) + \
                     pL(json['fecha_constitucion']) + \
                     pL(json['fecha_inicio_actividades']) + \
                     pB(json['termino_giro']) + \
                     sL(json['rep_nombre']) + eS(json['rep_nombre']) + \
                     pL(json['rep_rut']) + \
                     sL(json['socios'])

    # Creación del packet de accionistas
    packet_hodlers = []
    id = 1

    for i in json['socios']:
        acc_rut = AESencrypt(str(i['rut']))
        acciones = AESencrypt(str(i['acciones']))

        packet =  pL(id) + eS('accionistas') + \
                  sL(i['nombre']) + eS(i['nombre']) + \
                  sL(acc_rut) + acc_rut + \
                  sL(acciones) + acciones

        id += 1
        packet_hodlers.append(packet)

    # Par de llaves de cabecera
    header_key_info = getkeys(rut, 'header')

    # lectura última tx
    last_tx_hash = get('https://explorer.cha.terahash.cl/api/addr/' + header_key_info[0]).json()
    last_tx = get('https://explorer.cha.terahash.cl/api/tx/' + last_tx_hash['transactions'][0]).json()

    # extracción de último header almacenado
    for i in last_tx['vout']:
        script = i['scriptPubKey']['asm']
        if script.find('OP_RETURN') == 0 and script.find('686561646572') > 0:
            last_header = script.replace('OP_RETURN ','')
            print('> last header: %s' % last_header)

    # escritura nuevo packet si cambia el header
    if not last_header == b2a_hex(packet_header).decode():
        new_tx_header = sendtx(header_key_info, packet_header)
        broadcasting = post('https://explorer.cha.terahash.cl/api/tx/send', data={'rawtx' : new_tx_header})

        try:
            print('# new header update: %s' % broadcasting.json()['txid'])
        except:
            print(broadcasting.text)


    # Par de llaves de accionistas
    hodlers_key_info = getkeys(rut, 'acc')

    last_hodler_changes = []

    last_tx_hash = get('https://explorer.cha.terahash.cl/api/addr/' + hodlers_key_info[0]).json()
    for i in last_tx_hash['transactions']:
        last_tx = get('https://explorer.cha.terahash.cl/api/tx/' + i).json()
        for j in last_tx['vout']:
            script = j['scriptPubKey']['asm']
            if script.find('OP_RETURN') == 0 and script.find('616363696f6e6973746173') > 0:
                last_hodl = script.replace('OP_RETURN ','')
                flag = False
                if len(last_hodler_changes) > 0:
                    for k in last_hodler_changes:
                        if last_hodl[:2] == k[:2]:
                            flag = True
                    if not flag:
                        last_hodler_changes.append(last_hodl)
                else:
                    last_hodler_changes.append(last_hodl)


    for i in packet_hodlers:
        print('> last hodler: %s' % b2a_hex(i).decode())
        if not b2a_hex(i).decode() in last_hodler_changes:
            new_tx_hodler = sendtx(hodlers_key_info, i)
            broadcasting = post('https://explorer.cha.terahash.cl/api/tx/send', data={'rawtx' : new_tx_hodler})
            try:
                print('# new hodler update: %s' % broadcasting.json()['txid'])
            except:
                print(broadcasting.text)

    print('# hodler addr: %s' % hodlers_key_info[0])
    print('# header addr: %s' % header_key_info[0])

if __name__ == '__main__':
    rut = 76891821
    main(rut)
