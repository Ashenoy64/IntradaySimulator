import pandas as pd
from . import ActionRankerBase
import numpy as np

class SimpleActionRanker( ActionRankerBase ):
    def rankAction( self )->None:
        df = self.readFile()
        # Calculate rolling max high and min low over the lookahead window shifted backward
        max_future_high = df[ 'high' ].rolling( window = self.lookahead, min_periods = 1 ).max().shift( -self.lookahead + 1 )
        min_future_low = df[ 'low' ].rolling( window = self.lookahead, min_periods = 1 ).min().shift( -self.lookahead + 1 )

        def rank_action( row ):
            idx = row.name
            action = str( row[ 'action' ] ).lower()
            price = row[ 'price' ]

            if idx >= len( df ) - self.lookahead:
                return self.rankLabel( 0.5 ) # Not enough future data for full lookahead window

            max_high = max_future_high.iloc[ idx ]
            min_low = min_future_low.iloc[ idx ]

            if pd.isna( max_high ) or pd.isna( min_low ):
                return self.rankLabel( 0.5 )

            if action == 'buy':
                profit_pct =  ( max_high - price ) / price
                if profit_pct >= 0.01:          # 1% or more gain → Excellent
                    return self.rankLabel( 0.9 )
                elif profit_pct >= 0.005:       # 0.5% to 1% gain → Good
                    return self.rankLabel( 0.7 )
                elif profit_pct >= -0.005:      # small range → Neutral
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )  # loss worse than -0.5%

            elif action == 'sell':
                profit_pct = ( price - min_low ) / price
                if profit_pct >= 0.01:          # 1% or more drop → Excellent
                    return self.rankLabel( 0.9 )
                elif profit_pct >= 0.005:       # 0.5% to 1% drop → Good
                    return self.rankLabel( 0.7 )
                elif profit_pct >= -0.005:      # small range → Neutral
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )  # price rose after sell — bad

            else:  # hold
                # Check price change after lookahead minutes
                future_close = df[ 'close' ].iloc[ idx + self.lookahead ] if idx + self.lookahead < len( df ) else None
                if future_close is None:
                    return self.rankLabel( 0.5 )
                change_pct = abs( ( future_close - price ) / price )
                if change_pct < 0.003:
                    return  self.rankLabel( 0.7 )
                elif change_pct < 0.01:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )

        df[ 'action_quality' ] = df.apply( rank_action, axis = 1 )
        self.writeFile( df )