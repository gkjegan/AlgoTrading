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



#tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
tickers = ["MSFT"]


class TradeApp(EWrapper, EClient): 
    
    def __init__(self): 
        EClient.__init__(self, self) 


    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId,errorCode,errorString))
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", self.nextValidOrderId )
        # Using this callback function as starting point and call the start method.
        self.start()
    
   
    def start(self):

        global db
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')  
        for ticker in tickers:
            try:
                query = "SELECT * from TECH_IND where ticker = '{}' and run_date = '{}';".format(ticker, '2021-11-26')
                self.tech_ind = pd.read_sql_query(query, db)
                print(self.tech_ind)
            except Exception as e:
                print("db error {}".format(e))
            try:
                db.commit()
            except:
                db.rollback()  
            
            buy_price = round(self.tech_ind.iloc[0]['s3'],2)
            sell_price = round(self.tech_ind.iloc[0]['r3'],2)
            
            print('buy_price: {}'.format(buy_price))
            print('sell: {}'.format(sell_price))
            #app.placeOrder(self.nextValidOrderId, self.usTechStk(ticker), self.limitOrder('BUY',1,buy_price)) # EClient function to request contract details
            time.sleep(5)
            #app.placeOrder(self.nextValidOrderId, self.usTechStk(ticker), self.limitOrder('SELL',1,sell_price)) # EClient function to request contract details
            #time.sleep(5)
        time.sleep(5)    
        app.disconnect()
       

    #creating object of the Contract class - will be used as a parameter for other function calls
    def usTechStk(self, symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.currency = currency
        contract.exchange = exchange
        return contract 

    #creating object of the limit order class - will be used as a parameter for other function calls
    def limitOrder(self, direction,quantity,lmt_price):
        order = Order()
        order.action = direction
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = lmt_price
        return order
               
    
def websocket_con(tickers):
    app.run()    

    
'''
There is no client method called here (as compared to reqHistoricalData or reqMktData in getting historical or streaming data)
Here, once the app is started, nextValidId is method is always called. we will use the callback function to start the but or sell actions.
Refer to nextValidId function the Trading App. 

'''
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=5002) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()
time.sleep(3) 




