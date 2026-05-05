# ========================================================
# MNQ 5-MINUTE WILLIAMS %R + MACD STRATEGY FOR TOPSTEPX
# GitHub: https://github.com/davidladdl1-source/Williams-R
# ========================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from math import floor
from datetime import datetime
import pytz

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20, 10)

# ================== CONFIG ==================
API_KEY = 'YOUR_EODHD_API_KEY_HERE'          # ←←← CHANGE THIS TO YOUR REAL KEY
SYMBOL = 'MNQ'                                # Micro E-mini Nasdaq-100 futures
INTERVAL = '5m'
START_DATE = '2024-01-01'                     # Intraday data available ~1 year back
INVESTMENT = 100000                           # Starting capital for backtest

# TopstepX trading hours (EST)
TOPSTEP_OPEN_SUNDAY = 18   # 6:00 PM EST Sunday
TOPSTEP_CLOSE_WEEKDAY = 16 # 4:00 PM EST (forced flat)

# =============================================

def get_intraday_data(symbol, interval='5m', start_date='2024-01-01'):
    url = f"https://eodhd.com/api/intraday/{symbol}?api_token={API_KEY}&interval={interval}&from={start_date}&fmt=json"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API Error: {response.text}")
    
    df = pd.DataFrame(response.json())
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df[['open', 'high', 'low', 'close', 'volume']]
    df = df.sort_index()
    return df

print("Downloading MNQ 5-minute data...")
mnq = get_intraday_data(SYMBOL, INTERVAL, START_DATE)
print(f"✅ Data loaded: {len(mnq)} candles from {mnq.index[0]} to {mnq.index[-1]}")

# ================== INDICATORS ==================
def get_wr(high, low, close, lookback=14):
    highh = high.rolling(lookback).max()
    lowl = low.rolling(lookback).min()
    wr = -100 * ((highh - close) / (highh - lowl))
    return wr

def get_macd(price, slow=26, fast=12, smooth=9):
    exp1 = price.ewm(span=fast, adjust=False).mean()
    exp2 = price.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=smooth, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

mnq['wr_14'] = get_wr(mnq['high'], mnq['low'], mnq['close'], 14)
mnq['macd'], mnq['macd_signal'], mnq['macd_hist'] = get_macd(mnq['close'])
mnq = mnq.dropna()

# ================== TOPSTEPX HOURS FILTER ==================
def is_topstepx_trading_time(dt):
    est = pytz.timezone('US/Eastern')
    dt_est = dt.tz_convert(est) if dt.tzinfo else est.localize(dt)
    hour = dt_est.hour
    weekday = dt_est.weekday()

    if weekday == 6:  # Sunday
        return hour >= TOPSTEP_OPEN_SUNDAY
    elif weekday < 5:  # Mon-Fri
        return hour < TOPSTEP_CLOSE_WEEKDAY
    return False

mnq['topstep_open'] = mnq.index.map(is_topstepx_trading_time)

# ================== TRADING STRATEGY ==================
def implement_wr_macd_strategy(prices, wr, macd, macd_signal, topstep_open):
    buy_price = []
    sell_price = []
    wr_macd_signal = []
    signal = 0

    for i in range(len(wr)):
        if not topstep_open.iloc[i]:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            wr_macd_signal.append(0)
            continue

        # BUY
        if wr.iloc[i-1] > -50 and wr.iloc[i] < -50 and macd.iloc[i] > macd_signal.iloc[i]:
            if signal != 1:
                buy_price.append(prices.iloc[i])
                sell_price.append(np.nan)
                signal = 1
                wr_macd_signal.append(1)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                wr_macd_signal.append(0)
        
        # SELL
        elif wr.iloc[i-1] < -50 and wr.iloc[i] > -50 and macd.iloc[i] < macd_signal.iloc[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices.iloc[i])
                signal = -1
                wr_macd_signal.append(-1)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                wr_macd_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            wr_macd_signal.append(0)

    return buy_price, sell_price, wr_macd_signal

buy_price, sell_price, wr_macd_signal = implement_wr_macd_strategy(
    mnq['close'], mnq['wr_14'], mnq['macd'], mnq['macd_signal'], mnq['topstep_open']
)

# Position & Backtest
position = []
for i in range(len(wr_macd_signal)):
    if wr_macd_signal[i] == 1:
        position.append(1)
    elif wr_macd_signal[i] == -1:
        position.append(0)
    else:
        position.append(position[i-1] if i > 0 else 0)

mnq['position'] = position
mnq['returns'] = mnq['close'].diff()
mnq['strategy_returns'] = mnq['returns'] * mnq['position']
mnq['strategy_pnl'] = mnq['strategy_returns'] * 2   # MNQ = $2 per point
mnq['cumulative_pnl'] = mnq['strategy_pnl'].cumsum()

print("\n✅ BACKTEST COMPLETE")
print(f"Total P&L: ${mnq['cumulative_pnl'].iloc[-1]:,.2f}")
print(f"Number of trades: {len(mnq[mnq['wr_macd_signal'].abs() == 1])}")

# mnq[['close', 'cumulative_pnl']].plot(subplots=True)
# plt.show()
