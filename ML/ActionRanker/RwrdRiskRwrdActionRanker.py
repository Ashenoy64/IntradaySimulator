import pandas as pd
from . import ActionRankerBase
import numpy as np

class RwrdRiskRwrdActionRanker( ActionRankerBase ):
    def __init__( self, atr_period:int = 14, risk_reward_threshold:float = 1.5 ):
        super().__init__()
        self.atr_period = atr_period
        self.risk_reward_threshold = risk_reward_threshold

    def rankAction( self )->None:
        df = self.readFile()
        high = df[ 'high' ]
        low = df[ 'low' ]
        close = df[ 'close' ]
        prev_close = close.shift( 1 )

        tr = pd.concat([
            ( high - low ),
            ( high - prev_close ).abs(),
            ( low - prev_close ).abs()
        ], axis=1 ).max( axis=1 )
        df[ 'atr' ] = tr.rolling( window = self.atr_period, min_periods = 1 ).mean()

        def rank_action( row ):
            idx = row.name
            action = str( row[ 'action' ] ).lower()
            price = row[ 'price' ]
            atr = row[ 'atr' ]

            if pd.isna( atr ) or atr == 0 or idx + self.lookahead >= len( df ):
                return self.rankLabel( 0.5 )

            future_close = df[ 'close' ].iloc[ idx + self.lookahead ]

            if action == 'buy':
                stop_loss = price - atr
                target = price + atr * self.risk_reward_threshold

                if future_close >= target:
                    return self.rankLabel( 0.9 )
                elif stop_loss < future_close < target:
                    return self.rankLabel( 0.7 )
                elif future_close <= stop_loss:
                    return self.rankLabel( 0.3 )
                else:
                    # Price stayed near entry, low movement
                    return self.rankLabel( 0.5 )

            elif action == 'sell':
                stop_loss = price + atr
                target = price - atr * self.risk_reward_threshold

                if future_close <= target:
                    return self.rankLabel( 0.9 )
                elif target < future_close < stop_loss:
                    return self.rankLabel( 0.7 )
                elif future_close >= stop_loss:
                    return self.rankLabel( 0.3 )
                else:
                    return self.rankLabel( 0.5 )

            else:  # hold
                # Consider hold good if price stays within half ATR range
                if abs( future_close - price ) <= atr * 0.5:
                    return self.rankLabel( 0.7 )
                elif abs( future_close - price ) <= atr:
                    return self.rankLabel( 0.5 )
                else:
                    return self.rankLabel( 0.3 )

        df[ 'action_quality' ] = df.apply( rank_action, axis = 1 )
        self.writeFile( df )
