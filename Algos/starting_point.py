#!/usr/bin/env python
# coding: utf-8

# In[4]:


import sys
sys.path.append('../../ShoonyaApi')
import configparser
from api_helper import ShoonyaApiPy
import pandas as pd
from time import sleep
from pytz import timezone
import datetime as dt
from datetime import datetime
from FV_functions import *
#from nine_twenty import *
from nine_twenty_playground import *

if __name__ == "__main__":
    pnl = 0
    pt = 1
    lot = 1
    lot_size = 25
    
    while(1):
        if (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(23, 10, 0) and
               dt.datetime.now(timezone("Asia/Kolkata")).time() > dt.time(9, 20, 0)):
            pnl = trigger_algo(sl=5,qty=lot*lot_size,pt=1)
            print("Algo ended: PnL ", pnl)
        else:
            print("Market closed")
            sleep(200)

