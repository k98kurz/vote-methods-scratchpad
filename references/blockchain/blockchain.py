import base64
import binascii
import json
from nacl.encoding import RawEncoder
from nacl.hash import sha256
from nacl.public import PrivateKey, Box, SealedBox
from nacl.signing import SigningKey, VerifyKey
import nacl.utils
import os.path
import sys

'''

'''

def tohex (text):
    return binascii.hexlify(text)

def fromhex (text):
    return binascii.unhexlify(text)

def b2a(text):
    return str(base64.b64encode(text))

def a2b (text):
    return base64.b64decode(text)

# determines if the block hash has enough preceding null bytes
def meets_difficulty (signature, difficulty=1):
    hash = sha256(signature, encoder=RawEncoder)
    for i in range(0, difficulty):
        if hash[i] > 0:
            return False

    return True

'''
    First 64 bytes: block signature
    Second 32 bytes: signer's address/verification key (address)
    Third 32 bytes: previous block hash
    Next 16 bytes: nonce for meeting difficulty
    Remainder: body

    Parameters: signing_key SigningKey, previous_block bytes(64), body bytes(*), difficulty int(0<x<5)
'''
def create_block (signing_key, previous_block, body, difficulty=1):
    signing_key = SigningKey(signing_key) if type(signing_key) == type('s') or type(signing_key) == type(b's') else signing_key
    previous_block = unpack_block(previous_block) if type(previous_block) == type('s') or type(previous_block) == type(b's') else previous_block
    nonce = nacl.utils.random(16)
    signature = signing_key.sign(previous_block['hash'] + nonce + body)
    # mild PoW
    while not meets_difficulty(signature.signature, difficulty):
        nonce = nacl.utils.random(16)
        signature = signing_key.sign(previous_block['hash'] + nonce + body)
    # return the block
    return signature.signature + signing_key.verify_key._key + previous_block['hash'] + nonce + body

'''
    First 64 bytes: block signature
    Second 32 bytes: genesis address
    Third 32 bytes: address/signing key of node
    Fourth 16 bytes: nonce for meeting difficulty target.
    Final 32 bytes (body): public key of node for ECDHE

    Parameters: genesis_key SigningKey, node_address bytes(64), public_key bytes(32), difficulty int(0<x<5)
'''
def create_genesis_block (genesis_key, node_address, public_key, difficulty=1):
    nonce = nacl.utils.random(16)
    signature = genesis_key.sign(node_address + nonce + public_key)
    difficulty = difficulty if difficulty < 5 and difficulty > 0 else 1
    # mild PoW
    while not meets_difficulty(signature.signature, difficulty):
        nonce = nacl.utils.random(16)
        signature = genesis_key.sign(node_address + nonce + public_key)
    # return the genesis block
    return signature.signature + genesis_key.verify_key._key + node_address + nonce + public_key

'''
    First 64 bytes: block signature
    Second 32 bytes: signer's address/verification key
    Third 32 bytes: previous block hash
    Fourth 16 bytes: nonce
    Remainder: body
'''
def unpack_block (block_bytes):
    if len(block_bytes) < 144:
        raise ValueError('Block must be at least 144 bytes. Supplied block was only ', len(block_bytes), ' bytes long.')
    signature = block_bytes[0:64]
    hash = sha256(signature, encoder=RawEncoder)
    address = block_bytes[64:96]
    previous_block = block_bytes[96:128]
    nonce = block_bytes[128:144]
    body = block_bytes[144:]
    return {'hash': hash, 'signature': signature, 'address': address, 'previous_block': previous_block, 'nonce': nonce, 'body': body}

'''
    First 64 bytes: block signature
    Second 32 bytes: genesis address
    Third 32 bytes: address/signing key of node
    Fourth 16 bytes: nonce for meeting difficulty target.
    Final 32 bytes (body): public key of node for ECDHE
'''
def unpack_genesis_block (block_bytes):
    if len(block_bytes) < 144:
        raise ValueError('Block must be at least 144 bytes. Supplied block was only ', len(block_bytes), ' bytes long.')
    signature = block_bytes[0:64]
    hash = sha256(signature, encoder=RawEncoder)
    address = block_bytes[64:96]
    node_address = block_bytes[96:128]
    nonce = block_bytes[128:144]
    public_key = block_bytes[144:]
    return {'hash': hash, 'signature': signature, 'address': address, 'node_address': node_address, 'public_key': public_key, 'nonce': nonce}

def unpack_chain (chain):
    unpacked = [unpack_genesis_block(chain[0])]
    for i in range(1, len(chain)):
        unpacked.append(unpack_block(chain[i]))
    return unpacked

def pack_block (block):
    return block['signature'] + block['address'] + block['previous_block'] + block['nonce'] + block['body']

def pack_genesis_block (block):
    return block['signature'] + block['address'] + block['node_address'] + block['nonce'] + block['public_key']

def verify_block (block, difficulty=1):
    try:
        # unpack bytes into a dict
        unpacked = unpack_block(block) if type(block) == type('s') or type(block) == type(b's') else block
        # reject if it does not meet the required difficulty
        if not meets_difficulty(unpacked['signature'], difficulty):
            return False
        # then verify the signature
        verify_key = VerifyKey(unpacked['address']) if type(unpacked['address']) == type('s') or type(unpacked['address']) == type(b's') else unpacked['address']
        verify_key.verify(unpacked['previous_block'] + unpacked['nonce'] + unpacked['body'], unpacked['signature'])
        return True
    except nacl.exceptions.BadSignatureError:
        return False
    except ValueError:
        return False

def verify_genesis_block (block, genesis_address, difficulty=1):
    try:
        # unpack bytes into a dict
        unpacked = unpack_genesis_block(block) if type(block) == type('s') or type(block) == type(b's') else block
        # reject if it is not signed by the genesis address
        if unpacked['address'] != genesis_address:
            return False
        # reject if it does not meet the required difficulty
        if not meets_difficulty(unpacked['signature'], difficulty):
            return False
        # then verify the signature
        verify_key = VerifyKey(unpacked['address']) if type(unpacked['address']) == type('s') or type(unpacked['address']) == type(b's') else unpacked['address']
        verify_key.verify(unpacked['node_address'] + unpacked['nonce'] + unpacked['public_key'], unpacked['signature'])
        return True
    except nacl.exceptions.BadSignatureError:
        return False
    except ValueError:
        return False

def verify_chain (blocks, genesis_address, difficulty=1):
    unpacked = []

    # verify other blocks
    for i in range(0, len(blocks)):
        if i == 0:
            unpacked.append(unpack_genesis_block(blocks[i]) if type(blocks[i]) == type('s') or type(blocks[i]) == type(b's') else blocks[i])
        else:
            unpacked.append(unpack_block(blocks[i]) if type(blocks[i]) == type('s') or type(blocks[i]) == type(b's') else blocks[i])

        # throw it out if its genesis block is invalid
        if i == 0 and not verify_genesis_block(unpacked[0], genesis_address):
            return False

        # throw it out if any non-genesis block has a corrupt or fraudulent signature
        if i > 0 and not verify_block(unpacked[i], difficulty):
            return False

        # throw it out if the current block does not reference previous block
        if i > 0 and unpacked[i]['previous_block'] != unpacked[i-1]['hash']:
            return False

        # throw it out if the previous, non-genesis block's address is not the same as the current one
        if i > 1 and unpacked[i]['address'] != unpacked[i-1]['address']:
            return False

    return True

def create_node (seed):
    node = {'signing_key': SigningKey(seed), 'seed': seed}
    node['verify_key'] = node['signing_key'].verify_key
    node['private_key'] = node['signing_key'].to_curve25519_private_key()
    node['public_key'] = node['verify_key'].to_curve25519_public_key()
    return node

def save_block_chain (name, chain):
    dir = name + '_chain'
    if not os.path.isdir(dir):
        os.mkdir(os.path.join('./', dir))

    # save genesis block
    # print('save_block_chain saving genesis block')
    genesis_hash = chain[0]['hash'] if type(chain[0]) == type([]) else unpack_genesis_block(chain[0])['hash']
    data = pack_genesis_block(chain[0]) if type(chain[0]) == type([]) else chain[0]
    open(os.path.join(dir, '0_block'), 'wb').write(genesis_hash + data)

    # save other blocks
    for i in range(1, len(chain)):
        # print('save_block_chain saving block', i)
        # print('save_block_chain type(chain[', i, ']:) ', type(chain[i]))
        hash = chain[i]['hash'] if type(chain[0]) == type([]) else unpack_block(chain[i])['hash']
        data = pack_block(chain[i]) if type(chain[i]) == type([]) else chain[i]
        open(os.path.join(dir, str(i) + '_block'), 'wb').write(hash + data)

def load_block_chain (name):
    dir = name + '_chain'
    chain = []
    files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    for i in range(0, len(files)):
        chain.append(open(os.path.join(dir, files[i]), 'rb').read()[32:])
    chain = unpack_chain(chain)
    return chain

'''
    In production badge, the genesis.seed file will be present in the flashed
    package, then deleted after genesis block creation; the genesis verify_key
    will be stored in the genesis block, and each node will be able to validate
    other genesis blocks by comparing genesis addresses and verifying the
    signature via the verify_chain method.

    For this reference demonstration, we will just save the genesis seed.
'''
def main():
    # get genesis file from storage or create it
    if os.path.isfile('genesis.seed'):
        genesis = {'seed': open('genesis.seed', 'rb').read()}
    else:
        genesis = {'seed': PrivateKey.generate()._private_key}
        open('genesis.seed', 'wb').write(genesis['seed'])

    # derive some values
    genesis['signing_key'] = SigningKey(genesis['seed'])
    genesis['address'] = genesis['signing_key'].verify_key._key
    # print('genesis address ', tohex(genesis['address']))

    # create some nodes
    if os.path.isfile('node1.seed'):
        node1 = create_node(open('node1.seed', 'rb').read())
    else:
        node1 = create_node(PrivateKey.generate()._private_key)
        open('node1.seed', 'wb').write(node1['seed'])

    if os.path.isfile('node2.seed'):
        node2 = create_node(open('node2.seed', 'rb').read())
    else:
        node2 = create_node(PrivateKey.generate()._private_key)
        open('node2.seed', 'wb').write(node2['seed'])

    # create genesis blocks
    node1['blockchain'] = [create_genesis_block(genesis['signing_key'], node1['verify_key']._key, node1['public_key']._public_key)]
    node2['blockchain'] = [create_genesis_block(genesis['signing_key'], node2['verify_key']._key, node2['public_key']._public_key)]

    # print('node1[verify_key]._key ', tohex(node1['verify_key']._key))
    # print('node1[public_key]._public_key ', tohex(node1['public_key']._public_key))
    # print('Genesis block: ', tohex(node1['blockchain'][0]), ' :len: ', len(node1['blockchain'][0]))
    # genesis_block = unpack_genesis_block(node1['blockchain'][0])
    # print('unpacked genesis block:')
    # print('     signature', tohex(genesis_block['signature']))
    # print('     hash', tohex(genesis_block['hash']))
    # print('     address', tohex(genesis_block['address']))
    # print('     node_address', tohex(genesis_block['node_address']))
    # print('     public_key', tohex(genesis_block['public_key']))

    # sys.exit()

    # verify genesis blocks
    if verify_genesis_block(node1['blockchain'][0], genesis['address']):
        print('Node 1 genesis block verified.')
    else:
        print('Node 1 genesis block failed verification.')

    if verify_genesis_block(node2['blockchain'][0], genesis['address']):
        print('Node 2 genesis block verified.')
    else:
        print('Node 2 genesis block failed verification.')

    # add a block to each
    node1['blockchain'].append(create_block(node1['signing_key'], node1['blockchain'][0], b'Hail Julius Caesar or something.'))
    node2['blockchain'].append(create_block(node2['signing_key'], node2['blockchain'][0], b'Knives are cool tools of Roman politics.'))

    # print('node1 blockchain 0', tohex(node1['blockchain'][0]))
    # print('node1 blockchain 1', tohex(node1['blockchain'][1]))

    # verify blockchains
    if verify_chain(node1['blockchain'], genesis['address']):
        print('Node 1 block chain verified.')
    else:
        print('Node 1 block chain failed verification.')

    if verify_chain(node2['blockchain'], genesis['address']):
        print('Node 2 block chain verified.')
    else:
        print('Node 2 block chain failed verification.')


    print('type(node1[blockchain])', type(node1['blockchain']))
    print('type(node1[blockchain][0])', type(node1['blockchain'][0]))
    print('len node1[blockchain][0]', len(node1['blockchain'][0]))
    # write blockchains to file
    save_block_chain('node1', node1['blockchain'])
    save_block_chain('node2', node2['blockchain'])

    # load blockchain from file
    blockchain = load_block_chain('node1')

    # verify
    if verify_chain(blockchain, genesis['address']):
        print('Verified block chain retrieved from file system.')
    else:
        print('Failed to verify block chain retrieved from file system.')

    # hostile takeover
    blockchain.append(create_block(node2['signing_key'], node1['blockchain'][1], b'Hostile takeover of node1 chain by node2.'))

    # verify
    if verify_chain(blockchain, genesis['address']):
        print('Hostile takeover of node1 chain by node2 not detected.')
    else:
        print('Node2 gtfo of node1\'s blockchain')

main()
