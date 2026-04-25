# Workings

`data_fetcher` Fetches 1 day stock price data, it has configurable intervals and returns in a dataframe

`trend_iter` Since we dont want to deal with real world yet we use past data downloaded from data_fetcher,
and simulate the interval trades. It is supposed to iterated to get named tuple(Trend) ( ig this should be 
renamed to candel instead)
Maybe in future this guy will interface with irl stock priciing.

`Holdings` this will be maintaining the stocks you buy and sell( what i mean here is the stock quantity and 
the average buying price).

`Action` This is action we perform on the market per candle ie. HOLD ( dont do anything ), SELL ( sell some 
defined amount of stocks ) BUY ( buy some specified amount of stocks )

`Metrics`  These are the indicators which we calculate on the seen set of candels, using this algorithm 
maybe can decide much better.
Using the previous data and new candle it updates the metric.

`metric_calculator` This gathers all the metric objects and calculates them every candle sticks and return 
them

`algorithm` This is where we define algoritms, purpose of this is to decide the current action to perform on 
the market.
In a particular day it uses the past candels, and some calculated metric on those past data and decides what 
to do with the current candle seen in the market. It also has to decide the number of units.
- Algorihtm can set the required metrics it wants

`action_resolver` Supposed to perform the trade based on the actions, currently it will update the holdings only


`runner` This is the one who performs the simulation, 
It gets the candle data using TrendIter ( basically iterates over ) per iteration it will calculate the 
all the metrics it needs, and calls the algorithm, algoritm decides the action to perform and it will call the action_resolver.
There can be optional callback which can be used to display realtime information
runner also maintains an history of data seen, and action performed.

`simulation_writer` using the runner it will write down the simulation to a csv file.


`action_ranker` This will rank the action the algorithm performed.
Action ranker ranks each action taken withing a range from 0 to 1, Rank labler lables them approprieatly




# TODO
    - [ ] Clean Up
    - [ ] Fix inconsistent formatting across the code
        - [ ]  Variable naming
    - [ ] Trainer uses fixed hyperparms
    - [ ] Trainer me might need to apply some ops on training data
    - [ ] 



