import pandas as pd
from . import ActionRankerBase
import numpy as np

class AtrActionRanker( ActionRankerBase ):
    def rankAction( self )->None:
        df = self.readFile()
        df[ 'tr' ] = np.maximum( df[ 'high' ] - df[ 'low' ], 
                          np.maximum( abs(df[ 'high' ] - df[ 'close' ].shift ( 1 ) ), 
                                     abs( df[ 'low' ] - df[ 'close' ].shift( 1 ) ) ) )
        df[ 'atr' ] = df[ 'tr' ].rolling( window = 14, min_periods = 1 ).mean()

        def rank_act( row ):
            idx = row.name
            action = str( row[ 'action' ] ).lower()
            price = row[ 'price' ]

            if idx + self.lookahead >= len( df ):
                return self.rankLabel( 0.5 )

            future_close = df[ 'close' ].iloc[ idx + self.lookahead ]
            atr = df[ 'atr' ].iloc[ idx ]

            if pd.isna( atr ):
                return self.rankLabel( 0.5 )

            move = future_close - price
            move_pct = move / price
            move_atr_ratio = move / atr if atr > 0 else 0

            if action == 'buy':
                # Positive move crossing half ATR = Good, full ATR = Excellent
                if move_atr_ratio >= 1.0:
                    return self.rankLabel( 0.7 )
                elif move_atr_ratio >= 0.5:
                    return self.rankLabel( 0.9 )
                elif move_atr_ratio >= -0.3:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )

            elif action == 'sell':
                move = price - future_close
                move_atr_ratio = move / atr if atr > 0 else 0
                if move_atr_ratio >= 1.0:
                    return self.rankLabel( 0.7 )
                elif move_atr_ratio >= 0.5:
                    return self.rankLabel( 0.9 )
                elif move_atr_ratio >= -0.3:
                   return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )

            else:
                # Hold: if price remains within half ATR → Good, else Neutral or Bad
                if abs(move) <= 0.5 * atr:
                    return 'good'
                elif abs(move) <= atr:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )

        df[ 'action_quality' ] = df.apply( rank_act, axis = 1 )
        self.writeFile( df )