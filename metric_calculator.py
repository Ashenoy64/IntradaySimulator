from Trend import Trend
from Metrics import MultiMetricsBase, SingleMetricsBase
from typing import Union


class MetricCalculator:

    def __init__(self):
        self.metrics: list[Union[MultiMetricsBase, SingleMetricsBase]] = []
        self.metricHistory = []

    def calculateMetric(self, history:list, trend:Trend) -> dict:
        calculations = {}
        
        for metric in self.metrics:
            metric.update(trend)
            if isinstance(metric, SingleMetricsBase):
                key, calculation = metric.run()
                calculations[key] = calculation
            else:
                for key, calculation in metric.run():
                    calculations[key] = calculation

        self.metricHistory.append(calculations)
        return calculations


    def addMetric(self, metric: Union[MultiMetricsBase, SingleMetricsBase]):
        self.metrics.append(metric)

    def addMetrics(self, metrics: list[Union[MultiMetricsBase, SingleMetricsBase]]):
        self.metrics.extend( metrics )

    def getMetircHistory(self):
        return self.metricHistory