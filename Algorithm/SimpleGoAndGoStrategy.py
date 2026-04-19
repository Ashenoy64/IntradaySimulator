from Sim import Holdings, Act, Action
from datetime import datetime
from . import AlgorithmBase

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