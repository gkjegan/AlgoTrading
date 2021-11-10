# -*- coding: utf-8 -*-
"""
IBAPI - Getting historical data intro

@author: Mayank Rasu (http://rasuquant.com/wp/)
"""


from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time


class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)
        
    def historicalData(self, reqId, bar):
        print("HistoricalData. ReqId:", reqId, "BarData.", bar)
        

def websocket_con():
    app.run()
    
app = TradingApp()      
app.connect("127.0.0.1", 7497, clientId=2)

# starting a separate daemon thread to execute the websocket connection
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established

#creating object of the Contract class - will be used as a parameter for other function calls

contract = Contract()
contract.symbol = "EUR"
contract.secType = "CASH"
contract.currency = "GBP"
contract.exchange = "IDEALPRO"


"""
contract = Contract()
contract.symbol = "912828C57"
contract.secType = "BOND"
contract.currency = "USD"
contract.exchange = "SMART"
"""

app.reqHistoricalData(reqId=1, 
                      contract=contract,
                      endDateTime='',
                      durationStr='1 M',
                      barSizeSetting='5 mins',
                      whatToShow='MIDPOINT',
                      useRTH=1,
                      formatDate=1,
                      keepUpToDate=0,
                      chartOptions=[])	 # EClient function to request contract details
time.sleep(5) # some latency added to ensure that the contract details request has been processed