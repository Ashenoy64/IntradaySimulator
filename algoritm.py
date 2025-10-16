from Action import Act, Action
from datetime import datetime
from Holdings import Holdings

from Metrics import *

class AlgorithmBase:
    def __init__(self)->None:
        pass
    
    def getAlgoMetrics(self):
        return {}

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:
        
        return Action(Act.HOLD, 0)

from datetime import time as dt_time

class AlgorithmBaseWithRisk(AlgorithmBase):
    def __init__(self, stop_loss_pct=0.05, target_pct=0.07, square_off_time=dt_time(15, 15)):
        super().__init__()
        self.stop_loss_pct = stop_loss_pct
        self.target_pct = target_pct
        self.square_off_time = square_off_time  # datetime.time object
        self.entry_price = None
        self.position_open_time = None

    def checkRiskControls(self, mrkt_price, current_dt, positions):
        stock_qty = positions.getHoldingQuantity()

        # If no positions, reset
        if stock_qty == 0:
            self.entry_price = None
            self.position_open_time = None
            return None  

        # Square off before intraday cutoff
        if current_dt.time() >= self.square_off_time:   # ✅ FIXED for datetime
            return Action(Act.SELL, stock_qty)

        # Check SL/Target
        if self.entry_price:
            pnl_pct = (mrkt_price - self.entry_price) / self.entry_price
            # Stop-loss hit
            if pnl_pct <= -self.stop_loss_pct:
                return Action(Act.SELL, stock_qty)
            # Target hit
            if pnl_pct >= self.target_pct:
                return Action(Act.SELL, stock_qty)

        return None


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
                return Action(Act.BUY, qty)

        if latest.close < previous.close and stock_qty > 0:
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

class EMARsiAlgo(AlgorithmBaseWithRisk):
    def __init__(self):
        super().__init__()
        self.metrics = [
            EMA("fast_ema", 9),
            EMA("slow_ema", 21),
            RSI("rsi_14", 14),
            VWMA("vwma", 20),
        ]
        self.prev_fast_ema = None
        self.prev_slow_ema = None

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, current_dt, positions, funds, history):
        fast_ema = metrics.get("fast_ema")
        slow_ema = metrics.get("slow_ema")
        rsi = metrics.get("rsi_14", 50)
        vwma = metrics.get("vwma", mrkt_price)
        stock_qty = positions.getHoldingQuantity()

        # Risk management check
        risk_action = self.checkRiskControls(mrkt_price, current_dt, positions)
        if risk_action: return risk_action

        if fast_ema is None or slow_ema is None:
            return Action(Act.HOLD)
        if self.prev_fast_ema is None or self.prev_slow_ema is None:
            self.prev_fast_ema, self.prev_slow_ema = fast_ema, slow_ema
            return Action(Act.HOLD)

        bullish_cross = self.prev_fast_ema <= self.prev_slow_ema and fast_ema > slow_ema
        bearish_cross = self.prev_fast_ema >= self.prev_slow_ema and fast_ema < slow_ema
        self.prev_fast_ema, self.prev_slow_ema = fast_ema, slow_ema

        # ✅ 3 confirmations
        bullish_confirm = bullish_cross and rsi < 70 and mrkt_price > vwma
        bearish_confirm = (bearish_cross or rsi > 70) and mrkt_price < vwma

        if bullish_confirm and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                self.entry_price = mrkt_price
                self.position_open_time = current_dt
                return Action(Act.BUY, qty)

        if bearish_confirm and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

class MACDStrategy(AlgorithmBaseWithRisk):
    def __init__(self):
        super().__init__()
        self.metrics = [
            MACD("macd_line", "macd_signal", "macd_histogram"),
            RSI("rsi_14", 14),
            VWAP("vwap"),
        ]
        self.prev_macd_line = None
        self.prev_macd_signal = None

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, current_dt, positions, funds, history):
        macd_line = metrics.get("macd_line")
        macd_signal = metrics.get("macd_signal")
        rsi = metrics.get("rsi_14", 50)
        vwap = metrics.get("vwap", mrkt_price)
        stock_qty = positions.getHoldingQuantity()

        # Risk check
        risk_action = self.checkRiskControls(mrkt_price, current_dt, positions)
        if risk_action: return risk_action

        if macd_line is None or macd_signal is None:
            return Action(Act.HOLD)
        if self.prev_macd_line is None or self.prev_macd_signal is None:
            self.prev_macd_line, self.prev_macd_signal = macd_line, macd_signal
            return Action(Act.HOLD)

        bullish_cross = self.prev_macd_line <= self.prev_macd_signal and macd_line > macd_signal
        bearish_cross = self.prev_macd_line >= self.prev_macd_signal and macd_line < macd_signal
        self.prev_macd_line, self.prev_macd_signal = macd_line, macd_signal

        # ✅ 3 confirmations
        bullish_confirm = bullish_cross and rsi < 70 and mrkt_price > vwap
        bearish_confirm = bearish_cross and rsi > 30 and mrkt_price < vwap

        if bullish_confirm and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                self.entry_price = mrkt_price
                self.position_open_time = current_dt
                return Action(Act.BUY, qty)
        if bearish_confirm and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

class RSIStrategy(AlgorithmBaseWithRisk):
    def __init__(self):
        super().__init__()
        self.metrics = [
            RSI("rsi_14", 14),
            VWMA("vwma", 20),
            ATR("atr_14", 14),
        ]

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, current_dt, positions, funds, history):
        rsi = metrics.get("rsi_14", 50)
        vwma = metrics.get("vwma", mrkt_price)
        atr = metrics.get("atr_14", 1.0)
        stock_qty = positions.getHoldingQuantity()

        # Risk check
        risk_action = self.checkRiskControls(mrkt_price, current_dt, positions)
        if risk_action: return risk_action

        # ✅ 3 confirmations
        bullish_confirm = rsi < 30 and mrkt_price > vwma and atr > 0
        bearish_confirm = rsi > 70 and mrkt_price < vwma

        if bullish_confirm and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                self.entry_price = mrkt_price
                self.position_open_time = current_dt
                return Action(Act.BUY, qty)

        if bearish_confirm and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

class MomentumAlgorithm(AlgorithmBaseWithRisk):
    def __init__(self):
        super().__init__()
        self.metrics = [
            ROC("roc_10", 10),
            RSI("rsi_14", 14),
            VWAP("vwap"),
        ]

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, current_dt, positions, funds, history):
        roc = metrics.get("roc_10", 0)
        rsi = metrics.get("rsi_14", 50)
        vwap = metrics.get("vwap", mrkt_price)
        stock_qty = positions.getHoldingQuantity()

        # Risk check
        risk_action = self.checkRiskControls(mrkt_price, current_dt, positions)
        if risk_action: return risk_action

        # ✅ 3 confirmations
        bullish_confirm = roc > 0 and rsi < 70 and mrkt_price > vwap
        bearish_confirm = (roc <= 0 or rsi >= 70) and mrkt_price < vwap

        if bullish_confirm and funds >= mrkt_price:
            qty = int(funds // mrkt_price)
            if qty > 0:
                self.entry_price = mrkt_price
                self.position_open_time = current_dt
                return Action(Act.BUY, qty)

        if bearish_confirm and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        return Action(Act.HOLD)

from datetime import time as dt_time

class ComprehensiveMetricsAlgo(AlgorithmBase):
    """
    A data collection algorithm that subscribes to ALL available technical indicators
    for maximum metric coverage. This algorithm doesn't make trading decisions but
    collects comprehensive market data for analysis.
    """
    def __init__(self):
        super().__init__()
        # Subscribe to ALL available metrics for maximum data collection
        self.metrics = [
            # Trend Following Indicators
            SMA("sma_5", 5),
            SMA("sma_10", 10),
            SMA("sma_20", 20),
            SMA("sma_50", 50),
            EMA("ema_5", 5),
            EMA("ema_9", 9),
            EMA("ema_12", 12),
            EMA("ema_21", 21),
            EMA("ema_26", 26),

            # Momentum Indicators
            RSI("rsi_7", 7),
            RSI("rsi_14", 14),
            RSI("rsi_21", 21),
            ROC("roc_5", 5),
            ROC("roc_10", 10),
            ROC("roc_14", 14),

            # Volatility Indicators
            BollingerBands("bb_20", 20, 2.0),
            ATR("atr_7", 7),
            ATR("atr_14", 14),
            ATR("atr_21", 21),

            # Volume Indicators
            VWAP("vwap"),
            VWMA("vwma_5", 5),
            VWMA("vwma_10", 10),
            VWMA("vwma_20", 20),
            VolumeAvg("volume_avg_5", 5),
            VolumeAvg("volume_avg_10", 10),
            VolumeAvg("volume_avg_20", 20),
            MFI("mfi_14", 14),

            # Oscillator Indicators
            MACD("macd_12_26_9", 12, 26, 9),
            StochasticOscillator("stoch_14_3_3", 14, 3, 3),
            CCI("cci_14", 14),

            # Trend Strength Indicators
            ADX("adx_14", 14),

            # Price Indicators
            TypicalPrice("typical_price"),
        ]

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:
        """
        This algorithm only collects data - it never trades.
        Returns HOLD action always to maintain position for data collection.
        """
        return Action(Act.HOLD)


class ProfitableIntradayAlgo(AlgorithmBase):
    def __init__(self):
        super().__init__()
        self.metrics = [
            VWAP("vwap"),
            ATR("atr_14", 14),
            RSI("rsi_14", 14),
            ROC("roc_5", 5),  # faster momentum
            VWMA("vwma_20", 20),
        ]
        self.position_open_time = None
        self.stop_loss = None
        self.target_price = None
        self.risk_per_trade = 0.01  # risk 1% of funds per trade
        self.square_off_time = dt_time(15, 10)  # square off before 3:10 PM

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics, mrkt_price, current_dt, positions, funds, history):
        vwap = metrics.get("vwap", mrkt_price)
        atr = metrics.get("atr_14", 1.0)
        rsi = metrics.get("rsi_14", 50)
        roc = metrics.get("roc_5", 0)
        vwma = metrics.get("vwma_20", mrkt_price)
        stock_qty = positions.getHoldingQuantity()

        # Avoid trading first 15 minutes (market open noise)
        if current_dt.time() < dt_time(9, 45):
            return Action(Act.HOLD)

        # Square off at cut-off time
        if current_dt.time() >= self.square_off_time and stock_qty > 0:
            return Action(Act.SELL, stock_qty)

        entry_price = positions.getHoldingAvgPrice()
        # Exit if stop-loss or target hit
        if stock_qty > 0 and entry_price:
            pnl_pct = (mrkt_price - entry_price) / entry_price
            if pnl_pct <= -1.5 * atr / entry_price or pnl_pct >= 3 * atr / entry_price:
                self.stop_loss = None
                self.target_price = None
                return Action(Act.SELL, stock_qty)

        # Entry conditions: simple momentum breakout with confirmation
        # Price above VWAP + ROC positive + RSI < 70 + VWMA confirms trend + low volatility condition
        if stock_qty == 0:
            if (mrkt_price > vwap and roc > 0 and rsi < 70 and mrkt_price > vwma and atr > 0):
                # Calculate position size based on risk_per_trade and ATR stop-loss
                stop_loss_price = mrkt_price - 1.5 * atr
                if stop_loss_price <= 0:
                    return Action(Act.HOLD)
                risk_per_share = mrkt_price - stop_loss_price
                max_risk_amount = funds * self.risk_per_trade
                qty = int(max_risk_amount // risk_per_share)
                if qty > 0 and qty * mrkt_price <= funds:
                    self.entry_price = mrkt_price
                    self.position_open_time = current_dt
                    self.stop_loss = stop_loss_price
                    self.target_price = mrkt_price + 3 * atr  # approx 2:1 RR
                    return Action(Act.BUY, qty)

        return Action(Act.HOLD)
