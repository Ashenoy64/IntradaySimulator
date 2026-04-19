from Holdings import Holdings
from collections.abc import Callable
import time
from metric_calculator import MetricCalculator
from algoritm import AlgorithmBase
from trend_iter import TrendIter, Trend
from Action import Action
from datetime import datetime


class Runner:
    def __init__( self, 
                funds:float,
                positions:Holdings,
                algorithm:AlgorithmBase|None = None,
                metric_calculator:MetricCalculator|None = None,
                timer:int=0 ) -> None:
        self.funds = funds
        self.positions = positions

        self.callback = None
        self.algorithm = algorithm
        self.metric_calculator = metric_calculator
        self.timer = timer

        self.action_history = []
        self.data_history = []
        self.time_history = []

    def run( self, data_iter:TrendIter,
            action_resolver:Callable[[Action,float, Holdings, float],float] ):
        self.data_history = []
        self.action_history = []
        metrics = {}

        if not self.algorithm:
            raise Exception( "Algorithm for Runner not set" )

        for datetime, mrkt_price, trend in data_iter:
            if self.metric_calculator:
                metrics = self.metric_calculator.calculateMetric( self.data_history, trend )

            action = self.algorithm.run( metrics, mrkt_price, datetime,
                    self.positions, self.funds, self.data_history )
            self.funds = action_resolver( action, mrkt_price, self.positions, self.funds )
            
            # In case i need to do the trade irl?
            if self.callback:
                self.callback( datetime, mrkt_price, trend, metrics,
                                    action, self.funds, self.positions )
            self.action_history.append( action )
            self.data_history.append( trend )
            self.time_history.append( datetime )
            if self.timer > 0:
                time.sleep( self.timer )


    def getDataHistory( self )->list:
        return self.data_history
    
    def getActionHistory( self )->list:
        return self.action_history
    
    def getTimeHistory( self )->list:
        return self.time_history

    def getMetircHistory( self )->list:
        if self.metric_calculator:
            return self.metric_calculator.getMetircHistory()
        else:
            return []

    def setCallback( self, func )->None:
        if func is not callable:
            raise Exception( "func needs to be callable" )
        self.callback = func

    def setAlgorithm( self, algorithm:AlgorithmBase )->None:
        self.algorithm = algorithm

    def setCalculator( self, metric_calculator:MetricCalculator )->None:
        self.metric_calculator = metric_calculator

    def getPositions( self )->Holdings:
        return self.positions

    def getFunds( self )->float:
        return self.funds

    def setFunds( self, funds:float ):
        self.funds = funds

    def setPositions( self, positions:Holdings ):
        self.positions = positions
        