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
import opstrat as op
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import time

import pandas as pd


def strike_through(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

#defining containers
header = st.container()
select_param = st.container()
plot_spot = st.empty()
plot_df = st.empty()
def get_chart_47579095(pnl):

    fig = px.line(pnl, x="pnl_time", y="pnl_calc", title='Day pnl')
  #  fig.update_layout(width=900, height=570, xaxis_title='time', yaxis_title='pnl_calc')
   # tab1, tab2 = st.tabs(["Streamlit theme (default)", "Plotly native theme"])
    now = datetime.now()
 #   st.write("Current Time =", now.strftime("%H:%M:%S"))

    st.plotly_chart(fig, theme="streamlit")

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
    atm_strike=get_atm_strike(symbol)
    kkg = api.searchscrip(exchange='MCX', searchtext='Crude')
    print(kkg)
    ce_data = {}
    pe_data = {}

    print("ATM Strike value",atm_strike)

    # find corrosponding CE and PE symbols example strike at 42000 then 42000CE and 42000PE
    ce_data["tradingsymbol"]=get_instrument(symbol,atm_strike,'CE',0)['TradingSymbol']
    pe_data["tradingsymbol"]=get_instrument(symbol,atm_strike,'PE',0)['TradingSymbol']

    print(pe_data["tradingsymbol"])
    print(ce_data["tradingsymbol"])

    ce_data["entry_price"] = api.get_quotes("MCX", ce_data["tradingsymbol"])['lp']
    pe_data["entry_price"] = api.get_quotes("MCX", pe_data["tradingsymbol"])['lp']

    # for continuous monitoring of prices (if trigger happens)
    ce_data["token_id"] = str(get_instrument(symbol,atm_strike,'CE',0)['Token'])
    pe_data["token_id"] = str(get_instrument(symbol,atm_strike,'PE',0)['Token'])
    ce_data["subscribe_symbol"] = 'MCX' + '|' + (ce_data["token_id"])
    pe_data["subscribe_symbol"] = 'MCX' + '|' + (pe_data["token_id"])
    
    print("Entering: ", ce_data["tradingsymbol"])
    print("CE entry: ", ce_data["entry_price"])
    
    print("Entering: ", pe_data["tradingsymbol"])
    print("PE entry: ", pe_data["entry_price"])
    
    return ce_data, pe_data, atm_strike
    
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
    now = datetime.now()
 #   st.write("Current Time =", now.strftime("%H:%M:%S"))
 #   st.write("____________________________________________________________________")
    df = pd.DataFrame()
 #   pnl = pnl.append(pd.DataFrame({"pnl_time": pnl_time, "pnl_calc": pnl_calc}, index=[pnl_counter]))

    df = df.append(pd.DataFrame(
        {"Instrument_Name": ce_data["tradingsymbol"], "Quantity": qty, "Entry_Price": ce_data["entry_price"], "LTP":ce_ltp, "PnL":ce_pnl}, index = [0]))
    df = df.append(pd.DataFrame(
        {"Instrument_Name": pe_data["tradingsymbol"], "Quantity": qty, "Entry_Price": pe_data["entry_price"],
         "LTP": pe_ltp, "PnL": pe_pnl}, index = [1]))

    st.write(df)
#    print(df)
    return pnl


"""
    st.write("Instrument_Name","Quantity","Entry_Price", "LTP", "PnL")
    ce_data_print = str(ce_data["tradingsymbol"])  + str(qty)  + str(ce_data["entry_price"])  + str(ce_ltp)  + str(ce_pnl)
    pe_data_print = str(pe_data["tradingsymbol"]) + str(qty)  + str(pe_data["entry_price"])  + str(pe_ltp)  + str(pe_pnl)

    if(ce_data["sl_hit"]):
        st.write(strike_through(ce_data_print))
    else:
        st.write(ce_data_print)
    if(pe_data["sl_hit"]):
        st.write(strike_through(pe_data_print))
    else:
        st.write(pe_data_print)
    st.write("PNL: ",round(pnl,2))
    st.write("____________________________________________________________________")
    
"""


def trigger_algo_pt(sl,qty,symbol="CRUDEOIL"):
    global start_button
    global header
    global select_param
    global plot_spot
    global plot_df
    ce_data, pe_data, atm_strike = trade_attributes(symbol)
    pnl_counter = 0
    pnl = pd.DataFrame()
    # this subscribes if CE or PE is hit
    print(ce_data["subscribe_symbol"])
    print(pe_data["subscribe_symbol"])
    api.subscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    # the below sleep is important
    sleep(3)

    pe_data["sl_hit"] = 0
    pe_data["sl_hit_price"] = 0

    ce_data["sl_hit"] = 0
    ce_data["sl_hit_price"] = 0

    while (dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(23,10,0)):
        ce_ltp = feedJson[ce_data["token_id"]]['ltp']
        pe_ltp = feedJson[pe_data["token_id"]]['ltp']
        if(float(ce_ltp) > float(ce_data["entry_price"]) * (1+sl/100) and ce_data["sl_hit"] != 1):
            place_order_pt('B',ce_data["tradingsymbol"],qty)
            ce_data["sl_hit_price"] = float(ce_ltp)
            ce_data["sl_hit"] = 1
            print("CE SL hit")

        if(float(pe_ltp) > float(pe_data["entry_price"]) * (1+sl/100) and pe_data["sl_hit"] != 1):
            place_order_pt('B', pe_data["tradingsymbol"], qty)
            pe_data["sl_hit_price"] = float(pe_ltp)
            pe_data["sl_hit"] = 1
            print("PE SL hit")
        now = datetime.now()

        with plot_df:
            pnl_time = now.strftime("%H:%M:%S")
            pnl_calc = pnl_calculation(ce_data, pe_data, qty)
            pnl = pnl.append(pd.DataFrame({"pnl_time": pnl_time, "pnl_calc": pnl_calc}, index=[pnl_counter]))
            pnl_counter += 1
            time.sleep(0.5)

        with plot_spot:
            get_chart_47579095(pnl)
            time.sleep(0.5)

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
    return pnl

def trigger_algo_exchange(sl,qty):
    
    ce_data, pe_data = trade_attributes(symbol)
    # Place CE and PE orders
    ce_orderid=place_order('S',ce_data["tradingsymbol"],qty)
    pe_orderid=place_order('S',pe_data["tradingsymbol"],qty)
    # wait for 3 seconds if order is not filled
    
    # this subscribes if CE or PE is hit
    api.subscribe([ce_data["subscribe_symbol"], pe_data["subscribe_symbol"]])
    # the below sleep is important
    sleep(3)

    pe_data["sl_hit"] = 0
    pe_data["sl_hit_price"] = 0

    ce_data["sl_hit"] = 0
    ce_data["sl_hit_price"] = 0

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
    pnl = pnl_calculation(ce_data, pe_data,qty)
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