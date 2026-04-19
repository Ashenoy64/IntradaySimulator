from Sim import Holdings, Act, Action
from datetime import datetime
from Metrics.Metrics import MACD, RSI, VWAP
from . import AlgorithmBaseWithRisk

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

    def run(self, metrics:dict, mrkt_price:float, current_dt:datetime,
             positions:Holdings, funds:float, history:list )->Action:
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
