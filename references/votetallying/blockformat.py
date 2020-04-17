from collections import OrderedDict
from datetime import datetime, timedelta
from nacl.encoding import RawEncoder
from nacl.hash import sha256
from nacl.public import PrivateKey
from nacl.signing import SigningKey, VerifyKey
import nacl
import os.path
import sys
import tally
# add lib folder
sys.path.insert(1, '/home/sithlord/Documents/programming/python/votebadge/lib')
import blockchain
import const
from utils import tohex, fromhex, b2a, a2b


'''
    Control characters. Each block can contain one action. Each action is defined
    by the first byte of the body being one of these control characters.
'''
def define_consts ():
    conST.PROTOCOL_VERSION      = b'\x00'
    const.PROPOSAL_PLURALITY    = b'\x00' # First-past-the-post/bloc voting
    const.PROPOSAL_IRV          = b'\x01' # Instant Run-off Vote/Alternative Vote
    const.PROPOSAL_IRV_COOMBS   = b'\x02' # IRV with Coomb's Method
    const.PROPOSAL_STV_DROOP    = b'\x03' # Single Transferable Vote (Droop quota)
    const.PROPOSAL_STV_HARE     = b'\x04' # Single Transferable Vote (Hare quota)
    const.PROPOSAL_APPROVAL     = b'\x05' # Highest approval wins
    const.PROPOSAL_CAV          = b'\x06' # Combined Approval Voting; highest score wins
    const.PROPOSAL_BORDA        = b'\x07' # Ranked voting used in the Vatican
    const.PROPOSAL_DOWDAL       = b'\x08' # Version of Borda used in Nauru
    const.PROPOSAL_BUCKLIN      = b'\x09' # Bucklin/Grand Junction System; ranked voting
    const.PROPOSAL_SCORE        = b'\x0a' # Highest score wins
    const.PROPOSAL_STAR         = b'\x0b' # Score Then Automatic Run-off
    const.PROPOSAL_COPELAND     = b'\x0c' # Copeland's Pairwise Aggregation (Condorcet method); uses 2nd-order algorithm for tie-breaking
    const.PROPOSAL_SCHULZE      = b'\x0d' # Schulze aka Beatpath (Condorcet method)
    const.PROPOSAL_SORTITION    = b'\x0e' # Sortition/Lottery
    const.PROPOSAL_MMP          = b'\x0f' # Mixed-Member Proportional (requires prior party elections to rank candidates)
    const.PROPOSAL_AVP          = b'\x10' # Alternative Vote Plus (requires prior party elections to rank candidates)
    const.VOTE_PLURALITY        = b'\x11'
    const.VOTE_RANKED           = b'\x12' # used for IRV, STV, Bucklin, Copeland, and Schulze ballots
    const.VOTE_APPROVAL         = b'\x13' # used just for Approval ballots
    const.VOTE_SCORE            = b'\x14' # used for CAV, Score, and STAR ballots
    const.VOTE_MMP              = b'\x15'
    const.VOTE_AVP              = b'\x16'
    const.NOMINATE              = b'\x17' # references a proposal block
    const.COLLECT_BALLOTS       = b'\x18' # references to ballot blocks collected by end of election; must precede a vote tally; can be chained together
    const.TALLY_OF_VOTES        = b'\x19' # references the previous COLLECT_BALLOTS block
    const.TALLY_NEW_ALG         = b'\x1a' # in case the TALLY_OF_VOTES was inconclusive, specifies new algorithm from first 10 characters and references previous block
    const.PAY_RESPECTS          = b'F' # used in reply to TALLY_OF_VOTES when quorum was not met
    const.DECLARE_PARTY         = b'\x1b' # declare one's party affiliation; first to declare for a party also gets to decide election method for leader(s)
    const.PARTY_MATTER          = b'\x1c' # use as first control character followed by hash of party name as prefix for anything else excluding \x1a, \x1b, or \x1c
    const.MESSAGE               = b'\x1d' # ECDHE message to another node
    const.BROADCAST             = b'\x1e' # public broadcast on one's block chain
    const.REFERENCE             = b'\x1f' # references any other block on any chain, e.g. for public comments
    const.OTHER                 = b'\x20' # used in genesis block before introducing the public key for the node

define_consts()

'''
    DEPRECATED
    Each block can contain one action. Each action is defined in the block body
    by using 2 bytes of control character data, followed by the relevant data.
    This can be made more efficient by combining into a single byte.
    Control characters:
        1st byte:   P for Proposal
                    V for Vote
                    N for Nominate
                    T for Tally of Votes
                    M for Message
                    B for Broadcast
                    R for Reply to Broadcast
                    F for Pay Respects
                    O for Other
        2nd byte:   P for Plurality
                    I for Instant Run-off/Alternative Vote
                    T for Single Transferable Vote
                    A for Approval Voting
                    B for Borda Count
                    D for Dowdall System (Nauru Count)
                    S for Score
                    Z for STAR (Score Then Automatic Runoff)
                    U for Schulze aka Beatpath (Condorcet method)
                    E for Copeland's Pairwise Aggregation (Condorcet method)
                    null to be ignored
'''


def get_control_char (code):
    control_chars = {
        'PROPOSAL_PLURALITY'    :   b'\x00', # First-past-the-post/bloc voting
        'PROPOSAL_IRV'          :   b'\x01', # Instant Run-off Vote/Alternative Vote
        'PROPOSAL_IRV_COOMBS'   :   b'\x02', # IRV with Coomb's Method
        'PROPOSAL_CONTINGENT'   :   b'\x03', # Contingent Vote/Top-Two IRV
        'PROPOSAL_STV_DROOP'    :   b'\x04', # Single Transferable Vote (Droop quota)
        'PROPOSAL_STV_HARE'     :   b'\x05', # Single Transferable Vote (Hare quota)
        'PROPOSAL_APPROVAL'     :   b'\x06', # Highest approval wins
        'PROPOSAL_CAV'          :   b'\x07', # Combined Approval Rating; highest score wins
        'PROPOSAL_BORDA'        :   b'\x08', # Ranked voting used in the Vatican
        'PROPOSAL_DOWDAL'       :   b'\x09', # Version of Borda used in Nauru
        'PROPOSAL_BUCKLIN'      :   b'\x0a', # Bucklin/Grand Junction System; ranked voting
        'PROPOSAL_SCORE'        :   b'\x0b', # Highest score wins
        'PROPOSAL_STAR'         :   b'\x0c', # Score Then Automatic Run-off
        'PROPOSAL_COPELAND'     :   b'\x0d', # Copeland's Pairwise Aggregation (Condorcet method); uses 2nd-order algorithm for tie-breaking
        'PROPOSAL_SCHULZE'      :   b'\x0e', # Schulze aka Beatpath (Condorcet method)
        'PROPOSAL_SORTITION'    :   b'\x0f', # Sortition/Lottery
        'PROPOSAL_MMP'          :   b'\x10', # Mixed-Member Proportional (requires prior party elections to rank candidates)
        'BALLOT_PLURALITY'      :   b'\x11',
        'BALLOT_RANKED'         :   b'\x12', # used for IRV, STV, Bucklin, Copeland, and Schulze ballots
        'BALLOT_APPROVAL'       :   b'\x13', # used just for Approval ballots
        'BALLOT_SCORE'          :   b'\x14', # used for CAV, Score, and STAR ballots
        'BALLOT_MMP'            :   b'\x15',
        'NOMINATE'              :   b'\x16', # references a proposal block
        'COLLECT_BALLOTS'       :   b'\x17', # references to ballot blocks collected by end of election; must precede a vote tally; can be chained together
        'TALLY_OF_VOTES'        :   b'\x18', # references the previous COLLECT_BALLOTS block
        'TALLY_NEW_ALG'         :   b'\x19', # in case the TALLY_OF_VOTES was inconclusive, specifies new algorithm from first 15 characters and references previous block
        'PAY_RESPECTS'          :   b'F', # used in reply to TALLY_OF_VOTES when quorum was not met
        'DECLARE_PARTY'         :   b'\x1a', # declare one's party affiliation; first to declare for a party also gets to decide election method for leader(s)
        'PARTY_MATTER'          :   b'\x1b', # use as first control character followed by hash of party name as prefix for anything else excluding \x1a, \x1b, or \x1c
        'MESSAGE'               :   b'\x1c', # ECDHE message to another node
        'BROADCAST'             :   b'\x1d', # public broadcast on one's block chain
        'REFERENCE'             :   b'\x1e', # references any other block on any chain, e.g. for public comments
        'OTHER'                 :   b'\x1f' # used in genesis block before introducing the public key for the node
    }

    if not code in control_chars:
        raise ValueError('Invalid code for get_control_char.')

    return control_chars[code]

def get_control_code (char):
    control_codes = {
        b'\x00' :   'PROPOSAL_PLURALITY',
        b'\x01' :   'PROPOSAL_IRV',
        b'\x02' :   'PROPOSAL_IRV_COOMBS',
        b'\x03' :   'PROPOSAL_STV_DROOP',
        b'\x04' :   'PROPOSAL_STV_HARE',
        b'\x05' :   'PROPOSAL_APPROVAL',
        b'\x06' :   'PROPOSAL_CAV',
        b'\x07' :   'PROPOSAL_BORDA',
        b'\x08' :   'PROPOSAL_DOWDAL',
        b'\x09' :   'PROPOSAL_BUCKLIN',
        b'\x0a' :   'PROPOSAL_SCORE',
        b'\x0b' :   'PROPOSAL_STAR',
        b'\x0c' :   'PROPOSAL_COPELAND',
        b'\x0d' :   'PROPOSAL_SCHULZE',
        b'\x0e' :   'PROPOSAL_SORTITION',
        b'\x0f' :   'PROPOSAL_MMP',
        b'\x10' :   'BALLOT_PLURALITY',
        b'\x11' :   'BALLOT_RANKED',
        b'\x12' :   'BALLOT_APPROVAL',
        b'\x13' :   'BALLOT_SCORE',
        b'\x14' :   'BALLOT_MMP',
        b'\x15' :   'NOMINATE',
        b'\x16' :   'COLLECT_BALLOTS',
        b'\x17' :   'TALLY_OF_VOTES',
        b'\x18' :   'TALLY_NEW_ALG',
        b'F'    :   'PAY_RESPECTS', # \x46
        b'\x19' :   'DECLARE_PARTY',
        b'\x1a' :   'PARTY_MATTER',
        b'\x1b' :   'MESSAGE',
        b'\x1c' :   'BROADCAST',
        b'\x1d' :   'REFERENCE',
        b'\x1e' :   'POLICY_ISSUE',
        b'\x20' :   'REQUIREMENT',
        b'\x21' :   'MEET_REQUIREMENT',
        b'\x22' :   'POLITICAL_CAPITAL',
        b'\x23' :   'MULTISIG',
        b'\x24' :   'CREATE',
        b'\x25' :   'TRANSFER',
        b'\x26' :   'DELEGATE',
        b'\x2' :   '',
        b'\x30' :   'OTHER'
    }

    if not char in control_codes:
        raise ValueError('Invalid char for get_control_code.')

    return control_codes[char]

'''
    Argument: body bytes (including control character)

    Output: dict {block_type:str, data:{...} or bytes}
'''
def unpack_block (body):
    # logic depends upon the kind of block
    control_code = get_control_code(body[0:1])

    # handle proposals
    if len(control_code) > 9 and control_code[0:9] == 'PROPOSAL_':
        # non-MMP
        if control_code[9:] != 'MMP':
            proposal = unpack_proposal(body[1:])
            proposal['election_method'] = control_code[9:]
            return {'block_type': 'PROPOSAL', 'data': proposal}
        else:
            proposal = unpack_mmp_proposal(body[1:])
            return {'block_type': 'PROPOSAL_MMP', 'data': proposal}

    # handle ballots
    if len(control_code) > 7 and control_code[0:7] == 'BALLOT_':
        # non-MMP
        if control_code[7:] != 'MMP':
            ballot = unpack_ballot(body[1:])
            ballot['election_method'] = control_code[7:]
            return {'block_type': 'BALLOT', 'data': ballot}
        else:
            ballot = unpack_mmp_ballot(body[1:])
            return {'block_type': 'BALLOT', 'data': ballot}

    # handle nominations
    if control_code == 'NOMINATE':
        nomination = unpack_nomination(body[1:])
        return {'block_type': 'NOMINATION', 'data': nomination}

    # handle ballot collection
    if control_code == 'COLLECT_BALLOTS':
        collection = unpack_collection_of_ballots(body[1:])
        return {'block_type': 'COLLECTION', 'data': collection}

    # handle tallies
    if len(control_code) > 6 and control_code[0:6] == 'TALLY_':
        tally = unpack_tally(body)
        return {'block_type': control_code, 'data': tally}

    # handle the meme
    if control_code == 'PAY_RESPECTS':
        respects = unpack_respects(body[1:])
        return {'block_type': 'PAY_RESPECTS', 'data': respects}

    # party affiliation
    if control_code == 'DECLARE_PARTY':
        party_declaration = unpack_declare_party(body[1:])
        return {'block_type': 'DECLARE_PARTY', 'data': party_declaration}

    # party matter; just recurse and return hierarchical structure
    if control_code == 'PARTY_MATTER':
        party_matter = unpack_block(body[1:])
        return {'block_type': 'PARTY_MATTER', 'data': party_matter}

    # direct message
    if control_code == 'MESSAGE':
        message = unpack_message(body[1:])
        return {'block_type': 'MESSAGE', 'data': message}

    # broadcast
    if control_code == 'BROADCAST':
        broadcast = unpack_broadcast(body[1:])
        return {'block_type': 'BROADCAST', 'data': broadcast}

    # reply to broadcast
    if control_code == 'REPLY_TO_BROADCAST':
        reply = unpack_reply_to_broadcast(body[1:])
        return {'block_type': 'REPLY_TO_BROADCAST', 'data': reply}

    # other
    if control_code == 'OTHER':
        return {'block_type': 'OTHER', 'data': body[1:]}

'''
    Arguments: election_method bytes, intro bytes, number_of_winners int,
                quorum_requirement int, candidates [bytes,...],
                start_time datetime, end_time datetime
    Important: election_method must be one of 'PLURALITY', 'IRV', 'IRV_COOMBS',
            'STV_DROOP', 'STV_HARE', 'APPROVAL', 'CAV', 'BORDA', 'DOWDAL',
            'BUCKLIN', 'SCORE', 'STAR', 'COPELAND', 'SCHULZE', 'SORTITION', or
            'MMP'.

    Proposes an election/referendum between all candidates of the specified
    election_method.

    Output: control_char (1 byte) +
            start_time (4 bytes) +
            end_time (4 bytes) +
            quorum_requirement (2 bytes) +
            number_of_winners (1 bytes) +
            number_of_candidates (1 byte) +
            number_bytes_intro (2 bytes) + intro +
            (for c in candidates: sha256(c) + number_bytes_c(int.to_bytes(2)) + c)
'''
def pack_proposal (election_method, intro, number_of_winners, quorum_requirement, candidates, start_time, end_time):
    # input validation
    if len(intro) > 65535:
        raise ValueError('intro data cannot be more than 65535 bytes long.')

    if len(candidates) > 255:
        raise ValueError('Maximum of 255 candidates per election.')

    if len(candidates) < 1:
        raise ValueError('At least 1 candidate must be nominated per election.')

    if not number_of_winners < len(candidates):
        raise ValueError('The number_of_winners must be less than the number of candidates.')

    if number_of_winners > 256 or number_of_winners < 1:
        raise ValueError('The number_of_winners must be between 1 and 255.')

    for i in range(0, len(candidates)):
        if len(candidates[i]) > 65535:
            raise ValueError('candidates['+str(i)+'] data cannot be more than 65535 bytes long.')

    # get control char and serialize metadata
    body = get_control_char('PROPOSAL_' + election_method)
    body += (int(start_time.timestamp())).to_bytes(4, byteorder='big')
    body += (int(end_time.timestamp())).to_bytes(4, byteorder='big')
    body += quorum_requirement.to_bytes(2, byteorder='big')
    body += number_of_winners.to_bytes(1, byteorder='big')
    body += bytes([len(candidates)])

    # add intro
    body += len(intro).to_bytes(2, byteorder='big') + intro

    # add all candidates to the body
    for i in range(0, len(candidates)):
        hash = sha256(candidates[i], encoder=RawEncoder)
        body += hash + (len(candidates[i])).to_bytes(2, byteorder='big') + candidates[i]

    return body

'''
    Arguments: body bytes (stripped of control character)

    Output: dict {start_time:datetime, end_time:datetime, quorum_requirement:int, number_of_candidates:int, number_of_winners:int, intro:bytes, candidates:[[hash, candidate_bytes],...]}
'''
def unpack_proposal (body):
    # parse metadata
    start_time = datetime.fromtimestamp(int.from_bytes(body[0:4], byteorder='big'))
    end_time = datetime.fromtimestamp(int.from_bytes(body[4:8], byteorder='big'))
    quorum_requirement = int.from_bytes(body[8:10], byteorder='big')
    number_of_winners = int.from_bytes(body[10:11], byteorder='big')
    number_of_candidates = int.from_bytes(body[11:12], byteorder='big')

    # parse intro
    intro_size = int.from_bytes(body[12:14], byteorder='big')
    intro = body[14:14+intro_size]

    # parse candidates
    candidates_bytes, candidates_list = body[14+intro_size:len(body)], []
    i, j = 0, len(candidates_bytes)
    while i < j:
        # first 32 bytes are hash
        candidate_hash = tohex(candidates_bytes[i:i+32])
        i += 32
        # next 2 bytes define length of candidate data
        candidate_length = int.from_bytes(candidates_bytes[i:i+2], byteorder='big')
        i += 2
        # the next candidate_length bytes are the candidate data
        candidates_list.append((candidate_hash, candidates_bytes[i:i+candidate_length]))
        i += candidate_length

    return {'start_time': start_time, 'end_time': end_time, 'quorum_requirement': quorum_requirement, 'number_of_candidates': number_of_candidates, 'number_of_winners': number_of_winners, 'intro': intro, 'candidates': candidates_list}

'''
    Arguments: intro bytes, number_of_winners int, quorum_requirement int,
                candidates [bytes,...], start_time datetime, end_time datetime

    Proposes a plurality election between all candidates. Only the number_of_winners
    candidates with the most votes by the time that end_time is reached win.
    Note that a majority is not needed to win this type of election. Each voter
    must vote for number_of_winners candidates for their ballot to be valid.
    For the result to be valid, at least quorum_requirement votes must be
    collected. A maximum of 255 candidates can be proposed, but more can be
    nominated and voted for.

    Output: const.PROPOSAL_PLURALITY +
            start_time (4 bytes) +
            end_time (4 bytes) +
            quorum_requirement (2 bytes) +
            number_of_winners (1 byte) +
            number_of_candidates (1 byte) +
            number_bytes_intro (2 bytes) + intro +
            (for c in candidates: sha256(c) + number_bytes_c(int.to_bytes(2)) + c)
'''
def pack_plurality_proposal (intro, number_of_winners, quorum_requirement, candidates, start_time, end_time):
    # input validation
    if len(intro) > 65535:
        raise ValueError('intro data cannot be more than 65535 bytes long.')

    if len(candidates) > 255:
        raise ValueError('Maximum of 255 candidates per election.')

    if len(candidates) < 1:
        raise ValueError('At least 1 candidate must be nominated per election.')

    if not number_of_winners < len(candidates):
        raise ValueError('The number_of_winners must be less than the number of candidates.')

    for i in range(0, len(candidates)):
        if len(candidates[i]) > 65535:
            raise ValueError('candidates['+str(i)+'] data cannot be more than 65535 bytes long.')

    # create body
    body = const.PROPOSAL_PLURALITY
    body += (int(start_time.timestamp())).to_bytes(4, byteorder='big')
    body += (int(end_time.timestamp())).to_bytes(4, byteorder='big')
    body += quorum_requirement.to_bytes(2, byteorder='big')
    body += bytes([number_of_winners])
    body += bytes([len(candidates)])
    body += (len(intro)).to_bytes(2, byteorder='big') + intro
    # print('pack_plurality_proposal number_of_winners bytes([number_of_winners])', number_of_winners, bytes([number_of_winners]))
    # print('pack_plurality_proposal len(candidates) bytes([len(candidates)])', len(candidates), bytes([len(candidates)]))

    # add all candidates to the body
    for i in range(0, len(candidates)):
        hash = sha256(candidates[i], encoder=RawEncoder)
        body += hash + (len(candidates[i])).to_bytes(2, byteorder='big') + candidates[i]

    return body

'''
    Arguments: body bytes (stripped of control character)

    Output: dict {start_time:datetime, end_time:datetime, quorum_requirement:int, number_of_candidates:int, number_of_winners:int, intro:bytes, candidates:[[hash, candidate_bytes],...]}
'''
def unpack_plurality_proposal (body):
    # parse metadata
    start_time = datetime.fromtimestamp(int.from_bytes(body[0:4], byteorder='big'))
    end_time = datetime.fromtimestamp(int.from_bytes(body[4:8], byteorder='big'))
    quorum_requirement = int.from_bytes(body[8:10], byteorder='big')
    number_of_winners = int.from_bytes(body[10:11], byteorder='big')
    number_of_candidates = int.from_bytes(body[11:12], byteorder='big')

    # parse intro
    intro_size = int.from_bytes(body[12:14], byteorder='big')
    intro = body[14:14+intro_size]

    # parse candidates
    candidates_bytes, candidates_list = body[14+intro_size:len(body)], []
    i, j = 0, len(candidates_bytes)
    while i < j:
        # first 32 bytes are hash
        candidate_hash = tohex(candidates_bytes[i:i+32])
        i += 32
        # next 2 bytes define length of candidate data
        candidate_length = int.from_bytes(candidates_bytes[i:i+2], byteorder='big')
        i += 2
        # the next candidate_length bytes are the candidate data
        candidates_list.append((candidate_hash, candidates_bytes[i:i+candidate_length]))
        i += candidate_length

    return {'start_time': start_time, 'end_time': end_time, 'quorum_requirement': quorum_requirement, 'number_of_candidates': number_of_candidates, 'number_of_winners': number_of_winners, 'intro': intro, 'candidates': candidates_list}

'''
    Arguments: intro bytes, quorum_requirement int, candidates [bytes,...],
                start_time datetime, end_time datetime

    Proposes an instant run-off election/referendum between all candidates. If
    fewer than three candidates are nominated in total, it becomes a plurality
    election/referendum.

    Output: const.PROPOSAL_IRV +
            start_time (4 bytes) +
            end_time (4 bytes) +
            quorum_requirement (2 bytes) +
            number_of_candidates (1 byte) +
            number_bytes_intro (2 bytes) + intro +
            (for c in candidates: sha256(c) + number_bytes_c(int.to_bytes(2)) + c)
'''
def pack_irv_proposal (intro, quorum_requirement, candidates, start_time, end_time):
    # input validation
    if len(intro) > 65535:
        raise ValueError('intro data cannot be more than 65535 bytes long.')

    if len(candidates) > 255:
        raise ValueError('Maximum of 255 candidates per election.')

    if len(candidates) < 1:
        raise ValueError('At least 1 candidate must be nominated per election.')

    for i in range(0, len(candidates)):
        if len(candidates[i]) > 65535:
            raise ValueError('candidates['+str(i)+'] data cannot be more than 65535 bytes long.')

    # create body
    body = const.PROPOSAL_IRV + (int(start_time.timestamp())).to_bytes(4, byteorder='big')
    body += (int(end_time.timestamp())).to_bytes(4, byteorder='big')
    body += quorum_requirement.to_bytes(2, byteorder='big')
    body += bytes([len(candidates)])
    body += (len(intro)).to_bytes(2, byteorder='big') + intro

    # add all candidates to the body
    for i in range(0, len(candidates)):
        hash = sha256(candidates[i], encoder=RawEncoder)
        body += hash + (len(candidates[i])).to_bytes(2, byteorder='big') + candidates[i]

    return body

'''
    Arguments: body bytes (stripped of control character)

    Output: dict {start_time:datetime, end_time:datetime, quorum_requirement:int, number_of_candidates:int, intro:bytes, candidates:[[hash, candidate_bytes],...]}
'''
def unpack_irv_proposal (body):
    # parse metadata
    start_time = datetime.fromtimestamp(int.from_bytes(body[0:4], byteorder='big'))
    end_time = datetime.fromtimestamp(int.from_bytes(body[4:8], byteorder='big'))
    quorum_requirement = int.from_bytes(body[8:10], byteorder='big')
    number_of_candidates = int.from_bytes(body[10:11], byteorder='big')

    # parse intro
    intro_size = int.from_bytes(body[11:13], byteorder='big')
    intro = body[13:13+intro_size]

    # parse candidates
    candidates_bytes, candidates_list = body[13+intro_size:len(body)], []
    i, j = 0, len(candidates_bytes)
    while i < j:
        # first 32 bytes are hash
        candidate_hash = tohex(candidates_bytes[i:i+32])
        i += 32
        # next 2 bytes define length of candidate data
        candidate_length = int.from_bytes(candidates_bytes[i:i+2], byteorder='big')
        i += 2
        # the next candidate_length bytes are the candidate data
        candidates_list.append((candidate_hash, candidates_bytes[i:i+candidate_length]))
        i += candidate_length

    return {'start_time': start_time, 'end_time': end_time, 'quorum_requirement': quorum_requirement, 'number_of_candidates': number_of_candidates, 'intro': intro, 'candidates': candidates_list}

'''
    Arguments: intro bytes, quorum_requirement int, candidates [bytes,...],
                start_time datetime, end_time datetime

    Proposes an instant run-off election/referendum between all candidates. Same
    serialization as normal IRV but with a different control character.

    Output: const.PROPOSAL_IRV_COOMBS + start_time (4 bytes) +
            end_time (4 bytes) +
            quorum_requirement (2 bytes) +
            number_of_candidates (1 byte) +
            number_bytes_intro (2 bytes) + intro +
            (for c in candidates: sha256(c) + number_bytes_c(int.to_bytes(2)) + c)
'''
def pack_irv_coombs_proposal (intro, quorum_requirement, candidates, start_time, end_time):
    # same thing, but with a different control character
    return const.PROPOSAL_IRV_COOMBS + pack_irv_proposal(intro, quorum_requirement, candidates, start_time, end_time)[1:]

'''
    Arguments: body bytes (stripped of control characters)

    Output: dict {start_time:datetime, end_time:datetime, quorum_requirement:int, number_of_candidates:int, intro:bytes, candidates:[[hash, candidate_bytes],...]}
'''
def unpack_irv_coombs_proposal (body):
    # same as regular IRV serialization
    return unpack_irv_proposal(body)

'''
    Arguments:  intro bytes, number_of_winners int, quorum_requirement int,
                candidates [bytes, ...], start_time datetime, end_time datetime

    Single transferable vote, using Droop quota. Output is basically the same as
    for plurality, except with different control character.

    Output: const.PROPOSAL_STV_DROOP + start_time (4 bytes) +
            end_time (4 bytes) +
            quorum_requirement (2 bytes) +
            number_of_winners (1 byte) +
            number_bytes_intro (2 bytes) + intro +
            (for c in candidates: sha256(c) + number_bytes_c + c)
'''
def pack_stv_proposal (intro, number_of_winners, quorum_requirement, candidiates, start_time, end_time):
    return const.PROPOSAL_STV_DROOP + pack_plurality_proposal(intro, number_of_winners, quorum_requirement, candidates, start_time, end_time)[1:]

'''
    Arguments: proposal_ref_hash bytes, candidate_hashes [bytes,...]

    Output: const.VOTE_PLURALITY + proposal_ref_hash +
            (for h in candidate_hashes: h)
'''
def pack_plurality_ballot (proposal_ref_hash, candidate_hashes):
    body = const.VOTE_PLURALITY + proposal_ref_hash
    for i in range(0, len(candidate_hashes)):
        if len(candidate_hashes[i]) < 32:
            raise ValueError('Candidate hash must be 32 bytes long. Candidate hash ', i, ' was only ', len(candidate_hashes[i]))
        body += candidate_hashes[i]

    return body

'''
    Arguments: body bytes (stripped of control characters)

    Output: dict {proposal_ref_hash:bytes, candidate_hashes:[bytes,...]}
'''
def unpack_plurality_ballot (body):
    proposal_ref_hash = body[0:32]
    candidate_hashes_bytes = body[32:len(body)]
    candidate_hashes = []
    i, j = 0, len(candidate_hashes_bytes)
    while i < j:
        candidate_hashes.append(candidate_hashes_bytes[i:i+32])
        i += 32

    return {'proposal_ref_hash': proposal_ref_hash, 'candidate_hashes': candidate_hashes}

'''
    Arguments: proposal_ref_hashbytes, candidate_hashes [bytes,...]

    Output: const.VOTE_RANKED + proposal_ref_hash + for (h in candidate_hashes h)
'''
def pack_ranked_ballot (proposal_ref_hash, candidate_hashes):
    body = const.VOTE_RANKED + proposal_ref_hash
    for i in range(0, len(candidate_hashes)):
        if len(candidate_hashes[i]) < 32:
            raise ValueError('Candidate hash must be 32 bytes long. Candidate hash ', i, ' was only ', len(candidate_hashes[i]))
        body += candidate_hashes[i]

    return body

'''
    Argument: body bytes (stripped of control characters)

    Output: dict {proposal_ref_hash:bytes, candidate_hashes:[bytes,...]}
'''
def unpack_ranked_ballot (body):
    proposal_ref_hash = body[0:32]
    candidate_hashes_bytes = body[32:len(body)]
    candidate_hashes = []
    i, j = 0, len(candidate_hashes_bytes)
    while i < j:
        candidate_hashes.append(candidate_hashes_bytes[i:i+32])
        i += 32

    return {'proposal_ref_hash': proposal_ref_hash, 'candidate_hashes': candidate_hashes}

'''
    Arguments: proposal_ref_hash bytes, candidate_hashes [bytes,...]

    Output: const.VOTE_IRV + proposal_ref_hash + for (h in candidate_hashes: h)
'''
def pack_irv_ballot (proposal_ref_hash, candidate_hashes):
    return pack_ranked_ballot(proposal_ref_hash, candidate_hashes)

'''
    Argument: body bytes (stripped of control characters)

    Output: dict {proposal_ref_hash:bytes, candidate_hashes:[bytes,...]}
'''
def unpack_irv_ballot(body):
    return unpack_ranked_ballot(body)


'''
    Arguments:  collection_ref_hash bytes,
        result dict {
            tally:OrderedDict {candidate_hash:votes int},
            winners:[winner_hash bytes,...],
            invalid_ballots:int,
            invalid_votes:int,
            valid_ballots:int,
            valid_votes:int,
            meets_quorum:bool
        }

    Output: const.TALLY_OF_VOTES + const.PROPOSAL_PLURALITY + collection_ref_hash +
        meets_quorum (\x00 or \x01) + n_ties (1 byte)
        valid_ballots (2 bytes) + invalid_ballots (2 bytes) +
        valid_votes (2 bytes) + invalid_votes (2 bytes) +
        n_winners (1 byte) + (for w in winners: w (32 bytes)) +
        n_candidates (2 bytes) + (for ch, v in tally: ch (32 bytes) + v (2 bytes))
'''
def pack_plurality_tally (collection_ref_hash, result):
    body = const.TALLY_OF_VOTES + const.PROPOSAL_PLURALITY + collection_ref_hash
    body += (b'\x01' if result['meets_quorum'] else b'\x00')
    body += result['ties'].to_bytes(1, byteorder='big')
    body += result['valid_ballots'].to_bytes(2, byteorder='big')
    body += result['invalid_ballots'].to_bytes(2, byteorder='big')
    body += result['valid_votes'].to_bytes(2, byteorder='big')
    body += result['invalid_votes'].to_bytes(2, byteorder='big')

    # winners
    body += len(result['winners']).to_bytes(1, byteorder='big')
    for w in result['winners']:
        body += w

    # n_candidates
    body += len(result['tally']).to_bytes(2, byteorder='big')

    # each one
    for candidate_hash, votes in result['tally'].items():
        body += candidate_hash + votes.to_bytes(2, byteorder='big')

    return body

'''
    Argument: body (stripped of control characters)

    Output: dict {
        collection_ref_hash:bytes,
        tally:OrderedDict {candidate_hash:votes int},
        winners:[winner_hash bytes,...],
        invalid_ballots:int,
        invalid_votes:int,
        valid_ballots:int,
        valid_votes:int,
        meets_quorum:bool
    }
'''
def unpack_plurality_tally (body):
    # metadata
    collection_ref_hash = body[0:32]
    meets_quorum = (body[32:33] == b'\x01')
    ties = int.from_bytes(body[33:34], byteorder='big')
    valid_ballots = int.from_bytes(body[34:36], byteorder='big')
    invalid_ballots = int.from_bytes(body[36:38], byteorder='big')
    valid_votes = int.from_bytes(body[38:40], byteorder='big')
    invalid_votes = int.from_bytes(body[40:42], byteorder='big')

    # winners
    winners = []
    n_winners = int.from_bytes(body[42:43], byteorder='big')
    # print('unpack_plurality_tally n_winners', n_winners)
    winner_bytes_end = 43 + n_winners * 32
    winner_bytes = body[43:winner_bytes_end]

    for i in range(0, n_winners):
        start, end = i*32, i*32+32
        winners.append(winner_bytes[start:end])

    # tally
    tally = {}
    n_candidates = int.from_bytes(body[winner_bytes_end:winner_bytes_end+2], byteorder='big')
    tally_bytes_end = winner_bytes_end + 2 + n_candidates * 34
    tally_bytes = body[winner_bytes_end+2:tally_bytes_end]

    for i in range(0, n_candidates):
        hash_begin, hash_end, votes_end = i*34, i*34+32, i*34+34
        candidate_hash = tally_bytes[hash_begin:hash_end]
        candidate_votes = int.from_bytes(tally_bytes[hash_end:votes_end], byteorder='big')
        tally[candidate_hash] = candidate_votes

    def comp_candidates(c):
        return c[1]

    tally = OrderedDict(sorted(tally.items(), key=comp_candidates, reverse=True))

    return {
        'collection_ref_hash': collection_ref_hash,
        'tally': tally,
        'winners': winners,
        'valid_ballots': valid_ballots,
        'invalid_ballots': invalid_ballots,
        'valid_votes': valid_votes,
        'invalid_votes': invalid_votes,
        'meets_quorum': meets_quorum,
        'ties': ties
    }


'''
    Arguments:  collection_ref_hash bytes,
        result dict {
            tally:[OrderedDict {candidate_hash:highest_preference_votes int, ...}, ...],
            winner:winner_hash bytes,
            valid_ballots:int,
            invalid_ballots:int,
            exhausted_ballots:int,
            meets_quorum:bool
        }

    Output: const.TALLY_OF_VOTES + const.PROPOSAL_IRV + collection_ref_hash +
        meets_quorum (\x00 or \x01) +
        valid_ballots (2 bytes) + invalid_ballots (2 bytes) + exhausted_ballots (2 bytes) +
        winner (32 bytes) +
        n_rounds (1 byte) +
        (for round in tally:
            n_candidates (2 bytes) +
            (for ch, v in round: ch (32 bytes) + v (2 bytes))
        )
'''
def pack_irv_tally (collection_ref_hash, result):
    # metadata
    body = const.TALLY_OF_VOTES + const.PROPOSAL_IRV + collection_ref_hash
    body += (b'\x01' if result['meets_quorum'] else b'\x00')
    body += result['valid_ballots'].to_bytes(2, byteorder='big')
    body += result['invalid_ballots'].to_bytes(2, byteorder='big')
    body += result['exhausted_ballots'].to_bytes(2, byteorder='big')
    body += result['winner']

    # n_rounds
    body += len(result['tally']).to_bytes(1, byteorder='big')

    # each round
    for i in range(0, len(result['tally'])):
        # n_candidates
        body += len(result['tally'][i]).to_bytes(2, byteorder='big')

        # each one
        for candidate_hash, votes in result['tally'][i].items():
            body += candidate_hash + votes.to_bytes(2, byteorder='big')

    return body

'''
    Argument: body bytes (stripped of control characters)

    Output: dict {
        collection_ref_hash:bytes,
        winner:winner_hash bytes,
        meets_quorum:bool
        valid_ballots:int,
        invalid_ballots:int,
        exhausted_ballots:int,
        tally:[OrderedDict {candidate_hash:highest_preference_votes int, ...}, ...],
    }
'''
def unpack_irv_tally (body):
    # metadata
    collection_ref_hash = body[0:32]
    meets_quorum = (body[32:33] == b'\x01')
    valid_ballots = int.from_bytes(body[33:35], byteorder='big')
    invalid_ballots = int.from_bytes(body[35:37], byteorder='big')
    exhausted_ballots = int.from_bytes(body[37:39], byteorder='big')
    winner = body[39:71]

    # unpack tally; set control structure variables
    n_rounds = int.from_bytes(body[71:72], byteorder='big')
    tally_bytes = body[72:]
    tally = []

    # for each round
    for r in range(0, n_rounds):
        # start with empty round_tally
        round_tally = OrderedDict({})
        # parse number of candidates
        n_candidates = int.from_bytes(tally_bytes[0:2], byteorder='big')
        # get the bytes for the current round
        round_bytes = tally_bytes[2:2+n_candidates*34]
        # trim the remainder
        tally_bytes = tally_bytes[2+n_candidates*34:]

        # get the hash of each candidate and set its vote count
        for c in range(0, n_candidates):
            hash_begin, hash_end, votes_end = c*34, c*34+32, c*34+34
            candidate_hash = round_bytes[hash_begin:hash_end]
            round_tally[candidate_hash] = int.from_bytes(round_bytes[hash_end:votes_end], byteorder='big')

        # add to the total tally
        tally.append(round_tally)

    return {'collection_ref_hash': collection_ref_hash, 'winner': winner, 'meets_quorum': meets_quorum, 'valid_ballots': valid_ballots, 'invalid_ballots': invalid_ballots, 'exhausted_ballots': exhausted_ballots, 'tally': tally}

'''
    Arguments:  collection_ref_hash bytes,
        result dict {
            tally:[OrderedDict {candidate_hash:highest_preference_votes int, ...}, ...],
            winner:winner_hash bytes,
            valid_ballots:int,
            invalid_ballots:int,
            exhausted_ballots:int,
            meets_quorum:bool
        }

    Output: const.TALLY_OF_VOTES + const.PROPOSAL_IRV_COOMBS + collection_ref_hash +
        meets_quorum (\x00 or \x01) +
        valid_ballots (2 bytes) + invalid_ballots (2 bytes) + exhausted_ballots (2 bytes) +
        winner (32 bytes) +
        n_rounds (1 byte) +
        (for round in tally:
            n_candidates (2 bytes) +
            (for ch, v in round: ch (32 bytes) + v (2 bytes))
        )
'''
def pack_irv_coombs_tally (collection_ref_hash, result):
    # same as normal IRV tally but with different control character
    return const.TALLY_OF_VOTES + const.PROPOSAL_IRV_COOMBS + pack_irv_tally(collection_ref_hash, result)[2:]

'''
    Argument: body bytes (stripped of control characters)

    Output: dict {
        collection_ref_hash:bytes,
        winner:winner_hash bytes,
        meets_quorum:bool
        valid_ballots:int,
        invalid_ballots:int,
        exhausted_ballots:int,
        tally:[OrderedDict {candidate_hash:highest_preference_votes int, ...}, ...],
    }
'''
def unpack_irv_coombs_tally (body):
    # same as unpacking a normal IRV tally
    return unpack_irv_tally(body)
