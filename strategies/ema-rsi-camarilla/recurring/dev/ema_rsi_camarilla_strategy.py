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
db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')  
c = db.cursor()
tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#tickers = ["FB","MSFT"]



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
app.connect(host='127.0.0.1', port=4002, clientId=2002) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()
time.sleep(1) 
order_id = app.nextValidOrderId


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

'''
Make Buy or Sell decision for individual ticker and date.
This function is for one row. used loc[0]. not for more than one rows.
'''
def  strategy_ema_rsi_cam(intra_date, current_price, ticker):
    query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and run_date = "'''+str(intra_date)+'''"'''
    #print(query_intra_sql)
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
    query_current_price_sql = ''' SELECT * from TICKER_{} ORDER BY time DESC LIMIT 1'''.format(ticker)
    result_df = pd.read_sql_query(query_current_price_sql, db)
    print(result_df)
    return result_df



def decideBuyOrSell(intraday_data, ticker, order_id):
    #During runtime, intraday isonly one record.
    for index, item in intraday_data.iterrows():
        data = {}
        data['ticker'] = ticker
        data['strategy_name'] = 'ema-rsi-camarilla'
        data['unit_price'] = item['delayed_last_traded']
        data['quantity'] = 1
        data['total_price'] =  1 * item['delayed_last_traded']
        data['status'] =  0

        if item['delayed_last_traded'] == 0:
            data['tech_indicator'] =  'NA'
            data['action'] =  'NO ACTION'
        else:
            intra_time = dt.datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S").date()
            if intra_time == dt.datetime.today().date():
                history_date = (dt.datetime.today() - dt.timedelta(days=1)).date()
            else:
                history_date = intra_time
            strategy_result_df = strategy_ema_rsi_cam(history_date, item['delayed_last_traded'], ticker)
            if strategy_result_df.empty:
                data['tech_indicator'] =  'NA'
                data['action'] =  'NO ACTION'
            else:
                data['tech_indicator'] =  '''ema:{}, rsi:{}, camarilla_r3:{}, camarilla_s3:{}'''.format(strategy_result_df.iloc[0]['ema'], strategy_result_df.iloc[0]['rsi'], strategy_result_df.iloc[0]['r3'], strategy_result_df.iloc[0]['s3'])
                data['action'] = strategy_result_df.iloc[0]['action']
        
        print('stock:{} - action:{}'.format(ticker,data['action'] ))
        if data['action'] == "NO ACTION":
            continue
        
        try:

            print(order_id)
            app.placeOrder(order_id,usTechStk(data['ticker']),limitOrder("BUY",data['quantity'],data['unit_price'])) # EClient function to request contract details
            time.sleep(10) # some latency added to ensure that the contract details request has been processed
            columns = ', '.join("'" + str(x) + "'" for x in data.keys())
            columns = columns+', "time"'
            values = ', '.join("'" + str(x)+ "'" for x in data.values())
            values = values + ', CURRENT_TIMESTAMP'
            query = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('TRADE_TRANSACTION', columns, values)
            c.execute(query)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()  
        


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
    intraday_data= getCurrentPrice(ticker)
    decideBuyOrSell(intraday_data, ticker, order_id)
    order_id = order_id + 1
    

















#order_id = app.nextValidOrderId
#app.placeOrder(order_id,usTechStk("MSFT"),limitOrder("BUY",1,200)) # EClient function to request contract details
#time.sleep(5) # some latency added to ensure that the contract details request has been processed

