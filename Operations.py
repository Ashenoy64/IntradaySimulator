import pandas as pd
from RegexStr import RegexString
from Metrics import SMA, BollingerBands
from Trend import Trend

class OperationBase:
    def __init__(self, cols:list[str]|None=None, inPlace:bool=False) -> None:
        self.operationColums = cols if cols else []
        self.inPlace = inPlace

    def operate(self, df:pd.DataFrame)->pd.DataFrame:
        raise NotImplementedError()
    
    def setOperationColums(self, cols:list[str])->None:
        self.operationColums = cols

    def getOperationColumns(self)->list[str]:
        return self.operationColums
    
    def isInplace(self)->bool:
        return self.inPlace
    

class RemoveEmptyNullRows( OperationBase ):
    def __init__( self ) -> None:
        super().__init__( cols=[ RegexString(".*") ] )

    def operate(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna().copy()
    

class RemoveColumns( OperationBase ):
    def __init__( self, cols:list[str]|None=None ) -> None:
        super().__init__( cols=cols, inPlace=True )

    def operate(self, df: pd.DataFrame) -> pd.DataFrame:
        other_columns = list(set(df.columns)-set(self.operationColums))
        return df[other_columns]
    


class PercentChange( OperationBase ):
    def __init__(self, cols: list[str] | None = None) -> None:
        super().__init__(cols)

    def operate(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pct_change() * 100 
    

class AddSmaFiveMetricColumn( OperationBase ):
    def __init__( self ) -> None:
        super().__init__( cols=['high', 'low', 'open', 'close', 'volume' ]  )
        self.sma_calc = SMA("sma", 5)

    def operate(self, df: pd.DataFrame) -> pd.DataFrame:
        sma_values = []
        for row in df.itertuples(index=False):
            trend_obj = Trend(row.high, row.low, row.open, row.close, row.volume)
            self.sma_calc.update(trend_obj)
            _, sma_value = self.sma_calc.run()
            sma_values.append(sma_value)
        df = pd.DataFrame()
        df['sma'] = sma_values

        return df[['sma']]
            
class AddBollingerBandTwentyColumn(OperationBase):
    def __init__(self):
        super().__init__( cols=['high', 'low', 'open', 'close', 'volume' ]  )
        self.bbands = BollingerBands(key_upper='bb_upper', key_middle='bb_middle', key_lower='bb_lower', N=20, num_std=2)

    def operate(self, df: pd.DataFrame) -> pd.DataFrame:
        upper_values = []
        middle_values = []
        lower_values = []

        for row in df.itertuples(index=False):
            trend_obj = Trend(row.high, row.low, row.open, row.close, row.volume)
            self.bbands.update(trend_obj)
            results = self.bbands.run()
            upper_values.append(results[0][1])
            middle_values.append(results[1][1])
            lower_values.append(results[2][1])
        df = pd.DataFrame()
        df['bb_upper'] = upper_values
        df['bb_middle'] = middle_values
        df['bb_lower'] = lower_values

        return df[['bb_upper', 'bb_middle', 'bb_lower']]
    
