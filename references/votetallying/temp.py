t = [
    1,
    2,
    [3,4,5,6],
    7,
    [8,9]
]

ballot = []

# for rank in t:
#     # traverse ties
#     if type(rank) is list:
#         # remove eliminated candidates from rank
#         nonrank = [c for c in rank if c%2 is not 0]
#         for n in nonrank:
#             rank.remove(n)
#         # add to ballot
#         if len(rank) == 1:
#             ballot.append(rank[0])
#         elif len(rank) > 1:
#             ballot.append(rank)
#     else:
#         # keep only votes for uneliminated candidates
#         if rank%2 is 0:
#             ballot.append(rank)
# # t = [r for r in t if type(r) is list or r%2 is 0]
#
# print(ballot)

# for b in t:
#     if type(b) is list and len([c for c in b if c%2]):
#         print('no ', b)
#     elif b%2:
#         print('no ', b)
#     else:
#         ballot.append(b)
#
# print(ballot)

worst = [['abc', 123]]
ties_for_worst = [['bac', 123], ['cab', 123]]
# eliminated = []
# eliminated.append(worst)
# eliminated.extend(ties_for_worst)
# print(eliminated)

worst.extend([a for a in ties_for_worst if a[1] > worst[0][1]])
print(worst)
