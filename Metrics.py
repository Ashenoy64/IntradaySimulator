from collections import deque
from math import sqrt
from Trend import Trend

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

class SMA( SingleMetricsBase ):
    def __init__( self, key:str, N:int ):
        super().__init__( key )
        self.N = N
        self.window = deque()
        self.sum = 0.0
    
    def reset( self ):
        self.window.clear()
        self.sum = 0.0
    
    def update( self, trend:Trend ):
        close = trend.close
        self.window.append( close )
        self.sum += close
        if len( self.window ) > self.N:
            removed = self.window.popleft()
            self.sum -= removed
    
    def sma( self ):
        if len( self.window ) < self.N:
            return 0.0
        return self.sum / self.N
    
    def run( self )-> tuple[str,float]:
        return (self.key, self.sma() )

class EMA( SingleMetricsBase ):
    def __init__( self, key, N ):
        super().__init__( key )
        self.N = N
        self.k = 2 /  ( N + 1 )
        self.ema = None
        self.init_window = deque()
    
    def reset( self ):
        self.ema = None
        self.init_window.clear()
    
    def update( self, trend:Trend ):
        close = trend.close
        if self.ema is None:
            self.init_window.append( close )
            if len( self.init_window ) == self.N:
                self.ema = sum( self.init_window ) / self.N
        else:
            self.ema = close * self.k + self.ema * ( 1 - self.k )
    
    def run( self )-> tuple[str,float]:
        return ( self.key, self.ema if self.ema is not None else 0.0 )

class BollingerBands( MultiMetricsBase ):
    def __init__( self, key_upper:str, key_middle:str, key_lower:str, N:int=20, num_std:int=2 ):
        super().__init__( [ key_upper, key_middle, key_lower ] )
        self.key_upper = key_upper
        self.key_middle = key_middle
        self.key_lower = key_lower
        self.N = N
        self.num_std = num_std
        self.window = deque()
    
    def reset( self ):
        self.window.clear()
    
    def update( self, trend:Trend):
        self.window.append( trend.close )
        if len( self.window ) > self.N:
            self.window.popleft()
    
    def run( self )-> list[tuple[str,float]]:
        if len( self.window ) < self.N:
            return [ ( self.key_upper, 0.0 ),
                        ( self.key_middle, 0.0 ), ( self.key_lower, 0.0 ) ]
        
        sma = sum( self.window ) / self.N
        variance = sum( ( x - sma ) ** 2 for x in self.window ) / self.N
        stddev = sqrt( variance )
        upper = sma + self.num_std * stddev
        lower = sma - self.num_std * stddev
        return [ ( self.key_upper, upper ),
                    ( self.key_middle, sma ), ( self.key_lower, lower ) ]

class RSI( SingleMetricsBase ):
    def __init__( self, key:str, N:int=14 ):
        super().__init__( key )
        self.N = N
        self.gains = deque()
        self.losses = deque()
        self.avg_gain = None
        self.avg_loss = None
        self.prev_close = None
    
    def reset( self ):
        self.gains.clear()
        self.losses.clear()
        self.avg_gain = None
        self.avg_loss = None
        self.prev_close = None
    
    def update( self, trend:Trend ):
        if self.prev_close is None:
            self.prev_close = trend.close
            return
        change = trend.close - self.prev_close
        gain = max( change, 0 )
        loss = max( -change, 0 )
        self.gains.append( gain )
        self.losses.append( loss )
        if len( self.gains ) > self.N:
            self.gains.popleft()
            self.losses.popleft()
        self.prev_close = trend.close

        if len( self.gains ) == self.N:
            if self.avg_gain is None or self.avg_loss is None:
                self.avg_gain = sum( self.gains ) / self.N
                self.avg_loss = sum( self.losses ) / self.N
            else:
                self.avg_gain = ( self.avg_gain * ( self.N - 1 ) + gain ) / self.N
                self.avg_loss = ( self.avg_loss * ( self.N - 1 ) + loss ) / self.N
    
    def run( self )-> tuple[str,float]:
        if self.avg_gain is None or self.avg_loss is None:
            return ( self.key, 50.0 )
        if self.avg_loss == 0:
            return ( self.key, 100.0 )
        rs = self.avg_gain / self.avg_loss
        rsi = 100 - ( 100 / ( 1 + rs ) )
        return ( self.key, rsi )

class MACD( MultiMetricsBase ):
    def __init__( self,
                key_macd:str,
                key_signal:str,
                key_histogram:str,
                short_N:int=12,
                long_N:int=26,
                signal_N:int=9 ):
        super().__init__( [ key_macd, key_signal, key_histogram ] )
        self.key_macd = key_macd
        self.key_signal = key_signal
        self.key_histogram = key_histogram
        self.short_ema = EMA( key_macd + "_short", short_N )
        self.long_ema = EMA( key_macd + "_long", long_N )
        self.signal_ema = EMA( key_signal, signal_N )
        self.macd = None
    
    def reset( self ):
        self.short_ema.reset()
        self.long_ema.reset()
        self.signal_ema.reset()
        self.macd = None
    
    def update( self, trend:Trend ):
        self.short_ema.update( trend )
        self.long_ema.update( trend )
        _,short_val = self.short_ema.run()
        _,long_val = self.long_ema.run()
        if short_val == 0 or long_val == 0:
            self.macd = None
            return
        self.macd = short_val - long_val
        # Create a fake Trend to feed to signal EMA with macd as close
        macd_trend = Trend( 0, 0, 0, self.macd, 0 )
        self.signal_ema.update( macd_trend )
    
    def run( self )-> list[tuple[str,float]]:
        if self.macd is None:
            return [ ( self.key_macd, 0.0 ),
                    ( self.key_signal, 0.0 ), ( self.key_histogram, 0.0 ) ]
        _,signal_val = self.signal_ema.run()
        histogram = self.macd - signal_val
        return [ ( self.key_macd, self.macd ), ( self.key_signal, signal_val ),
                ( self.key_histogram, histogram ) ]

class VWAP( SingleMetricsBase ):
    def __init__( self, key:str ):
        super().__init__( key )
        self.cum_vol_price = 0.0
        self.cum_vol = 0.0
    
    def reset( self ):
        self.cum_vol_price = 0.0
        self.cum_vol = 0.0
    
    def update( self, trend:Trend ):
        self.cum_vol_price += trend.close * trend.volume
        self.cum_vol += trend.volume
    
    def run( self )->tuple[str,float]:
        if self.cum_vol == 0:
            return ( self.key, 0.0 )
        return ( self.key, self.cum_vol_price / self.cum_vol )

class ATR( SingleMetricsBase ):
    def __init__( self, key:str, N:int=14 ):
        super().__init__( key )
        self.N = N
        self.trs = deque()
        self.prev_close = None
        self.atr = None
    
    def reset( self ):
        self.trs.clear()
        self.prev_close = None
        self.atr = None

    def true_range( self, trend:Trend ):
        if self.prev_close is None:
            return trend.high - trend.low
        else:
            return max(
                trend.high - trend.low,
                abs( trend.high - self.prev_close ),
                abs( trend.low - self.prev_close )
            )
    
    def update( self, trend:Trend ):
        tr = self.true_range( trend )
        self.trs.append( tr )
        if len( self.trs ) > self.N:
            self.trs.popleft()
        if self.atr is None and len( self.trs ) == self.N:
            self.atr = sum( self.trs ) / self.N
        elif self.atr is not None:
            self.atr = ( self.atr * ( self.N - 1 ) + tr) / self.N
        self.prev_close = trend.close

    def run( self )->tuple[str,float]:
        return ( self.key, self.atr if self.atr is not None else 0.0 )

class CCI( SingleMetricsBase ):
    def __init__(self, key, N=20):
        super().__init__( key )
        self.N = N
        self.tp_window = deque()

    def reset( self ):
        self.tp_window.clear()

    def update( self, trend:Trend ):
        tp = ( trend.high + trend.low + trend.close) / 3
        self.tp_window.append( tp )
        if len( self.tp_window ) > self.N:
            self.tp_window.popleft()
    
    def run( self )->tuple[str,float]:
        if len( self.tp_window ) < self.N:
            return ( self.key, 0.0 )
        ma = sum( self.tp_window ) / self.N
        mean_dev = sum( abs( tp - ma ) for tp in self.tp_window ) / self.N
        if mean_dev == 0:
            return ( self.key, 0.0 )
        return ( self.key, ( self.tp_window[-1] - ma ) / ( 0.015 * mean_dev ) )

class ADX( SingleMetricsBase ):
    def __init__( self, key, N=14 ):
        super().__init__( key )
        self.N = N
        self.plus_dm = deque()
        self.minus_dm = deque()
        self.trs = deque()
        self.prev_trend = None
        self.adx = None
    
    def reset( self ):
        self.plus_dm.clear()
        self.minus_dm.clear()
        self.trs.clear()
        self.prev_trend = None
        self.adx = None

    def update( self, trend:Trend ):
        if self.prev_trend is None:
            self.prev_trend = trend
            return
        
        up_move = trend.high - self.prev_trend.high
        down_move = self.prev_trend.low - trend.low
        
        pdm = up_move if up_move > down_move and up_move > 0 else 0
        mdm = down_move if down_move > up_move and down_move > 0 else 0

        tr = max(
            trend.high - trend.low,
            abs(trend.high - self.prev_trend.close),
            abs(trend.low - self.prev_trend.close)
        )

        self.plus_dm.append( pdm )
        self.minus_dm.append( mdm )
        self.trs.append( tr )

        if len( self.plus_dm ) > self.N:
            self.plus_dm.popleft()
            self.minus_dm.popleft()
            self.trs.popleft()

        self.prev_trend = trend

        if len( self.plus_dm ) == self.N:
            atr_sum = sum( self.trs )
            if atr_sum == 0:
                self.adx = 0.0
                return
            plus_di = 100 * ( sum( self.plus_dm ) / atr_sum )
            minus_di = 100 * ( sum( self.minus_dm ) / atr_sum )

            dx = abs( plus_di - minus_di ) /\
                ( plus_di + minus_di if ( plus_di + minus_di ) != 0 else 1 )
            self.adx = 100 * dx
    
    def run( self )->tuple[str,float]:
        return ( self.key, self.adx if self.adx is not None else 0.0 )

class MFI( SingleMetricsBase ):
    def __init__( self, key, N=14 ):
        super().__init__( key )
        self.N = N
        self.pos_flow = deque()
        self.neg_flow = deque()
        self.prev_trend = None
    
    def reset( self ):
        self.pos_flow.clear()
        self.neg_flow.clear()
        self.prev_trend = None
    
    def update( self, trend:Trend ):
        tp = ( trend.high + trend.low + trend.close ) / 3
        if self.prev_trend is None:
            self.prev_trend = trend
            return
        prev_tp = ( self.prev_trend.high + self.prev_trend.low + self.prev_trend.close) / 3
        flow = tp * trend.volume

        if tp > prev_tp:
            self.pos_flow.append( flow )
            self.neg_flow.append( 0 )
        elif tp < prev_tp:
            self.pos_flow.append( 0 )
            self.neg_flow.append( flow )
        else:
            self.pos_flow.append( 0 )
            self.neg_flow.append( 0 )

        if len( self.pos_flow ) > self.N:
            self.pos_flow.popleft()
            self.neg_flow.popleft()

        self.prev_trend = trend

    def run( self )->tuple[str,float]:
        pos_sum = sum( self.pos_flow )
        neg_sum = sum( self.neg_flow )
        if pos_sum + neg_sum == 0:
            return ( self.key, 50.0 )
        mfr = pos_sum / ( neg_sum if neg_sum != 0 else 1 )
        mfi = 100 - ( 100 / (1 + mfr ) )
        return ( self.key, mfi )

class ROC( SingleMetricsBase ):
    def __init__( self, key, N=10 ):
        super().__init__( key )
        self.N = N
        self.window = deque()
    
    def reset( self ):
        self.window.clear()
    
    def update( self, trend:Trend ):
        self.window.append( trend.close )
        if len( self.window ) > self.N + 1:
            self.window.popleft()
    
    def run( self )->tuple[str,float]:
        if len( self.window ) < self.N + 1:
            return ( self.key, 0.0 )
        prev = self.window[ 0 ]
        curr = self.window[ -1 ]
        if prev == 0:
            return ( self.key, 0.0 )
        return ( self.key, ( curr - prev ) / prev * 100 )

class StochasticOscillator( MultiMetricsBase ):
    def __init__( self, key_k:str, key_d:str, N=14, d_N=3 ):
        super().__init__( [ key_k, key_d ] )
        self.key_k = key_k
        self.key_d = key_d
        self.N = N
        self.d_N = d_N
        self.low_window = deque()
        self.high_window = deque()
        self.close_window = deque()
        self.k_values = deque()
    
    def reset( self ):
        self.low_window.clear()
        self.high_window.clear()
        self.close_window.clear()
        self.k_values.clear()
    
    def update( self, trend:Trend ):
        self.low_window.append( trend.low )
        self.high_window.append( trend.high )
        self.close_window.append( trend.close )
        if len( self.low_window ) > self.N:
            self.low_window.popleft()
            self.high_window.popleft()
            self.close_window.popleft()

        # Calculate %K value
        if len( self.low_window ) == self.N:
            lowest_low = min( self.low_window )
            highest_high = max( self.high_window )
            if highest_high - lowest_low == 0:
                k = 0.0
            else:
                k = 100 * ( self.close_window[ -1 ] - lowest_low ) / ( highest_high - lowest_low )
        else:
            k = 0.0
        self.k_values.append( k )
        if len( self.k_values ) > self.d_N:
            self.k_values.popleft()

    def run( self )->list[tuple[str,float]]:
        if len( self.k_values ) < 1:
            return [ ( self.key_k, 0 ), ( self.key_d, 0 ) ]
        k = self.k_values[ -1 ]
        d = sum( self.k_values ) / len( self.k_values )
        return [ ( self.key_k, k ),( self.key_d, d ) ]

class TypicalPrice( SingleMetricsBase ):
    def __init__( self, key:str ):
        super().__init__( key )
        self.value = 0.0
    
    def reset( self ):
        self.value = 0.0
    
    def update( self, trend:Trend ):
        self.value = ( trend.high + trend.low + trend.close ) / 3
    
    def run( self )->tuple[str,float]:
        return ( self.key, self.value )

class VWMA( SingleMetricsBase ):
    def __init__( self, key:str, N:int=10 ):
        super().__init__( key )
        self.N = N
        self.vol_close_sum = 0.0
        self.vol_sum = 0.0
        self.window = deque()
    
    def reset( self ):
        self.vol_close_sum = 0.0
        self.vol_sum = 0.0
        self.window.clear()
    
    def update( self, trend:Trend ):
        vc = trend.close * trend.volume
        self.window.append( trend )
        self.vol_close_sum += vc
        self.vol_sum += trend.volume
        if len( self.window ) > self.N:
            oldest = self.window.popleft()
            self.vol_close_sum -= (oldest.close * oldest.volume)
            self.vol_sum -= oldest.volume
    
    def run( self )->tuple[str,float]:
        if self.vol_sum == 0:
            return ( self.key, 0.0)
        return ( self.key, self.vol_close_sum / self.vol_sum )

class VolumeAvg( SingleMetricsBase ):
    def __init__( self, key:str, N:int=10 ):
        super().__init__( key )
        self.N = N
        self.window = deque()
        self.sum_vol = 0.0
    
    def reset( self ):
        self.window.clear()
        self.sum_vol = 0.0
    
    def update( self, trend:Trend ):
        vol = trend.volume
        self.window.append( vol )
        self.sum_vol += vol
        if len( self.window ) > self.N:
            removed = self.window.popleft()
            self.sum_vol -= removed
    
    def run( self )->tuple[str,float]:
        if len( self.window ) < self.N:
            return ( self.key, 0.0 )
        return ( self.key, self.sum_vol / self.N )

# sma, ema, TypicalPrice, VWMA, VolumeAvg,bollingerbands, rsi, 
# macd, vwap, atr, cci, adx, mfi, roc, StochasticOscillator,