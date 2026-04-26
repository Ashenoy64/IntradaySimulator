from . import RankLabeler

class FloatLabeler( RankLabeler ):
    def mapRank( self, rank:float )->str:
        return rank