from Sim import Holdings, Act, Action
from datetime import datetime, time as dt_time
from Metrics.Metrics import VWAP, ATR, RSI, ROC, VWMA
from . import AlgorithmBase


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

    def run(self, metrics:dict, mrkt_price:float, current_dt:datetime,
             positions:Holdings, funds:float, history:list )->Action:
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