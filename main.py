from runner import Runner
from algoritm import *
from action_resolver import action_resolver
from Holdings import Holdings
from trend_iter import TrendIter
from metric_calculator import MetricCalculator
from datetime import date
from simulation_writer import writer
# test_writer()
from action_ranker import rwrd_risk_reward_action_ranker as action_ranker

def run(name, date, Algo):
    funds = 10000
    data_iter = TrendIter( name, date=date )
    holdings = Holdings(0,0.0)
    runner = Runner(funds,holdings)
    algo = Algo()
    mc = MetricCalculator()
    mc.addMetrics(algo.getAlgoMetrics())
    investment = funds + holdings.getTotal()
    runner.run(data_iter,mc.metricCalculator,algo.run, action_resolver)
    funds_left = runner.getFunds()
    holdings = runner.getPositions()
    history = runner.getDataHistory()
    return investment,funds_left, holdings, history[-1].close


def collective_sim():
    collection={
        "emar" : EMARsiAlgo,
    }

    cmps = [
        "ANET",
    ]

    result = {}

    d = date(month=8, day=12, year=2025)

    for cmp in cmps:
        _cmps = {}
        for key,algo in collection.items():
            investment,funds_left, holdings, close_price  = run(cmp,d,algo)
            _cmps[key] = {
                "invested_start" : investment,
                "funds_left" : funds_left,
                "holding_qnt" : holdings.getHoldingQuantity(),
                "holding_avgprice" : holdings.getHoldingAvgPrice(),
                "market_close" : close_price,
                "holding_value" : holdings.getTotal(),
                "holding_sellvalue" : holdings.getHoldingQuantity() * close_price,
                "net_holdingvalue" : holdings.getTotal() + funds_left,
                "net_holding_sellvalue" : funds_left + (holdings.getHoldingQuantity() * close_price),
            }
        result[cmp] = _cmps

    import json


    with open('out.json', 'w') as f:
        json.dump(result,f)


def test_writer(name='AAPL', date=date(2025, 10, 1), Algo=EMARsiAlgo):
    funds = 1000
    data_iter = TrendIter( name, date=date )
    holdings = Holdings(0,0.0)
    runner = Runner(funds,holdings)
    algo = Algo()
    mc = MetricCalculator()
    mc.addMetrics(algo.getAlgoMetrics())

    runner.run(data_iter,mc.metricCalculator,algo.run, action_resolver)
    investment = funds + holdings.getTotal()
    funds_left = runner.getFunds()
    data_history = runner.getDataHistory()
    action_history = runner.getActionHistory()
    metric_history = mc.getMetircHistory()
    time_history =runner.getTimeHistory()
    print({
                "invested_start" : investment,
                "funds_left" : funds_left,
                "holding_qnt" : holdings.getHoldingQuantity(),
                "holding_avgprice" : holdings.getHoldingAvgPrice(),
                "market_close" : data_history[-1].close,
                "holding_value" : holdings.getTotal(),
                "holding_sellvalue" : holdings.getHoldingQuantity() * data_history[-1].close,
                "net_holdingvalue" : holdings.getTotal() + funds_left,
                "net_holding_sellvalue" : funds_left + (holdings.getHoldingQuantity() * data_history[-1].close),
            })
    writer(name+str(date),action_history,data_history,metric_history,time_history)
    action_ranker(f'{name}{date}', inplace=True)


def test_comprehensive_metrics(name='AAPL', date=date(2025, 10, 1)):
    """
    Run simulation with ComprehensiveMetricsAlgo to collect ALL available metrics.
    This generates maximum data for analysis without making any trading decisions.
    """
    funds = 10000  # Starting funds (won't be used for trading)
    data_iter = TrendIter(name, date=date)
    holdings = Holdings(0, 0.0)
    runner = Runner(funds, holdings)
    algo = ComprehensiveMetricsAlgo()
    mc = MetricCalculator()
    mc.addMetrics(algo.getAlgoMetrics())

    runner.run(data_iter, mc.metricCalculator, algo.run, action_resolver)
    investment = funds + holdings.getTotal()
    funds_left = runner.getFunds()
    data_history = runner.getDataHistory()
    action_history = runner.getActionHistory()
    metric_history = mc.getMetircHistory()
    time_history = runner.getTimeHistory()

    print(f"Comprehensive Metrics Collection for {name}")
    print(f"Starting Investment: ${investment}")
    print(f"Funds Left: ${funds_left}")
    print(f"Data Points Collected: {len(data_history)}")
    print(f"Metrics per Data Point: {len(metric_history[0]) if metric_history else 0}")
    print(f"Total Metrics Collected: {len(data_history) * len(metric_history[0]) if metric_history else 0}")

    # Save the comprehensive data
    writer(f"{name}_comprehensive{str(date)}", action_history, data_history, metric_history, time_history)
    return data_history, metric_history


# Uncomment to run comprehensive metrics collection instead of default trading simulation
# test_comprehensive_metrics()

test_writer()
