#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 11:02:57 2021

@author: jegankarunakaran
"""


from daily_price import dailyPrice
from portfolio import portfolio
from trade_transaction import tradeTransaction
from tech_ind import techIndicator
from emi_rsi_camarilla_strategy import emaRsiCamarillaStrategy

import datetime as dt

class TradeAppTest:
    def __init__(self): 
        print('init')   
        global dPrice, portfolio, tTransaction, emaRsiCamarillaStrategy, tIndicator
        
        dPrice = dailyPrice()
        portfolio = portfolio()
        tTransaction = tradeTransaction()
        emaRsiCamarillaStrategy = emaRsiCamarillaStrategy()
        tIndicator = techIndicator()
        self.start()

        
    def start(self):
        print('start')
        #dp_df = dPrice.getDailyPriceGTdate( 'MSFT', '2021-04-14')
        #print(dp_df)
        
        dp_df_1 = dPrice.getDailyPriceByDate('MSFT', '2021-04-14')
        print(dp_df_1)

        portfoli_df = portfolio.getTickerStrategy('MSFT', 'ema_rsi_camarilla')
        print(portfoli_df)
        
        portfoli_df_1 = portfolio.getTickerStrategyBackTest('MSFT', 'ema_rsi_camarilla')
        print(portfoli_df_1)
        
        today = dt.date.today()
        timestamp = today.strftime("%Y-%m-%d %H:%M:%S")
        portfolio.updatePortfolioBackTest('MSFT', 'ema_rsi_camarilla', 'BUY', 320, 1, timestamp)


        portfoli_df_2 = portfolio.getTickerStrategyBackTest('MSFT', 'ema_rsi_camarilla')
        print(portfoli_df_2)
        
        trade_transaction_data = {}
        trade_transaction_data['ticker'] = 'JEG'
        trade_transaction_data['strategy_name'] = 'ema_rsi_camarilla'
        trade_transaction_data['status'] =  0
        trade_transaction_data['action'] = 'BUY'
        trade_transaction_data['unit_price'] = 344.0
        trade_transaction_data['quantity'] = 1
        trade_transaction_data['total_price'] = 344.0
        trade_transaction_data['tech_indicator'] = 'sample test tech indicator '
        
        t_df = tTransaction.populateTradeTransactionBackTest(trade_transaction_data, timestamp)
        
        t_ind_df = tIndicator.getByTickerAndCloseDate('JPM','2021-11-30',)
        print(t_ind_df)
        
        result = emaRsiCamarillaStrategy.strategy_ema_rsi_cam( 'JPM', '2021-11-30')
        print(result)
        
        result = emaRsiCamarillaStrategy.strategy_ema_rsi_cam( 'JPM', '2021-12-07')
        print(result)
        
        result = emaRsiCamarillaStrategy.strategy_ema_rsi_cam( 'JPM', '2021-12-05')
        print(result)
        
        
TradeAppTest()