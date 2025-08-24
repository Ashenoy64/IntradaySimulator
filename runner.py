from Holdings import Holdings
from collections.abc import Callable
import time
from trend_iter import TrendIter, Trend
from Action import Action
from datetime import datetime


class Runner:
    def __init__( self, funds:float, positions:Holdings, timer:int=0 ) -> None:
        self.funds = funds
        self.positions = positions
        self.callback = None
        self.timer = timer
        self.action_history = []
        self.data_history = []

    def run( self, data_iter:TrendIter, metric_calculator:Callable[ [ list, Trend ], dict ],
            algoritm:Callable[ [ dict, float, datetime, Holdings, float, list ], Action ],
            action_resolver:Callable[ [Action,float, Holdings, float], float ] ):
        self.data_history = []
        self.action_history = []
        for datetime, mrkt_price, trend in data_iter:
            metrics = metric_calculator( self.data_history, trend )
            action = algoritm( metrics, mrkt_price, datetime, self.positions, self.funds, self.data_history )
            self.funds = action_resolver( action, mrkt_price, self.positions, self.funds )
            if self.timer>0:
                time.sleep(self.timer)
            self.action_history.append( action )
            self.data_history.append( trend )
            if self.callback:
                self.callback( datetime, mrkt_price, trend, metrics, action, self.funds, self.positions )


    def getDataHistory( self )->list:
        return self.data_history
    
    def getActionHistory( self )->list:
        return self.action_history

    def setCallback( self, func )->None:
        if func is not callable:
            raise Exception("func needs to be callable")
        self.callback = func

    def getPositions( self )->Holdings:
        return self.positions

    def getFunds( self )->float:
        return self.funds

    def setFunds( self, funds:float ):
        self.funds = funds

    def setPositions( self, positions:Holdings ):
        self.positions = positions
        