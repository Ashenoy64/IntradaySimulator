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
    TypeVar,
)
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split
from Settings import MODELS_STORE_PATH
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVR
from sklearn.metrics import accuracy_score, mean_squared_error
from Scaler import ScalerBase

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


class MODEL_TYPE(Enum):
    DECIDER = "decider"
    PREDICTOR = "predictor"


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

        self.scaler:Optional[ScalerBase] = None
        self.evaluator = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

    def train(self) -> None:
        raise NotImplementedError()

    def test(self) -> None:
        raise NotImplementedError()

    def setSeed(self, seed: int) -> None:
        self.random_seed = seed

    def setShuffle(self, shuffle: bool) -> None:
        self.do_shuffle = shuffle

    def setSplitRate(self, rate: float) -> None:
        self.split_rate = rate

    def setDataSplitter(self, splitter: DataSplitFunc) -> None:
        self.splitter = splitter

    def loadLoadedObject(self, obj: Dict[str, Any]) -> None:
        raise NotImplementedError("loadLoadedObject() must be implemented by subclass")

    def load(self, name: str) -> None:
        file_path = os.path.join(MODELS_STORE_PATH, self.model_type.value, f"{name}.joblib")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Saved model not found at {file_path}")

        saved = joblib.load(file_path)
        self.loadLoadedObject(saved)

    def setSaveObject(self) -> Dict[str, Any]:
        raise NotImplementedError("setSaveObject() must be implemented by subclass")

    def save(self, name: str) -> None:
        filePath = os.path.join(MODELS_STORE_PATH, self.model_type.value, f"{name}.joblib")
        os.makedirs(os.path.dirname(filePath), exist_ok=True)
        save_obj = self.setSaveObject()
        joblib.dump(save_obj, filePath, compress=3)

    def evaluate(self) -> Dict[str, float]:
        if self.evaluator is None:
            raise ValueError("Evaluator function is not set.")
        return self.evaluator(self.model, self.X_test, self.y_test)

    def setEvaluator(self, evaluator: EvaluatorFunc) -> None:
        self.evaluator = evaluator

    def setScaler(self, scaler:ScalerBase)->None:
        self.scaler = scaler

class RandomForestDecider(TrainerBase):
    def __init__(self, X: pd.DataFrame, Y: pd.Series) -> None:
        super().__init__(X, Y, MODEL_TYPE.DECIDER)

    def train(self) -> None:
        self.X_train, self.X_test, self.y_train, self.y_test = self.splitter(
            self.x, 
            self.y,
            test_size=self.split_rate,
            random_state=self.random_seed,
            shuffle=self.do_shuffle,
        )
        if self.scaler is not None:
            print("Columns in training data before scaling:", self.X_train.columns.tolist())
            self.scaler.fit(self.X_train)
            self.X_train = self.scaler.transform(self.X_train)
            self.X_test = self.scaler.transform(self.X_test)

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,
            random_state=self.random_seed,
            n_jobs=-1
        )
        self.model.fit(self.X_train, self.y_train)

    def test(self) -> Dict[str, float]:
        preds = self.model.predict(self.X_test)
        acc = accuracy_score(self.y_test, preds)
        return {"accuracy": float(acc)}

    def loadLoadedObject(self, obj: Dict[str, Any]) -> None:
        self.model = obj["model"]
        self.X_train = obj.get("X_train", None)
        self.X_test = obj.get("X_test", None)
        self.y_train = obj.get("y_train", None)
        self.y_test = obj.get("y_test", None)

    def setSaveObject(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "X_train": self.X_train,
            "X_test": self.X_test,
            "y_train": self.y_train,
            "y_test": self.y_test
        }



class SVRPredictor(TrainerBase):
    def __init__(self, X: pd.DataFrame, Y: pd.Series) -> None:
        super().__init__(X, Y, MODEL_TYPE.PREDICTOR)

    def train(self) -> None:
        self.X_train, self.X_test, self.y_train, self.y_test = self.splitter(
            self.x,
            self.y,
            test_size=self.split_rate,
            random_state=self.random_seed,
            shuffle=self.do_shuffle
        )
        if self.scaler is not None:
            self.scaler.fit(self.X_train)
            self.X_train = self.scaler.transform(self.X_train)
            self.X_test = self.scaler.transform(self.X_test)

        self.model = SVR(
            kernel="rbf",
            C=100,
            gamma=0.1,
            epsilon=0.1
        )
        self.model.fit(self.X_train, self.y_train)

    def test(self) -> Dict[str, float]:
        preds = self.model.predict(self.X_test)
        mse = mean_squared_error(self.y_test, preds)
        rmse = np.sqrt(mse)
        return {"mse": mse, "rmse": rmse}

    def loadLoadedObject(self, obj: Dict[str, Any]) -> None:
        self.model = obj["model"]
        self.X_train = obj.get("X_train", None)
        self.X_test = obj.get("X_test", None)
        self.y_train = obj.get("y_train", None)
        self.y_test = obj.get("y_test", None)

    def setSaveObject(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "X_train": self.X_train,
            "X_test": self.X_test,
            "y_train": self.y_train,
            "y_test": self.y_test
    }

