#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl

"""

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore


class MarketDataWidget(QtWidgets.QWidget):
    """
    market bar data visulization widget
    """
    def __init__(self):
        ...