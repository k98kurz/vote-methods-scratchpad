import random
from tally import irv, irv_coombs
import copy

def fisheryates(arr):
    for i in range(len(arr) - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

def normalize_ranked_ballots_old(ballots, candidates):
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

def normalize_ranked_ballots_no_ties(ballots, candidates, placeholder = 'Unranked/Write-Ins/Other'):
    # add write-in candidates in the Unranked/Write-Ins/Other slot
    for b in ballots:
        for c in b:
            if c not in candidates and c is not placeholder:
                candidates.append(c)

        if placeholder not in b:
            b.append(placeholder)

    for b in ballots:
        # compile unranked candidates
        unranked = []
        for c in candidates:
            if c not in b:
                unranked.append(c)

        # shuffle unranked candidates
        unranked = fisheryates(unranked)

        # put unranked candidates on the ballot in place of Unranked/Write-Ins/Other
        new_ballot = b[0:b.index(placeholder)]
        new_ballot[len(new_ballot):] = unranked
        new_ballot[len(new_ballot):] = b[b.index(placeholder)+1:]
        for i in range(0, len(new_ballot)):
            if i >= len(b):
                b.append(new_ballot[i])
            else:
                b[i] = new_ballot[i]

    # return noramlized ballots and candidates list
    return ballots, candidates

def normalize_ranked_ballots_coombs_no_ties(ballots, candidates):
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

        # add unranked candidates to the ballot just before last
        c = b.pop()
        b[len(b):] = unranked
        b.append(c)

    # return noramlized ballots and candidates list
    return ballots, candidates

def normalize_ranked_ballots(ballots, candidates, placeholder = b'Unranked/Write-Ins/Other'):
    new_ballots = []

    # get complete list of all candidates
    for b in ballots:
        found_ph = False
        for rank in b:
            # handle ties
            if type(rank) is list:
                for t in rank:
                    if t not in candidates and t is not placeholder:
                        candidates.append(t)
                    elif t is placeholder:
                        found_ph = True
            else:
                if rank not in candidates and rank is not placeholder:
                    candidates.append(rank)
                elif rank is placeholder:
                    found_ph = True

        # add write-in candidates in the Unranked/Write-Ins/Other slot
        if not found_ph:
            b.append(placeholder)

    for b in ballots:
        # compile unranked candidates
        unranked = []
        for c in candidates:
            # handle ties
            found_c = False
            for rank in b:
                if type(rank) is list:
                    if c in rank:
                        found_c = True

            if not found_c and c not in b:
                unranked.append(c)

        # put unranked candidates on the ballot in place of Unranked/Write-Ins/Other as a tie
        nb = b[0:b.index(placeholder)]
        nb.append(unranked)
        nb[len(nb):] = b[b.index(placeholder)+1:]
        new_ballots.append(nb)

    # return noramlized ballots and candidates list
    return new_ballots, candidates


original_candidates = ['Albert', 'Billy', 'Cindy']
original_ballots = [
    ['Albert', 'Cindy', 'Billy'],
    ['Billy', 'Dilbert', 'Albert'],
    ['Dilbert', 'Billy', 'Albert'],
    ['Billy', 'Dilbert'],
    ['Edmund', 'Dilbert', 'Billy'],
    ['Edmund', 'Dilbert', 'Billy', 'Sam'],
    ['Sam', 'Edmund'],
    ['Edmund', 'Sam', 'Albert'],
    ['Edmund', 'Sam'],
    ['Edmund'],
    ['Edmund'],
    # [b'Unranked/Write-Ins/Other', 'Edmund'],
    # [b'Unranked/Write-Ins/Other', 'Edmund'],
    [['Dilbert', 'Cindy'], 'Edmund']
]
ballots = copy.deepcopy(original_ballots)
candidates = original_candidates[:]

# print('ballots:')
# for b in ballots:
#     print(b)
#
# print('')
# print('candidates: ', candidates)
#
# print('')
# print('***normalize***')
# print('')

ballots, candidates = normalize_ranked_ballots(ballots, candidates)

# print('ballots:')
# for b in ballots:
#     print(b)
#
# print('')
# print('candidates: ', candidates)
# print('')
# print('')





ballots = copy.deepcopy(original_ballots)
ballots, candidates = normalize_ranked_ballots(ballots, candidates)
print('ballots: ')
for b in ballots:
    print('\t', b)
result = irv(candidates[:], ballots, 3)
# scores[result['winner']] += 1
print('winner: ', result['winner'])
print('valid_ballots: ', result['valid_ballots'])
print('invalid_ballots: ', result['invalid_ballots'])
print('exhausted_ballots: ', result['exhausted_ballots'])
for t in result['tally']:
    print('\ttally round:', t)
    # print('\thighest-pref: ', t[0])
    # print('\tlowest-pref: ', t[1])
