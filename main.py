from runner import Runner
from algoritm import SimpleGoAndGoStrg, SimpleMomentum
from action_resolver import action_resolver
from Holdings import Holdings
from trend_iter import TrendIter


def calculate_metrics(*args)->dict:
    return {}



data_iter = TrendIter('ANET')

funds = 1000
holdings = Holdings(0,0.0)
holdings.getTotal()

runner = Runner(funds,holdings)
algo = SimpleMomentum()

investment = funds + holdings.getTotal()
runner.run(data_iter,calculate_metrics,algo.run, action_resolver)
funds_left = runner.getFunds()
holdings = runner.getPositions()
after_day = funds_left + holdings.getTotal()

print("Investment ", investment)
print('After ', after_day )