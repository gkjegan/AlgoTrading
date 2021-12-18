#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 11:58:35 2021

@author: jegankarunakaran
"""

import sqlite3

class tradeTransaction:
    
    def __init__(self):
        global db
        db = sqlite3.connect('/Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/db/algotrade_live.db')     
 
        

    def populateTradeTransaction(self, trade_transaction_data, timestamp):
        try:
            c = db.cursor()
            #insert a buy transaction in trade_transaction table
            columns = ', '.join("'" + str(x) + "'" for x in trade_transaction_data.keys())
            columns = columns+', "time"'
            values = ', '.join("'" + str(x)+ "'" for x in trade_transaction_data.values())
            values = values + ', "' + timestamp + '" '
            query = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('TRADE_TRANSACTION', columns, values)
            #print(query)
            c.execute(query)
        except Exception as e:
            print("db error {}".format(e))
        try:
            db.commit()
        except:
            db.rollback()  