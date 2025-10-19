from pandas import DataFrame as DF
import os
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from Settings import SCALER_PATH
from typing import Dict, Optional, List
from collections import Counter


class ScalerBase:
    def __init__(self, numCols: Optional[List[str]] = None, catCols: Optional[List[str]]= None) -> None:
        self.numericCols = [] if numCols is None else numCols
        self.categoricalCols = [] if catCols is None else catCols
        self.numericScaler = None
        self.categoricalEncoders = None

    def determineColTypes(self, df: DF) -> None:
        if df.isnull().any(axis=1).any():
            print("Warning: Some rows have missing values!")
        if self.numericCols is not None and self.numericCols == []:
            self.numericCols = df.select_dtypes(include='number').columns.tolist()
        if self.categoricalCols is not None and self.categoricalCols == []:
            self.categoricalCols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    def fit(self, df: DF) -> 'ScalerBase':
        raise NotImplementedError("fit() must be implemented by subclass")

    def transform(self, df: DF) -> DF:
        raise NotImplementedError("transform() must be implemented by subclass")

    def fit_transform(self, df: DF) -> DF:
        self.fit(df)
        return self.transform(df)


    def loadLoadedObject(self, obj:Dict)->None:
        raise NotImplementedError("loadLoadedObject() must be implemented by subclass")
    
    def load(self, name: str) -> None:
        file_path = os.path.join(SCALER_PATH, f"{name}.joblib")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Saved scaler not found at {file_path}")

        saved = joblib.load(file_path)
        self.loadLoadedObject(saved)

    def setSaveObject(self)->Dict:
        raise NotImplementedError("setSaveObject() must be implemented by subclass")

    def save(self, name: str) -> None:
        filePath = os.path.join(SCALER_PATH,f"{name}.joblib")
        os.makedirs( os.path.dirname(filePath), exist_ok=True)
        save_obj = self.setSaveObject()
        joblib.dump(save_obj,filePath, compress=3)

    def setNumericCols(self, cols: List[str]) -> None:
        self.numericCols = cols

    def setCategoricalCols(self, cols: List[str]) -> None:
        self.categoricalCols = cols

    def getNumericCols(self) -> List[str]:
        return self.numericCols

    def getCategoricalCols(self) -> list[str]:
        return self.categoricalCols

class STDScaler(ScalerBase):
    def __init__(self, numCols:Optional[List[str]] = None, catCols: Optional[List[str]] = None) -> None:
        super().__init__(numCols, catCols)
        self.numericScaler = StandardScaler()
        self.categoricalEncoders = dict()

    def fit(self, df: DF) -> 'STDScaler':
        if not (self.numericCols or self.categoricalCols):
            self.determineColTypes(df)

        if self.numericCols:
            self.numericScaler.fit(df[self.numericCols])
        
        self.categoricalEncoders = {}
        for col in self.categoricalCols:
            enc = LabelEncoder()
            enc.fit(df[col].astype(str))
            self.categoricalEncoders[col] = enc
        return self

    def transform(self, df: DF) -> DF:
        df_copy = df.copy()

        if self.numericCols:
            df_copy[self.numericCols] = self.numericScaler.transform(df_copy[self.numericCols])

        for col in self.categoricalCols:
            if col in self.categoricalEncoders:
                enc = self.categoricalEncoders[col]
                df_copy[col] = enc.transform(df_copy[col].astype(str))

        return df_copy

    def fit_transform(self, df: DF) -> DF:
        self.fit(df)
        return self.transform(df)

    def setSaveObject(self) -> Dict:
        return  {
            'numericScaler': self.numericScaler,
            'categoricalEncoders': self.categoricalEncoders,
            'numericCols': self.numericCols,
            'categoricalCols': self.categoricalCols
        }
        

    def loadLoadedObject(self, saved:Dict) -> None:
        self.numericScaler = saved['numericScaler']
        self.categoricalEncoders = saved['categoricalEncoders']
        self.numericCols = saved['numericCols']
        self.categoricalCols = saved['categoricalCols']


class WeightedLabelScaler(ScalerBase):
    def __init__(self, numCols: Optional[List[str]] = None, catCols: Optional[List[str]] = None) -> None:
        super().__init__(numCols, catCols)
        self.numericScaler = StandardScaler()
        self.labelWeights: Dict[str, Dict[str, float]] = {}

    def fit(self, df: DF) -> 'WeightedLabelScaler':
        if not (self.numericCols or self.categoricalCols):
            self.determineColTypes(df)

        if self.numericCols:
            self.numericScaler.fit(df[self.numericCols])

        self.labelWeights = {}
        for col in self.categoricalCols:
            counts = Counter(df[col].astype(str))
            total = sum(counts.values())
            weights = {label: total / count for label, count in counts.items()}
            self.labelWeights[col] = weights

        return self

    def transform(self, df: DF) -> DF:
        df_copy = df.copy()

        if self.numericCols:
            df_copy[self.numericCols] = self.numericScaler.transform(df_copy[self.numericCols])

        for col in self.categoricalCols:
            weights = self.labelWeights.get(col, {})
            df_copy[col] = df_copy[col].astype(str).map(weights).fillna(0).astype(float)

        return df_copy

    def fit_transform(self, df: DF) -> DF:
        self.fit(df)
        return self.transform(df)

    def setSaveObject(self) -> Dict:
        return {
            'numericScaler': self.numericScaler,
            'labelWeights': self.labelWeights,
            'numericCols': self.numericCols,
            'categoricalCols': self.categoricalCols
        }

    def loadLoadedObject(self, saved: Dict) -> None:
        self.numericScaler = saved['numericScaler']
        self.labelWeights = saved['labelWeights']
        self.numericCols = saved['numericCols']
        self.categoricalCols = saved['categoricalCols']