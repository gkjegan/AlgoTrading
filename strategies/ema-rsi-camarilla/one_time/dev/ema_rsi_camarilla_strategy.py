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
c = db.cursor()
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


'''
transaction df details
- transaction_id - not needed in df. needed in db
- strategy_name 
- ticker
- tech_indicator (json/dict)
- action
- unit price (current price)
- total price
- status
- time of transaction
'''
transaction_df = pd.DataFrame()

def  strategy_ema_rsi_cam(intra_date, current_price, ticker):
    query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and run_date = "'''+str(intra_date)+'''"'''
    result_df = pd.read_sql_query(query_intra_sql, db)

    if not result_df.empty:
        result_df['action'] = 'NO ACTION'
        if current_price > result_df.iloc[0]['ema']:
            if  result_df.iloc[0]['rsi'] <= 20 and current_price < result_df.iloc[0]['s3']:
                result_df['action'] = 'BUY'
            if result_df.iloc[0]['rsi'] >= 80 and current_price < result_df.iloc[0]['r3']:
                result_df['action'] = 'SELL'
    #print(result_df)                
    return result_df
    

def getCurrentPrice(ticker):
    """get current price from ticker table"""
    query_current_price_sql = ''' SELECT * from TICKER_{}'''.format(ticker)
    result_df = pd.read_sql_query(query_current_price_sql, db)
    return result_df


'''    
for ticker in tickers:
    intraday_data = getCurrentPrice(ticker)
    
    #During runtime, intraday isonly one record.
    for index, item in intraday_data.iterrows():

        temp_data = {}
        temp_data['ticker'] = ticker
        temp_data['strategy_name'] = 'ema-rsi-camarilla'
        temp_data['unit_price'] =item['delayed_last_traded']
        temp_data['quantity'] = 1
        temp_data['total_price'] = item['delayed_last_traded']
        temp_data['status'] = 1
        intra_time = dt.datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S").date()
        result_df = strategy_ema_rsi_cam(intra_time, item['delayed_last_traded'], ticker)
        if result_df.empty:
            temp_data['tech_indicator'] =\'''NA\'''
            temp_data['action'] = 'NO ACTION'
        else:
            temp_data['tech_indicator'] =\'''ema:{}, rsi:{}, camarilla_r3:{}, camarilla_s3:{}\'''.format(result_df['ema'], result_df['rsi'], result_df['r3'], result_df['s3'])
            temp_data['action'] = result_df.iloc[0]['action']
        
        transaction_df = transaction_df.append(temp_data, ignore_index=True)
'''    
for ticker in tickers:
    intraday_data = getCurrentPrice(ticker)
    
    #During runtime, intraday isonly one record.
    for index, item in intraday_data.iterrows():

        val = []
        val.append(ticker)
        val.append('ema-rsi-camarilla')
        val.append(item['delayed_last_traded'])
        val.append(1)
        val.append(item['delayed_last_traded'])
        val.append(1)
        intra_time = dt.datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S").date()
        result_df = strategy_ema_rsi_cam(intra_time, item['delayed_last_traded'], ticker)
        if result_df.empty:
            val.append('''NA''')
            val.append('NO ACTION')
        else:
            val.append('''ema:{}, rsi:{}, camarilla_r3:{}, camarilla_s3:{}'''.format(result_df['ema'], result_df['rsi'], result_df['r3'], result_df['s3']))
            val.append(result_df.iloc[0]['action'])
            
        try:
            query = "INSERT INTO TRADE_TRANSACTION (ticker, strategy_name, unit_price, quantity, total_price, status,tech_indicator,action, time) VALUES (?,?,?,?,?,?,?,?, CURRENT_TIMESTAMP)"
            c.execute(query,val)
        except Exception as e:
            print("db error {}".format(e))
        
        try:
            db.commit()
        except:
            db.rollback()        



print(transaction_df)    
















#order_id = app.nextValidOrderId
#app.placeOrder(order_id,usTechStk("MSFT"),limitOrder("BUY",1,200)) # EClient function to request contract details
#time.sleep(5) # some latency added to ensure that the contract details request has been processed

