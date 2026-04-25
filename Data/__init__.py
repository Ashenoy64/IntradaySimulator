from .RegexStr import RegexString
from typing import Optional, List
import pandas as pd

class OperationBase:
    def __init__( self, cols:Optional[List[str]] = None, inPlace:bool = False ) -> None:
        self.operationColumns = cols if cols else []
        self.inPlace = inPlace

    def operate( self, df:pd.DataFrame )->pd.DataFrame:
        raise NotImplementedError()
    
    def setOperationColumns( self, cols:list[ str ] )->None:
        self.operationColumns = cols

    def getOperationColumns( self )->list[ str ]:
        return self.operationColumns
    
    def isInplace( self )->bool:
        return self.inPlace
    