import pandas as pd
from typing import Dict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVR
from sklearn.metrics import accuracy_score, mean_squared_error
from . import ScalerBase
from . import TrainerBase, MODEL_TYPE

class RandomForestDecider( TrainerBase ):
    def __init__( self, X:pd.DataFrame, Y:pd.Series ) -> None:
        super().__init__( X, Y, MODEL_TYPE.DECIDER )

    def train( self ) -> None:
        self.X_train, self.X_test, self.y_train, self.y_test = self.splitter(
            self.x, 
            self.y,
            test_size=self.split_rate,
            random_state=self.random_seed,
            shuffle=self.do_shuffle,
        )
        if self.scaler is not None:
            print( "Columns in training data before scaling:", self.X_train.columns.tolist() )
            self.scaler.fit( self.X_train )
            self.X_train = self.scaler.transform( self.X_train )
            self.X_test = self.scaler.transform( self.X_test )

        self.model = RandomForestClassifier(
            n_estimators = self.modelParams.get( 'n_estimators',100 ),
            max_depth = self.modelParams.get( 'max_depth', None ),
            random_state = self.random_seed,
            n_jobs = self.modelParams.get( 'n_jobs', -1 )
        )
        self.model.fit( self.X_train, self.y_train )

    def setModelHyperParams( self,
                    n_estimators:str = 100,
                    max_depth:int|None = None,
                    n_jobs:int = -1 ):
        self.modelParams["n_estimators"] = n_estimators
        self.modelParams["max_depth"] = max_depth
        self.modelParams["n_jobs"] = n_jobs

    def test( self ) -> Dict[str, float]:
        preds = self.model.predict( self.X_test )
        acc = accuracy_score( self.y_test, preds )
        return { "accuracy": float( acc ) }



class SVRPredictor( TrainerBase ):
    def __init__( self, X:pd.DataFrame, Y:pd.Series ) -> None:
        super().__init__( X, Y, MODEL_TYPE.PREDICTOR )

    def train( self ) -> None:
        self.X_train, self.X_test, self.y_train, self.y_test = self.splitter(
            self.x,
            self.y,
            test_size = self.split_rate,
            random_state = self.random_seed,
            shuffle = self.do_shuffle
        )
        if self.scaler is not None:
            self.X_train = self.scaler.fit_transform( self.X_train )
            self.X_test = self.scaler.transform( self.X_test )

        self.model = SVR(
            kernel = self.modelParams.get( 'kernel', 'rbf' ),
            C =  self.modelParams.get( 'c', 100 ),
            gamma = self.modelParams.get( 'gamma', 0.1 ),
            epsilon = self.modelParams.get( 'epsilon', 0.1 )
        )
        self.model.fit( self.X_train, self.y_train )
    
    def setModelHyperParams( self,
                    kernel:str = 'rbf',
                    c:int = 100,
                    gamma:float = 0.1,
                    epsilon:float = 0.1 ):
        self.modelParams["kernel"] = kernel
        self.modelParams["c"] = c
        self.modelParams["gamma"] = gamma
        self.modelParams["epsilon"] = epsilon


    def test( self ) -> Dict[ str, float ]:
        preds = self.model.predict( self.X_test )
        mse = mean_squared_error( self.y_test, preds )
        rmse = np.sqrt( mse )
        return { "mse": mse, "rmse": rmse }
    
