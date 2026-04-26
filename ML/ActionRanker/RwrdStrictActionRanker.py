import pandas as pd
import numpy as np
from . import ActionRankerBase
from ..RankLabler.FloatLabeler import FloatLabeler

class RwrdStrictActionRanker(ActionRankerBase):
    def __init__( self, name, lookahead:int= 5 , updated_name:Optional[str] = None )->None:
        super().__init__( name, lookahead, updated_name )
        self.rankLabeler = FloatLabeler()

    def _compute_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low   = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift(1)).abs()
        low_close  = (df['low']  - df['close'].shift(1)).abs()
        tr  = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr

    def rankAction(self) -> None:
        df = self.readFile()

        # ATR as % of price — normalizes volatility per row
        atr      = self._compute_atr(df)
        atr_pct  = (atr / df['close']).fillna(0.01)   # fallback 1% if ATR missing

        def rank_action(row):
            idx    = row.name
            action = str(row['action']).lower()
            price  = row['price']

            # Edge: not enough future data
            if idx + self.lookahead >= len(df):
                return self.rankLabel(0.5)

            future_close = df['close'].iloc[idx + self.lookahead]
            raw_ret      = (future_close - price) / price

            # Normalize return by ATR so thresholds adapt to volatility
            vol          = atr_pct.iloc[idx]
            norm_ret     = raw_ret / vol   # e.g., +2 means moved 2x ATR in your favour

            if action == 'buy':
                # Positive norm_ret = price rose = good for buy
                if   norm_ret >= 2.0:   return self.rankLabel(0.95)  # Excellent: rose 2+ ATRs
                elif norm_ret >= 1.0:   return self.rankLabel(0.75)  # Good: rose 1+ ATR
                elif norm_ret >= -0.5:  return self.rankLabel(0.5)   # Neutral: flat
                elif norm_ret >= -1.5:  return self.rankLabel(0.25)  # Poor: fell ~1 ATR
                else:                   return self.rankLabel(0.05)  # Terrible: fell 1.5+ ATRs

            elif action == 'sell':
                # Negative raw_ret = price dropped after sell = good
                sell_ret = -norm_ret
                if   sell_ret >= 2.0:   return self.rankLabel(0.95)
                elif sell_ret >= 1.0:   return self.rankLabel(0.75)
                elif sell_ret >= -0.5:  return self.rankLabel(0.5)
                elif sell_ret >= -1.5:  return self.rankLabel(0.25)
                else:                   return self.rankLabel(0.05)

            else:  # hold
                abs_norm = abs(norm_ret)
                # Holding during a big move (in either direction) is penalized harshly
                if   abs_norm < 0.3:   return self.rankLabel(0.75)  # Good: truly flat, hold was right
                elif abs_norm < 0.8:   return self.rankLabel(0.5)   # Neutral: mild move
                elif abs_norm < 1.5:   return self.rankLabel(0.25)  # Poor: notable move, should have acted
                else:                  return self.rankLabel(0.05)  # Terrible: big move, hold was wrong

        df['action_quality'] = df.apply(rank_action, axis=1)
        self.writeFile(df)