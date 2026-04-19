from Sim import Trend

class SingleMetricsBase:
    def __init__(self, key:str ):
        self.key = key
    
    def update( self, trend:Trend ):
        """Update internal state with new bar."""
        raise NotImplementedError()
    
    def run( self ) -> tuple[str,float]:
        """Return current metric value."""
        raise NotImplementedError()
    
    def reset( self ):
        """Reset internal state before new simulation day."""
        pass

class MultiMetricsBase:
    def __init__( self, keys:list[str] ):
        self.keys = keys
    
    def update( self, trend:Trend ):
        """Update internal state with new bar."""
        raise NotImplementedError()
    
    def run( self ) -> list[tuple[str,float]]:
        """Return current metric value."""
        raise NotImplementedError()
    
    def reset( self ):
        """Reset internal state before new simulation day."""
        pass