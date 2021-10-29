from binance import Client
import pandas as pd
import ta
import numpy as np
import time
import datetime

api_key = "C7nnYvPJ1ME9AK6WcusR9j60JMMQ0azIx9AlHeChans0JSiXlBY7ynVJHHMfAZC5";
api_secret = "bgeM4aOdP9k4QSnqILrg8S6me2hrp1VkRElrVcW8WZ0BPKQJ0OTNEGi8KhzrGWHy";
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
client = Client(api_key, api_secret);

def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'min ago UTC'))

    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def applytechnicals(df):
    df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window=14, smooth_window=3)

    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.Close, window=14)
    df['macd'] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)

class Signals:

    def __init__(self, df, lags):
        self.df = df
        self.lags = lags

    def gettrigger(self):
        dfx = pd.DataFrame()
        for i in range(self.lags +1):
            mask = (self.df['%K'].shift(1) < 20) & (self.df['%D'].shift(1) < 20)
            dfx = dfx.append(mask, ignore_index=True)
        return dfx.sum(axis=0)

    def decide(self):
        self.df['trigger'] = np.where(self.gettrigger(), 1, 0)
        self.df['Buy'] = np.where((self.df.trigger) & (self.df['%K'].between(20,80)) & (self.df['%D'].between(20,80))
                                                    & (self.df.rsi > 50) & (self.df.macd > 0), 1, 0)


def strat(pair, qty, open_position=False):
    df = getminutedata(pair, '1m', '100')
    applytechnicals(df)
    inst = Signals(df, 30)
    inst.decide()
    print(f'{st}: current Close of {pair} is ' + str(df.Close.iloc[-1]))
    if df.Buy.iloc[-1]:
        order = client.create_order(symbol=pair, 
                                    side='BUY', 
                                    type='MARKET', 
                                    quantity=qty)
        print(order)
        buyprice = float(order['fills'][0]['price'])
        open_position = True
    while open_position:
        time.sleep(0.5)
        df = getminutedata(pair, '1m', '2')
        print(f'current Close ' + str(df.Close.iloc[-1]))
        print(f'current Target ' + str(buyprice * 1.005))
        print(f'current Stop is ' + str(buyprice * 0.995))
        if df.Close[-1] <= buyprice * 0.99 or df.Close[-1] >= 1.005 * buyprice:
             order = client.create_order(symbol=pair, 
                                    side='SELL', 
                                    type='MARKET', 
                                    quantity=qty)
             print(order)
             break

while True:
    strat('ADAUSDT', 20)
    time.sleep(0.5)