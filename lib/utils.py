import base64
import binascii

def tohex (text):
    return binascii.hexlify(text)

def fromhex (text):
    return binascii.unhexlify(text)

def b2a(text):
    return str(base64.b64encode(text))

def a2b (text):
    return base64.b64decode(text)
