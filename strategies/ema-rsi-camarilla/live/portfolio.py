#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 11:19:05 2021

@author: jegankarunakaran
"""

import sqlite3
import pandas as pd

class portfolio:
    
    def __init__(self):
        global db
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/algotrade_live.db')     
 
        

    def getByTickerStrategy(self, ticker, strategy_name):
        try:
            query = "SELECT * from PORTFOLIO where strategy_name = '{}' and ticker = '{}';".format(strategy_name, ticker)
            portfolio_df = pd.read_sql_query(query, db)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()
        
        return portfolio_df


    
    def updatePortfolio(self, ticker, strategy_name,  action, total_price, quantity, timestamp):
        try:
            c = db.cursor()
            #update portfolio table
            cash_df =  self.getByTickerStrategy('CASH', strategy_name)
            portfolio_df = self.getByTickerStrategy(ticker, strategy_name)
            
            cash_balance = cash_df.iloc[0]['total_price']
            portfolio_active_stocks = portfolio_df.iloc[0]['active_stocks']
            portfolio_total_price = portfolio_df.iloc[0]['total_price']
            profit  = portfolio_df.iloc[0]['profit']

            print(action)
            if action == 'BUY':
                cash_balance = cash_balance - total_price
                portfolio_active_stocks = portfolio_active_stocks +  quantity
                portfolio_total_price = portfolio_total_price + total_price 
            if action == 'SELL':
                cash_balance = cash_balance + total_price 
                portfolio_active_stocks = portfolio_active_stocks -  quantity
                profit +=  total_price - portfolio_total_price
                portfolio_total_price = 0
                print("portfolio_active_stocks: {}".format(portfolio_total_price))

            
            update_query_cash = "update portfolio set total_price = {}, time = {} where strategy_name = '{}' and ticker = 'CASH'".format( cash_balance, timestamp, strategy_name);
            print(update_query_cash)
            c.execute(update_query_cash)
          
            update_query = "update portfolio set active_stocks = {}, total_price = {} , profit={},  time = {} where strategy_name = '{}' and ticker = '{}'".format(portfolio_active_stocks, portfolio_total_price,profit, timestamp, strategy_name,  ticker);
            print(update_query)
            c.execute(update_query)

        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback() 
            
            
    
    def upsertPortfolio(self, ticker, position, avgCost):
        try:
            c = db.cursor()
            upsert_query_sql = "INSERT INTO portfolio (strategy_name, ticker, active_stocks, total_price, time) VALUES ('ema_rsi_camarilla', '{}', {}, {}, CURRENT_TIMESTAMP)  ON CONFLICT (strategy_name,ticker) DO UPDATE SET active_stocks={}, total_price={}, time=CURRENT_TIMESTAMP".format(ticker, position, avgCost, position, avgCost)
            print(upsert_query_sql)
            c.execute(upsert_query_sql)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()  


    def resetPortfolio(self, tickers):
        try:
            c = db.cursor()
            for ticker in tickers:
                update_query = "update portfolio set active_stocks = {}, total_price = {} , time = CURRENT_TIMESTAMP where strategy_name = 'ema_rsi_camarilla' and ticker = '{}'".format(0, 0, ticker);
                print(update_query)
                c.execute(update_query)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            