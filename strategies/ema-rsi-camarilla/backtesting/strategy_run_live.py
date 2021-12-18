#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:00:47 2021

@author: archanajegan

"""

#import sqlite3
import datetime as dt
from daily_price import dailyPrice
from portfolio import portfolio
from trade_transaction import tradeTransaction
from emi_rsi_camarilla_strategy import emaRsiCamarillaStrategy
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
from ibapi.order import Order
import time
#from uuid import uuid4
import requests
from decimal import Decimal

tickers = ['AAPL', 'MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#tickers = ['MSFT']
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
        #Cancel all open orders
        self.reqGlobalCancel()
        time.sleep(5)
        
        #Get all filled orders or positions and update portfolio
        self.reqPositions()
        time.sleep(5)
        #now go for buy or sell        
        self.start()


    def position(self, account: str, contract: Contract, position: Decimal,
                 avgCost: float):
        super().position(account, contract, position, avgCost)
        print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",
              contract.secType, "Currency:", contract.currency,
              "Position:", position, "Avg cost:", avgCost)  
        portfolio.upsertPortfolio(contract.symbol, position, avgCost) 


    def start(self):       
        for ticker in tickers:
            today = dt.datetime.today().date()
            #today -= dt.timedelta(days=1)
            daily_df = dPrice.getByTickerEQdate(ticker, today)
            print(daily_df) 
            for index, row in daily_df.iterrows():
                print(row['close_date'], row['low_price'], row['high_price']) 
                close_date = dt.datetime.strptime(row['close_date'], "%Y-%m-%d").date()
                
                #call strategy to decide buy or sell or no action for prior weekday
                #prior_weekday = self.prev_weekday(close_date)
                strategy_result_dict = emaRsiCamarillaStrategy.strategy_ema_rsi_cam( ticker, close_date)
                
                #Based on strategy action, start backtesting to place order
                self.placeOrder(ticker,close_date , row['low_price'],row['high_price'],strategy_result_dict)
            
            time.sleep(10)    
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


    def placeOrder(self, ticker, close_date, low_price, high_price, strategy_result_dict):
        try:

            #create trade_transaction_data
            trade_transaction_data = {}
            trade_transaction_data['ticker'] = ticker
            trade_transaction_data['strategy_name'] = 'ema_rsi_camarilla'
            trade_transaction_data['status'] =  0            
            trade_transaction_data['action'] = strategy_result_dict['action']
            trade_transaction_data['tech_indicator'] = strategy_result_dict['action_msg']
            trade_transaction_data['unit_price'] = strategy_result_dict['action_price']
            print('trade_transaction_data: {}'.format(trade_transaction_data))
            
            
            #get portfolio data
            portfolio_df = portfolio.getByTickerStrategy(ticker, 'ema_rsi_camarilla')
            print('portfolio_df: {}'.format(portfolio_df))
            
            
            
            if trade_transaction_data['action'] == 'BUY':
                if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] < 2:
                    print("Buy order placed for trade_transaction_data = {}".format(trade_transaction_data))
                    trade_transaction_data['quantity'] = 1
                    trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                    app.placeOrder(self.nextValidOrderId, self.usTechStk(trade_transaction_data['ticker']), self.limitOrder(trade_transaction_data['action'],trade_transaction_data['quantity'],trade_transaction_data['unit_price'])) # EClient function to request contract details
                    self.nextValidOrderId= self.nextValidOrderId+1
                    time.sleep(10) # some latency added to ensure that the contract details request has been processed
                    tTransaction.populateTradeTransaction(trade_transaction_data, str(close_date))                      
                    #portfolio.updatePortfolio(trade_transaction_data['ticker'],  trade_transaction_data['strategy_name'] , trade_transaction_data['action'], trade_transaction_data['total_price'], trade_transaction_data['quantity'] , close_date)

                else:
                    print("Skipping buy for ticker: {} as we already hold max active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))
             
            if trade_transaction_data['action'] == 'SELL':
                if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] > 0:
                    average_cost = portfolio_df.iloc[0]['total_price'] / portfolio_df.iloc[0]['active_stocks']
                    if trade_transaction_data['unit_price'] > average_cost:
                        print('unit price is greater than average price')
                        profit_margin = ((trade_transaction_data['unit_price'] - average_cost)/average_cost) * 100
                        if profit_margin >= 2.0:
                            print("Sell order placed for trade_transaction_data = {}, portfolio_data = {}".format(trade_transaction_data,portfolio_df ))
                            trade_transaction_data['quantity'] = portfolio_df.iloc[0]['active_stocks']
                            trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                            app.placeOrder(self.nextValidOrderId, self.usTechStk(trade_transaction_data['ticker']), self.limitOrder(trade_transaction_data['action'],trade_transaction_data['quantity'],trade_transaction_data['unit_price'])) # EClient function to request contract details
                            self.nextValidOrderId= self.nextValidOrderId+1
                            time.sleep(10) # some latency added to ensure that the contract details request has been processed                            
                            tTransaction.populateTradeTransaction(trade_transaction_data, str(close_date))
                            #portfolio.updatePortfolio(trade_transaction_data['ticker'],  trade_transaction_data['strategy_name'] , trade_transaction_data['action'], trade_transaction_data['total_price'], trade_transaction_data['quantity'] , close_date)                               
                        else:
                            print('Sell skipped. profit margin {} is less than 2%'.format(profit_margin))
                    else:
                        print('Sell skipped. Unit price {} is less than average_cost  {}'.format(trade_transaction_data['unit_price'], average_cost))
            else:
                print("Skipping sell for ticker: {} as we already hold no active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))  
        
        except Exception as e:
            print("error {}".format(e))


def websocket_con(tickers):
    global db, dPrice, portfolio, tTransaction, emaRsiCamarillaStrategy
    dPrice = dailyPrice()
    portfolio = portfolio()
    tTransaction = tradeTransaction()
    emaRsiCamarillaStrategy = emaRsiCamarillaStrategy()    
    app.run() 


'''
There is no client method called here (as compared to reqHistoricalData or reqMktData in getting historical or streaming data)
Here, once the app is started, nextValidId is method is always called. we will use the callback function to start the but or sell actions.
Refer to nextValidId function the Trading App. 

'''
app = TradeApp()
app.connect(host='127.0.0.1', port=4001, clientId=2002) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
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












