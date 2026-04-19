from data_fetcher import fetch_data
from datetime import date
from typing import Optional
from Interval import Interval
from Trend import Trend


class TrendIter:
    def __init__(self, tick,
                date:Optional[ date ] = None,
                interval:Optional[ Interval ] = None ) -> None:
        args = [ tick ]
        if date:
            args.append( date )
        if interval:
            args.append( interval )

        self.data = fetch_data( *args )
        self.indices = self.data.index.tolist()
        self.index_pos = 0

    def __iter__( self ):
        return self

    def getTrendTuple( self, row )->Trend:
        trend = Trend(
            close = row.Close,
            high=row.High,
            open=row.Open,
            low=row.Low,
            volume=row.Volume
        )
        return trend

    def __next__( self ):
        if self.index_pos >= len( self.data ):
            raise StopIteration
        i = self.indices[ self.index_pos ]
        row = self.data.loc[i]
        result = self.getTrendTuple( row )
        self.index_pos += 1
        return i, result.close, result
    