#!/bin/bash
source /Users/jegankarunakaran/opt/anaconda3/bin/activate algotrade
cd /Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/ema-rsi-camarilla/live/
python daily_price_load.py
conda deactivate

