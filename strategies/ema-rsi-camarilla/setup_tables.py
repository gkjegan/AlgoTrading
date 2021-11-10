#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 20:55:25 2021

@author: archanajegan

Python SQllite3 table setup
db location - "/Users/archanajegan/AlgoTrading/code/strategies/db"

"""


import sqlite3
import datetime as dt


########## *********Create a DAILY_PRICE Table*************
create_daily_price_sql = '''CREATE TABLE IF NOT EXISTS DAILY_PRICE(
    ticker TEXT NOT NULL, 
    close_date date, 
    open_price real(15,5), 
    close_price real(15,5), 
    high_price real(15,5),
    low_price real(15,5), 
    volume bigint , 
    PRIMARY KEY (ticker, close_date)
)'''

delete_daily_price_sql = '''DELETE FROM DAILY_PRICE'''
drop_daily_price_sql = '''DROP TABLE DAILY_PRICE'''


queryDate = (dt.datetime.today() - dt.timedelta(days=2)).date()

start_date = dt.datetime.strptime('20211101', "%Y%m%d").date()
end_date = (dt.datetime.strptime('20211101', "%Y%m%d") - dt.timedelta(days=2)).date()


query_daily_price_sql = '''SELECT * from DAILY_PRICE 
    where close_date < "''' + str(queryDate) + '''"'''


query_daily_price_backtest_sql = '''SELECT * from DAILY_PRICE 
    where close_date between "''' + str(end_date) + '''" and "''' + str(start_date) +'''"'''
    

########## *********Create a TECH_IND Table*************
create_tech_ind_sql = '''CREATE TABLE IF NOT EXISTS TECH_IND(
    ticker TEXT NOT NULL, 
    run_date date, 
    ema real(15,5), 
    rsi real(15,5), 
    r3 real(15,5),
    s3 real(15,5),
    PRIMARY KEY (ticker, run_date)
)'''



db = sqlite3.connect('/Users/archanajegan/AlgoTrading/code/strategies/db/ema_rsi_camarilla.db')
c = db.cursor()
c.execute(create_tech_ind_sql)
result = c.fetchall()
db.commit()
db.close()

#c.execute('CREATE TABLE IF NOT EXISTS DAILY_PRICE(ticker TEXT NOT NULL, time datetime, open_price real(15,5), close_price real(15,5), high_price real(15,5), low_price real(15,5), volume bigint , PRIMARY KEY (ticker, time))')
#c.execute('''SELECT * from DAILY_PRICE where time > date('now')-3''')
#result = c.fetchall()

