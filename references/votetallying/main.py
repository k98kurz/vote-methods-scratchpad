from datetime import datetime, timedelta
from nacl.encoding import RawEncoder
from nacl.hash import sha256
import tally
import blockformat
import os.path
import sys
# add lib folder
sys.path.insert(1, '/home/sithlord/Documents/programming/python/votebadge/lib')
import blockchain
from utils import tohex, fromhex, b2a, a2b


# output control bools
print_all = False
print_proposal = False
print_ballot = False
print_tally = True
print_tally_packing = True


# election parameters
start_time = datetime.now()
end_time = start_time + timedelta(days=1)
number_of_winners = 2
quorum_requirement = 10

# candidate hashes
jesus = sha256(b'Jesus', encoder=RawEncoder)
trump = sha256(b'Trump', encoder=RawEncoder)
obama = sha256(b'Obama', encoder=RawEncoder)
gandi = sha256(b'Gandi', encoder=RawEncoder)
candidates = [b'Jesus', b'Trump', b'Obama', b'Gandi']
candidate_hashes = [jesus, trump, obama, gandi]

# ballots for plurality and approval voting
mntv_ballots = [
    (gandi, jesus),
    (gandi, jesus),
    (gandi, trump),
    (gandi, trump),
    (gandi, trump),
    (jesus, trump),
    (jesus, trump),
    (jesus, obama),
    (trump, obama),
    (trump, jesus),
    (trump, gandi),
    (obama, jesus),
    (obama, gandi),
    (obama, gandi)
]

# ballots for ranked voting methods
ranked_ballots = [
    (gandi, jesus, trump, obama),
    (gandi, jesus, trump, obama),
    (gandi, jesus, trump, obama),
    (gandi, jesus, trump, obama),
    (gandi, jesus, obama, trump),
    (gandi, jesus, obama, trump),
    (gandi, jesus, obama, trump),
    (gandi, obama, trump, jesus),
    (jesus, obama, trump, gandi),
    (jesus, gandi, trump, obama),
    (jesus, gandi, trump, obama),
    (jesus, gandi, trump, obama),
    (jesus, gandi, trump, obama),
    (jesus, gandi, trump, obama),
    (trump, gandi, jesus, obama),
    (trump, gandi, jesus, obama),
    (trump, obama, jesus, gandi),
    (obama, gandi, trump, jesus),
    (obama, gandi, trump, jesus),
    (obama, trump) # one exhausted ballot for IRV
]

# ballots for scored voting methods
scored_ballots = [
    {gandi: 5, jesus: 5, obama: 0, trump: 0},
    {gandi: 5, jesus: 5, obama: 0, trump: 0},
    {gandi: 5, jesus: 4, obama: 1, trump: 0},
    {gandi: 5, jesus: 4, obama: 1, trump: 1},
    {gandi: 4, jesus: 5, obama: 0, trump: 2},
    {gandi: 4, jesus: 3, obama: 2, trump: 2},
    {gandi: 4, jesus: 2, obama: 3, trump: 0},
    {gandi: 3, jesus: 4, obama: 0, trump: 5},
    {gandi: 3, jesus: 4, obama: 0, trump: 5},
    {gandi: 3, jesus: 5, obama: 1, trump: 5},
    {gandi: 3, jesus: 4, obama: 2, trump: 4},
    {gandi: 3, jesus: 2, obama: 5, trump: 1},
    {gandi: 3, jesus: 1, obama: 5, trump: 1},
    {gandi: 0, jesus: 1, obama: 1, trump: 5},
    {gandi: 0, jesus: 1, obama: 0, trump: 2}
]


def test_plurality ():
    # pack plurality proposal
    pp = blockformat.pack_plurality_proposal(b'GOATs.', number_of_winners, quorum_requirement, candidates, start_time, end_time)
    pp2 = blockformat.pack_proposal('PLURALITY', b'GOATs.', number_of_winners, quorum_requirement, candidates, start_time, end_time)
    # unpack
    proposal = blockformat.unpack_plurality_proposal(pp[1:])
    proposal2 = blockformat.unpack_block(pp2)

    if print_all or print_proposal:
        print('packed plurality proposal', tohex(pp))
        print('unpacked plurality proposal', proposal)

    # pack a ballot (using the hash of the packed proposal instead of the hash of the relevant PROPOSAL_PLURALITY block signature)
    bb = blockformat.pack_plurality_ballot(sha256(pp, encoder=RawEncoder), [jesus, gandi])
    # unpack a ballot
    ballot = blockformat.unpack_plurality_ballot(bb[1:])

    if print_all or print_ballot:
        ballot['proposal_ref_hash'] = tohex(ballot['proposal_ref_hash'])
        for i in range(0, len(ballot['candidate_hashes'])):
            ballot['candidate_hashes'][i] = tohex(ballot['candidate_hashes'][i])
        print('packed plurality ballot: ', tohex(bb))
        print('unpacked plurality ballot: ', ballot)

    # tally plurality-at-large
    plurality_result = tally.plurality(number_of_winners, candidate_hashes, mntv_ballots, quorum_requirement)

    if print_all or print_tally:
        print('candidates:')
        print('     Gandi=', tohex(gandi))
        print('     Jesus=', tohex(jesus))
        print('     Obama=', tohex(obama))
        print('     Trump=', tohex(trump))

        print('plurality_result winners: ')
        for f in plurality_result['winners']:
            print('     ', tohex(f))

        print('plurality_result[tally]: ')
        for c, t in plurality_result['tally'].items():
            print('     ', tohex(c), t)

        print('plurality_result[ties]: ', plurality_result['ties'])
        print('plurality_result[valid_ballots]: ', plurality_result['valid_ballots'])
        print('plurality_result[invalid_ballots]: ', plurality_result['invalid_ballots'])
        print('plurality_result[valid_votes]: ', plurality_result['valid_votes'])
        print('plurality_result[invalid_votes]: ', plurality_result['invalid_votes'])
        print('plurality_result[meets_quorum]: ', plurality_result['meets_quorum'])

    # pack tally (using hash of a ballot instead of the hash of the relevant COLLECT_BALLOTS block signature)
    pt_hash = sha256(bb, encoder=RawEncoder)
    pt = blockformat.pack_plurality_tally(pt_hash, plurality_result)
    # unpack tally
    election = blockformat.unpack_plurality_tally(pt[2:])

    if print_all or print_tally_packing:
        print('  ')
        # print('packed plurality election', tohex(pt))

        print('unpacked plurality election winners: ')
        for f in election['winners']:
            print('     ', tohex(f))

        # print('unpacked plurality election[tally]: ', type(election['tally']), len(election['tally']))
        print('unpacked plurality election[tally]:')
        for c, t in election['tally'].items():
            print('     ', tohex(c), t)

        # print('unpacked plurality election[collection_ref_hash]: ', tohex(election['collection_ref_hash']))
        print('unpacked plurality election[ties]: ', election['ties'])
        print('unpacked plurality election[valid_ballots]: ', election['valid_ballots'])
        print('unpacked plurality election[invalid_ballots]: ', election['invalid_ballots'])
        print('unpacked plurality election[valid_votes]: ', election['valid_votes'])
        print('unpacked plurality election[invalid_votes]: ', election['invalid_votes'])
        print('unpacked plurality election[meets_quorum]: ', election['meets_quorum'])


def test_irv ():
    # pack IRV proposal
    ip = blockformat.pack_irv_proposal(b'GOAT', quorum_requirement, candidates, start_time, end_time)
    # unpack IRV proposal
    proposal = blockformat.unpack_irv_proposal(ip[1:])

    if print_all or print_proposal:
        print('packed IRV proposal', tohex(ip))
        print('unpacked IRV proposal', proposal)

    # pack IRV ballot
    ib = blockformat.pack_irv_ballot(sha256(ip, encoder=RawEncoder), ranked_ballots[0])
    # unpack IRV ballot
    ballot = blockformat.unpack_irv_ballot(ib[1:])

    if print_all or print_ballot:
        ballot['proposal_ref_hash'] = tohex(ballot['proposal_ref_hash'])
        for i in range(0, len(ballot['candidate_hashes'])):
            ballot['candidate_hashes'][i] = tohex(ballot['candidate_hashes'][i])
        print('packed IRV ballot', tohex(ib))
        print('unpacked IRV ballot', ballot)

    # tally IRV
    irv_result = tally.irv(candidate_hashes, ranked_ballots, quorum_requirement)

    if print_all or print_tally:
        print('candidates:')
        print('     Gandi=', tohex(gandi))
        print('     Jesus=', tohex(jesus))
        print('     Obama=', tohex(obama))
        print('     Trump=', tohex(trump))

        print('irv_result winner: ', tohex(irv_result['winner']))
        print('irv_result[tally]: ')
        for i in range(0, len(irv_result['tally'])):
            print('     round {}:'.format(i))
            for c in irv_result['tally'][i]:
                print('     ', tohex(c), ': ', irv_result['tally'][i][c])

        print('irv_result[valid_ballots]: ', irv_result['valid_ballots'])
        print('irv_result[invalid_ballots]: ', irv_result['invalid_ballots'])
        print('irv_result[exhausted_ballots]: ', irv_result['exhausted_ballots'])
        print('irv_result[meets_quorum]: ', irv_result['meets_quorum'])

    # pack IRV tally (using hash of a ballot instead of the hash of the relevant COLLECT_BALLOTS block signature)
    it = blockformat.pack_irv_tally(sha256(ib, encoder=RawEncoder), irv_result)
    # unpack tally
    election = blockformat.unpack_irv_tally(it[2:])

    if print_all or print_tally_packing:
        print('packed IRV tally', tohex(it))
        print('unpacked IRV tally:')
        print('collection_ref_hash:', tohex(election['collection_ref_hash']))
        print('winner:', tohex(election['winner']))
        for r in range(0, len(election['tally'])):
            print('     round {}:'.format(r))
            for c in election['tally'][r]:
                print('     ', tohex(c), ': ', election['tally'][r][c])

        print('valid_ballots: ', election['valid_ballots'])
        print('invalid_ballots: ', election['invalid_ballots'])
        print('exhausted_ballots: ', election['exhausted_ballots'])
        print('meets_quorum: ', election['meets_quorum'])


def test_irv_coombs ():
    # pack IRV proposal
    ip = blockformat.pack_irv_coombs_proposal(b'GOAT', quorum_requirement, candidates, start_time, end_time)
    # unpack IRV proposal
    proposal = blockformat.unpack_irv_coombs_proposal(ip[1:])

    if print_all or print_proposal:
        print('packed IRV proposal', tohex(ip))
        print('unpacked IRV proposal', proposal)

    # pack IRV ballot
    ib = blockformat.pack_irv_ballot(sha256(ip, encoder=RawEncoder), ranked_ballots[0])
    # unpack IRV ballot
    ballot = blockformat.unpack_irv_ballot(ib[1:])

    if print_all or print_ballot:
        ballot['proposal_ref_hash'] = tohex(ballot['proposal_ref_hash'])
        for i in range(0, len(ballot['candidate_hashes'])):
            ballot['candidate_hashes'][i] = tohex(ballot['candidate_hashes'][i])
        print('packed IRV ballot', tohex(ib))
        print('unpacked IRV ballot', ballot)

    # tally IRV
    irv_coombs_result = tally.irv_coombs(candidate_hashes, ranked_ballots, quorum_requirement)

    if print_all or print_tally:
        print('candidates:')
        print('     Gandi=', tohex(gandi))
        print('     Jesus=', tohex(jesus))
        print('     Obama=', tohex(obama))
        print('     Trump=', tohex(trump))

        print('irv_coombs_result winner: ', tohex(irv_coombs_result['winner']))
        print('irv_coombs_result[tally]: ')
        for i in range(0, len(irv_coombs_result['tally'])):
            print('     round {}:'.format(i))
            for c in irv_coombs_result['tally'][i]:
                print('     ', tohex(c), ': ', irv_coombs_result['tally'][i][c])

        print('irv_coombs_result[valid_ballots]: ', irv_coombs_result['valid_ballots'])
        print('irv_coombs_result[invalid_ballots]: ', irv_coombs_result['invalid_ballots'])
        print('irv_coombs_result[exhausted_ballots]: ', irv_coombs_result['exhausted_ballots'])
        print('irv_coombs_result[meets_quorum]: ', irv_coombs_result['meets_quorum'])

    # pack IRV tally (using hash of a ballot instead of the hash of the relevant COLLECT_BALLOTS block signature)
    it = blockformat.pack_irv_tally(sha256(ib, encoder=RawEncoder), irv_coombs_result)
    # unpack tally
    election = blockformat.unpack_irv_tally(it[2:])

    if print_all or print_tally_packing:
        print('packed IRV tally', tohex(it))
        print('unpacked IRV tally:')
        print('winner:', tohex(election['winner']))
        print('collection_ref_hash:', tohex(election['collection_ref_hash']))
        for r in range(0, len(election['tally'])):
            print('     round {}:'.format(r))
            for c in election['tally'][r]:
                print('     ', tohex(c), ': ', election['tally'][r][c])

        print('valid_ballots: ', election['valid_ballots'])
        print('invalid_ballots: ', election['invalid_ballots'])
        print('exhausted_ballots: ', election['exhausted_ballots'])
        print('meets_quorum: ', election['meets_quorum'])




# test_plurality()
# test_irv()
test_irv_coombs()

sys.exit()





def test_blockchain():
    from nacl.signing import SigningKey, VerifyKey
    import nacl

    # get genesis file from storage or create it
    if os.path.isfile('genesis.seed'):
        genesis = {'seed': open('genesis.seed', 'rb').read()}
    else:
        genesis = {'seed': nacl.utils.random(size=32)}
        open('genesis.seed', 'wb').write(genesis['seed'])

    # derive some values
    genesis['signing_key'] = SigningKey(genesis['seed'])
    genesis['address'] = genesis['signing_key'].verify_key._key

    # create a node
    node = blockchain.setup_node(nacl.utils.random(size=32))

    # create genesis block
    blocks = [blockchain.create_genesis_block(genesis['signing_key'], node['address'], node['public_key']._public_key)]

    # verify
    if blockchain.verify_block(blocks[0]):
        print('Verified genesis block')
    else:
        print('Fuck')

    print('Genesis block signature:', tohex(blockchain.unpack_block(blocks[0])['signature']))
    print('Genesis block hash:', tohex(blockchain.unpack_block(blocks[0])['hash']))

    # add block
    blocks.append(blockchain.create_block(node['signing_key'], blocks[0], b'Sample block body'))

    # verify
    if blockchain.verify_chain(blocks, genesis['address']):
        print('Verified chain')
    else:
        print('Fuck')

    unpacked = blockchain.unpack_chain(blocks)
    print('Block 1 signature:', tohex(unpacked[1]['signature']))
    print('Block 1 hash:', tohex(unpacked[1]['hash']))
