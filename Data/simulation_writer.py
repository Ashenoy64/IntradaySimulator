from Sim import Action, Trend
from Sim.runner import Runner
import csv
import os
from datetime import datetime
from typing import Optional, List
from Settings import SIMULATION_RESULTS_PATH

def writer( name:str, runner:Runner, disable_time:bool = False, disable_metric: bool = False, subpath:str = "" ):
    if not os.path.exists( os.path.join( SIMULATION_RESULTS_PATH, subpath ) ):
        os.mkdir( os.path.join( SIMULATION_RESULTS_PATH, subpath ) )

    field_names = [
        'action',
        'close',
        'open',
        'high',
        'low',
        'volume',
        'price',
    ]

    time_history = runner.getTimeHistory()
    if time_history and not disable_time:
        field_names.append( 'time' )
    
    metric_history = runner.getMetircHistory()
    if metric_history and not disable_metric:
        metric_names = list( metric_history[ 0 ].keys() )
    else:
        metric_names = []

    action_history = runner.getActionHistory()
    data_history = runner.getDataHistory()

    path = os.path.join( SIMULATION_RESULTS_PATH, subpath, name + ".csv" )
    fp = open( path, 'w' , newline='' )
    wr = csv.DictWriter( fp, fieldnames = field_names + metric_names )
    wr.writeheader()
    for index in range( 0, len( action_history ) ):
        trend = data_history[ index ]
        wr.writerow({
            'action':action_history[ index ].getActonStr(),
            'close': trend.close,
            'open':trend.open,
            'high': trend.high,
            'low':trend.low,
            'volume':trend.volume,
            'price': trend.close,
            **metric_history[ index ]
        } | ( { 'time': time_history[ index ] } if time_history is not None else {} ) )
    fp.close()