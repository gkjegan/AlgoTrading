#!/bin/bash
#conda activate rapids WRONG
source /Users/jegankarunakaran/opt/anaconda3/bin/activate algotrade #correct
#python Documents/my_python_file_name.py WRONG SEPARATLY GO TO FOLER WHTAN EXECUTE EITH python
cd /Users/jegankarunakaran/AlgoTrading/code/AlgoTrading/strategies/ema-rsi-camarilla/release/ #correct
python ema_rsi_camarilla_strategy.py #correct
conda deactivate
