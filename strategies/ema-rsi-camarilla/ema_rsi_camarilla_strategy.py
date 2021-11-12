#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:00:47 2021

@author: archanajegan
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import sqlite3
from ibapi.order import Order
import time
import pandas as pd
import datetime as dt


global db
db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/db/ema_rsi_camarilla.db')
tickers = ["FB","MSFT"]


'''

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 

    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId,errorCode,errorString))
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
        

#creating object of the Contract class - will be used as a parameter for other function calls
def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

#creating object of the limit order class - will be used as a parameter for other function calls
def limitOrder(direction,quantity,lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order

    

    
def websocket_con(tickers):
    app.run()    


app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()
time.sleep(1) 
'''

def  strategy_ema_rsi_cam(intra_date, current_price, ticker):
    query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and run_date = "'''+str(intra_date)+'''"'''
    result_df = pd.read_sql_query(query_intra_sql, db)
    action = 'NO ACTION'
    if current_price > result_df.iloc[0]['ema']:
        if  result_df.iloc[0]['rsi'] <= 20 and current_price < result_df.iloc[0]['s3']:
            action = 'BUY'
        if result_df.iloc[0]['rsi'] >= 80 and current_price < result_df.iloc[0]['r3']:
            action = 'BUY'
    return action
    

def getCurrentPrice(ticker):
    """get current price from ticker table"""
    query_current_price_sql = ''' SELECT * from TICKER_{}'''.format(ticker)
    result_df = pd.read_sql_query(query_current_price_sql, db)
    return result_df
    
for ticker in tickers:
    intraday_data = getCurrentPrice(ticker)
    intraday_data['action'] = "NO ACTION"
    #During runtime, intraday isonly one record.

    for index, item in intraday_data.iterrows():
        intra_time = dt.datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S").date()
        intraday_data.loc[index, 'action'] = strategy_ema_rsi_cam(intra_time, item['price'], ticker)
    print(intraday_data)    
















#order_id = app.nextValidOrderId
#app.placeOrder(order_id,usTechStk("MSFT"),limitOrder("BUY",1,200)) # EClient function to request contract details
#time.sleep(5) # some latency added to ensure that the contract details request has been processed

