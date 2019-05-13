#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl

"""

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import (
    EVENT_TICK, EVENT_ORDER, EVENT_TRADE,)
from vnpy.trader.constant import (Direction, Offset, OrderType)
from vnpy.trader.object import (SubscribeRequest, OrderRequest)
from vnpy.trader.utility import load_json, save_json

# from .template import AlgoTemplate


APP_NAME = "MarketDataVisulization"

EVENT_MKDATA_LOG = "eMKDataLog"
EVENT_ALGO_SETTING = "eAlgoSetting"
EVENT_ALGO_VARIABLES = "eAlgoVariables"
EVENT_ALGO_PARAMETERS = "eAlgoParameters"


class MarketDataEngine(BaseEngine):
    """"""
    setting_filename = "market_data_visulization_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """Constructor"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.symbol_mkdata_map = {}
        self.symbol_order_map = {}
        self.symbol_trade_map = {}

        self.register_event()

    def init_engine(self):
        """"""
        self.write_log("市场数据可视化引擎启动")

    def register_event(self):
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)

    def process_tick_event(self, event: Event):
        """"""
        tick = event.data

        #TODO: update tick


    def process_trade_event(self, event: Event):
        """"""
        trade = event.data

        #TODO: mark the trade

    def process_order_event(self, event: Event):
        """"""
        order = event.data

        #TODO:mark the order


    def subscribe(self, vt_symbol: str):
        """"""
        contract = self.main_engine.get_contract(vt_symbol)
        if not contract:
            self.write_log(f'订阅行情失败，找不到合约：{vt_symbol}')
            return

        req = SubscribeRequest(
            symbol=contract.symbol,
            exchange=contract.exchange
        )
        self.main_engine.subscribe(req, contract.gateway_name)


    def get_tick(self, vt_symbol: str):
        """"""
        tick = self.main_engine.get_tick(vt_symbol)

        if not tick:
            self.write_log(f"查询行情失败，找不到行情：{vt_symbol}")

        return tick

    def get_contract(self, vt_symbol: str):
        """"""
        contract = self.main_engine.get_contract(vt_symbol)

        if not contract:
            self.write_log(f"查询合约失败，找不到合约：{vt_symbol}")

        return contract

    def write_log(self, msg: str):
        """"""

        event = Event(EVENT_MKDATA_LOG)
        event.data = msg
        self.event_engine.put(event)

