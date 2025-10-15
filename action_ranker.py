import pandas as pd
import os
import numpy as np
from typing import Optional

def simple_action_ranker(name: str, inplace: bool = False, updated_name: Optional[str] = None, lookahead: int = 5):
    path = os.path.join('simulation_results/', name + '.csv')
    if not os.path.exists(path):
        raise Exception("File does not exist")

    df = pd.read_csv(path)

    # Calculate rolling max high and min low over the lookahead window shifted backward
    max_future_high = df['high'].rolling(window=lookahead, min_periods=1).max().shift(-lookahead + 1)
    min_future_low = df['low'].rolling(window=lookahead, min_periods=1).min().shift(-lookahead + 1)

    def rank_action(row):
        idx = row.name
        action = str(row['action']).lower()
        price = row['price']

        if idx >= len(df) - lookahead:
            return 'neutral'  # Not enough future data for full lookahead window

        max_high = max_future_high.iloc[idx]
        min_low = min_future_low.iloc[idx]

        if pd.isna(max_high) or pd.isna(min_low):
            return 'neutral'

        if action == 'buy':
            profit_pct = (max_high - price) / price
            if profit_pct >= 0.01:          # 1% or more gain → Excellent
                return 'excellent'
            elif profit_pct >= 0.005:       # 0.5% to 1% gain → Good
                return 'good'
            elif profit_pct >= -0.005:      # small range → Neutral
                return 'neutral'
            else:
                return 'bad'                 # loss worse than -0.5%

        elif action == 'sell':
            profit_pct = (price - min_low) / price
            if profit_pct >= 0.01:          # 1% or more drop → Excellent
                return 'excellent'
            elif profit_pct >= 0.005:       # 0.5% to 1% drop → Good
                return 'good'
            elif profit_pct >= -0.005:      # small range → Neutral
                return 'neutral'
            else:
                return 'bad'                 # price rose after sell — bad

        else:  # hold
            # Check price change after lookahead minutes
            future_close = df['close'].iloc[idx + lookahead] if idx + lookahead < len(df) else None
            if future_close is None:
                return 'neutral'
            change_pct = abs((future_close - price) / price)
            if change_pct < 0.003:
                return 'good'
            elif change_pct < 0.01:
                return 'neutral'
            else:
                return 'bad'

    df['action_quality'] = df.apply(rank_action, axis=1)

    if inplace:
        df.to_csv(path, index=False)
    else:
        updated_path = os.path.join('simulation_results/', updated_name if updated_name else name + '_updated' + '.csv')
        df.to_csv(updated_path, index=False)

def atr_action_ranker(name: str, inplace: bool = False, updated_name: Optional[str] = None, hold_period: int = 5):
    path = os.path.join('simulation_results', name + '.csv')
    if not os.path.exists(path):
        raise Exception("File does not exist")

    df = pd.read_csv(path)

    # Calculate True Range and ATR (14-period)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(window=14, min_periods=1).mean()

    def rank_act(row):
        idx = row.name
        action = str(row['action']).lower()
        price = row['price']

        if idx + hold_period >= len(df):
            return 'neutral'

        future_close = df['close'].iloc[idx + hold_period]
        atr = df['atr'].iloc[idx]

        if pd.isna(atr):
            return 'neutral'

        move = future_close - price
        move_pct = move / price
        move_atr_ratio = move / atr if atr > 0 else 0

        if action == 'buy':
            # Positive move crossing half ATR = Good, full ATR = Excellent
            if move_atr_ratio >= 1.0:
                return 'excellent'
            elif move_atr_ratio >= 0.5:
                return 'good'
            elif move_atr_ratio >= -0.3:
                return 'neutral'
            else:
                return 'bad'

        elif action == 'sell':
            move = price - future_close
            move_atr_ratio = move / atr if atr > 0 else 0
            if move_atr_ratio >= 1.0:
                return 'excellent'
            elif move_atr_ratio >= 0.5:
                return 'good'
            elif move_atr_ratio >= -0.3:
                return 'neutral'
            else:
                return 'bad'

        else:
            # Hold: if price remains within half ATR → Good, else Neutral or Bad
            if abs(move) <= 0.5 * atr:
                return 'good'
            elif abs(move) <= atr:
                return 'neutral'
            else:
                return 'bad'

    df['action_quality'] = df.apply(rank_act, axis=1)

    if inplace:
        df.to_csv(path, index=False)
    else:
        updated_path = os.path.join('simulation_results', updated_name if updated_name else name + '_updated' + '.csv')
        df.to_csv(updated_path, index=False)


import pandas as pd
import os
import numpy as np

def rwrd_realized_return_action_ranker(name: str, inplace: bool = False, updated_name: Optional[str] = None, hold_period: int = 5):
    path = os.path.join('simulation_results', name + '.csv')
    if not os.path.exists(path):
        raise Exception("File does not exist")

    df = pd.read_csv(path)

    def rank_action(row):
        idx = row.name
        action = str(row['action']).lower()
        price = row['price']

        if idx + hold_period >= len(df):
            return 'neutral'

        future_close = df['close'].iloc[idx + hold_period]
        ret = (future_close - price) / price

        if action == 'buy':
            if ret >= 0.02:
                return 'excellent'
            elif ret >= 0.005:
                return 'good'
            elif ret > -0.005:
                return 'neutral'
            else:
                return 'bad'
        elif action == 'sell':
            ret = -ret  # Price drop after sell considered positive
            if ret >= 0.02:
                return 'excellent'
            elif ret >= 0.005:
                return 'good'
            elif ret > -0.005:
                return 'neutral'
            else:
                return 'bad'
        else:  # hold
            abs_ret = abs(ret)
            if abs_ret < 0.005:
                return 'good'
            elif abs_ret < 0.015:
                return 'neutral'
            else:
                return 'bad'

    df['action_quality'] = df.apply(rank_action, axis=1)

    if inplace:
        df.to_csv(path, index=False)
    else:
        updated_path = os.path.join('simulation_results', updated_name if updated_name else name + '_updated.csv')
        df.to_csv(updated_path, index=False)


def rwrd_risk_reward_action_ranker(name: str, inplace: bool = False, updated_name: Optional[str] = None, hold_period: int = 5, atr_period: int = 14, risk_reward_threshold: float = 1.5):
    path = os.path.join('simulation_results', name + '.csv')
    if not os.path.exists(path):
        raise Exception("File does not exist")

    df = pd.read_csv(path)
    
    # Calculate True Range and ATR
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=atr_period, min_periods=1).mean()

    def rank_action(row):
        idx = row.name
        action = str(row['action']).lower()
        price = row['price']
        atr = row['atr']

        if pd.isna(atr) or atr == 0 or idx + hold_period >= len(df):
            return 'neutral'

        future_close = df['close'].iloc[idx + hold_period]

        if action == 'buy':
            stop_loss = price - atr
            target = price + atr * risk_reward_threshold

            if future_close >= target:
                return 'excellent'
            elif stop_loss < future_close < target:
                return 'good'
            elif future_close <= stop_loss:
                return 'bad'
            else:
                # Price stayed near entry, low movement
                return 'neutral'

        elif action == 'sell':
            stop_loss = price + atr
            target = price - atr * risk_reward_threshold

            if future_close <= target:
                return 'excellent'
            elif target < future_close < stop_loss:
                return 'good'
            elif future_close >= stop_loss:
                return 'bad'
            else:
                return 'neutral'

        else:  # hold
            # Consider hold good if price stays within half ATR range
            if abs(future_close - price) <= atr * 0.5:
                return 'good'
            elif abs(future_close - price) <= atr:
                return 'neutral'
            else:
                return 'bad'

    df['action_quality'] = df.apply(rank_action, axis=1)

    if inplace:
        df.to_csv(path, index=False)
    else:
        updated_path = os.path.join('simulation_results', updated_name if updated_name else name + '_updated.csv')
        df.to_csv(updated_path, index=False)
