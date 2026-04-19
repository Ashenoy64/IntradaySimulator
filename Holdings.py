class Holdings:
    def __init__( self, quantity:int = 0, avg_price:float = 0 ) -> None:
        self.quantity = quantity
        self.average_price = avg_price

    def addPosition( self, quantity:int, price:float )->None:
        amt = quantity * price
        self.average_price = ( ( self.average_price * quantity ) + amt ) /\
          ( quantity + self.quantity )
        self.quantity += quantity 

    def removePosition( self, quantity:int )->None:
        if quantity > self.quantity:
            raise Exception("Quantity to sell is more than holdings")
        
        self.quantity -= quantity
        if self.quantity == 0:
            self.average_price = 0

    def getHoldingQuantity( self )->int:
        return self.quantity
    
    def getHoldingAvgPrice( self )->float:
        return self.average_price
    
    def getTotal(self)->float:
        return self.quantity * self.average_price