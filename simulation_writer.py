from Action import Action
from Trend import Trend
import csv
import os


def writer(name:str,action_history:list[Action], data_history:list[Trend], metric_history:list[dict]):
    if not os.path.exists('simulation_results/'):
        os.mkdir('simulation_results')

    field_names = [
        'action',
        'close',
        'open',
        'high',
        'low',
        'volume',
        'price',
    ]

    if metric_history:
        metric_names = list( metric_history[0].keys() )
    else:
        metric_names = []

    fp = open('simulation_results/' + name + ".csv",'w', newline='')
    wr = csv.DictWriter( fp, fieldnames=field_names+metric_names )
    wr.writeheader()
    for index in range(0,len(action_history)):
        trend = data_history[index]
        wr.writerow({
            'action':action_history[index].getActonStr(),
            'close': trend.close,
            'open':trend.open,
            'high': trend.high,
            'low':trend.low,
            'volume':trend.volume,
            'price': trend.close,
            **metric_history[index]
        })
    
    fp.close()