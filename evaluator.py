import pandas as pd
from sklearn.metrics import accuracy_score, mean_squared_error
from typing import (
    Dict,
)
import numpy as np


def SimpleDeciderEval(model, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    return {"accuracy": float(acc)}


def SimplePredictorEval(model, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    rmse = np.sqrt(mse)
    return {"mse": mse, "rmse": rmse}