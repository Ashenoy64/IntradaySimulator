from Sim import Holdings, Act, Action
from datetime import datetime
from Metrics.Metrics import EMA, RSI, VWMA
from . import AlgorithmBaseWithRisk

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

    def run(self, metrics:dict, mrkt_price:float, current_dt:datetime,
             positions:Holdings, funds:float, history:list )->Action:
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