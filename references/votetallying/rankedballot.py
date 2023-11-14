class RankedBallot(list):
    def __init__ (self):
        self.weight = 1

    @classmethod
    def from_list (cls, ballot):
        rankedballot = cls()
        rankedballot.extend(ballot)
        return rankedballot

    def add_rank (self, rank):
        # tied candidates
        if type(rank) is list:
            if [c for c in rank if not self.contains(c)]:
                self.append(rank)
        else:
            if not self.contains(rank):
                self.append(rank)

    def contains (self, candidate):
        if candidate in self:
            return True

        for rank in self:
            if type(rank) is list:
                if candidate in rank:
                    return True

        return False

    def eliminate_candidate (self, candidate):
        self.remove(candidate)
        for rank in self:
            if type(rank) is list:
                if candidate in rank:
                    rank.remove(candidate)

    def elect_candidate (self, candidate, surplus_weight_ratio):
        if type(self[0]) is list and candidate in self[0]:
            self.weight *= (surplus_weight_ratio + len(self[0]) - 1) / len(self[0])
        elif self[0] == candidate:
            self.weight *= surplus_weight_ratio
        self.remove(candidate)
