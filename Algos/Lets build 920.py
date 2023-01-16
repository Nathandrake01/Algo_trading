#!/usr/bin/env python
# coding: utf-8

# In[4]:


import sys
import numpy as np
import pandas as pd

sys.path.append('../../Algo_Trading/ShoonyaApi')

import configparser
from api_helper import ShoonyaApiPy

import pandas as pd
import time

from time import sleep
from pytz import timezone 
import datetime as dt 

import numpy as np
from datetime import datetime


#login

config = configparser.ConfigParser()
config.read('credential.ini')
user=config['finvasia']['user']
u_pwd=config['finvasia']['u_pwd']
factor2=config['finvasia']['factor2']
vc=config['finvasia']['vc']
app_key= config['finvasia']['app_key']
imei= config['finvasia']['imei']


# In[5]:


global master_contract, api


# In[6]:


token = 'B6D32I442C4F743D5BVX6E76DPSBK732'


# In[7]:


import pyotp
pyotp.TOTP(token).now()


# In[8]:



# In[9]:


while dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(9,20,0):
    sleep(1)
    continue
api = ShoonyaApiPy()
#credentials by login 
ret = api.login(userid=user, password=u_pwd, twoFA=pyotp.TOTP(token).now(), vendor_code=vc,
api_secret=app_key, imei=imei)


# In[10]:


master_contract = pd.read_csv('https://shoonya.finvasia.com/NFO_symbols.txt.zip',compression='zip', engine='python',delimiter=',')
master_contract['Expiry'] = pd.to_datetime(master_contract['Expiry'])
master_contract['StrikePrice'] = master_contract['StrikePrice'].astype(float)
master_contract.sort_values('Expiry',inplace=True)
master_contract.reset_index(drop=True, inplace=True)


# In[11]:


def get_instrument(Symbol,strike_price,optiontype,expiry_offset):
    #to get a intstrument token from the master contract downloaded from shoonya website
    return(master_contract[(master_contract['Symbol']==Symbol) & (master_contract['OptionType']==optiontype) & (master_contract['StrikePrice']==strike_price)].iloc[expiry_offset])

def get_atm_strike():
    bnspot_token=api.searchscrip(exchange='NSE',searchtext='Nifty bank')['values'][0]['token']
    while True:
        bnflp=float(api.get_quotes(exchange='NSE', token=bnspot_token)['lp'])
        if bnflp!=None:
            break
    atmprice=round(bnflp/base)*base
    return atmprice


def place_order(BS,tradingsymbol,quantity,product_type='I',price_type='MKT',exchange='NFO',price=0,trigger_price=None):
    order_place=api.place_order(buy_or_sell=BS, product_type=product_type,
                        exchange=exchange, tradingsymbol=tradingsymbol, 
                        quantity=quantity, discloseqty=0,price_type=price_type,price=price,trigger_price=trigger_price) #M for NRML AND I For intraday in product type
    print(order_place)
    return order_place['norenordno']

def stop_loss_order(qty,tradingsymbol,price,SL):
    stop_price=round((1+SL/100)*price,1)
    price=stop_price+2
    trigger_price=stop_price
    stop_loss_orderid=place_order(BS='B',tradingsymbol=tradingsymbol,quantity=qty,price_type='SL-LMT',price=price,trigger_price=trigger_price) 
    return stop_loss_orderid     



def single_order_history(orderid,req):
    ''''stat','norenordno', 'uid', 'src_uid', 'actid', 'exch', 'tsym', 'q 'trantyty',pe', 'prctyp', 'ret', 'rejby', 'kidid',
       'pan', 'ordersource', 'token', 'pp', 'ls', 'ti', 'prc', 'dscqty', 'prd', 'status', 'rpt', 'ordenttm', 'norentm', 'rejreason','exch_tm'''
    #this required to made to avoid unnecesary making a lof of Dataframes
    #dl=pd.DataFrame(api.single_order_history(orderid))
    #sleep(1)
    #return dl[req].iloc[0]

    while True: 
        json_data=api.single_order_history(orderid)
        if json_data!=None:
            break

    for id in json_data:
        value_return=id[req]
        break

    return value_return
        


# In[12]:


feed_opened = False
feedJson = {}
counter = 0
def event_handler_order_update(order):
    counter = counter + 1
    print(f"order feed {counter/2}")
    
def event_handler_feed_update(tick_data):
    if 'lp' in tick_data and 'tk' in tick_data :
        timest = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feedJson[tick_data['tk']] = {'ltp': float(tick_data['lp']) , 'tt': timest}

def open_callback():
    global feed_opened
    feed_opened = True


api.start_websocket( order_update_callback=event_handler_order_update,
                     subscribe_callback=event_handler_feed_update, 
                     socket_open_callback=open_callback)

while(feed_opened==False):
    pass


# In[13]:


base=100
symbol="BANKNIFTY"
#while dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(9,20,0):
#    sleep(1)


# In[ ]:

def place_order_pt(type,tradingsymbol,qty):
    print("Order filled", type, tradingsymbol, qty)

def trigger_algo_pt(sl,qty):
    # this gives atm strike price
    atm_strike=get_atm_strike()

    print("ATM Strike value",atm_strike)

    # find corrosponding CE and PE symbols example strike at 42000 then 42000CE and 42000PE
    ce_tradingsymbol=get_instrument(symbol,atm_strike,'CE',0)['TradingSymbol']
    pe_tradingsymbol=get_instrument(symbol,atm_strike,'PE',0)['TradingSymbol']

    ce_entry_price = api.get_quotes("NFO", ce_tradingsymbol)['lp']
    pe_entry_price = api.get_quotes("NFO", pe_tradingsymbol)['lp']

    # Place CE and PE orders
#       ce_orderid=place_order('S',ce_tradingsymbol,qty)
#       pe_orderid=place_order('S',pe_tradingsymbol,qty)
    # wait for 3 seconds if order is not filled
#       sleep(3)

    # Entry price is required for SL eg 25% from entry price
 #   ce_entry_price=float(single_order_history(ce_orderid,'avgprc'))
 #   pe_entry_price=float(single_order_history(pe_orderid,'avgprc'))

    # for continuous monitoring of prices (if trigger happens)
    ce_token_id = str(get_instrument(symbol,atm_strike,'CE',0)['Token'])
    pe_token_id = str(get_instrument(symbol,atm_strike,'PE',0)['Token'])
    ce_subscribe = 'NFO' + '|' + (ce_token_id)
    pe_subscribe = 'NFO' + '|' + (pe_token_id)

    print("CE entry: ", ce_entry_price)
    print("PE entry: ", pe_entry_price)

    # this subscribes if CE or PE is hit
    api.subscribe([ce_subscribe, pe_subscribe])
    # the below sleep is important
    sleep(3)

    pe_sl_hit = 0
    ce_sl_hit = 0
    ce_sl_hit_price = 0
    pe_sl_hit_price = 0
    pnl = 0
    while (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(15,10,0)):
        if(float(feedJson[ce_token_id]['ltp']) > float(ce_entry_price) * (1+sl/100) and ce_sl_hit != 1):
#                api.unsubscribe(ce_subscribe)
            place_order_pt('B',ce_tradingsymbol,qty)
            ce_sl_hit_price = float(feedJson[ce_token_id]['ltp'])
           # place_order('B',ce_tradingsymbol,qty)
            ce_sl_hit = 1
            print("CE SL hit")

        if(float(feedJson[pe_token_id]['ltp']) > float(pe_entry_price) * (1+sl/100) and pe_sl_hit != 1):
#                api.unsubscribe(pe_subscribe)
            place_order_pt('B', pe_tradingsymbol, qty)
            pe_sl_hit_price = float(feedJson[pe_token_id]['ltp'])
          #  place_order('B',pe_tradingsymbol,qty)
            pe_sl_hit = 1
            print("PE SL hit")
        print("-------------------")
        # if sl is not hit then take current price for pnl calculation
        if(ce_sl_hit != 1):
            ce_sl_hit_price = float(feedJson[ce_token_id]['ltp'])
        if(pe_sl_hit != 1):
            pe_sl_hit_price = float(feedJson[pe_token_id]['ltp'])

        pnl = float(ce_entry_price) - float(ce_sl_hit_price) + float(pe_entry_price) - float(pe_sl_hit_price)
        pnl = pnl*qty
        print("PNL: ", pnl)
        sleep(60)

    if(ce_sl_hit != 1):
        place_order_pt('B',ce_tradingsymbol,qty)
        ce_sl_hit_price = float(feedJson[ce_token_id]['ltp'])
    if(pe_sl_hit != 1):
        place_order_pt('B',pe_tradingsymbol,qty)
        pe_sl_hit_price = float(feedJson[pe_token_id]['ltp'])
    api.unsubscribe([ce_subscribe, pe_subscribe])
    sleep(120)
    pnl = float(ce_entry_price) - float(ce_sl_hit_price) + float(pe_entry_price) - float(pe_sl_hit_price)
    pnl = pnl * qty
    return pnl

if __name__ == "__main__":
    pnl = 0
    while(1):
        if (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(15, 10, 0) and
               dt.datetime.now(timezone("Asia/Kolkata")).time() > dt.time(9, 20, 0)):
            pnl = trigger_algo_pt(5,25)
            print("Algo ended: PnL ", pnl)
        else:
            print("Market closed")
            sleep(200)


