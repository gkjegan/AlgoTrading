#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 12 12:11:35 2021

@author: jegankarunakaran
"""

from daily_price import dailyPrice
from tech_ind import techIndicator

class emaRsiCamarillaStrategy:
    def __init__(self):
        global db, dPrice, portfolio, tTransaction, tIndicator
        dPrice = dailyPrice()
        tIndicator = techIndicator()
            
 
        

    '''
    Inputs: close_date, ticker
    close_date: close_date is used to DAILY_PRICE and TECH_IND to calculate BUY/SELL 
    
    
    MThe core strategy to decide BUY or SELL
    if RSI < 20, ASK_PRICE > EMA, and ASK_PRICE < S3:
        BUY
    if RSI > 20, BID_PRICE > EMA, and BID_PRICE < R3:
        SELL    
    '''
    def  strategy_ema_rsi_cam(self, ticker, close_date):
        
        result = {}
        result['action'] = 'NO ACTION'
        result['action_price'] = 0
        result['action_msg'] = ''
              
        daily_price_df = dPrice.getDailyPriceByDate(ticker, close_date)
        if daily_price_df.empty:
            result['action_msg'] = "NO ACTION - No DAILY PRICE for ticker {} and close date {}".format(ticker, close_date)
            return result 

        close_price = daily_price_df.iloc[0]['close_price']
        tech_ind_df = tIndicator.getByTickerAndCloseDate(ticker, close_date)
        
        if tech_ind_df.empty:
            result['action_msg'] = "NO ACTION - No technical indicator for ticker {} and close date {}".format(ticker, close_date)
            return result
        
        else:
            tech_indicator_data = tech_ind_df.iloc[0]
            result['action_msg'] = "Tech Indicator:  ema-{}, rsi-{}, r3-{}, s3-{}".format(tech_indicator_data['ema'], tech_indicator_data['rsi'],tech_indicator_data['r3'],tech_indicator_data['s3'])
            
            if close_price > tech_indicator_data['ema']: 
                #print("EMA Condition True")
                if tech_indicator_data['rsi'] <= 20:
                    result['action'] = "BUY"
                    result['action_price'] = round(tech_indicator_data['s3'],2)#ask_price
                    print("BUY SIGNAL:  RSI condition - {}, EMA condition - {}, Camarilla S3 - {} ".format(tech_indicator_data['rsi'] <= 20 , close_price > tech_indicator_data['ema'], tech_indicator_data['s3'])) 
                elif tech_indicator_data['rsi'] >= 80:
                     result['action'] = "SELL"
                     result['action_price'] = round(tech_indicator_data['r3'],2)#bid_price
                     print("SELL SIGNAL: RSI condition - {}, EMA condition - {}, Camarilla R3 - {} ".format(tech_indicator_data['rsi'] >= 80 , close_price > tech_indicator_data['ema'],  tech_indicator_data['r3'])) 
                else:
                     print("NO ACTION - RSI Failed - {}".format(tech_indicator_data['rsi']))
                     
            else:
                print("NO ACTION - EMA Failed - EMA {}, close_price {} ".format(tech_indicator_data['ema'], close_price))
                result['action'] = "NO ACTION"
            
            return result
        
        
        
        
        
        
        
        
        
        
        
        
        
