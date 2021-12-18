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
import threading
import time
import datetime as dt
import sqlite3
import requests

#tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#APPL stock is not available, so removed
tickers = ["SPX"]
'''
 Steps to follow for every TWA API Calls

1. Create a class that inherits EClient and EWrapper classes from TWA API. class TradeApp(EWrapper, EClient): 
2. Instantiate the class app = TradeApp()
3. Connect the app to TWA withP, port, and clientId app.connect(host='127.0.0.1', port=7497, clientId=23) 
4. Identify what client API to use. for example, to get historical data, you need to call  app.reqHistoricalData EClient.
5. The results are available in the callback functions defined in EWrapper Interface that needs to be implemented.
    Again, for the same example, calling app.reqHistoricalData will return historical data in the callback function called "historicalData" of EWrapper interface
    So, implement historicalData function.

'''


'''
Step 1 and 5 from above
Create a class to inherit EClient and EWrapper and implement historicalData

historicalData:
    receives historical data from callback and store it in INDEX_DAILY_PRICE table.
'''
class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
    
    #Callback function for reqHistoricalData
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
        
        print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(tickers[reqId],bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))
        try:
            c = db.cursor()
            #print(" ticker:", tickers[reqId], "Time:",dt.datetime.strptime(bar.date, "%Y%m%d").date(), "Open Price:", bar.open,"Close Price:", bar.close,"High Price:", bar.high,"Low Price:", bar.low, "Volume:", bar.volume)
            vals = [tickers[reqId], dt.datetime.strptime(bar.date, "%Y%m%d").date(), bar.open, bar.close, bar.high, bar.low,bar.volume]
            query = "INSERT INTO INDEX_DAILY_PRICE (ticker, close_date, open_price, close_price, high_price, low_price,volume) VALUES (?,?,?,?,?,?,?)"
            c.execute(query,vals)
        except Exception as e:
            print("db error {}".format(e))
        
        try:
            db.commit()
        except:
            db.rollback()



'''
Step 4 from above

histData:
    histData function calls the EClient API reqHistoricalData with
    request id - Unique request id for API call.
    contract - objext to encapsulate ticker symbol, type(stocks, options, cash), curreny and exchange information
    endDateTime - ending time if request for previous history. this is used combined with next attribute "durationStr":
        - endDateTime: 20130701 23:59:59 GMT
        - durationStr: 3 D
        - will return three days of data counting backwards from July 1st 2013 at 23:59:59 GMT
        - empty string is the endtime is runtime
    durationStr - for our daily run, it is 1 day.
    barSizeSetting - for our use case, it is 1day. options available upto 1 sec. Means every 1 sec of historical data is available.
    whatToShow - ADJUSTED_LAST gives the divident adjusted traded price. for more options look for API doc.
    useRTH - data generated using regular trading hours. set to yes here
    formatDate - format the data and time return
    keepUpToDate - is false to stop continous update. as we are taking daily price, this is not needed
    chartOptions - usually empty. I think, EWrapper uses this.
    
https://interactivebrokers.github.io/tws-api/historical_bars.html
'''
def usTechStk(symbol,sec_type="IND",currency="USD",exchange="CBOE"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def histData(req_num, contract, duration, candle_size):
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


    
'''
Step 2 and 3 from above
Instantiate and connect the app to TWA
Also, connect to SQLLite3 database to insert the historical data.
'''      
def websocket_con():
    global db
    db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')
    app.run()

app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=1001) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established


'''
Once the App is started, now call the API for each ticker symbol
histData:
    call histData with following parameters
    request id - index of each ticker. we can map the index back to ticker when storing in database.
    contract - contract object from usTechStk(ticker) function
    duration - 1 D for every day run. need to change if need to backfill data
    candle size - 1 day - daily candles.
    
'''
for ticker in tickers:
    histData(tickers.index(ticker), usTechStk(ticker),'200 D', '1 day')
    time.sleep(10)


'''
Ping to healthchecks.io for  monitoring
'''
try:
    requests.get("https://hc-ping.com/ca8d6614-399b-4fb8-8672-6f535cda4d58", timeout=10)
except requests.RequestException as e:
    # Log ping failure here...
    print("Ping failed: %s" % e)
