import pandas as pd
import sqlalchemy
from binance.client import Client
from binance import BinanceSocketManager
import asyncio
import config

pair = 'ADAUSDT'

client = Client(config.api_key, config.api_secret)

bsm = BinanceSocketManager(client)

socket = bsm.trade_socket(pair)

engine = sqlalchemy.create_engine('sqlite:///'+pair+'stream.db')

def createframe(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:,['s', 'E', 'p']]
    df.columns = ['symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df


async def main():

    async with socket as tscm:
        while True:
            res = await tscm.recv()
            if res:
                frame = createframe(res)
                frame.to_sql(pair, engine, if_exists='append', index=False)
                print(frame)

    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())