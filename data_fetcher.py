from Interval import Interval
from utility import get_last_working_day
from datetime import date
from pandas import DataFrame
import yfinance

def fetch_data( tick:str, start:date = get_last_working_day(), interval:Interval = Interval.ONE_MIN)->DataFrame:
    """
    Fetches 1 day worth of stock movement
    """
    data = yfinance.download( tick, interval = interval.value , start = start, period= '1d' )
    data.columns = data.columns.get_level_values(0)
    data['time'] = data.index
    return data


if __name__ == "__main__":
    df = fetch_data( "ANET" )
    print( df.head() )
