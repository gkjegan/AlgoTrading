#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 10:56:30 2021

@author: jegankarunakaran
"""

import sqlite3
import pandas as pd

class techIndicator:
    
    def __init__(self):
        global db
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/ema_rsi_camarilla.db')     
 
        
    def getByTickerAndCloseDate (self, ticker, close_date):
        tech_ind_df = ''
        try:                 
            query_intra_sql = ''' SELECT * from TECH_IND where ticker = "'''+ticker+'''" and close_date = "'''+str(close_date)+'''"'''
            tech_ind_df = pd.read_sql_query(query_intra_sql, db)
            #print(tech_ind_df)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()
        return tech_ind_df

