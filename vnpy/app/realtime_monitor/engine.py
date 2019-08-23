#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl

"""

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import (
    EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_LOG)
from vnpy.trader.constant import (Direction, Offset, OrderType,Interval)
from vnpy.trader.object import (SubscribeRequest, OrderRequest, LogData)
from vnpy.trader.utility import load_json, save_json
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.trader.ibdata import ibdata_client
from vnpy.trader.object import BarData
import weakref
import datetime as dt
from dateutil import parser
from threading import Thread
from queue import Empty


APP_NAME = "Visulization"

# EVENT_MKDATA_LOG = "eMKDataLog"
# EVENT_VISULIZE_HiSTORICAL_DATA = "eVisulizeHistoricalData"
# EVENT_VISULIZE_REALTIME_DATA = "eVisulizeRealtimeData"
# EVENT_ALGO_PARAMETERS = "eAlgoParameters"
# EVENT_SUBSCRIBE_BAR = 'eSubscribeBar'
# EVENT_UNSUBSCRIBE_BAR = 'eUnsubscribeBar'
# EVENT_BAR_UPDATE = 'eBarUpdate'
#
#
# class VisulizationEngine(BaseEngine):
#     """"""
#     setting_filename = "visulization_setting.json"
#
#     def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
#         """Constructor"""
#         super().__init__(main_engine, event_engine, APP_NAME)
#
#         self.symbol_mkdata_map = {}
#         self.symbol_order_map = {}
#         self.symbol_trade_map = {}
#         self.realtimebar_threads = {}
#         self.first = True
#
#         # self.register_event()
#         self.init_engine()
#
#     def init_engine(self):
#         """"""
#         self.write_log("市场数据可视化引擎启动")
#         # self.init_ibdata()
#
#     def get_tick(self, vt_symbol: str):
#         """"""
#         tick = self.main_engine.get_tick(vt_symbol)
#
#         if not tick:
#             self.write_log(f"查询行情失败，找不到行情：{vt_symbol}")
#
#         return tick
#
#     def get_contract(self, vt_symbol: str):
#         """"""
#         contract = self.main_engine.get_contract(vt_symbol)
#
#         if not contract:
#             self.write_log(f"查询合约失败，找不到合约：{vt_symbol}")
#
#         return contract
#
#     def write_log(self, msg: str):
#         """"""
#
#         event = Event(EVENT_LOG)
#         log = LogData(msg=msg, gateway_name='IB')
#         event.data = log
#         self.event_engine.put(event)
#
#     def close(self):
#         ...
#         # ibdata_client.deinit()
#         # for subscription in self.realtimebar_threads:
#         #     reqId = ibdata_client.subscription2reqId(subscription)
#         #     q = ibdata_client.result_queues[reqId]
#         #     q.put_nowait(0)


class VisualEngine(BaseEngine):
    """"""
    setting_filename = "visual_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """Constructor"""
        super().__init__(main_engine, event_engine, APP_NAME)
        self.bar_generator = None
        self.first = True

        # self.register_event()
        self.init_engine()

    def init_engine(self):
        """"""
        self.write_log("市场数据可视化引擎启动")
        # self.init_ibdata()

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

        event = Event(EVENT_LOG)
        log = LogData(msg=msg, gateway_name='IB')
        event.data = log
        self.event_engine.put(event)

    def close(self):
        ...
        # ibdata_client.deinit()
        # for subscription in self.realtimebar_threads:
        #     reqId = ibdata_client.subscription2reqId(subscription)
        #     q = ibdata_client.result_queues[reqId]
        #     q.put_nowait(0)


