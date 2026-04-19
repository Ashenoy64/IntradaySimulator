from Sim import Holdings, Act, Action
from datetime import datetime
from Metrics.Metrics import RSI, VWMA, ATR
from . import AlgorithmBaseWithRisk

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

    def run(self, metrics:dict, mrkt_price:float, current_dt:datetime,
             positions:Holdings, funds:float, history:list )->Action:
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