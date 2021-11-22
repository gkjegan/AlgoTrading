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
import time
import requests



tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#APPL stock is not available, so removed
#tickers = ['MSFT', "TSLA"]


'''
 Steps to follow for every TWA Streaming API Calls

1. Create a class that inherits EClient and EWrapper classes from TWA API. class TradeApp(EWrapper, EClient): 
2. Instantiate the class app = TradeApp()
3. Connect the app to TWA withP, port, and clientId app.connect(host='127.0.0.1', port=7497, clientId=23) 
4. Identify what client API to use. for example, to get streaming data, you need to call  app.reqMktData EClient.
5. The results are available in the callback functions defined in EWrapper Interface that needs to be implemented.
    Again, for the same example, calling app.reqMktData will return streaming data in the callback function called "tickPrice" of EWrapper interface
    So, implement tickPrice function. Along with tickPrice, tickSize is also received but not used for our usecase. 
 
'''



'''
Step 1, and 5 from above
Create a class to inherit EClient and EWrapper and implement tickPrice and tickSize

tickPrice is more complex than historic data.
    a. it is streaming - so we need to call "cancelMktData" to stop the stream
    b. different tick types of streaming data comes in the callback. we are interested in specific tick types. 
    for more details refer to  - https://interactivebrokers.github.io/tws-api/tick_types.html
    c. Also the streaming data is collected in a global dictionary with ticker index as key and a dictonary as values. sample structure for one ticker
    data = {
        0<ticker Index> : { "delayed_bid":324.0, "delayed_ask": 325.2, "delayed_last_traded": 314.0, "delayed_prior": 325}, 
        1 : {...},
        .
        .
        n: {...}        
        }    
    
ticker types used
1 - Highest priced bid for the contract
2 - Lowest price offer on the contract
4 - Last price at which contract traded
9 - The last available closing price for the previous day 

The above four are real-time market data. If we have mardata subscription, we will get real-time automatically.
even is we ask for delayed data using   "app.reqMarketDataType(3)" 

if the real-time is not available, we will get 15 mins delayed data
66 - Delayed bid price
67 - Delayed ask price
68 - Delayed last traded price
75 - The prior day's closing price. 
'''
data = {}
class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        print("TickPrice. TickerId:", reqId, "tickType:", tickType, "Price:", price)
        
        if reqId not in data:
            data[reqId] = {}
        
        if tickType == 66 or tickType == 1:
            if price > 0:
                data[reqId]['delayed_bid'] = price

        if tickType == 67 or tickType == 2:
            if price > 0:
                data[reqId]['delayed_ask'] = price
        
        if tickType == 68 or tickType == 4:
            if price > 0:
                data[reqId]['delayed_last_traded'] = price

        if tickType == 75 or tickType == 9:
            if price > 0:
                data[reqId]['delayed_prior'] = price            


    def tickSize(self, reqId, tickType, size):
        super().tickSize(reqId, tickType, size)
        print("TickSize Ignored.")

    
'''
HELPER FUNCTIONS
usTechStk - used to create a contract
streamSnapshotData - used as wrapper to call "reqMktData" to start the streaming data
cancelMarketData - used as wrapper to call "cancelMarketData" to stop the streaming data
websocket_com - wrapper to start the app
'''
def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def streamSnapshotData(req_num,contract):
    #print(req_num)
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

    
'''
Connect to Trading App and start a thread.
'''
app = TradeApp()
app.connect(host='127.0.0.1', port=4002, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established


'''
for each ticker, call streamSnapshotData method by passing 
1. the ticker, 
2. index of the ticker and 
3. contract object 
to start the streaming data.
'''
for ticker in tickers:
    print(ticker)
    streamSnapshotData(tickers.index(ticker),usTechStk(ticker))
    time.sleep(10)
    #print(data)
    

'''
for each ticker, call cancelMarketData method by passing 
1. the ticker, 
2. index of the ticker and 
3. contract object 
to stop the streaming data.
'''
#time.sleep(5) # some latency added to ensure that the contract details request has been processed
for ticker in tickers:
    time.sleep(3)
    print("canceling ticker - {}".format(ticker))
    cancelMarketData(tickers.index(ticker))
    
    
'''
once you got the data dictionary of all tickers
    data = {
        0<ticker Index> : { "delayed_bid":324.0, "delayed_ask": 325.2, "delayed_last_traded": 314.0, "delayed_prior": 325}, 
        1 : {...},
        .
        .
        n: {...}        
        }  
    
connect to db and insert into ticker_{} tables.
time is the primary key, every time the script run, the latest data is recorded in the table.
'''
#print(data)
global db
db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')   
c=db.cursor()
for items in data:
    print(items)
    ticker = tickers[items]
    delayed_last_traded = 0
    delayed_bid = 0
    delayed_ask = 0
    delayed_prior = 0
    if data[items]:
        if 'delayed_last_traded' in data[items]:
            delayed_last_traded = data[items]['delayed_last_traded']
        if 'delayed_bid' in data[items]:
            delayed_bid = data[items]['delayed_bid']
        if 'delayed_ask' in data[items]:
            delayed_ask = data[items]['delayed_ask']
        if 'delayed_prior' in data[items]:
            delayed_prior = data[items]['delayed_prior']
            
    vals = [delayed_bid, delayed_ask, delayed_last_traded, delayed_prior ] 
    print(vals)
    query = "INSERT INTO TICKER_{}(time,delayed_bid,delayed_ask,delayed_last_traded,delayed_prior) VALUES (CURRENT_TIMESTAMP,?,?,?,?)".format(ticker)
    c.execute(query,vals)
    try:
        db.commit()
    except:
        db.rollback() 


'''
Ping to healthchecks.io for  monitoring
'''
try:
    requests.get("https://hc-ping.com/29c13e21-4792-4418-9e68-b03dc73eef58", timeout=10)
except requests.RequestException as e:
    # Log ping failure here...
    print("Ping failed: %s" % e)
time.sleep(120)
app.disconnect()