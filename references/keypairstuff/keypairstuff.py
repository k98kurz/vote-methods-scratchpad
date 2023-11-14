import base64
import binascii
import json
import nacl.encoding
from nacl.public import PrivateKey, Box, SealedBox
from nacl.signing import SigningKey, VerifyKey
import nacl.utils
import os.path
import sys

'''
    The root, stored key must be a 32 byte seed. From it, the Ed25519 signature
        key, verification key,and curve25519 encryption key pair are derived. So
        each node must store a signature private key seed.

    In a distributed network, the verification key is the node address/GUID.
        If the node desires communications to it to be encrypted, it then adds
        its public key to its block chain and publishes the signature. Other
        nodes will download the block chain, verify the signature, and store the
        public key in their routing table.

    However, encrypted messages are not necessary in a network storing multiple
        block chains, and the overhead will likely be too much for a LoRa mesh
        network running something like kademlia DHT.
'''


def tohex (text):
    return binascii.hexlify(text)

def fromhex (text):
    return binascii.unhexlify(text)

def b2a(text):
    return base64.b64encode(text)

def a2b (text):
    return base64.b64decode(text)


# get signing key seeds from storage or generate new ones
if os.path.isfile('alice.seed'):
    alice = {"seed": open('alice.seed', 'rb').read()}
else:
    alice = {"seed": PrivateKey.generate()._private_key}
    open('alice.seed', 'wb').write(alice['seed'])


if os.path.isfile('bob.seed'):
    bob = {"seed": open('bob.seed', 'rb').read()}
else:
    bob = {"seed": PrivateKey.generate()._private_key}
    open('bob.seed', 'wb').write(bob['seed'])



# derive keys from seed
alice['signing'] = SigningKey(alice['seed'])
alice['verify'] = alice['signing'].verify_key
alice['private'] = alice['signing'].to_curve25519_private_key()
alice['public'] = alice['verify'].to_curve25519_public_key()

bob['signing'] = SigningKey(bob['seed'])
bob['verify'] = bob['signing'].verify_key
bob['private'] = bob['signing'].to_curve25519_private_key()
bob['public'] = bob['verify'].to_curve25519_public_key()


# print("Alice public key: ", tohex(alice['public']._public_key), ' :len: ', len(alice['public']._public_key))
# print("Alice verify key: ", tohex(alice['verify']._key), ' :len: ', len(alice['verify']._key))
# print("Bob public key: ", tohex(bob['public']._public_key), ' :len: ', len(bob['public']._public_key))
# print("Bob verify key: ", tohex(bob['verify']._key), ' :len: ', len(bob['verify']._key))
print('Alice signing key: ', tohex(alice['signing']._signing_key), ' :len: ', len(alice['signing']._signing_key))

message = b"(1844 (worldwide (racecar (now))))"

# sign
sig = bob['signing'].sign(message)
msg = json.dumps({"msg": b2a(sig.message).decode('utf-8'), "sig": b2a(sig.signature).decode('utf-8'), "verify_key": b2a(bob['verify']._key).decode('utf-8')})

# ECDHE
sealed_box = SealedBox(alice['public'])

# encrypt
encrypted_msg = sealed_box.encrypt(bytes(msg, 'utf-8'))

# save file
open('bob-to-alice.msg', 'wb').write(encrypted_msg)

print("Plaintext + signature: ", msg)
# print("     len of signature: ", len(sig.signature))
print("Ciphertext: ", b2a(encrypted_msg))

# ECDHE
unseal_box = SealedBox(alice['private'])

# decrypt
decrypted_msg = unseal_box.decrypt(encrypted_msg)
json_msg = json.loads(decrypted_msg)
json_msg['msg'] = a2b(json_msg['msg'])
json_msg['sig'] = a2b(json_msg['sig'])
json_msg['verify_key'] = a2b(json_msg['verify_key'])

print("Decrypted: ", decrypted_msg)
print("json_msg[verify_key]: ", json_msg['verify_key'])
print("json_msg[msg]: ", json_msg['msg'])

# verify signature
try:
    # print('***')
    # print("VERIFY TIME")
    # print('***')
    # print('type sig.message: ', type(sig.message))
    # print('type json_msg[msg]: ', type(json_msg['msg']))
    # print('type sig.signature: ', type(sig.signature))
    # print('type json_msg[sig]: ', type(json_msg['sig']))
    verify_key = VerifyKey(json_msg['verify_key'])
    verify_key.verify(sig.message, sig.signature)
    verify_key.verify(json_msg['msg'], json_msg['sig'])
    print("Signature verified.")
except nacl.exceptions.BadSignatureError:
    print("Signature corrupt.")
