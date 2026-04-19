from enum import Enum

class Act(Enum):
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'

class Action:
    def __init__(self, act:Act, quantity:int=0 )->None:
        self.act =act
        self.quantity = quantity

    def getActonStr( self )->str:
        return self.act.value
    
    def getAction( self )->Act:
        return self.act
    
    def getQuantity( self )->int:
        return self.quantity