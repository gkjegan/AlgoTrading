#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 09:30:43 2021

@author: archanajegan

calculate tech indicators for EMA-RSI-CAMARILLA
"""

import sqlite3
import datetime as dt
import pandas as pd
import numpy as np

'''
This script will calculate all the technical indicators needed for the EMA-RSI-CAMRARILLA strategy.
As the name of the strategy imples the technical indicator needed are
EMA
RSI
and CAMARILLA (only R3 and S3)
'''
tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#APPL stock is not available, so removed
#tickers = ["FB"]



'''
 Exponential Moving Average (EMA)
     An exponential moving average (EMA) is a type of moving average (MA) that places a greater weight 
     and significance on the most recent data points. 
     
Ref: https://www.investopedia.com/terms/e/ema.asp 
'''
def EMA(DF,a=200):
    """function to calculate EMA with default span of 200 days"""
    df = DF.copy()
    df["EMA"]=df["close price"].ewm(span=a, min_periods=a).mean()
    return df['EMA']


'''
Relative Strength Index:
    is a momentum indicator used in technical analysis that measures the magnitude of recent price changes 
    to evaluate overbought or oversold conditions in the price of a stock or other asset. For formula refer to the link below
Ref: https://www.investopedia.com/terms/r/rsi.asp
'''
def rsi(DF,n=2):
    "function to calculate RSI"
    df = DF.copy()
    df['delta']=df['close price'] - df['close price'].shift(1)
    df['gain']=np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean()[n])
            avg_loss.append(df['loss'].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
    df['avg_gain']=np.array(avg_gain)
    df['avg_loss']=np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    return df['RSI']



'''
Camarilla R3 and S3 are pivot points. A pivot point is a technical analysis indicator, or calculations, 
used to determine the overall trend of the market over different time frames.

Ref: https://www.investopedia.com/terms/p/pivotpoint.asp
'''
def CAMARILLA_R3(DF):
    """function to calculate EMA with default span of 200 days"""
    df = DF.copy()
    df["R3"]=df["close price"].shift(1) + ((df["high price"].shift(1) - df["low price"].shift(1)) * (1.1/4))
    return df['R3']

def CAMARILLA_S3(DF):
    """function to calculate EMA with default span of 200 days"""
    df = DF.copy()
    df["S3"]=df["close price"].shift(1) - ((df["high price"].shift(1) - df["low price"].shift(1)) * (1.1/4))
    return df['S3']




#Connect to db and get all daily price
db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')

#runDate = dt.datetime.today().date()
#queryDate = (dt.datetime.today() - dt.timedelta(days=250)).date()
query_daily_price_sql = '''SELECT * from DAILY_PRICE where close_date >= date('now', '-320 days') '''
result_df = pd.read_sql_query(query_daily_price_sql, db)
result_dict = result_df.to_dict('records')


#Calculate technical indicator for each ticker and date
data = {}
for result in result_dict:
    temp_dict = {"close date":result['close_date'],"open price":result['open_price'],"close price":result['close_price']
                                  ,"high price":result['high_price'],"low price":result['low_price'],"volume":result['volume']}
    temp_dict_df = pd.DataFrame(temp_dict, index=[0])
    if result['ticker'] not in data:
        data[result['ticker']] = temp_dict_df
    else:
       data[result['ticker']] =  data[result['ticker']].append(temp_dict_df, ignore_index=True)

for key in data:
    data[key]['rsi'] = rsi(data[key])
    data[key]['ema'] = EMA(data[key])
    data[key]['r3'] = CAMARILLA_R3(data[key])
    data[key]['s3'] = CAMARILLA_S3(data[key])

print(data)

c = db.cursor()
for key in data:
    data[key]['close date']= pd.to_datetime(data[key]['close date'])
    data[key].set_index("close date",inplace=True)
    data_to_insert = data[key].last('5D')
    for index, row in data_to_insert.iterrows():
        #print(row)
        try:
            print(" ticker:", key, "Run Date:",index, "ema:", row['ema'],"rsi:", row['rsi'],"r3:", row['r3'],"s3:", row['s3'])
            vals = [key, dt.datetime.strptime(str(index), "%Y-%m-%d %H:%M:%S").date(), row['ema'], row['rsi'], row['r3'], row['s3']]
            query = "INSERT INTO TECH_IND (ticker, run_date, ema, rsi, r3, s3) VALUES (?,?,?,?,?,?)"
            c.execute(query,vals)
        except Exception as e:
            print("db error {}".format(e))
            
        try:
            db.commit()
        except:
            db.rollback()

db.close()




#c=db.cursor()
#query_daily_price_sql = '''SELECT * from DAILY_PRICE 
 #   where close_date < "''' + str(queryDate) + '''"'''
#Use for backtesting
#start_date = dt.datetime.strptime('20211101', "%Y%m%d").date()
#end_date = (dt.datetime.strptime('20211101', "%Y%m%d") - dt.timedelta(days=2)).date()
#query_daily_price_backtest_sql = '''SELECT * from DAILY_PRICE 
#    where close_date between "''' + str(end_date) + '''" and "''' + str(start_date) +'''"'''

#c.execute(query_daily_price_backtest_sql)
#result = c.fetchall()
#print all rows for a given table
