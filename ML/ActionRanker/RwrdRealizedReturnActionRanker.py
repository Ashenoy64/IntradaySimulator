import pandas as pd
from . import ActionRankerBase
import numpy as np

class RwrdRealizedReturnActionRanker( ActionRankerBase ):
    def rankAction( self )->None:
        df = self.readFile()
        def rank_action( row ):
            idx = row.name
            action = str( row[ 'action' ]).lower()
            price = row[ 'price' ]

            if idx + self.lookahead >= len( df ):
                return self.rankLabel( 0.5 )
    
            future_close = df[ 'close' ].iloc[ idx + self.lookahead ]
            ret = ( future_close - price ) / price

            if action == 'buy':
                if ret >= 0.02:
                    return self.rankLabel( 0.9 )
                elif ret >= 0.005:
                    return self.rankLabel( 0.7 )
                elif ret > -0.005:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )
            elif action == 'sell':
                ret = -ret  # Price drop after sell considered positive
                if ret >= 0.02:
                    return self.rankLabel( 0.9 )
                elif ret >= 0.005:
                    return self.rankLabel( 0.7 )
                elif ret > -0.005:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )
            else:  # hold
                abs_ret = abs(ret)
                if abs_ret < 0.005:
                    return self.rankLabel( 0.7 )
                elif abs_ret < 0.015:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )
        df[ 'action_quality' ] = df.apply( rank_action, axis = 1 )
        self.writeFile( df )