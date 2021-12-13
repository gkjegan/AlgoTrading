#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:00:47 2021

@author: archanajegan

"""

import sqlite3
import datetime as dt
from daily_price import dailyPrice
from portfolio import portfolio
from trade_transaction import tradeTransaction
from emi_rsi_camarilla_strategy import emaRsiCamarillaStrategy


tickers = ['MSFT', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ', 'UNH', 'WMT', 'BAC', 'PG']
#tickers = ['MSFT']
#tickers = ["FB","MSFT", "JPM"]


class TradeApp(): 
    
    def __init__(self): 
        global db, dPrice, portfolio, tTransaction, emaRsiCamarillaStrategy
        dPrice = dailyPrice()
        portfolio = portfolio()
        tTransaction = tradeTransaction()
        emaRsiCamarillaStrategy = emaRsiCamarillaStrategy()
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')        
        self.start()

    
    def prev_weekday(self, adate):
        adate -= dt.timedelta(days=1)
        while adate.weekday() > 4: # Mon-Fri are 0-4
            adate -= dt.timedelta(days=1)
        return adate

    def start(self):       
        for ticker in tickers:
            daily_df = dPrice.getDailyPriceGTdate(ticker, '2021-04-14')
            for index, row in daily_df.iterrows():
                print(row['close_date'], row['low_price'], row['high_price']) 
                close_date = dt.datetime.strptime(row['close_date'], "%Y-%m-%d").date()
                
                #call strategy to decide buy or sell or no action for prior weekday
                prior_weekday = self.prev_weekday(close_date)
                strategy_result_dict = emaRsiCamarillaStrategy.strategy_ema_rsi_cam( ticker, prior_weekday)
                
                #Based on strategy action, start backtesting to place order
                self.placeOrder(ticker,close_date , row['low_price'],row['high_price'],strategy_result_dict)
  


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
            portfolio_df = portfolio.getTickerStrategyBackTest(ticker, 'ema_rsi_camarilla')
            print('portfolio_df: {}'.format(portfolio_df))
            
            
            
            if trade_transaction_data['action'] == 'BUY':
                if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] < 2:
                    
                    #Backtest Buying
                    if trade_transaction_data['unit_price'] >= low_price and trade_transaction_data['unit_price'] <= high_price:
                        print("Buy order placed for trade_transaction_data = {}".format(trade_transaction_data))
                        trade_transaction_data['quantity'] = 1
                        trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                        tTransaction.populateTradeTransactionBackTest(trade_transaction_data, str(close_date))                      
                        portfolio.updatePortfolioBackTest(trade_transaction_data['ticker'],  trade_transaction_data['strategy_name'] , trade_transaction_data['action'], trade_transaction_data['total_price'], trade_transaction_data['quantity'] , str(close_date))

                    else:
                        print("Buy expired for ticker: {}. date {}, unit_price {}, low_price {}, high price {}".format(trade_transaction_data['ticker'],close_date, trade_transaction_data['unit_price'], low_price, high_price))

                else:
                    print("Skipping buy for ticker: {} as we already hold max active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))
             
            if trade_transaction_data['action'] == 'SELL':
                if not portfolio_df.empty and portfolio_df.iloc[0]['active_stocks'] > 0:

                    #Backtest Buying
                    if trade_transaction_data['unit_price'] >= low_price and trade_transaction_data['unit_price'] <= high_price:
                        average_cost = portfolio_df.iloc[0]['total_price'] / portfolio_df.iloc[0]['active_stocks']
                        if trade_transaction_data['unit_price'] > average_cost:
                            print('unit price is greater than average price')
                            profit_margin = ((trade_transaction_data['unit_price'] - average_cost)/average_cost) * 100
                            if profit_margin >= 2.0:
                                print("Sell order placed for trade_transaction_data = {}, portfolio_data = {}".format(trade_transaction_data,portfolio_df ))
                                trade_transaction_data['quantity'] = portfolio_df.iloc[0]['active_stocks']
                                trade_transaction_data['total_price'] =  trade_transaction_data['quantity'] * trade_transaction_data['unit_price']
                                tTransaction.populateTradeTransactionBackTest(trade_transaction_data, str(close_date))
                                portfolio.updatePortfolioBackTest(trade_transaction_data['ticker'],  trade_transaction_data['strategy_name'] , trade_transaction_data['action'], trade_transaction_data['total_price'], trade_transaction_data['quantity'] , str(close_date))                               
                            else:
                                print('Sell skipped. profit margin {} is less than 2%'.format(profit_margin))
                        
                        else:
                            print('Sell skipped. Unit price {} is less than average_cost  {}'.format(trade_transaction_data['unit_price'], average_cost))
                        
                        
                    else:
                        print("SELL expired for ticker: {}. date {}, unit_price {}, low_price {}, high price {}".format(trade_transaction_data['ticker'],close_date, trade_transaction_data['unit_price'], low_price, high_price))
                                        
                else:
                    print("Skipping sell for ticker: {} as we already hold no active stocks. portfolio details: {}".format(trade_transaction_data['ticker'],portfolio_df))  
        
        except Exception as e:
            print("error {}".format(e))


TradeApp()












