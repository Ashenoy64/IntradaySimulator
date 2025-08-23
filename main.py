from runner import Runner
from algoritm import  EMARsiAlgo, MultiMetricIntradayAlgo, RSIStrategy, MACDStrategy
from action_resolver import action_resolver
from Holdings import Holdings
from trend_iter import TrendIter
from metric_calculator import MetricCalculator





funds = 1000

data_iter = TrendIter('ANET')
holdings = Holdings(0,0.0)
runner = Runner(funds,holdings)
algo = MACDStrategy()
mc = MetricCalculator()
mc.addMetrics(algo.getAlgoMetrics())



investment = funds + holdings.getTotal()
runner.run(data_iter,mc.metricCalculator,algo.run, action_resolver)
funds_left = runner.getFunds()
holdings = runner.getPositions()
after_day = funds_left + holdings.getTotal()

print("Investment ", investment)
print('After ', after_day )