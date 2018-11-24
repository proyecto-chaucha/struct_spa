from binascii import b2a_hex
from struct import pack
from Crypto.Cipher import AES

def AESencrypt(s):
    msg = s.encode()
    while not len(msg) % 16 == 0:
        msg += b'@'

    suite = AES.new(b'chaucha luka 666', AES.MODE_CBC, b'This is an IV...')
    return suite.encrypt(msg)

# pack(len(string))
def sL(s):
    return pack('<H', len(s))

# pack(Long)
def pL(n):
    return pack('<L', n)

# encode(String)
def eS(s):
    return s.encode('utf-8')

# pack(boolean)
def pB(b):
    return pack('<?', b)
