from nacl.public import PrivateKey
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from nacl.encoding import RawEncoder
import nacl
import os.path


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
    Third 64 bytes: previous block signature
    Next 16 bytes: nonce for meeting difficulty
    Remainder: body

    Parameters: signing_key SigningKey, previous_block bytes(64), body bytes(*), difficulty int(0<x<5)
'''
def create_block (signing_key, previous_block, body, difficulty=1):
    signing_key = SigningKey(signing_key) if type(signing_key) == type('s') or type(signing_key) == type(b's') else signing_key
    previous_block = unpack_block(previous_block) if type(previous_block) == type('s') or type(previous_block) == type(b's') else previous_block
    nonce = nacl.utils.random(16)
    signature = signing_key.sign(previous_block['signature'] + nonce + body)
    # mild PoW
    while not meets_difficulty(signature.signature, difficulty):
        nonce = nacl.utils.random(16)
        signature = signing_key.sign(previous_block['signature'] + nonce + body)
    # return the block
    return signature.signature + signing_key.verify_key._key + previous_block['signature'] + nonce + body

'''
    First 64 bytes: block signature
    Second 32 bytes: genesis address
    Third 32 bytes: address/signing key of node
    Fourth 32 bytes: public key of node for ECDHE
    Final 16 bytes: nonce for meeting difficulty target.

    Parameters: genesis_key SigningKey, node_address bytes(64), public_key bytes(32), difficulty int(0<x<5)
'''
def create_genesis_block (genesis_key, node_address, public_key, difficulty=1):
    nonce = nacl.utils.random(16)
    signature = genesis_key.sign(node_address + public_key + nonce)
    difficulty = difficulty if difficulty < 5 and difficulty > 0 else 2
    # mild PoW
    while not meets_difficulty(signature.signature, difficulty):
        nonce = nacl.utils.random(16)
        signature = genesis_key.sign(node_address + public_key + nonce)
    # return the genesis block
    return signature.signature + genesis_key.verify_key._key + node_address + public_key + nonce

'''
    First 64 bytes: block signature
    Second 32 bytes: signer's address/verification key
    Third 64 bytes: previous block signature
    Fourth 16 bytes: nonce
    Remainder: body
'''
def unpack_block (block_bytes):
    if len(block_bytes) < 176:
        raise ValueError('Block must be at least 176 bytes. Supplied block was only ', len(block_bytes), ' bytes long.')
    signature = block_bytes[0:64]
    hash = sha256(signature, encoder=RawEncoder)
    address = block_bytes[64:96]
    previous_block = block_bytes[96:160]
    nonce = block_bytes[160:176]
    body = block_bytes[176:]
    return {'hash': hash, 'signature': signature, 'address': address, 'previous_block': previous_block, 'nonce': nonce, 'body': body}

'''
    Genesis block has node_address and public_key where normal block contains
    previous_block; genesis block has no body.
'''
def unpack_genesis_block (block_bytes):
    block = unpack_block(block_bytes)
    node_address = block['previous_block'][:32]
    public_key = block['previous_block'][32:]
    return {'hash': block['hash'], 'signature': block['signature'], 'address': block['address'], 'node_address': node_address, 'public_key': public_key, 'nonce': block['nonce']}

def unpack_chain (chain):
    unpacked = [unpack_genesis_block(chain[0])]
    for i in range(1, len(chain)):
        unpacked.append(unpack_block(chain[i]))
    return unpacked

def pack_block (block):
    return block['signature'] + block['address'] + block['previous_block'] + block['nonce'] + block['body']

def verify_block (block, difficulty=1):
    try:
        # unpack bytes into a dict
        block = unpack_block(block) if type(block) == type('s') or type(block) == type(b's') else block
        # reject if it does not meet the required difficulty
        if not meets_difficulty(block['signature'], difficulty):
            return False
        # then verify the signature
        verify_key = VerifyKey(block['address']) if type(block['address']) == type('s') or type(block['address']) == type(b's') else block['address']
        verify_key.verify(block['previous_block'] + block['nonce'] + block['body'], block['signature'])
        return True
    except nacl.exceptions.BadSignatureError:
        return False
    except ValueError:
        return False

def verify_chain (blocks, genesis_address, difficulty=1):
    unpacked = []
    for i in range(0, len(blocks)):
        unpacked.append(unpack_block(blocks[i]) if type(blocks[i]) == type('s') or type(blocks[i]) == type(b's') else blocks[i])

        # throw it out if any block has a corrupt or fraudulent signature
        if not verify_block(unpacked[i], difficulty):
            return False

        # throw it out if its genesis block was not signed by the genesis address
        if i == 0 and unpacked[0]['address'] != genesis_address:
            return False

        # throw it out if the current block does not reference previous block
        if i > 0 and unpacked[i]['previous_block'] != unpacked[i-1]['signature']:
            return False

        # throw it out if the previous, non-genesis block's address is not the same as the current one
        if i > 1 and unpacked[i]['address'] != unpacked[i-1]['address']:
            return False

    return True

def save_block_chain (path, name, chain):
    dir = os.path.join(path, name + '_chain')
    if not os.path.isdir(dir):
        os.mkdir(os.path.join('./', dir))

    for i in range(0, len(chain)):
        open(os.path.join(dir, str(i) + '_block'), 'wb').write(chain[i][hash] + pack_block(chain[i]))

def load_block_chain (path, name):
    dir = os.path.join(path, name + '_chain')
    chain = []
    files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    for i in range(0, len(files)):
        chain.append(unpack_block(open(os.path.join(dir, files[i]), 'rb').read()))
    return chain

def setup_node (seed):
    node = {'signing_key': SigningKey(seed), 'seed': seed}
    node['verify_key'] = node['signing_key'].verify_key
    node['address'] = node['verify_key']._key
    node['private_key'] = node['signing_key'].to_curve25519_private_key()
    node['public_key'] = node['verify_key'].to_curve25519_public_key()
    return node
