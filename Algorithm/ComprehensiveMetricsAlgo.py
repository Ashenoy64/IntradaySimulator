from datetime import datetime
from Sim import Holdings, Act, Action
from Metrics.Metrics import *
from . import AlgorithmBase

class ComprehensiveMetricsAlgo(AlgorithmBase):
    """
    A data collection algorithm that subscribes to ALL available technical indicators
    for maximum metric coverage. This algorithm doesn't make trading decisions but
    collects comprehensive market data for analysis.
    """
    def __init__(self):
        super().__init__()
        # Subscribe to ALL available metrics for maximum data collection
        self.metrics = [
            # Trend Following Indicators
            SMA("sma_5", 5),
            SMA("sma_10", 10),
            SMA("sma_20", 20),
            SMA("sma_50", 50),
            EMA("ema_5", 5),
            EMA("ema_9", 9),
            EMA("ema_12", 12),
            EMA("ema_21", 21),
            EMA("ema_26", 26),

            # Momentum Indicators
            RSI("rsi_7", 7),
            RSI("rsi_14", 14),
            RSI("rsi_21", 21),
            ROC("roc_5", 5),
            ROC("roc_10", 10),
            ROC("roc_14", 14),

            # Volatility Indicators
            BollingerBands("bb_20", 20, 2.0),
            ATR("atr_7", 7),
            ATR("atr_14", 14),
            ATR("atr_21", 21),

            # Volume Indicators
            VWAP("vwap"),
            VWMA("vwma_5", 5),
            VWMA("vwma_10", 10),
            VWMA("vwma_20", 20),
            VolumeAvg("volume_avg_5", 5),
            VolumeAvg("volume_avg_10", 10),
            VolumeAvg("volume_avg_20", 20),
            MFI("mfi_14", 14),

            # Oscillator Indicators
            MACD("macd_12_26_9", 12, 26, 9),
            StochasticOscillator("stoch_14_3_3", 14, 3, 3),
            CCI("cci_14", 14),

            # Trend Strength Indicators
            ADX("adx_14", 14),

            # Price Indicators
            TypicalPrice("typical_price"),
        ]

    def getAlgoMetrics(self):
        return self.metrics

    def run(self, metrics:dict, mrkt_price:float, time:datetime,
            positions:Holdings, funds:float, history:list ) -> Action:
        """
        This algorithm only collects data - it never trades.
        Returns HOLD action always to maintain position for data collection.
        """
        return Action(Act.HOLD)


