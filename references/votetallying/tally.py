from collections import OrderedDict
import binascii
import random

def tohex (text):
    return binascii.hexlify(text)

'''
    Argument: dict {candidate_hash bytes:votes int,...}

    Output: OrderedDict {candidate_hash bytes:votes int,...}
'''
def sort_candidates(tally):
    def comp_candidates(c):
        return c[1]

    return OrderedDict(sorted(tally.items(), key=comp_candidates, reverse=True))


'''
    Standard fisher yates shuffle for a list.
'''
def fisheryates(arr):
    for i in range(len(arr) - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

'''
    Arguments: ballots list [ballot list,...], candidates list [candidate_hash bytes,...]

    This goes through each ballot, attaches any write-ins to the candidates list,
    and puts unranked candidiates at the bottom of each ballot in a random order.

    Output: ballots list, candidates list
'''
def normalize_ranked_ballots(ballots, candidates):
    # add write-in candidates
    for b in ballots:
        for c in b:
            if c not in candidates:
                candidates.append(c)

    for b in ballots:
        # compile unranked candidates
        unranked = []
        for c in candidates:
            if c not in b:
                unranked.append(c)

        # shuffle unranked candidates
        unranked = fisheryates(unranked)

        # append unranked candidates to the ballot
        b[len(b):] = unranked

    # return noramlized ballots and candidates list
    return ballots, candidates

'''
    Arguments:  number_of_winners int, candidates [hash bytes,...],
                ballots [[hash bytes,...],...], quorum_requirement int

    This is intended to tally ballots for both FPTP and plurality-at-large/multiple
    non-transferable vote/bloc voting.

    Output: dict {
        tally:OrderedDict {candidate_hash:votes int},
        winners:[winner_hash bytes,...],
        invalid_ballots:int,
        invalid_votes:int,
        valid_ballots:int,
        valid_votes:int,
        meets_quorum:bool
    }
'''
def plurality (number_of_winners, candidates, ballots, quorum_requirement):
    tally = {}
    invalid_ballots = 0
    invalid_votes = 0
    valid_ballots = 0
    valid_votes = 0

    for c in candidates:
        tally[c] = 0

    # tally ballots
    for v in ballots:
        # for MNTV
        if number_of_winners > 1:
            # make sure it is a list
            if type(v) == type(b's'):
                v = [v]

            # only process valid ballots
            if not len(v) > number_of_winners:
                ballot_valid = True
                for i in range(0, len(v)):
                    # only process valid votes
                    if type(v[i]) == type(b's') and v[i] in tally:
                        tally[v[i]] += 1
                        valid_votes += 1
                    else:
                        invalid_votes += 1
                        ballot_valid = False

                # stats about whether or not ballot was valid
                if ballot_valid:
                    valid_ballots += 1
                else:
                    invalid_ballots += 1
            else:
                invalid_ballots += 1
        # for FPTP
        else:
            # only process valid ballots
            if type(v) == type(b's'):
                tally[v] += 1
                valid_ballots += 1
            else:
                invalid_ballots += 1


    # rank candidates
    tally = sort_candidates(tally)
    tally_list = []

    # determine winners
    winners = []
    i = 0
    for key,value in tally.items():
        tally_list.append((key, value))
        # print('tally.plurality tally_list.append((key, value))', (key, value))
        if i < number_of_winners:
            winners.append(key)
        i += 1

    # handle ties
    n_ties = 0
    # print('tally.plurality tally_list', tally_list)
    a = tally[winners[-1:][0]]
    b = tally_list[len(winners)][1]
    while a == b and len(winners) > 0:
        winners = winners[:-1]
        a = tally[winners[-1:][0]]
        b = tally_list[len(winners)][1]
        n_ties += 1

    return {
        'tally': tally,
        'winners': winners,
        'invalid_ballots': invalid_ballots,
        'invalid_votes': invalid_votes,
        'valid_ballots': valid_ballots,
        'valid_votes': valid_votes,
        'ties': n_ties,
        'meets_quorum': valid_ballots >= quorum_requirement
    }

'''
    Arguments:  candidates [hash bytes, ...],
                ballots [[hash bytes, ...], ...],
                quorum_requirement int

    The tally will be a list with an OrderedDict for each successive elimination
    round. Candidates with fewest highest-preference votes are eliminated and
    those ballots reassigned until one candidate has a majority of highest-
    preference votes.

    Output: dict {
        tally:list [OrderedDict {candidate_hash:votes int}, ...],
        winner:winner_hash bytes,
        invalid_ballots:int,
        valid_ballots:int,
        exhausted_ballots:int,
        meets_quorum:bool
    }
'''
def irv (candidates, ballots, quorum_requirement):
    tally = []
    eliminated_candidates = []
    total_ballots = len(ballots)
    invalid_ballots = 0
    exhausted_ballots = 0
    winner = ''
    winner_found = False
    round = 0

    # until a winner is found
    while not winner_found:
        # set up new tally for each round
        round_tally = {}
        counted_ballots = []
        total_votes = 0
        for c in candidates:
            round_tally[c] = 0

        # go through each ballot and tally to its highest-preference candidate
        for b in ballots:
            if len(b) < 1:
                if round == 0:
                    invalid_ballots += 1
                else:
                    exhausted_ballots += 1
            else:
                if b[0] not in candidates:
                    invalid_ballots += 1
                else:
                    counted_ballots.append(b)
                    round_tally[b[0]] += 1

        # sort candidiates
        round_tally = sort_candidates(round_tally)

        # add round_tally to full tally
        tally.append(round_tally)

        # get total and set up for elimination
        for k in round_tally:
            total_votes += round_tally[k]
        worst_candidate = ['total', total_votes]


        # inspect each candidate's tally
        for c in round_tally:
            # see if someone has a majority of highest-preference votes
            if round_tally[c] > int(total_votes / 2):
                winner_found = True
                winner = c
                break

            # also find the candidate with fewest highest-preference votes
            if round_tally[c] < worst_candidate[1]:
                worst_candidate = [c, round_tally[c]]

        # check for ties for worst_candidate
        ties_for_worst = []
        for c in round_tally:
            if c != worst_candidate[0] and round_tally[c] == worst_candidate[1]:
                ties_for_worst.append(c)

        # eliminate worst_candidate and ties_for_worst
        eliminated_candidates.append(worst_candidate[0])
        for i in range(0, len(ties_for_worst)):
            eliminated_candidates.append(ties_for_worst[i])

        # remove eliminated_candidates from candidates
        for c in eliminated_candidates:
            if c in candidates:
                candidates.remove(c)

        # stop if all candidates eliminated due to tie
        if len(candidates) == 0:
            break

        # re-assign ballots
        next_round_ballots = []
        for b in counted_ballots:
            ballot = []
            for c in b:
                # keep only votes for uneliminated candidates
                if c not in eliminated_candidates:
                    ballot.append(c)
            # add to next round if the ballot is not exhausted
            if len(ballot) > 0:
                next_round_ballots.append(ballot)
            else:
                exhausted_ballots += 1

        # set up for next round
        ballots = next_round_ballots

    # final tabulations
    valid_ballots = total_ballots - invalid_ballots
    meets_quorum = valid_ballots - exhausted_ballots > quorum_requirement
    if not winner_found:
        winner = 'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    # return statement
    return {'tally': tally, 'winner': winner, 'invalid_ballots': invalid_ballots, 'valid_ballots': valid_ballots, 'exhausted_ballots': exhausted_ballots, 'meets_quorum': meets_quorum}

'''
    Arguments:  candidates [hash bytes, ...],
                ballots [[hash bytes, ...], ...],
                quorum_requirement int

    The tally will be a list with an OrderedDict for each successive elimination
    round. Candidates with most lowest-preference votes are eliminated and
    those ballots reassigned until one candidate has a majority of highest-
    preference votes.

    Output: dict {
        tally:list [OrderedDict {candidate_hash:votes int}, ...],
        winner:winner_hash bytes,
        invalid_ballots:int,
        valid_ballots:int,
        exhausted_ballots:int,
        meets_quorum:bool
    }
'''
def irv_coombs (candidates, ballots, quorum_requirement):
    tally = []
    eliminated_candidates = []
    total_ballots = len(ballots)
    invalid_ballots = 0
    exhausted_ballots = 0
    winner = ''
    winner_found = False
    round = 0

    # until a winner is found
    while not winner_found:
        # set up new tally for each round
        round_tally = {}
        round_tally_lowest_pref = {}
        counted_ballots = []
        total_votes = 0
        for c in candidates:
            round_tally[c] = 0
            round_tally_lowest_pref[c] = 0

        # go through each ballot and tally its highest- and lowest-preference candidates
        for b in ballots:
            if len(b) < len(candidates):
                invalid_ballots += 1
            if len(b) < 1:
                if round == 0:
                    invalid_ballots += 1
                else:
                    exhausted_ballots += 1
            else:
                # handle ties
                first_choices_valid = True
                last_choices_valid = True
                if type(b[0]) is list:
                    for c in b[0]:
                        if c not in candidates:
                            first_choices_valid = False
                elif b[0] not in candidates:
                    first_choices_valid = False

                if type(b[-1]) is list:
                    for c in b[-1]:
                        if c not in candidates:
                            last_choices_valid = False
                elif b[-1] not in candidates:
                    last_choices_valid = False

                if not first_choices_valid or not last_choices_valid:
                    invalid_ballots += 1
                else:
                    counted_ballots.append(b)
                    if type(b[0]) is list:
                        for c in b[0]:
                            round_tally[c] += 1
                            # round_tally[c] += 1 / len(b[0])
                    else:
                        round_tally[b[0]] += 1

                    if type(b[-1]) is list:
                        for c in b[-1]:
                            round_tally_lowest_pref[c] += 1
                            # round_tally_lowest_pref[c] += 1 / len(b[-1])
                    else:
                        round_tally_lowest_pref[b[-1]] += 1

        # sort candidiates
        round_tally = sort_candidates(round_tally)
        round_tally_lowest_pref = sort_candidates(round_tally_lowest_pref)

        # add round_tally to full tally
        tally.append([round_tally, round_tally_lowest_pref])

        # get total and set up for elimination
        for k in round_tally:
            total_votes += round_tally[k]
        worst_candidate = ['none', 0]


        # inspect each candidate's tally
        for c in round_tally:
            # see if someone has a majority of highest-preference votes
            if round_tally[c] > int(total_votes / 2):
                winner_found = True
                winner = c
                break

            # also find the candidate with greatest lowest-preference votes
            if round_tally_lowest_pref[c] > worst_candidate[1]:
                worst_candidate = [c, round_tally_lowest_pref[c]]

        # check for ties for worst_candidate
        ties_for_worst = []
        for c in round_tally_lowest_pref:
            if c != worst_candidate[0] and round_tally_lowest_pref[c] == worst_candidate[1]:
                ties_for_worst.append(c)

        # eliminate worst_candidate and ties_for_worst
        eliminated_candidates.append(worst_candidate[0])
        for i in range(0, len(ties_for_worst)):
            eliminated_candidates.append(ties_for_worst[i])

        # remove eliminated_candidates from candidates
        for c in eliminated_candidates:
            if c in candidates:
                candidates.remove(c)

        # stop if all candidates eliminated due to tie
        if len(candidates) == 0:
            break

        # remove eliminated candidates from ballots
        next_round_ballots = []
        for b in counted_ballots:
            ballot = []
            for rank in b:
                # traverse ties
                if type(rank) is list:
                    # remove eliminated candidates from rank
                    nonrank = [c for c in rank if c in eliminated_candidates]
                    for n in nonrank:
                        rank.remove(n)
                    # add to ballot
                    if len(rank) == 1:
                        ballot.append(rank[0])
                    elif len(rank) > 1:
                        ballot.append(rank)
                else:
                    # keep only votes for uneliminated candidates
                    if rank not in eliminated_candidates:
                        ballot.append(rank)

            # add to next round if the ballot is not exhausted
            if len(ballot) > 0:
                next_round_ballots.append(ballot)
            else:
                exhausted_ballots += 1

        # set up for next round
        ballots = next_round_ballots

    # final tabulations
    valid_ballots = total_ballots - invalid_ballots
    meets_quorum = valid_ballots - exhausted_ballots > quorum_requirement
    if not winner_found:
        winner = 'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    # return statement
    return {'tally': tally, 'winner': winner, 'invalid_ballots': invalid_ballots, 'valid_ballots': valid_ballots, 'exhausted_ballots': exhausted_ballots, 'meets_quorum': meets_quorum}


'''
    Arguments:  candidates [hash bytes, ...],
                ballots [[hash bytes, ...], ...],
                seats_available int,
                quorum_requirement int

    This uses the Droop quota rather than Hare:
        total_votes / (seats_available+1) + 1
    Similar to irv, except surplus votes are distributed before eliminations.

    Output: dict {
        tally:list [OrderedDict {candidate_hash:votes int}, ...],
        winner:winner_hash bytes,
        invalid_ballots:int,
        valid_ballots:int,
        exhausted_ballots:int,
        meets_quorum:bool
    }
'''
# def stv (candidates, ballots, seats_available, quorum_requirement):
