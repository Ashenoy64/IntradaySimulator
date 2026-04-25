from pandas import DataFrame as DF
from Settings import SCALER_PATH, MODELS_STORE_PATH
from collections import Counter
import os
import joblib
import pandas as pd
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Tuple,
    List,
)
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split

DataSplitFunc = Callable[
    [
        pd.DataFrame,         # X
        pd.Series | pd.DataFrame,  # y
        float | None,         # test_size
        float | None,         # train_size
        int | None,           # random_state
        bool,                 # shuffle
        Optional[pd.Series],  # stratify
    ],
    Tuple[pd.DataFrame, pd.DataFrame, pd.Series | pd.DataFrame, pd.Series | pd.DataFrame],
]

EvaluatorFunc = Callable[
    [BaseEstimator, pd.DataFrame, pd.Series | pd.DataFrame], Dict[str, float]
]

class MODEL_TYPE( Enum ):
    DECIDER = "decider"
    PREDICTOR = "predictor"


class ScalerBase:
    def __init__( self, numCols:Optional[List[str]] = None, catCols:Optional[List[str]]= None ) -> None:
        self.numericCols = [] if numCols is None else numCols
        self.categoricalCols = [] if catCols is None else catCols
        self.numericScaler = None
        self.categoricalEncoders = None
        self.base_dir = SCALER_PATH

    def determineColTypes( self, df:DF ) -> None:
        if df.isnull().any( axis = 1 ).any():
            print( "Warning: Some rows have missing values!" )
        if self.numericCols is not None and self.numericCols == []:
            self.numericCols = df.select_dtypes( include = 'number' ).columns.tolist()
        if self.categoricalCols is not None and self.categoricalCols == []:
            self.categoricalCols = df.select_dtypes( include = [ 'object', 'category' ] ).columns.tolist()

    def fit( self, df:DF ) -> 'ScalerBase':
        raise NotImplementedError( "fit() must be implemented by subclass" )

    def transform( self, df:DF ) -> DF:
        raise NotImplementedError( "transform() must be implemented by subclass" )

    def fit_transform( self, df:DF ) -> DF:
        self.fit( df )
        return self.transform( df )

    def setScalerBaseDir( self, base_dir:str )->None:
        self.base_dir = base_dir

    def loadLoadedObject( self, saved:Dict )->None:
        pass

    def __loadLoadedObject( self, saved:Dict )->None:
        self.numericScaler = saved['numericScaler']
        self.categoricalEncoders = saved['categoricalEncoders']
        self.numericCols = saved['numericCols']
        self.categoricalCols = saved['categoricalCols']
        self.loadLoadedObject( saved )
    
    def load( self, name:str ) -> None:
        file_path = os.path.join( self.base_dir, f"{ name }.joblib" )
        if not os.path.exists( file_path ):
            raise FileNotFoundError( f"Saved scaler not found at { file_path }" )

        saved = joblib.load( file_path )
        self.__loadLoadedObject( saved )

    def setSaveObject( self )->Dict:
        return {}
    
    def __setSaveObject( self )->Dict:
        save_obj = {
            'numericScaler': self.numericScaler,
            'categoricalEncoders': self.categoricalEncoders,
            'numericCols': self.numericCols,
            'categoricalCols': self.categoricalCols
        }
        user_set = self.setSaveObject()
        save_obj.update( user_set )
        return save_obj

    def save( self, name:str ) -> None:
        filePath = os.path.join( self.base_dir, f"{ name }.joblib" )
        os.makedirs( os.path.dirname( filePath ), exist_ok = True )
        save_obj = self.__setSaveObject()
        joblib.dump( save_obj, filePath, compress = 3 )

    def setNumericCols( self, cols:List[str] ) -> None:
        self.numericCols = col

    def setCategoricalCols( self, cols:List[str] ) -> None:
        self.categoricalCols = cols

    def getNumericCols( self ) -> List[str]:
        return self.numericCols

    def getCategoricalCols( self ) -> list[str]:
        return self.categoricalCols



class TrainerBase:
    def __init__(
        self,
        X: pd.DataFrame,
        Y: pd.Series | pd.DataFrame,
        model_type: MODEL_TYPE = MODEL_TYPE.DECIDER,
    ) -> None:
        self.splitter = train_test_split
        self.x: pd.DataFrame = X
        self.y: pd.Series | pd.DataFrame = Y
        self.model_type: MODEL_TYPE = model_type

        self.model = None
        self.do_shuffle: bool = False
        self.split_rate: float = 0.25
        self.random_seed: int = 42

        self.scaler:Optional[ ScalerBase ] = None
        self.evaluator = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        self.base_dir = MODELS_STORE_PATH
        self.cols = X.columns

    def train( self ) -> None:
        raise NotImplementedError()

    def test( self ) -> None:
        raise NotImplementedError()

    def setSeed( self, seed:int ) -> None:
        self.random_seed = seed

    def setModelHyperParams( self, **kwargs )->None:
        return

    def setShuffle( self, shuffle: bool ) -> None:
        self.do_shuffle = shuffle

    def setSplitRate( self, rate:float ) -> None:
        self.split_rate = rate

    def setDataSplitter( self, splitter:DataSplitFunc ) -> None:
        self.splitter = splitter

    def __loadLoadedObject( self, obj: Dict[str, Any] ) -> None:
        self.model = obj.get( "model", None )
        self.X_train = obj.get( "X_train", None )
        self.X_test = obj.get("X_test", None )
        self.y_train = obj.get( "y_train", None )
        self.y_test = obj.get( "y_test", None )
        self.evaluator = obj.get( "evaluator", None )
        scaler = obj.get( "scaler", None )
        self.cols = obj.get( "columns", [] )
        if scaler:
            self.scaler = scaler
        
        self.loadLoadedObject( obj )

    def loadLoadedObject( self, obj: Dict[str, Any] ) -> None:
        pass

    def setModelPath( self, base_dir:str )->None:
        self.base_dir = base_dir

    def load( self, name:str ) -> None:
        base_dir =  os.path.join( self.base_dir, name, self.model_type.value )
        file_path = os.path.join( base_dir, f"{ name }.joblib" )
        if not os.path.exists( file_path ):
            raise FileNotFoundError( f"Saved model not found at { file_path }" )

        saved = joblib.load( file_path )
        self.__loadLoadedObject( saved )
        if self.scaler:
            self.scaler.setScalerBaseDir( base_dir )
            self.scaler.load( f"{name}_scaler" )

    def __setSaveObject( self ) -> Dict[str, Any]:
        save_obj = {
            "model": self.model,
            "X_train": self.X_train,
            "X_test": self.X_test,
            "y_train": self.y_train,
            "y_test": self.y_test,
            "evaluator": self.evaluator,
            "columns" : self.cols
        }

        if self.scaler:
            save_obj[ "scaler" ] = self.scaler
        
        user_set = self.setSaveObject()
        save_obj.update( user_set )
        return save_obj
    
    def setSaveObject(self) -> Dict[str, Any]:
        return {}

    def save( self, name:str ) -> None:
        base_dir =  os.path.join( self.base_dir, name, self.model_type.value )
        os.makedirs( base_dir, exist_ok = True )
        save_obj = self.__setSaveObject()
        file_path =  os.path.join(  base_dir, f"{ name }.joblib")
        joblib.dump( save_obj, file_path, compress = 3 )
        if self.scaler:
            self.scaler.setScalerBaseDir( base_dir )
            self.scaler.save( f"{name}_scaler" )

    def evaluate( self ) -> Dict[str, float]:
        if self.evaluator is None:
            raise ValueError( "Evaluator function is not set." )
        return self.evaluator( self.model, self.X_test, self.y_test )

    def setEvaluator( self, evaluator:EvaluatorFunc ) -> None:
        self.evaluator = evaluator

    def setScaler( self, scaler:ScalerBase )->None:
        self.scaler = scaler

    def predict(self, X:list[dict])->list:
        X = pd.DataFrame(X, columns=self.cols)
        if self.scaler:
            X = self.scaler.transform(X)
        y = self.model.predict(X)
        return y

    @classmethod
    def load_only(cls) -> "TrainerBase":
        """Create an empty instance for loading a saved model."""
        empty_X = pd.DataFrame()
        empty_Y = pd.Series(dtype=float)
        instance = cls(empty_X, empty_Y)
        return instance