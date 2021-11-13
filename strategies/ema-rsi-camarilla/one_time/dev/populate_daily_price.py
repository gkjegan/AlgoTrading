#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 21:14:31 2021

@author: jegankarunakaran
"""

# Import libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import threading
import time
import datetime as dt
import sqlite3


tickers = ["FB"]

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
        
        print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(tickers[reqId],bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))
        try:
            c = db.cursor()
            print(" ticker:", tickers[reqId], "Time:",dt.datetime.strptime(bar.date, "%Y%m%d").date(), "Open Price:", bar.open,"Close Price:", bar.close,"High Price:", bar.high,"Low Price:", bar.low, "Volume:", bar.volume)
            vals = [tickers[reqId], dt.datetime.strptime(bar.date, "%Y%m%d").date(), bar.open, bar.close, bar.high, bar.low,bar.volume]
            query = "INSERT INTO DAILY_PRICE (ticker, close_date, open_price, close_price, high_price, low_price,volume) VALUES (?,?,?,?,?,?,?)"
            c.execute(query,vals)
        except Exception as e:
            print("db error {}".format(e))
        
        try:
            db.commit()
        except:
            db.rollback()
            

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def histData(req_num,contract,duration,candle_size):
    """extracts historical data"""
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='ADJUSTED_LAST',
                          useRTH=1,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[])	 # EClient function to request contract details

def websocket_con():
    global db
    db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/db/ema_rsi_camarilla.db')
    app.run()
    
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established


#tickers = ['MSFT', 'APPL', 'TSLA', 'FB', 'BRK.B', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']


for ticker in tickers:
    histData(tickers.index(ticker),usTechStk(ticker),'20 D', '1 day')
    time.sleep(10)



