from Action import Act, Action
from datetime import datetime
from Holdings import Holdings

from Metrics import *

class AlgorithmBase:
    def __init__(self)->None:
        pass

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:
        
        return Action(Act.HOLD, 0)



class SimpleMomentum(AlgorithmBase):
    def __init__(self) -> None:
        super().__init__()

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:

        if len(history) < 2:
            return Action(Act.HOLD) 

        latest = history[-1]
        previous = history[-2]

        stock_qty = positions.getHoldingQuantity()
        if latest.close > previous.close and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                print("BUY", qty, mrkt_price)
                return Action(Act.BUY, qty)

        if latest.close < previous.close and stock_qty > 0:
            print("SELL", stock_qty, mrkt_price)
            return Action(Act.SELL, stock_qty)

        return  Action(Act.HOLD)


class SimpleGoAndGoStrg(AlgorithmBase):
    def __init__(self) -> None:
        super().__init__()
        self.MIN_GAP = 2.0  # Minimum gap up percent to trade
        self.MAX_MINUTES = 15  # Only trade at open
        self.MAX_BUY = 0.2  # Max percent of cash to use per trade

    
    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:

        if len(history) < 2:
            return Action(Act.HOLD)
        
        prev_close = history[-2].close
        curr_open = history[-1].open
        gap_percent = ((curr_open - prev_close) / prev_close) * 100

        market_open_time = time
        minutes_since_open = (time - market_open_time).total_seconds() / 60
        
        # 3. Gap condition and time window
        if gap_percent > self.MIN_GAP and minutes_since_open <= self.MAX_MINUTES:
            # Only buy if not already holding
            if positions.getHoldingQuantity == 0:
                qty = int((funds * self.MAX_BUY) // mrkt_price)
                if qty > 0:
                    return Action(Act.BUY, qty)

        if positions.getHoldingQuantity() > 0:
            # Exit if price drops below entry or target met (e.g., 2% gain)
            entry_price = positions.getHoldingAvgPrice()
            if mrkt_price < entry_price * 0.98 or mrkt_price > entry_price * 1.02:
                return Action(Act.SELL, positions.getHoldingQuantity())

        return Action(Act.HOLD)

class MultiMetricIntradayAlgo(AlgorithmBase):
    def __init__(self):
        super().__init__()
        self.metrics = [
            EMA("fast_ema", 9),
            EMA("slow_ema", 21),
            RSI("rsi_14", 14),
            MACD("macd_line", "macd_signal", "macd_histogram"),
            ADX("adx_14", 14),
            CCI("cci_20", 20),
            ATR("atr_14", 14),
            BollingerBands("bollinger_upper_20", "bollinger_middle_20", "bollinger_lower_20", 20, 2),
            MFI("mfi_14", 14),
            VolumeAvg("volume_avg_10", 10),
            ROC("roc_10", 10),
            StochasticOscillator("stochastic_k_14", "stochastic_d_14", 14, 3),
            VWMA("vwma_10", 10),
            SMA("ema_21", 21),  # For trend confirmation
        ]

        # State variables to track previous crossovers and metric values
        self.prev_macd_line = None
        self.prev_macd_signal = None
        self.atr_threshold = 0.5  # Tuneable parameter for ATR breakout filter

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics: dict, mrkt_price: float, time: datetime,
            positions: Holdings, funds: float, history: list) -> Action:

        stock_qty = positions.getHoldingQuantity()

        # Defensive checks for presence of necessary metrics
        required_metrics = [
            "adx_14", "macd_line", "macd_signal", "cci_20",
            "atr_14", "bollinger_upper_20", "bollinger_lower_20",
            "mfi_14", "volume_avg_10", "rsi_14", "stochastic_k_14", "roc_10", "vwma_10", "ema_21"
        ]
        for key in required_metrics:
            if key not in metrics:
                return Action(Act.HOLD)

        adx = metrics["adx_14"]
        macd_line = metrics["macd_line"]
        macd_signal = metrics["macd_signal"]
        cci = metrics["cci_20"]
        atr = metrics["atr_14"]
        boll_upper = metrics["bollinger_upper_20"]
        boll_lower = metrics["bollinger_lower_20"]
        mfi = metrics["mfi_14"]
        volume_avg = metrics["volume_avg_10"]
        rsi = metrics["rsi_14"]
        stochastic_k = metrics["stochastic_k_14"]
        roc = metrics["roc_10"]
        vwma = metrics["vwma_10"]
        ema_21 = metrics["ema_21"]

        # Detect MACD crossover signals:
        if self.prev_macd_line is None or self.prev_macd_signal is None:
            self.prev_macd_line = macd_line
            self.prev_macd_signal = macd_signal
            return Action(Act.HOLD)

        macd_bull_cross = (self.prev_macd_line <= self.prev_macd_signal) and (macd_line > macd_signal)
        macd_bear_cross = (self.prev_macd_line >= self.prev_macd_signal) and (macd_line < macd_signal)

        self.prev_macd_line = macd_line
        self.prev_macd_signal = macd_signal

        # Volatility breakout filters
        breakout_long = mrkt_price >= boll_upper and atr > self.atr_threshold
        breakout_short = mrkt_price <= boll_lower and atr > self.atr_threshold

        # Volume confirmation
        strong_volume = volume_avg > 0 and mfi > 50

        # Long entry conditions
        enter_long = (
            adx > 25 and macd_bull_cross and mrkt_price > ema_21 and
            rsi >= 30 and rsi <= 70 and
            (
                (mrkt_price <= boll_lower and mfi > 50) or
                (breakout_long and strong_volume)
            )
        )

        # Long exit conditions
        exit_long = (
            macd_bear_cross or
            rsi > 80 or
            (mrkt_price >= boll_upper and mfi < 50)
        )

        # Short entry conditions
        enter_short = (
            adx > 25 and macd_bear_cross and mrkt_price < ema_21 and
            rsi >= 30 and rsi <= 70 and
            (
                (mrkt_price >= boll_upper and mfi < 50) or
                (breakout_short and strong_volume)
            )
        )

        # Short exit conditions
        exit_short = (
            macd_bull_cross or
            rsi < 20 or
            (mrkt_price <= boll_lower and mfi > 50)
        )

        # Position management logic
        if stock_qty == 0:
            if enter_long and funds >= mrkt_price:
                qty = int(funds // mrkt_price)
                if qty > 0:
                    print(f"ENTER LONG: Buy {qty} @ {mrkt_price}")
                    return Action(Act.BUY, qty)
            elif enter_short:
                # If short selling enabled in your system, implement here
                # Otherwise ignore or hold
                pass
        else:
            # We have a position, decide exit or hold
            if exit_long and stock_qty > 0:
                print(f"EXIT LONG: Sell {stock_qty} @ {mrkt_price}")
                return Action(Act.SELL, stock_qty)
            elif exit_short and stock_qty > 0:
                print(f"EXIT SHORT / REDUCE: Sell {stock_qty} @ {mrkt_price}")
                return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

class EMARsiAlgo(AlgorithmBase):
    def __init__(self):
        super().__init__()
        self.metrics = [EMA("fast_ema", 9), EMA("slow_ema", 21), RSI("rsi_14", 14)]
        self.prev_fast_ema = None
        self.prev_slow_ema = None

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, time, positions, funds, history):
        fast_ema = metrics.get("fast_ema")
        slow_ema = metrics.get("slow_ema")
        rsi = metrics.get("rsi_14", 50)
        stock_qty = positions.getHoldingQuantity()

        if fast_ema is None or slow_ema is None:
            return Action(Act.HOLD)

        if self.prev_fast_ema is None or self.prev_slow_ema is None:
            self.prev_fast_ema = fast_ema
            self.prev_slow_ema = slow_ema
            return Action(Act.HOLD)

        bullish_cross = self.prev_fast_ema <= self.prev_slow_ema and fast_ema > slow_ema
        bearish_cross = self.prev_fast_ema >= self.prev_slow_ema and fast_ema < slow_ema

        self.prev_fast_ema = fast_ema
        self.prev_slow_ema = slow_ema

        if bullish_cross and rsi < 70 and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                return Action(Act.BUY, qty)

        if (bearish_cross or rsi > 70) and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

class MACDStrategy(AlgorithmBase):
    def __init__(self):
        super().__init__()
        self.metrics = [
            MACD("macd_line", "macd_signal", "macd_histogram"),
        ]
        self.prev_macd_line = None
        self.prev_macd_signal = None

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, time, positions, funds, history):
        macd_line = metrics.get("macd_line")
        macd_signal = metrics.get("macd_signal")
        stock_qty = positions.getHoldingQuantity()
        
        if macd_line is None or macd_signal is None:
            return Action(Act.HOLD)
        
        if self.prev_macd_line is None or self.prev_macd_signal is None:
            self.prev_macd_line = macd_line
            self.prev_macd_signal = macd_signal
            return Action(Act.HOLD)
        
        bullish_cross = self.prev_macd_line <= self.prev_macd_signal and macd_line > macd_signal
        bearish_cross = self.prev_macd_line >= self.prev_macd_signal and macd_line < macd_signal
        
        self.prev_macd_line = macd_line
        self.prev_macd_signal = macd_signal
        
        if bullish_cross and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                return Action(Act.BUY, qty)
        elif bearish_cross and stock_qty > 0:
            return Action(Act.SELL, stock_qty)
        else:
            return Action(Act.HOLD)


class RSIStrategy(AlgorithmBase):
    def __init__(self):
        super().__init__()
        self.metrics = [
            RSI("rsi_14", 14),
        ]

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, time, positions, funds, history):
        rsi = metrics.get("rsi_14", 50)
        stock_qty = positions.getHoldingQuantity()
        
        if rsi < 30 and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                return Action(Act.BUY, qty)
        elif rsi > 70 and stock_qty > 0:
            return Action(Act.SELL, stock_qty)
        else:
            return Action(Act.HOLD)
