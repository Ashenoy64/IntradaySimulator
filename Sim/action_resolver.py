from .Action import Action, Act
from .Holdings import Holdings


def action_resolver(action:Action,mrkt_price:float, positions:Holdings, funds:float)->float:
    if( action.getAction() == Act.BUY ):
        quantity = action.getQuantity()
        positions.addPosition( quantity, mrkt_price )
        funds -= quantity*mrkt_price

    elif( action.getAction() == Act.SELL ):
        quantity = action.getQuantity()
        positions.removePosition(quantity)
        funds += quantity*mrkt_price
        
    return funds