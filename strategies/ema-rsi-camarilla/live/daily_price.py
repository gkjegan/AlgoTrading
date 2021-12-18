#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 10:56:30 2021

@author: jegankarunakaran
"""

import sqlite3
import pandas as pd

class dailyPrice:
    
    def __init__(self):
        global db
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/algotrade_live.db')     
 
        
    def getByTickerGTdate (self, ticker, close_date):
        daily_price_df = ''
        try:
            query_daily_price = "SELECT * from DAILY_PRICE where close_date >= '{}' and ticker = '{}' order by close_date;".format(close_date, ticker)
            daily_price_df = pd.read_sql_query(query_daily_price, db)
            print(daily_price_df)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()
        return daily_price_df

    def getByNumberOfDays (self, num_of_days):
        daily_price_df = ''
        try:
            query_daily_price = '''SELECT * from DAILY_PRICE where close_date >= date('now', '-320 days') '''
            #query_daily_price = "SELECT * from DAILY_PRICE"
            #print(query_daily_price)
            daily_price_df = pd.read_sql_query(query_daily_price, db)
            #print(daily_price_df)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()
        return daily_price_df

    def getByTickerEQdate(self, ticker, close_date):
        """get daily price from ticker table"""
        result_df = ''
        try:
            query_current_price_sql = ''' SELECT * from DAILY_PRICE where ticker='{}' and close_date='{}'  '''.format(ticker, close_date)
            result_df = pd.read_sql_query(query_current_price_sql, db)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()            
        return result_df  
    
    
    def insertDailyPrice(self, daily_data):
        """insert into daily price for each ticker"""
        try:
            c = db.cursor()
            query = "INSERT INTO DAILY_PRICE (ticker, close_date, open_price, close_price, high_price, low_price,volume) VALUES (?,?,?,?,?,?,?)"
            c.execute(query,daily_data)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()