#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:00:47 2021

@author: archanajegan
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.execution import  Execution #, ExecutionFilter
#from ibapi.commissionReport import CommissionReport
import threading
#import sqlite3
from ibapi.order import Order
from ibapi.order_state import OrderState
import time
#import pandas as pd
#import datetime as dt
#from uuid import uuid4
#import requests
from decimal import Decimal


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
        
    
    def openOrder(self, orderId, contract: Contract, order: Order, orderState: OrderState):
        super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId, 
              "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
              "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
              "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty, 
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)

        order.contract = contract
        #self.permId2ord[order.permId] = order

    
    def orderStatus(self, orderId, status: str, filled: Decimal,
                    remaining: Decimal, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:",
              whyHeld, "MktCapPrice:", mktCapPrice)
        
    def openOrderEnd(self):
        super().openOrderEnd()
        print("OpenOrderEnd")
        #print("Received %d openOrders", len(self.permId2ord))

    def position(self, account: str, contract: Contract, position: Decimal,
                 avgCost: float):
        super().position(account, contract, position, avgCost)
        print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",
              contract.secType, "Currency:", contract.currency,
              "Position:", position, "Avg cost:", avgCost)

    def positionEnd(self):
        super().positionEnd()
        print("PositionEnd")        

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
       super().execDetails(reqId, contract, execution)
       print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:", contract.currency, execution)
    
    def commissionReport(self, commissionReport):
        super().commissionReport(commissionReport)
        print("CommissionReport.", commissionReport)    
    
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        print("ExecDetailsEnd. ReqId:", reqId)    
 
                
    
def websocket_con(tickers):
    app.run()    

    
'''
There is no client method called here (as compared to reqHistoricalData or reqMktData in getting historical or streaming data)
Here, once the app is started, nextValidId is method is always called. we will use the callback function to start the but or sell actions.
Refer to nextValidId function the Trading App. 

'''
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=2002) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()
time.sleep(3) 

app.reqAllOpenOrders()
app.reqPositions()
#app.reqExecutions(2002, ExecutionFilter())
#app.reqGlobalCancel()





