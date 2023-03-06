#!/usr/bin/env python
# coding: utf-8

import configparser
import sys
sys.path.append('ShoonyaApi')
sys.path.append('Algos')

from api_helper import ShoonyaApiPy
import datetime as dt
from datetime import datetime
import pyotp
import pandas as pd

# login
"""
config = configparser.ConfigParser()
config.read('credential.ini')
user = config['finvasia']['user']
u_pwd = config['finvasia']['u_pwd']
factor2 = config['finvasia']['factor2']
vc = config['finvasia']['vc']
app_key = config['finvasia']['app_key']
imei = config['finvasia']['imei']
"""
user = "FA73256"
u_pwd = "Lombard@1234"
factor2 = "11-11-1964"
vc = "FA73256_U"
app_key = "cec399ba4d05cbd209dd457d6e38dd69"
imei = "abc1234"


global master_contract, api

token = 'B6D32I442C4F743D5BVX6E76DPSBK732'

pyotp.TOTP(token).now()

base=100

api = ShoonyaApiPy()

# login by credentials
ret = api.login(userid=user, password=u_pwd, twoFA=pyotp.TOTP(token).now(), vendor_code=vc,
                api_secret=app_key, imei=imei)

master_contract = pd.read_csv('https://api.shoonya.com/MCX_symbols.txt.zip', compression='zip', engine='python',
                              delimiter=',')
master_contract['Expiry'] = pd.to_datetime(master_contract['Expiry'])
master_contract['StrikePrice'] = master_contract['StrikePrice'].astype(float)
master_contract.sort_values('Expiry', inplace=True)
master_contract.reset_index(drop=True, inplace=True)
print("login successful")


def get_instrument(Symbol, strike_price, optiontype, expiry_offset):
    # to get a intstrument token from the master contract downloaded from shoonya website
    return (master_contract[(master_contract['Symbol'] == Symbol) & (master_contract['OptionType'] == optiontype) & (
                master_contract['StrikePrice'] == strike_price)].iloc[expiry_offset])


def get_atm_strike(text):
    bnspot_token = api.searchscrip(exchange='MCX', searchtext=text)['values'][0]['token']
    while True:
        bnflp = float(api.get_quotes(exchange='MCX', token=bnspot_token)['lp'])
        if bnflp != None:
            break
    atmprice = round(bnflp / base) * base
    return atmprice


def place_order(BS, tradingsymbol, quantity, product_type='I', price_type='MKT', exchange='NFO', price=0,
                trigger_price=None):
    order_place = api.place_order(buy_or_sell=BS, product_type=product_type,
                                  exchange=exchange, tradingsymbol=tradingsymbol,
                                  quantity=quantity, discloseqty=0, price_type=price_type, price=price,
                                  trigger_price=trigger_price)  # M for NRML AND I For intraday in product type
    print(order_place)
    sleep(3)
    return order_place['norenordno']


def stop_loss_order(qty, tradingsymbol, price, SL):
    stop_price = round((1 + SL / 100) * price, 1)
    price = stop_price + 2
    trigger_price = stop_price
    stop_loss_orderid = place_order(BS='B', tradingsymbol=tradingsymbol, quantity=qty, price_type='SL-LMT', price=price,
                                    trigger_price=trigger_price)
    return stop_loss_orderid


def single_order_history(orderid, req):
    ''''stat','norenordno', 'uid', 'src_uid', 'actid', 'exch', 'tsym', 'q 'trantyty',pe', 'prctyp', 'ret', 'rejby', 'kidid',
       'pan', 'ordersource', 'token', 'pp', 'ls', 'ti', 'prc', 'dscqty', 'prd', 'status', 'rpt', 'ordenttm', 'norentm', 'rejreason','exch_tm'''
    # this required to made to avoid unnecesary making a lof of Dataframes
    # dl=pd.DataFrame(api.single_order_history(orderid))
    # sleep(1)
    # return dl[req].iloc[0]

    while True:
        json_data = api.single_order_history(orderid)
        if json_data != None:
            break

    for id in json_data:
        value_return = id[req]
        break

    return value_return


# In[12]:



feed_opened = False


def event_handler_order_update(order):
    counter = counter + 1
    print(f"order feed {counter / 2}")


def event_handler_feed_update(tick_data):
    if 'lp' in tick_data and 'tk' in tick_data:
        timest = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feedJson[tick_data['tk']] = {'ltp': float(tick_data['lp']), 'tt': timest}

feedJson = {}
counter = 0


def open_callback():
    global feed_opened
    feedJson = {}
    counter = 0
    feed_opened = True

try:
    api.start_websocket(order_update_callback=event_handler_order_update,
                    subscribe_callback=event_handler_feed_update,
                    socket_open_callback=open_callback)
except:
    print("Cant subscribe to feed")


