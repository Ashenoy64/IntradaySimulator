from Trend import Trend
from Metrics import MultiMetricsBase, SingleMetricsBase


class MetricCalculator:

    def __init__(self):
        self.metrics:list[MultiMetricsBase|SingleMetricsBase] = []

    def metricCalculator(self, history:list, trend:Trend)->dict:
        calculations = {}
        
        for metric in self.metrics:
            metric.update(trend)
            if isinstance(metric, SingleMetricsBase):
                key, calculation = metric.run()
                calculations[key] = calculation
            else:
                for key, calculation in metric.run():
                    calculations[key] = calculation

        return calculations


    def addMetric(self, metric:MultiMetricsBase|SingleMetricsBase):
        self.metrics.append(metric)

    def addMetrics(self, metrics:list[MultiMetricsBase|SingleMetricsBase]):
        self.metrics.extend( metrics )