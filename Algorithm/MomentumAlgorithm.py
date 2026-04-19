from Sim import Holdings, Act, Action
from datetime import datetime
from Metrics.Metrics import ROC, RSI, VWAP
from . import AlgorithmBaseWithRisk

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

    def run(self, metrics:dict, mrkt_price:float, current_dt:datetime,
             positions:Holdings, funds:float, history:list )->Action:
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

