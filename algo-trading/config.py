# all the tunable knobs for this project live here. don't hardcode numbers
# in the actual modules, just import config and use these.

# broker / account stuff
INITIAL_BALANCE = 100000       # starting cash, totally made up number
DEFAULT_QUANTITY = 10          # shares per trade, same for every order for now
SYMBOL = "DEMO"                 # only ticker this thing knows about

# MA crossover settings
MA_FAST_PERIOD = 10             # short window
MA_SLOW_PERIOD = 50             # long window

# RSI settings
RSI_PERIOD = 14                 # classic RSI window, Wilder's smoothing
RSI_OVERSOLD = 30               # below this -> oversold, might bounce
RSI_OVERBOUGHT = 70             # above this -> overbought, might pull back

# risk management
STOP_LOSS_PCT = 0.05            # bail out if we're down 5% from entry
TAKE_PROFIT_PCT = 0.10          # lock in the win if we're up 10%

# logging
LOG_FILE = "trading.log"

# data
DATA_FILE = "data/OHLC_data.csv"

# where results get dumped after a run
RESULTS_DIR = "results"
MA_TRADES_FILE = f"{RESULTS_DIR}/ma_crossover_trades.csv"
RSI_TRADES_FILE = f"{RESULTS_DIR}/rsi_trades.csv"
