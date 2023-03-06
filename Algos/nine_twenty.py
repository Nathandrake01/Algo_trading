#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 10:33:43 2023

@author: sumitsingh
"""

from api_helper import ShoonyaApiPy
import pandas as pd
from time import sleep
from pytz import timezone
import datetime as dt
from datetime import datetime
from FV_functions import *
import json


# import only system from os
from os import system, name
 
# import sleep to show output for some time period
from time import sleep
 

def place_order_pt(type,tradingsymbol,qty):
    print("Order filled", type, tradingsymbol, qty)
"""
if we are paper trading or real trading
CAUTION: keep pt = 1 till you are certain of the logic
"""
def trigger_algo(sl,qty,pt):
    
    if(pt==1):
        pnl = trigger_algo_pt(sl,qty)
    else:
        pnl = trigger_algo_exchange(sl,qty)
    return pnl

def trade_attributes(symbol):
    # this gives atm strike price
    atm_strike=get_atm_strike()
    
    ce_data = {}
    pe_data = {}

    print("ATM Strike value",atm_strike)

    # find corrosponding CE and PE symbols example strike at 42000 then 42000CE and 42000PE
    ce_data["tradingsymbol"]=get_instrument(symbol,atm_strike,'CE',0)['TradingSymbol']
    pe_data["tradingsymbol"]=get_instrument(symbol,atm_strike,'PE',0)['TradingSymbol']

    print(pe_data["tradingsymbol"])
    print(ce_data["tradingsymbol"])

    ce_data["entry_price"] = api.get_quotes("NFO", ce_data["tradingsymbol"])['lp']
    pe_data["entry_price"] = api.get_quotes("NFO", pe_data["tradingsymbol"])['lp']

    # for continuous monitoring of prices (if trigger happens)
    ce_data["token_id"] = str(get_instrument(symbol,atm_strike,'CE',0)['Token'])
    pe_data["token_id"] = str(get_instrument(symbol,atm_strike,'PE',0)['Token'])
    ce_data["subscribe_symbol"] = 'NFO' + '|' + (ce_data["token_id"])
    pe_data["subscribe_symbol"] = 'NFO' + '|' + (pe_data["token_id"])
    
    print("Entering: ", ce_data["tradingsymbol"])
    print("CE entry: ", ce_data["entry_price"])
    
    print("Entering: ", pe_data["tradingsymbol"])
    print("PE entry: ", pe_data["entry_price"])
    
    return ce_data, pe_data
    
def pnl_calculation(ce_data, pe_data,qty):
    pnl = 0
    if(ce_data["sl_hit"] != 1):
        ce_data["sl_hit_price"] = float(feedJson[ce_data["token_id"]]['ltp'])
    if(pe_data["sl_hit"] != 1):
        pe_data["sl_hit_price"] = float(feedJson[pe_data["token_id"]]['ltp'])

    ce_pnl = round(qty*(float(ce_data["entry_price"]) - float(ce_data["sl_hit_price"])),2)
    ce_ltp = round(float(feedJson[ce_data["token_id"]]['ltp']),2)
    
    pe_pnl = round(qty*(float(pe_data["entry_price"]) - float(pe_data["sl_hit_price"])),2)
    pe_ltp = round(float(feedJson[pe_data["token_id"]]['ltp']),2)
    
    pnl = ce_pnl + pe_pnl
    print("____________________________________________________________________")
    print("Instrument_Name","Quantity","Entry_Price", "LTP", "PnL", sep="\t")
    print(ce_data["tradingsymbol"], qty, ce_data["entry_price"], ce_ltp, ce_pnl, sep="\t")
    print(pe_data["tradingsymbol"], qty, pe_data["entry_price"], pe_ltp, pe_pnl, sep="\t")
    print("PNL: ",round(pnl,2))
    print("____________________________________________________________________")
    sleep(2)
    return pnl

def trigger_algo_pt(sl,qty,symbol="BANKNIFTY"):

    ce_data, pe_data = trade_attributes(symbol)
    # this subscribes if CE or PE is hit
    print(ce_data["subscribe_symbol"])
    print(pe_data["subscribe_symbol"])
    kkg = api.subscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    # the below sleep is important
    sleep(3)
    print(kkg)

    pe_data["sl_hit"] = 0
    pe_data["sl_hit_price"] = 0

    ce_data["sl_hit"] = 0
    ce_data["sl_hit_price"] = 0
    
    print("here")
    
    while (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(15,10,0)):
        if(float(feedJson[ce_data["token_id"]]['ltp']) > float(ce_data["entry_price"]) * (1+sl/100) and ce_data["sl_hit"] != 1):
            place_order_pt('B',ce_data["tradingsymbol"],qty)
            ce_data["sl_hit_price"] = float(feedJson[ce_data["token_id"]]['ltp'])
            ce_data["sl_hit"] = 1
            print("CE SL hit")

        if(float(feedJson[pe_data["token_id"]]['ltp']) > float(pe_data["entry_price"]) * (1+sl/100) and pe_data["sl_hit"] != 1):
            place_order_pt('B', pe_data["tradingsymbol"], qty)
            pe_data["sl_hit_price"] = float(feedJson[pe_data["token_id"]]['ltp'])
            pe_data["sl_hit"] = 1
            print("PE SL hit")
        print("now here")
        pnl_calculation(ce_data,pe_data,qty)

        # if both SL hit then exit
        if (ce_data["sl_hit"] and pe_data["sl_hit"]):
            break

        # if sl is not hit then take current price for pnl calculation
    if(ce_data["sl_hit"] != 1):
        place_order_pt('B',ce_data["tradingsymbol"],qty)
        ce_data["sl_hit_price"] = float(feedJson[ce_data["token_id"]]['ltp'])
    if(pe_data["sl_hit"] != 1):
        place_order_pt('B',pe_data["tradingsymbol"],qty)
        pe_data["sl_hit_price"] = float(feedJson[pe_data["token_id"]]['ltp'])


    api.unsubscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    sleep(120)
    pnl = pnl_calculation(ce_data, pe_data,qty)
  #  pnl = float(ce_data["entry_price"]) - float(ce_data["sl_hit_price"]) + float(pe_data["entry_price"]) - float(pe_data["sl_hit_price"])
    pnl = pnl * qty
    return pnl

def trigger_algo_exchange(sl,qty):
    
    ce_data, pe_data = trade_attributes(symbol)
    # Place CE and PE orders
    ce_orderid=place_order('S',ce_data["tradingsymbol"],qty)
    pe_orderid=place_order('S',pe_data["tradingsymbol"],qty)
    # wait for 3 seconds if order is not filled
    
    # this subscribes if CE or PE is hit
#    api.subscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    # the below sleep is important
    sleep(3)

    pe_data["sl_hit"] = 0
    pe_data["sl_hit_price"] = 0

    ce_data["sl_hit"] = 0
    ce_data["sl_hit_price"] = 0
    print("AA")
    
    while (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(15,10,0)):
        if(float(feedJson[ce_data["token_id"]]['ltp']) > float(ce_data["entry_price"]) * (1+sl/100) and ce_data["sl_hit"] != 1):
            place_order('B',ce_data["tradingsymbol"],qty)

            ce_data["sl_hit_price"] = float(feedJson[ce_data["token_id"]]['ltp'])
            ce_data["sl_hit"] = 1
            print("CE SL hit")

        if(float(feedJson[pe_data["token_id"]]['ltp']) > float(pe_data["entry_price"]) * (1+sl/100) and pe_data["sl_hit"] != 1):
            place_order('B', pe_data["tradingsymbol"], qty)
            pe_data["sl_hit_price"] = float(feedJson[pe_data["token_id"]]['ltp'])
            pe_data["sl_hit"] = 1
            print("PE SL hit")
        print("AAA")
        pnl = pnl_calculation(ce_data,pe_data,qty)

        # if both SL hit then exit
        if (ce_data["sl_hit"] and pe_data["sl_hit"]):
            break

        # if sl is not hit then take current price for pnl calculation
    if(ce_data["sl_hit"] != 1):
        place_order('B',ce_data["tradingsymbol"],qty)
        ce_data["sl_hit_price"] = float(feedJson[ce_data["token_id"]]['ltp'])
    if(pe_data["sl_hit"] != 1):
        place_order('B',pe_data["tradingsymbol"],qty)
        pe_data["sl_hit_price"] = float(feedJson[pe_data["token_id"]]['ltp'])


    api.unsubscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    sleep(120)
    pnl = pnl_calculation(ce_data, pe_data)
  #  pnl = float(ce_data["entry_price"]) - float(ce_data["sl_hit_price"]) + float(pe_data["entry_price"]) - float(pe_data["sl_hit_price"])
    pnl = pnl * qty
    return pnl



"""
    # this gives atm strike price
    atm_strike=get_atm_strike()

    print("ATM Strike value",atm_strike)

    # find corrosponding CE and PE symbols example strike at 42000 then 42000CE and 42000PE
    ce_tradingsymbol=get_instrument(symbol,atm_strike,'CE',0)['TradingSymbol']
    pe_tradingsymbol=get_instrument(symbol,atm_strike,'PE',0)['TradingSymbol']

    ce_entry_price = api.get_quotes("NFO", ce_tradingsymbol)['lp']
    pe_entry_price = api.get_quotes("NFO", pe_tradingsymbol)['lp']


    # Entry price is required for SL eg 25% from entry price
    ce_entry_price=float(single_order_history(ce_orderid,'avgprc'))
    pe_entry_price=float(single_order_history(pe_orderid,'avgprc'))

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
#            place_order_pt('B',ce_tradingsymbol,qty)
            ce_sl_hit_price = float(feedJson[ce_token_id]['ltp'])
            place_order('B',ce_tradingsymbol,qty)
            ce_sl_hit = 1
            print("CE SL hit")

        if(float(feedJson[pe_token_id]['ltp']) > float(pe_entry_price) * (1+sl/100) and pe_sl_hit != 1):
            pe_sl_hit_price = float(feedJson[pe_token_id]['ltp'])
            place_order('B',pe_tradingsymbol,qty)
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

"""