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

def normalize_ranked_ballots(ballots, candidates, placeholder = 'Unranked/Write-Ins/Other'):
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
        new_ballot = b[0:b.index(placeholder)]
        new_ballot.append(unranked)
        new_ballot[len(new_ballot):] = b[b.index(placeholder)+1:]
        for i in range(0, len(new_ballot)):
            if i < len(b):
                b[i] = new_ballot[i]
            else:
                b.append(new_ballot[i])

    # return noramlized ballots and candidates list
    return ballots, candidates


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
    ['Unranked/Write-Ins/Other', 'Edmund']
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







# print('IRV result after 10000 tallies (normal normalization):')
# scores = {'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':0}
# for c in candidates:
#     scores[c] = 0
#
# for i in range(0, 10000):
#     ballots = copy.deepcopy(original_ballots)
#     ballots, candidates = normalize_ranked_ballots(ballots, candidates)
#     result = irv(candidates[:], ballots, 3)
#     scores[result['winner']] += 1
#
# for c in candidates:
#     print('     ', c, ':', scores[c])
# print('      no winner:', scores['b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'])
#
# print('')
#
# print('IRV result after 10000 tallies (coombs normalization):')
# scores = {'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':0}
# for c in candidates:
#     scores[c] = 0
#
# for i in range(0, 10000):
#     ballots = copy.deepcopy(original_ballots)
#     ballots, candidates = normalize_ranked_ballots_coombs(ballots, candidates)
#     result = irv(candidates[:], ballots, 3)
#     scores[result['winner']] += 1
#
# for c in candidates:
#     print('     ', c, ':', scores[c])
# print('      no winner:', scores['b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'])
#
# print('')


# ********************************************

print('IRV Coomb\'s result after 100000 tallies (new normalization):')
scores = {'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':0}
for c in candidates:
    scores[c] = 0

for i in range(0, 100000):
    ballots = copy.deepcopy(original_ballots)
    ballots, candidates = normalize_ranked_ballots(ballots, candidates)
    result = irv_coombs(candidates[:], ballots, 3)
    scores[result['winner']] += 1

for c in candidates:
    print('     ', c, ':', scores[c])
print('      no winner:', scores['b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'])

print('')

# print('IRV Coomb\'s result after 100000 tallies (coombs normalization):')
# scores = {'b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00':0}
# for c in candidates:
#     scores[c] = 0
#
# for i in range(0, 100000):
#     ballots = copy.deepcopy(original_ballots)
#     ballots, candidates = normalize_ranked_ballots_coombs(ballots, candidates)
#     result = irv_coombs(candidates[:], ballots, 3)
#     scores[result['winner']] += 1
#
# for c in candidates:
#     print('     ', c, ':', scores[c])
# print('      no winner:', scores['b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'])
