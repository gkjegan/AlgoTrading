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
#from uuid import uuid4
import requests


tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#tickers = ["FB","MSFT", "JPM"]

'''
**Steps to follow for every TWA API Calls**

1. Create a class that inherits EClient and EWrapper classes from TWA API. class TradeApp(EWrapper, EClient): 
2. Instantiate the class app = TradeApp()
3. Connect the app to TWA withP, port, and clientId app.connect(host='127.0.0.1', port=7497, clientId=23) 
4. Identify what client API to use. for example, to get place an order we need a valid unique Order Id.\
    When the app is strated, the callback function called  "nextValidId" is called.
5. Using the next valid orderId, call the start method for buy or sell



**Data Needed for decision:**
PORTFOLIO - PORTFOLIO table holds the summary of all tickers and total number of active stocks and total price invested. 
This table will serve as a complete summary and also to apply caps on the total number of stocks or amount to invest.

CURRENT_PRICE - This is latest price from intraday price load  (intraday_price_load.py) stored in TICKER_{} table. 
we get the latest current price using query order by time and desc limit 1:
    TBD: Not a ideal way to get the latest. This script runs every 40 mins and intraday runs every 30 mins. Ideally we need the data that was loaded latest.
    If for any reason, if the last load fails, this query will fetch delayed data. For any delayed data, our order may not go through. need to revisit this logic

TECH_IND details - TECH_IND table holds the technical indicator for each ticker and prior date. This data will give ema, rsi and camarilla s3 and r3 to decide buy or sell

**Buy or Sell logic**
function "decideBuyOrSell" is run on each ticker and will take following parameter
for each ticker
- PORTFOLIO dataframe for the particular ticker with strategy_name, ticker, active_stocks, total_price, and time -  [ONLY ONE ROW SHOULD BE PRESENT]
- ticker - ticker symbol
- nextValidOrderId - unique orderid if buy or sell decision is made
- INTRADAY_DATA dataframe for the particular ticker with time, delayed_bid, delayed_ask, delayed_last_traded, and delayed_prior [AGAIN the query limits the result to ONE ROW]


1. build a data dictionary with the following sample format to store in TRADE_TRANSACTION table.
trade_transaction_data = {
        'ticker': 'MSFT'<ticker symbol>
        'strategy_name': 'ema-rsi-camarilla'
        'status': 0 [TBD: Need to revisit status to check if the order is filled, in progress or cancelled]
        'action': 'NO ACTION | BUY | SELL'
        'technical indicator': string to display the emi, rsi, r3, s3 data or NA
        'unit_price': bid price  or ask price based on buy or sell
        'quantity': quantity to buy (usualy 1) or sell (all the active_stocks usually 2)
        'total_price': quantity * unit_price
        'time': CURRENT TIMESTAMP
        }

1. ticker is straight forward. assign ticker from params
2. strategy name is also straignt forward. currently hard coded
3. status is also hard coded to 0. Need revisit. @TBD
4. action is the key to decision.
    to decide buy or sell, you need prior day technical indicator and latest delayed_bid and delayed_ask
    a. calculate prior weekday - take the current run date and use "prev_weekday" function to calculate the previous weekday
    b. call "strategy_ema_rsi_cam" function with prior weekday, delayed_bid, delayed_ask, ticker to get three things
        i. action - BUY or SELL or NO ACTION
        ii. technical indicator - details of rsi, ema, r3, and s3 for the ticker or NA if not available
        iii. unit_price - bid if action is SELL, ask if action is BUY
    c. add unit_price, action, and tech_indicator to trade_transaction_data
5. If BUY,
    a. Place limit order with fixed quantity 1 for ask price 
    b. populate trade_transaction table
    c. update portfolio table
6. If SELL,
    a. Place limit order with available stocks quantity (2) for bid price 
    b. populate trade_transaction table
    c. update portfolio table
    
'''
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
                query = "SELECT * from PORTFOLIO where strategy_name = 'ema_rsi_camarilla' and ticker = '{}';".format(ticker)
                self.portfolio_df = pd.read_sql_query(query, db)
                print(self.portfolio_df)
            except Exception as e:
                print("db error {}".format(e))
            try:
                db.commit()
            except:
                db.rollback()  
                
            self.intraday_data= self.getCurrentPrice(ticker)
            self.decideBuyOrSell(self.intraday_data, ticker, self.nextValidOrderId, self.portfolio_df)
            self.nextValidOrderId= self.nextValidOrderId+1
            time.sleep(5)
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

    def getCurrentPrice(self, ticker):
         """get current price from ticker table"""
         query_current_price_sql = ''' SELECT * from TICKER_{} ORDER BY time DESC LIMIT 1'''.format(ticker)
         result_df = pd.read_sql_query(query_current_price_sql, db)
         print("Intraday Data:")
         print(result_df)
         return result_df

    '''
    MThe core strategy to decide BUY or SELL
    if RSI < 20, ASK_PRICE > EMA, and ASK_PRICE < S3:
        BUY
    if RSI > 20, BID_PRICE > EMA, and BID_PRICE < R3:
        SELL    
    '''
    def  strategy_ema_rsi_cam(self, prior_weekday, bid_price, ask_price, ticker):
        query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and run_date = "'''+str(prior_weekday)+'''"'''
        print(query_intra_sql)
        result_df = pd.read_sql_query(query_intra_sql, db)

        if result_df.empty:
            return 0, "NA", "NO ACTION - No technical indicator for ticker {} and prior weekday {}".format(ticker, prior_weekday)
        
        else:
            tech_indicator_data = result_df.iloc[0]
            unit_price = 0
            action = ""
            tech_indicator_msg = "Tech Indicator: bid - {}, ask-{}, ema-{}, rsi-{}, r3-{}, s3-{}".format(bid_price, ask_price, tech_indicator_data['ema'], tech_indicator_data['rsi'],tech_indicator_data['r3'],tech_indicator_data['s3'])
            print(tech_indicator_msg) 
            if  tech_indicator_data['rsi'] <= 20 and ask_price > tech_indicator_data['ema'] and ask_price < tech_indicator_data['s3']:
                action = "BUY"
                unit_price = ask_price
                print("BUY SIGNAL:  RSI condition - {}, EMA condition - {}, Camarilla condition - {} ".format(tech_indicator_data['rsi'] <= 20 , ask_price > tech_indicator_data['ema'], ask_price < tech_indicator_data['s3'])) 
            else :
                action = "NO ACTION"
                print("NO ACTION - BUY SKIPPED RSI condition - {}, EMA condition - {}, Camarilla condition - {} ".format(tech_indicator_data['rsi'] <= 20 , ask_price > tech_indicator_data['ema'], ask_price < tech_indicator_data['s3']))
            if tech_indicator_data['rsi'] >= 80 and bid_price > tech_indicator_data['ema'] and bid_price < tech_indicator_data['r3']:
                action = "SELL"
                unit_price = bid_price
                print("SELL SIGNAL: RSI condition - {}, EMA condition - {}, Camarilla condition - {} ".format(tech_indicator_data['rsi'] >= 80 , bid_price > tech_indicator_data['ema'], bid_price < tech_indicator_data['r3'])) 
            else:
                action = "NO ACTION"
                print("NO ACTION - SELL SKIPPED RSI condition - {}, EMA condition - {}, Camarilla condition - {} ".format(tech_indicator_data['rsi'] >= 80 , bid_price > tech_indicator_data['ema'], bid_price < tech_indicator_data['r3']))
            return unit_price, tech_indicator_msg, action
            
    

    def prev_weekday(self, adate):
        adate -= dt.timedelta(days=1)
        while adate.weekday() > 4: # Mon-Fri are 0-4
            adate -= dt.timedelta(days=1)
        return adate

    def populate_trade_transaction(self, trade_transaction_date):
        try:
            c = db.cursor()
            #insert a buy transaction in trade_transaction table
            columns = ', '.join("'" + str(x) + "'" for x in trade_transaction_date.keys())
            columns = columns+', "time"'
            values = ', '.join("'" + str(x)+ "'" for x in trade_transaction_date.values())
            values = values + ', CURRENT_TIMESTAMP'
            query = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('TRADE_TRANSACTION', columns, values)
            c.execute(query)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()  
        
    def update_portfolio(self, trade_transaction_data, active_stocks, total_price):
        try:
            c = db.cursor()
            #update portfolio table
            update_query = "update portfolio set active_stocks = {}, total_price = {} , time = CURRENT_TIMESTAMP where strategy_name = 'ema_rsi_camarilla' and ticker = '{}'".format(active_stocks, total_price, trade_transaction_data['ticker']);
            c.execute(update_query)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback() 
            
    '''
    see detailed comments in the section **Buy or Sell logic** above
    '''
    def decideBuyOrSell(self, intraday_data, ticker, order_id, portfolio_df):
        intraday_item = intraday_data.iloc[0]
        trade_transaction_data = {}
        trade_transaction_data['ticker'] = ticker
        trade_transaction_data['strategy_name'] = 'ema-rsi-camarilla'
        trade_transaction_data['status'] =  0
        prior_weekday = self.prev_weekday(dt.datetime.today().date())
        #call strategy to decide buy or sell or no action
        unit_price, tech_indicator, action = self.strategy_ema_rsi_cam(prior_weekday,intraday_item['delayed_bid'],intraday_item['delayed_ask'], ticker )
        trade_transaction_data['action'] = action
        trade_transaction_data['tech_indicator'] = tech_indicator
        trade_transaction_data['unit_price'] = unit_price
        if trade_transaction_data['action'] == 'BUY':
            if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] < 2:
                trade_transaction_data['quantity'] = 1
                trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                app.placeOrder(order_id, self.usTechStk(trade_transaction_data['ticker']), self.limitOrder(trade_transaction_data['action'],trade_transaction_data['quantity'],trade_transaction_data['unit_price'])) # EClient function to request contract details
                time.sleep(10) # some latency added to ensure that the contract details request has been processed
                self.populate_trade_transaction(trade_transaction_data)
                active_stocks = portfolio_df.iloc[0]['active_stocks']+trade_transaction_data['quantity']
                total_price = portfolio_df.iloc[0]['total_price']+trade_transaction_data['unit_price']
                self.update_portfolio(trade_transaction_data, active_stocks, total_price)
            else:
                print("Skipping buy for ticker: {} as we already hold max active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))
         
        if trade_transaction_data['action'] == 'SELL':
            if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] > 0:
                trade_transaction_data['quantity'] = portfolio_df.iloc[0]['active_stocks']
                trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                app.placeOrder(order_id, self.usTechStk(trade_transaction_data['ticker']), self.limitOrder(trade_transaction_data['action'],trade_transaction_data['quantity'],trade_transaction_data['unit_price'])) # EClient function to request contract details
                time.sleep(10) # some latency added to ensure that the contract details request has been processed
                self.populate_trade_transaction(trade_transaction_data)
                active_stocks = portfolio_df.iloc[0]['active_stocks']-trade_transaction_data['quantity']
                total_price = portfolio_df.iloc[0]['total_price'] * active_stocks
                self.update_portfolio(trade_transaction_data, active_stocks, total_price)
            else:
                print("Skipping sell for ticker: {} as we already hold no active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))  
        
                
    
def websocket_con(tickers):
    app.run()    

    
'''
There is no client method called here (as compared to reqHistoricalData or reqMktData in getting historical or streaming data)
Here, once the app is started, nextValidId is method is always called. we will use the callback function to start the but or sell actions.
Refer to nextValidId function the Trading App. 

'''
app = TradeApp()
app.connect(host='127.0.0.1', port=4002, clientId=2002) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()
time.sleep(3) 



'''
Ping to healthchecks.io for  monitoring
'''
try:
    requests.get("https://hc-ping.com/5b26f911-a5b7-4876-a005-20722be58e74", timeout=10)
except requests.RequestException as e:
    # Log ping failure here...
    print("Ping failed: %s" % e)




