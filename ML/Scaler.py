from pandas import DataFrame as DF
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Dict, Optional, List
from collections import Counter
from . import ScalerBase


class STDScaler( ScalerBase ):
    def __init__( self, numCols:Optional[List[str]] = None, catCols:Optional[List[str]] = None ) -> None:
        super().__init__( numCols, catCols )
        self.numericScaler = StandardScaler()
        self.categoricalEncoders = dict()

    def fit(self, df:DF ) -> 'STDScaler':
        if not ( self.numericCols or self.categoricalCols ):
            self.determineColTypes( df )

        if self.numericCols:
            self.numericScaler.fit( df[ self.numericCols ] )
        
        self.categoricalEncoders = {}
        for col in self.categoricalCols:
            enc = LabelEncoder()
            enc.fit( df[ col ].astype( str ) )
            self.categoricalEncoders[ col ] = enc
        return self

    def transform( self, df:DF ) -> DF:
        df_copy = df.copy()

        if self.numericCols:
            df_copy[ self.numericCols ] = self.numericScaler.transform( df_copy[ self.numericCols ] )

        for col in self.categoricalCols:
            if col in self.categoricalEncoders:
                enc = self.categoricalEncoders[ col ]
                df_copy[ col ] = enc.transform( df_copy[ col ].astype( str ) )
        return df_copy

    def fit_transform( self, df:DF ) -> DF:
        self.fit( df )
        return self.transform( df )


class WeightedLabelScaler( ScalerBase ):
    def __init__( self, numCols:Optional[List[str]] = None, catCols:Optional[List[str]] = None ) -> None:
        super().__init__( numCols, catCols )
        self.numericScaler = StandardScaler()
        self.categoricalEncoders: Dict[str, Dict[str, float]] = {}

    def fit( self, df:DF ) -> 'WeightedLabelScaler':
        if not ( self.numericCols or self.categoricalCols ):
            self.determineColTypes( df )

        if self.numericCols:
            self.numericScaler.fit( df[ self.numericCols ] )

        for col in self.categoricalCols:
            counts = Counter( df[ col ].astype( str ) )
            total = sum( counts.values() )
            weights = { label: total / count for label, count in counts.items() }
            self.categoricalEncoders[ col ] = weights
        return self

    def transform( self, df:DF ) -> DF:
        df_copy = df.copy()

        if self.numericCols:
            df_copy[ self.numericCols ] = self.numericScaler.transform( df_copy[ self.numericCols ] )

        for col in self.categoricalCols:
            weights = self.categoricalEncoders.get( col, {} )
            df_copy[ col ] = df_copy[ col ].astype( str ).map( weights ).fillna( 0 ).astype( float )
        return df_copy

    def fit_transform( self, df:DF ) -> DF:
        self.fit( df )
        return self.transform( df )
