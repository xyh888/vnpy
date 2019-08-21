#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/20 0020 16:51
# @Author  : Hadrianl 
# @File    : engine


from vnpy.event import EventEngine, Event
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import (
    EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_LOG)
from vnpy.trader.constant import (Direction, Offset, OrderType,Interval)
from vnpy.trader.object import (SubscribeRequest, OrderRequest, LogData)


APP_NAME = "StrategyReviewer"


class StrategyReviewEngine(BaseEngine):
    """"""
    setting_filename = "strategy_review_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """Constructor"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.init_engine()

    def init_engine(self):
        """"""
        # self.write_log("策略执行回顾引擎启动")
        ...