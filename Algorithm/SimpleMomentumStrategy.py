from datetime import datetime
from Sim import Holdings, Act, Action
from . import AlgorithmBase

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

