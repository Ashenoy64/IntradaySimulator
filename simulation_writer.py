from Action import Action
from Trend import Trend
import csv
import os
from datetime import datetime


def writer(name:str,action_history:list[Action], data_history:list[Trend], metric_history:list[dict], time_history: list[datetime]|None = None):
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

    if time_history:
        field_names.append( 'time' )

    if metric_history:
        metric_names = list( metric_history[0].keys() )
    else:
        metric_names = []

    fp = open( 'simulation_results/' + name + ".csv",'w', newline='' )
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
        } | ({'time': time_history[index]} if time_history is not None else {}))
    
    fp.close()