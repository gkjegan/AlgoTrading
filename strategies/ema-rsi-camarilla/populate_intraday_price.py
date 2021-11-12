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
import datetime as dt


tickers = ["FB","AMZN","INTC"]


class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        print("TickPrice. TickerId:", reqId, "tickType:", tickType, "Price:", price)
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

    def tickSize(self, reqId, tickType, size):
        super().tickSize(reqId, tickType, size)
        print("TickSize. TickerId:", reqId, "TickType:", tickType, "Size:", size)        
        

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def streamSnapshotData(req_num,contract):
    """stream tick leve data"""
    app.reqMarketDataType(3)
    app.reqMktData(reqId=req_num, 
                   contract=contract,
                   genericTickList="",
                   snapshot=False,
                   regulatorySnapshot=False,
                   mktDataOptions=[])

    
def websocket_con(tickers):
    global db
    db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/db/ema_rsi_camarilla.db')
    c=db.cursor()
    for ticker in tickers:
        c.execute("CREATE TABLE IF NOT EXISTS TICKER_{} (time datetime primary key,price real(15,5), volume integer)".format(ticker))
        try:
            db.commit()
        except:
            db.rollback()    
    app.run()    


app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()

for ticker in tickers:
    streamSnapshotData(tickers.index(ticker),usTechStk(ticker))

