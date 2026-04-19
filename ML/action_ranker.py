import pandas as pd
import os
import numpy as np
from typing import Optional
from Settings import SIMULATION_RESULTS_PATH

class RankLabeler:
    def __init__(self)->None:
        pass

    def mapRank(self, rank:float)->str|float:
        raise NotImplementedError()

class GNBLabeler(RankLabeler):
    def mapRank(self, rank:float)->str:
        if rank<0.4:
            return "bad"
        elif rank>=0.7:
            return "good"
        else:
            return "neutral"

class ActionRankerBase:
    def __init__(self, name, lookahead:int= 5 ,updated_name: Optional[str] = None):
        self.file_name = self.maybeAddCSVExt(name)
        self.lookahead = lookahead
        
        self.new_file_name =  self.maybeAddCSVExt(updated_name) if updated_name else self.file_name
        self.base_dir = SIMULATION_RESULTS_PATH

        self.rankLabeler = GNBLabeler()
    
    def maybeAddCSVExt(self, name:str)->str:
        if name.endswith(".csv"):
            return name
        return name+".csv"

    def setBaseDir(self, base_dir:str)->None:
        self.base_dir = base_dir

    def readFile(self)->pd.DataFrame:
        path = os.path.join(self.base_dir, self.file_name)
        return pd.read_csv(path)  

    def writeFile(self,df:pd.DataFrame)->None:
        path = os.path.join(self.base_dir, self.new_file_name)   
        df.to_csv(path, index=False)

    def rankAction(self)->None:
        raise NotImplementedError()

    def setRankLabler(self, rankLabler:RankLabeler)->None:
        self.rankLabeler = rankLabler

    def rankLabel(self, rank:float)->str|float:
        return self.rankLabeler.mapRank(rank)
    

class SimpleActionRanker(ActionRankerBase):
    def rankAction(self)->None:
        df = self.readFile()
        # Calculate rolling max high and min low over the lookahead window shifted backward
        max_future_high = df['high'].rolling(window=self.lookahead, min_periods=1).max().shift(-self.lookahead + 1)
        min_future_low = df['low'].rolling(window=self.lookahead, min_periods=1).min().shift(-self.lookahead + 1)

        def rank_action(row):
            idx = row.name
            action = str(row['action']).lower()
            price = row['price']

            if idx >= len(df) - self.lookahead:
                return self.rankLabel(0.5) # Not enough future data for full lookahead window

            max_high = max_future_high.iloc[idx]
            min_low = min_future_low.iloc[idx]

            if pd.isna(max_high) or pd.isna(min_low):
                return self.rankLabel(0.5)

            if action == 'buy':
                profit_pct = (max_high - price) / price
                if profit_pct >= 0.01:          # 1% or more gain → Excellent
                    return self.rankLabel(0.9)
                elif profit_pct >= 0.005:       # 0.5% to 1% gain → Good
                    return self.rankLabel(0.7)
                elif profit_pct >= -0.005:      # small range → Neutral
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)  # loss worse than -0.5%

            elif action == 'sell':
                profit_pct = (price - min_low) / price
                if profit_pct >= 0.01:          # 1% or more drop → Excellent
                    return self.rankLabel(0.9)
                elif profit_pct >= 0.005:       # 0.5% to 1% drop → Good
                    return self.rankLabel(0.7)
                elif profit_pct >= -0.005:      # small range → Neutral
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)  # price rose after sell — bad

            else:  # hold
                # Check price change after lookahead minutes
                future_close = df['close'].iloc[idx + self.lookahead] if idx + self.lookahead < len(df) else None
                if future_close is None:
                    return self.rankLabel(0.5)
                change_pct = abs((future_close - price) / price)
                if change_pct < 0.003:
                    return  self.rankLabel(0.7)
                elif change_pct < 0.01:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)

        df['action_quality'] = df.apply(rank_action, axis=1)
        self.writeFile(df)

class AtrActionRanker(ActionRankerBase):
    def rankAction(self)->None:
        df = self.readFile()
        df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['tr'].rolling(window=14, min_periods=1).mean()

        def rank_act(row):
            idx = row.name
            action = str(row['action']).lower()
            price = row['price']

            if idx + self.lookahead >= len(df):
                return self.rankLabel(0.5)

            future_close = df['close'].iloc[idx + self.lookahead]
            atr = df['atr'].iloc[idx]

            if pd.isna(atr):
                return self.rankLabel(0.5)

            move = future_close - price
            move_pct = move / price
            move_atr_ratio = move / atr if atr > 0 else 0

            if action == 'buy':
                # Positive move crossing half ATR = Good, full ATR = Excellent
                if move_atr_ratio >= 1.0:
                    return self.rankLabel(0.7)
                elif move_atr_ratio >= 0.5:
                    return self.rankLabel(0.9)
                elif move_atr_ratio >= -0.3:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)

            elif action == 'sell':
                move = price - future_close
                move_atr_ratio = move / atr if atr > 0 else 0
                if move_atr_ratio >= 1.0:
                    return self.rankLabel(0.7)
                elif move_atr_ratio >= 0.5:
                    return self.rankLabel(0.9)
                elif move_atr_ratio >= -0.3:
                   return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)

            else:
                # Hold: if price remains within half ATR → Good, else Neutral or Bad
                if abs(move) <= 0.5 * atr:
                    return 'good'
                elif abs(move) <= atr:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)

        df['action_quality'] = df.apply(rank_act, axis=1)
        self.writeFile(df)

class RwrdRealizedReturnActionRanker(ActionRankerBase):
    def rankAction(self)->None:
        df = self.readFile()
        def rank_action(row):
            idx = row.name
            action = str(row['action']).lower()
            price = row['price']

            if idx + self.lookahead >= len(df):
                return self.rankLabel(0.5)
    
            future_close = df['close'].iloc[idx + self.lookahead]
            ret = (future_close - price) / price

            if action == 'buy':
                if ret >= 0.02:
                    return self.rankLabel(0.9)
                elif ret >= 0.005:
                    return self.rankLabel(0.7)
                elif ret > -0.005:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)
            elif action == 'sell':
                ret = -ret  # Price drop after sell considered positive
                if ret >= 0.02:
                    return self.rankLabel(0.9)
                elif ret >= 0.005:
                    return self.rankLabel(0.7)
                elif ret > -0.005:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)
            else:  # hold
                abs_ret = abs(ret)
                if abs_ret < 0.005:
                    return self.rankLabel(0.7)
                elif abs_ret < 0.015:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)
        df['action_quality'] = df.apply(rank_action, axis=1)
        self.writeFile(df)

class RwrdRiskRwrdActionRanker(ActionRankerBase):
    def __init__(self, atr_period: int = 14, risk_reward_threshold: float = 1.5):
        super().__init__()
        self.atr_period = atr_period
        self.risk_reward_threshold = risk_reward_threshold

    def rankAction(self)->None:
        df = self.readFile()
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)

        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=self.atr_period, min_periods=1).mean()

        def rank_action(row):
            idx = row.name
            action = str(row['action']).lower()
            price = row['price']
            atr = row['atr']

            if pd.isna(atr) or atr == 0 or idx + self.lookahead >= len(df):
                return self.rankLabel(0.5)

            future_close = df['close'].iloc[idx + self.lookahead]

            if action == 'buy':
                stop_loss = price - atr
                target = price + atr * self.risk_reward_threshold

                if future_close >= target:
                    return self.rankLabel(0.9)
                elif stop_loss < future_close < target:
                    return self.rankLabel(0.7)
                elif future_close <= stop_loss:
                    return self.rankLabel(0.3)
                else:
                    # Price stayed near entry, low movement
                    return self.rankLabel(0.5)

            elif action == 'sell':
                stop_loss = price + atr
                target = price - atr * self.risk_reward_threshold

                if future_close <= target:
                    return self.rankLabel(0.9)
                elif target < future_close < stop_loss:
                    return self.rankLabel(0.7)
                elif future_close >= stop_loss:
                    return self.rankLabel(0.3)
                else:
                    return self.rankLabel(0.5)

            else:  # hold
                # Consider hold good if price stays within half ATR range
                if abs(future_close - price) <= atr * 0.5:
                    return self.rankLabel(0.7)
                elif abs(future_close - price) <= atr:
                    return self.rankLabel(0.5)
                else:
                    return self.rankLabel(0.3)

        df['action_quality'] = df.apply(rank_action, axis=1)
        self.writeFile(df)
