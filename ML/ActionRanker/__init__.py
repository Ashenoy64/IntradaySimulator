from ..RankLabler import RankLabeler
from ..RankLabler.GNBLabler import GNBLabeler
import pandas as pd
import os
from typing import Optional
from Settings import SIMULATION_RESULTS_PATH

class ActionRankerBase:
    def __init__( self, name, lookahead:int= 5 ,updated_name:Optional[str] = None ):
        self.file_name = self.maybeAddCSVExt( name )
        self.lookahead = lookahead
        
        self.new_file_name =  self.maybeAddCSVExt( updated_name ) if updated_name else self.file_name
        self.read_base_dir = SIMULATION_RESULTS_PATH
        self.write_base_dir = SIMULATION_RESULTS_PATH

        self.rankLabeler = GNBLabeler()
    
    def maybeAddCSVExt( self, name:str )->str:
        if name.endswith( ".csv" ):
            return name
        return name+".csv"

    def setReadBaseDir( self, base_dir:str )->None:
        self.read_base_dir = base_dir
    
    def setWriteBaseDir( self, base_dir:str )->None:
        self.write_base_dir = base_dir

    def readFile( self )->pd.DataFrame:
        path = os.path.join( self.read_base_dir, self.file_name )
        return pd.read_csv( path )  

    def writeFile( self, df:pd.DataFrame )->None:
        path = os.path.join( self.write_base_dir, self.new_file_name )   
        df.to_csv( path, index=False )

    def rankAction( self )->None:
        raise NotImplementedError()

    def setRankLabler( self, rankLabler:RankLabeler )->None:
        self.rankLabeler = rankLabler

    def rankLabel( self, rank:float )->str|float:
        return self.rankLabeler.mapRank(rank)