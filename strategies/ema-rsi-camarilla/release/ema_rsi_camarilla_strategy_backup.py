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
1. PORTFOLIO dataframe for the particular ticker with strategy_name, ticker, active_stocks, total_price, and time -  [ONLY ONE ROW SHOULD BE PRESENT]
2. ticker - ticker symbol
3. nextValidOrderId - unique orderid if buy or sell decision is made
4. INTRADAY_DATA dataframe for the particular ticker with time, delayed_bid, delayed_ask, delayed_last_traded, and delayed_prior [AGAIN the query limits the result to ONE ROW]


1. build a data dictionary with the following sample format
data = {
        'ticker': 'MSFT'<ticker symbol>
        'strategy_name': 'ema-rsi-camarilla'
        'status': 0 [TBD: Need to revisit status to check if the order is filled, in progress or cancelled]
        
        
        
        }

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
    
   
    '''
    TBD: Comments
    '''
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
         print(result_df)
         return result_df

    '''
    Make Buy or Sell decision for individual ticker and date.
    This function is for one row. used loc[0]. not for more than one rows.
    '''
    def  strategy_ema_rsi_cam(self, intra_date, bid_price, ask_price, ticker):
        query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and run_date = "'''+str(intra_date)+'''"'''
        print(query_intra_sql)
        result_df = pd.read_sql_query(query_intra_sql, db)
        if not result_df.empty:
            print("Tech Indicator: bid - {}, ask-{}, ema-{}, rsi-{}, r3-{}, s3-{}".format(bid_price, ask_price,result_df.iloc[0]['ema'], result_df.iloc[0]['rsi'],result_df.iloc[0]['r3'],result_df.iloc[0]['s3'])) 
            result_df['action'] = "NO ACTION"
            result_df['unit_price'] = 0
            
            if  result_df.iloc[0]['rsi'] <= 20:
                if ask_price > result_df.iloc[0]['ema'] and ask_price < result_df.iloc[0]['s3']:
                    result_df['action'] = 'BUY'
                    result_df['unit_price'] = ask_price
            if result_df.iloc[0]['rsi'] >= 80:
                if bid_price > result_df.iloc[0]['ema'] and bid_price < result_df.iloc[0]['r3']:
                    result_df['action'] = 'SELL'
                    result_df['unit_price'] = bid_price
                    
            ''' 
            if ask_price > result_df.iloc[0]['ema']:
                if  result_df.iloc[0]['rsi'] <= 20 and ask_price < result_df.iloc[0]['s3']:
                    result_df['action'] = 'BUY'
            if bid_price > result_df.iloc[0]['ema']:
                    if result_df.iloc[0]['rsi'] >= 80 and bid_price < result_df.iloc[0]['r3']:
                        result_df['action'] = 'SELL'
            '''
        #print(result_df)                
        return result_df

    def prev_weekday(self, adate):
        adate -= dt.timedelta(days=1)
        while adate.weekday() > 4: # Mon-Fri are 0-4
            adate -= dt.timedelta(days=1)
        return adate


    def decideBuyOrSell(self, intraday_data, ticker, order_id, portfolio_df):
        c = db.cursor()
        #During runtime, intraday isonly one record.
        for index, item in intraday_data.iterrows(): #for loop is added only for testing multiple intraday data. In Live this should have only one item.
            data = {}
            data['ticker'] = ticker
            data['strategy_name'] = 'ema-rsi-camarilla'
            #data['bid_price'] = item['delayed_bid']
            #data['ask_price'] = item['delayed_ask']            
            #data['quantity'] = 1
            #data['total_price'] =  1 * item['delayed_bid']
            data['status'] =  0

            if item['delayed_bid'] == 0 or item['delayed_ask'] == 0:
                data['tech_indicator'] =  'NA'
                data['action'] =  "NO ACTION - Delyed Bid {}, Delayed ask {}".format(item['delayed_bid'], item['delayed_ask'])
            else:
                    intra_time = dt.datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S").date()
                    if intra_time == dt.datetime.today().date():
                        #history_date = (dt.datetime.today() - dt.timedelta(days=1)).date()
                        history_date = self.prev_weekday(dt.datetime.today().date())
                    else:
                        history_date = intra_time
                    strategy_result_df = self.strategy_ema_rsi_cam(history_date, item['delayed_bid'],item['delayed_ask'], ticker)
                    if strategy_result_df.empty:
                        data['tech_indicator'] =  'NA'
                        data['action'] =  'NO ACTION - strategy result is empty'
                    else:
                        data['tech_indicator'] =  '''ema:{}, rsi:{}, camarilla_r3:{}, camarilla_s3:{}'''.format(strategy_result_df.iloc[0]['ema'], strategy_result_df.iloc[0]['rsi'], strategy_result_df.iloc[0]['r3'], strategy_result_df.iloc[0]['s3'])
                        data['action'] = strategy_result_df.iloc[0]['action']
                        data['unit_price'] = strategy_result_df.iloc[0]['unit_price']
                        
        
            print('stock:{} - action:{}'.format(ticker,data['action'] ))
            if data['action'] == "NO ACTION":
                continue
        
            try:
                print(order_id)
                if data['action'] == 'BUY':
                    if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] < 2:
                        data['quantity'] = 1
                        data['total_price'] =  data['quantity'] * data['unit_price']
                        app.placeOrder(order_id, self.usTechStk(data['ticker']), self.limitOrder(data['action'],data['quantity'],data['unit_price'])) # EClient function to request contract details
                        time.sleep(10) # some latency added to ensure that the contract details request has been processed
                        
                        #insert a buy transaction in trade_transaction table
                        columns = ', '.join("'" + str(x) + "'" for x in data.keys())
                        columns = columns+', "time"'
                        values = ', '.join("'" + str(x)+ "'" for x in data.values())
                        values = values + ', CURRENT_TIMESTAMP'
                        query = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('TRADE_TRANSACTION', columns, values)
                        c.execute(query)
                        
                        #update portfolio table
                        active_stocks = portfolio_df.iloc[0]['active_stocks']+data['quantity']
                        total_price = portfolio_df.iloc[0]['total_price']+data['unit_price']
                        update_query = "update portfolio set active_stocks = {}, total_price = {} , time = CURRENT_TIMESTAMP where strategy_name = 'ema_rsi_camarilla' and ticker = '{}'".format(active_stocks, total_price, data['ticker']);
                        c.execute(update_query)
                    else:
                        print("Skipping buy for ticker: {} as we already hold max active stocks. portfolio details: {}".format(data['ticker'],portfolio_df))
 
                if data['action'] == 'SELL':
                    if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] > 0:
                        data['quantity'] = portfolio_df.iloc[0]['active_stocks']
                        data['total_price'] =  data['quantity'] * data['unit_price']
                        app.placeOrder(order_id, self.usTechStk(data['ticker']), self.limitOrder(data['action'],data['quantity'],data['unit_price'])) # EClient function to request contract details
                        time.sleep(10) # some latency added to ensure that the contract details request has been processed
                      
                        #insert a buy transaction in trade_transaction table
                        columns = ', '.join("'" + str(x) + "'" for x in data.keys())
                        columns = columns+', "time"'
                        values = ', '.join("'" + str(x)+ "'" for x in data.values())
                        values = values + ', CURRENT_TIMESTAMP'
                        query = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('TRADE_TRANSACTION', columns, values)
                        c.execute(query)
                      
                        #update portfolio table
                        active_stocks = portfolio_df.iloc[0]['active_stocks']-data['quantity']
                        total_price = portfolio_df.iloc[0]['total_price'] * active_stocks
                        update_query = "update portfolio set active_stocks = {}, total_price = {} , time = CURRENT_TIMESTAMP where strategy_name = 'ema_rsi_camarilla' and ticker = '{}'".format(active_stocks, total_price, data['ticker']);
                        c.execute(update_query)
                    else:
                        print("Skipping sell for ticker: {} as we already hold no active stocks. portfolio details: {}".format(data['ticker'],portfolio_df))                                      
                

            except Exception as e:
                print("db error {}".format(e))
            try:
                db.commit()
            except:
                db.rollback()  
                
                
                
                
    
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







