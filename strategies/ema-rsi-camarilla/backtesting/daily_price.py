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
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')     
 
        
    def getDailyPriceGTdate (self, ticker, close_date):
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



    def getDailyPriceByDate(self, ticker, close_date):
        """get daily price from ticker table"""
        query_current_price_sql = ''' SELECT * from DAILY_PRICE where ticker='{}' and close_date='{}'  '''.format(ticker, close_date)
        result_df = pd.read_sql_query(query_current_price_sql, db)
        return result_df  