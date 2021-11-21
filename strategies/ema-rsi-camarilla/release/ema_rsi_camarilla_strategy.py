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
    def  strategy_ema_rsi_cam(self, intra_date, current_price, ticker):
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


    def decideBuyOrSell(self, intraday_data, ticker, order_id, portfolio_df):
        c = db.cursor()
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
                    strategy_result_df = self.strategy_ema_rsi_cam(history_date, item['delayed_last_traded'], ticker)
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
                if data['action'] == 'BUY':
                    if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] < 2:
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







