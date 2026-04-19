from Sim import Holdings, Act, Action
from datetime import datetime, time as dt_time

class AlgorithmBase:
    def __init__(self)->None:
        pass
    
    def getAlgoMetrics(self):
        return {}

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:
        
        return Action(Act.HOLD, 0)

class AlgorithmBaseWithRisk(AlgorithmBase):
    def __init__(self, stop_loss_pct:float=0.05, target_pct:float=0.07, square_off_time=dt_time(15, 15)):
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
