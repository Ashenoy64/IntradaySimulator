from . import RankLabeler

class GNBLabeler( RankLabeler ):
    def mapRank( self, rank:float )->str:
        if rank<0.4:
            return "bad"
        elif rank>=0.7:
            return "good"
        else:
            return "neutral"