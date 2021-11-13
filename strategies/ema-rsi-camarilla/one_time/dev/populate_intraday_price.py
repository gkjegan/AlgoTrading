#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:00:47 2021

@author: jeganKarunakaran

PLEASE NOTE: THIS FILE IS RUNNING IN CRON JOB. ANY MODIFICATION WILL IMPACT THE DATA LOAD
*/15 * * * 1-5 conda activate algotrad; python /Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/ema-rsi-camarilla/populate_intraday_price.py; conda deactivate

"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import sqlite3
import datetime as dt
import time
import requests



tickers = ['MSFT', 'APPL', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#tickers = ['FB']
data = {}

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 


    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        print("TickPrice. TickerId:", reqId, "tickType:", tickType, "Price:", price)
        
        if reqId not in data:
            data[reqId] = {}
        
        if tickType == 66:
            data[reqId]['delayed_bid'] = price

        if tickType == 67:
            data[reqId]['delayed_ask'] = price
        
        if tickType == 68:
            data[reqId]['delayed_last_traded'] = price

        if tickType == 75:
            data[reqId]['delayed_prior'] = price            

        
        '''
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})        
        if tickType == 68:
            if price > 0:
                c=db.cursor()
                vals = [price]
                query = "INSERT INTO TICKER_{}(time,price,volume) VALUES (CURRENT_TIMESTAMP,?,0)".format(tickers[reqId])
                c.execute(query,vals)
                try:
                    db.commit()
                except:
                    db.rollback() 
        '''

    def tickSize(self, reqId, tickType, size):
        super().tickSize(reqId, tickType, size)
        print("TickSize Ignored.")

    

        

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def streamSnapshotData(req_num,contract):
    print(req_num)
    """stream tick leve data"""
    app.reqMarketDataType(3)
    app.reqMktData(reqId=req_num, 
                   contract=contract,
                   genericTickList="",
                   snapshot=True,
                   regulatorySnapshot=False,
                   mktDataOptions=[])
    


def cancelMarketData(reqId):
    app.cancelMktData(reqId)


def websocket_con():
        
    app.run()
    

app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established

for ticker in tickers:
    print(ticker)
    streamSnapshotData(tickers.index(ticker),usTechStk(ticker))
    time.sleep(2)
    print(data)
    
time.sleep(10)
#time.sleep(5) # some latency added to ensure that the contract details request has been processed
for ticker in tickers:
    time.sleep(3)
    print("canceling ticker - {}".format(ticker))
    cancelMarketData(tickers.index(ticker))
    
    
print(data)
global db
db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/db/ema_rsi_camarilla.db')   
c=db.cursor()
for items in data:
    ticker = tickers[items]
    vals = [data[items]['delayed_bid'], data[items]['delayed_ask'], data[items]['delayed_last_traded'], data[items]['delayed_prior']]  
    query = "INSERT INTO TICKER_{}(time,delayed_bid,delayed_ask,delayed_last_traded,delayed_prior) VALUES (CURRENT_TIMESTAMP,?,?,?,?)".format(ticker)
    c.execute(query,vals)
    try:
        db.commit()
    except:
        db.rollback() 


try:
    requests.get("https://hc-ping.com/29c13e21-4792-4418-9e68-b03dc73eef58", timeout=10)
except requests.RequestException as e:
    # Log ping failure here...
    print("Ping failed: %s" % e)
time.sleep(30)
app.disconnect()