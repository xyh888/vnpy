#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl
THANKS FOR th github project https://github.com/moonnejs/uiKLine
"""

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import SubscribeRequest, HistoryRequest
from vnpy.trader.object import Interval, Exchange
from vnpy.trader.constant import Status, Direction
import numpy as np
import pandas as pd
import datetime as dt
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
import pyqtgraph as pg
from functools import partial
from collections import deque
from .baseQtItems import KeyWraper, CandlestickItem, MyStringAxis, Crosshair, CustomViewBox
from vnpy.trader.event import EVENT_TRADE, EVENT_ORDER, EVENT_TICK, EVENT_CONTRACT
from dateutil import parser
from vnpy.trader.utility import BarGenerator
import talib
from typing import List

from vnpy.chart import ChartWidget, CandleItem, VolumeItem
from vnpy.trader.constant import Direction, Interval, Exchange
from vnpy.trader.object import HistoryRequest, BarData, ContractData, TickData, TradeData
from vnpy.trader.utility import BarGenerator
from vnpy.trader.ui import QtWidgets
from ..engine import APP_NAME


DEFAULT_MA = [5, 10, 30, 60]
DEFAULT_MA_COLOR = ['r', 'b', 'g', 'y']

# class KLineWidget(KeyWraper):
#     """用于显示价格走势图"""
#
#     # 窗口标识
#     clsId = 0
#
#     # 保存K线数据的列表和Numpy Array对象
#     listBar = []
#     listVol = []
#     listHigh = []
#     listLow = []
#     listSig = []
#     listMA = []
#     listOpenInterest = []
#     arrows = []
#
#     # 是否完成了历史数据的读取
#     initCompleted = False
#     signal_bar_update = QtCore.pyqtSignal(Event)
#     signal_trade_update = QtCore.pyqtSignal(Event)
#     signal_order_update = QtCore.pyqtSignal(Event)
#
#     # ----------------------------------------------------------------------
#     def __init__(self, main_engine: MainEngine, event_engine: EventEngine, isRealTime=True):
#         """Constructor"""
#         super().__init__()
#
#         self.main_engine = main_engine
#         self.event_engine = event_engine
#
#         # 当前序号
#         self.index = None  # 下标
#         self.countK = 60  # 显示的Ｋ线范围
#
#         KLineWidget.clsId += 1
#         self.windowId = str(KLineWidget.clsId)
#
#         # 缓存数据
#         self.bg = None
#         self.datas = []
#         self.listBar = []
#         self.listVol = []
#         self.listHigh = []
#         self.listLow = []
#         self.listSig = []
#         self.listMA = []
#         self.listOpenInterest = []
#         self.listTrade = []
#         self.dictOrder = {}
#         self.arrows = []
#         self.tradeArrows = []
#         self.orderLines = {}
#
#         # 所有K线上信号图
#         self.allColor = deque(['blue', 'green', 'yellow', 'white'])
#         self.sigData = {}
#         self.sigColor = {}
#         self.sigPlots = {}
#
#         # 所副图上信号图
#         self.allSubColor = deque(['blue', 'green', 'yellow', 'white'])
#         self.subSigData = {}
#         self.subSigColor = {}
#         self.subSigPlots = {}
#
#         self.vt_symbol = ''
#         self.symbol = ''
#         self.exchange = ''
#         self.interval = ''
#         self.barCount = 300
#         self.tick_event_type = ''
#
#
#         # 初始化完成
#         self.initCompleted = False
#
#         # 调用函数
#         self.initUi(isRealTime)
#         # self.register_event()
#
#     # ----------------------------------------------------------------------
#     #  初始化相关
#     # ----------------------------------------------------------------------
#     def initUi(self, isRealTime):
#         """初始化界面"""
#         self.setWindowTitle('数据可视化')
#         # 主图
#         self.pw = pg.PlotWidget()
#         # 界面布局
#         self.lay_KL = pg.GraphicsLayout(border=(100, 100, 100))
#         self.lay_KL.setContentsMargins(10, 10, 10, 10)
#         self.lay_KL.setSpacing(0)
#         self.lay_KL.setBorder(color=(255, 255, 255, 255), width=0.8)
#         self.lay_KL.setZValue(0)
#         self.KLtitle = self.lay_KL.addLabel(u'')
#         self.pw.setCentralItem(self.lay_KL)
#         # 设置横坐标
#         xdict = {}
#         self.axisTime = MyStringAxis(xdict, orientation='bottom')
#         # 初始化子图
#         self.initplotKline()
#         self.initplotVol()
#         self.initplotOI()
#         # 注册十字光标
#         self.crosshair = Crosshair(self.pw, self)
#         # 设置界面
#         self.vb = QVBoxLayout()
#
#         if isRealTime:
#             self.exchange_combo = QComboBox()
#             self.exchange_combo.addItems([exchange.value for exchange in Exchange])
#             self.exchange_combo.setCurrentIndex(15)  # default: HKFE
#
#             self.symbol_line = QLineEdit("")
#             self.symbol_line.returnPressed.connect(self.subscribe)
#
#             self.interval_combo = QComboBox()
#             for inteval in Interval:
#                 self.interval_combo.addItem(inteval.value)
#
#             self.barCount_line = QLineEdit("300")
#             pIntvalidator = QIntValidator(self)
#             pIntvalidator.setRange(30, 1000)
#             self.barCount_line.setValidator(pIntvalidator)
#
#             form = QFormLayout()
#             form.addRow("交易所", self.exchange_combo)
#             form.addRow("代码", self.symbol_line)
#             form.addRow("K线周期", self.interval_combo)
#             form.addRow("BarCount", self.barCount_line)
#
#             self.vb.addLayout(form)
#
#         self.vb.addWidget(self.pw)
#         self.setLayout(self.vb)
#         self.resize(1300, 700)
#         self.signal_bar_update.connect(self.process_bar_event)
#         self.signal_trade_update.connect(self.process_trade_event)
#         self.signal_order_update.connect(self.process_order_event)
#         # 初始化完成
#         self.initCompleted = True
#
#         if self.main_engine is not None:
#             for c in self.main_engine.get_all_contracts():
#                 now = dt.datetime.now()
#                 if (c.expiry.year, c.expiry.month) == (now.year, now.month):
#                     self.symbol_line.setText(str(c.symbol))
#                     self.exchange_combo.setCurrentText(c.exchange.value)
#                     self.subscribe()
#                     break
#
#
#
#
#         # ----------------------------------------------------------------------
#
#     # def register_event(self):
#     #     if self.event_engine is not None:
#     #         self.event_engine.register(EVENT_BAR_UPDATE, self.process_bar_event)
#
#     def subscribe(self):
#         old_symbol = self.symbol
#         self.symbol = str(self.symbol_line.text())
#         if not self.symbol:
#             return
#
#         old_exchange = self.exchange
#         old_interval = self.interval
#         old_vt_symbol = f"{old_symbol}.{old_exchange}"
#         self.exchange = str(self.exchange_combo.currentText())
#         self.interval = str(self.interval_combo.currentText())
#         vt_symbol = f"{self.symbol}.{self.exchange}"
#
#         if vt_symbol == self.vt_symbol:
#             return
#         self.vt_symbol = vt_symbol
#
#         contract = self.main_engine.get_contract(vt_symbol)
#         old_tick_event_type = self.tick_event_type
#         self.tick_event_type = EVENT_TICK + old_vt_symbol
#
#         if contract:
#             self.barCount = int(self.barCount_line.text())
#             self.clearData()
#             self.bg = None
#             interval2timedelta = {Interval.MINUTE: dt.timedelta(minutes=1), Interval.HOUR: dt.timedelta(hours=1), Interval.DAILY: dt.timedelta(days=1)}
#             start = dt.datetime.now() - self.barCount * interval2timedelta[Interval(self.interval)]
#             req = HistoryRequest(contract.symbol, contract.exchange, start=start, interval=Interval(self.interval))
#             bars = self.main_engine.query_history(req, contract.gateway_name)
#             self.barCount = len(bars)
#             self.index = self.barCount
#             self.loadData(bars)
#             self.refreshAll()
#             # for b in bars:
#             #     self.onBar(b)
#
#             self.bg = BarGenerator(self.onBar, interval=Interval(self.interval))
#             self.bg.bar = bars[-1]
#             if old_tick_event_type:
#                 self.event_engine.register(EVENT_TICK + old_vt_symbol, self.signal_bar_update.emit)
#                 self.event_engine.unregister(EVENT_TRADE, self.signal_trade_update.emit)
#                 self.event_engine.unregister(EVENT_ORDER, self.signal_order_update.emit)
#
#             self.event_engine.register(EVENT_TICK + contract.vt_symbol, self.signal_bar_update.emit)
#             self.event_engine.register(EVENT_TRADE, self.signal_trade_update.emit)
#             self.event_engine.register(EVENT_ORDER, self.signal_order_update.emit)
#             self.init_listTrade()
#             self.init_dictOrder()
#             self.plotTradeMark()
#             self.plotOrderMarkLine()
#
#
#     def init_listTrade(self):
#         all_trades = self.main_engine.get_all_trades()
#         trades = [t for t in all_trades if t.vt_symbol == self.vt_symbol]
#
#         interval = {'1m': 60, '1h': 3600}.get(self.interval)
#
#         if not interval:
#             return
#
#         for t in trades:
#             # t_time = parser.parse(t.time)
#             t_time = t.time
#             for i, _time in enumerate(self.axisTime.x_strings):
#                 timedelta = (t_time - _time).total_seconds()
#                 if 0 <= timedelta < interval:
#                     time_int = i
#                     if any(self.listTrade):
#                         self.listTrade.resize(len(self.listTrade) + 1, refcheck=0)
#                         self.listTrade[-1] = (time_int, t.direction.value, t.price, t.volume)
#                     else:
#                         self.listTrade = np.rec.array([(time_int, t.direction.value, t.price, t.volume)], \
#                                                       names=('time_int', 'direction', 'price', 'volume'))
#
#     def init_dictOrder(self):
#         all_orders = self.main_engine.get_all_orders()
#         for o in all_orders:
#             if o.vt_symbol == self.vt_symbol:
#                 self.dictOrder[o.vt_orderid] = o
#
#     def process_bar_event(self, event: Event):
#         tick = event.data
#         if self.bg:
#             self.bg.update_tick(tick)
#             self.onBar(self.bg.bar)
#             if len(self.datas) >= self.barCount:
#
#                 self.index = len(self.datas)
#                 vRange = self.pwKL.getViewBox().viewRange()
#                 xmax = max(0, int(vRange[0][1]))
#                 if xmax + 10 >= self.index or xmax <= self.countK:
#                     self.plotAll(False, 0, len(self.datas))
#                     self.updateAll()
#                     self.crosshair.signal.emit((None, None))
#
#             elif len(self.datas) >= self.barCount - 1:
#                 self.init_listTrade()
#                 self.init_dictOrder()
#                 self.plotTradeMark()
#                 self.plotOrderMarkLine()
#
#     def process_trade_event(self, event: Event):
#         trade = event.data
#         if trade.vt_symbol != self.vt_symbol:
#             return
#
#         interval = {'1m': 60, '1h': 3600}.get(self.interval)
#
#         if not interval:
#             return
#
#         timedelta = (trade.time - self.datas[-1].datetime.astype(dt.datetime)).total_seconds()
#         time_int = len(self.datas) - (timedelta // interval + 1)
#         if any(self.listTrade):
#             self.listTrade.resize(len(self.listTrade) + 1, refcheck=0)
#             self.listTrade[-1] = (time_int, trade.direction.value, trade.price, trade.volume)
#         else:
#             self.listTrade = np.rec.array([(time_int, trade.direction.value, trade.price, trade.volume)], \
#                      names=('time_int', 'direction', 'price', 'volume'))
#
#         self.plotTradeMark()
#         self.refreshAll(True, False)
#
#     def process_order_event(self, event: Event):
#         order = event.data
#         if order.vt_symbol != self.vt_symbol:
#             return
#
#         self.dictOrder[order.vt_orderid] = order
#
#         self.plotOrderMarkLine()
#         self.refreshAll(True, False)
#
#     def makePI(self, name):
#         """生成PlotItem对象"""
#         vb = CustomViewBox()
#         plotItem = pg.PlotItem(viewBox=vb, name=name, axisItems={'bottom': self.axisTime})
#         plotItem.setMenuEnabled(False)
#         plotItem.setClipToView(True)
#         plotItem.hideAxis('left')
#         plotItem.showAxis('right')
#         plotItem.setDownsampling(mode='peak')
#         plotItem.setRange(xRange=(0, 1), yRange=(0, 1))
#         plotItem.getAxis('right').setWidth(60)
#         plotItem.getAxis('right').setStyle(tickFont=QFont("Roman times", 10, QFont.Bold))
#         plotItem.getAxis('right').setPen(color=(255, 255, 255, 255), width=0.8)
#         plotItem.showGrid(True, True)
#         plotItem.hideButtons()
#         return plotItem
#
#     # ----------------------------------------------------------------------
#     def initplotVol(self):
#         """初始化成交量子图"""
#         self.pwVol = self.makePI('_'.join([self.windowId, 'PlotVOL']))
#         self.volume = CandlestickItem(self.listVol)
#         self.pwVol.addItem(self.volume)
#         self.pwVol.setMaximumHeight(150)
#         self.pwVol.setXLink('_'.join([self.windowId, 'PlotOI']))
#         self.pwVol.hideAxis('bottom')
#
#         self.lay_KL.nextRow()
#         self.lay_KL.addItem(self.pwVol)
#
#     # ----------------------------------------------------------------------
#     def initplotKline(self):
#         """初始化K线子图"""
#         self.pwKL = self.makePI('_'.join([self.windowId, 'PlotKL']))
#         self.candle = CandlestickItem(self.listBar)
#         self.pwKL.addItem(self.candle)
#         self.pwKL.addItem(self.candle.tickLine)
#         self.curveMAs = [self.pwKL.plot(pen=c, name=f'MA{p}') for p, c in zip(DEFAULT_MA, DEFAULT_MA_COLOR)]
#         self.pwKL.setMinimumHeight(350)
#         self.pwKL.setXLink('_'.join([self.windowId, 'PlotOI']))
#         self.pwKL.hideAxis('bottom')
#
#         self.lay_KL.nextRow()
#         self.lay_KL.addItem(self.pwKL)
#
#     # ----------------------------------------------------------------------
#     def initplotOI(self):
#         """初始化持仓量子图"""
#         self.pwOI = self.makePI('_'.join([self.windowId, 'PlotOI']))
#         self.curveOI = self.pwOI.plot()
#
#         self.lay_KL.nextRow()
#         self.lay_KL.addItem(self.pwOI)
#
#     # ----------------------------------------------------------------------
#     #  画图相关
#     # ----------------------------------------------------------------------
#     def plotVol(self, redraw=False, xmin=0, xmax=-1):
#         """重画成交量子图"""
#         if self.initCompleted:
#             self.volume.generatePicture(self.listVol[xmin:xmax], redraw)  # 画成交量子图
#
#     # ----------------------------------------------------------------------
#     def plotKline(self, redraw=False, xmin=0, xmax=-1):
#         """重画K线子图"""
#         if self.initCompleted:
#             self.candle.generatePicture(self.listBar[xmin:xmax], redraw)  # 画K线
#             self.plotMark()  # 显示开平仓信号位置
#             self.plotMA()
#
#     # ----------------------------------------------------------------------
#     def plotOI(self, xmin=0, xmax=-1):
#         """重画持仓量子图"""
#         if self.initCompleted:
#             self.curveOI.setData(np.append(self.listOpenInterest[xmin:xmax], 0), pen='w', name="OpenInterest")
#
#     # ----------------------------------------------------------------------
#
#     def addSig(self, sig, main=True):
#         """新增信号图"""
#         if main:
#             if sig in self.sigPlots:
#                 self.pwKL.removeItem(self.sigPlots[sig])
#             self.sigPlots[sig] = self.pwKL.plot()
#             self.sigColor[sig] = self.allColor[0]
#             self.allColor.append(self.allColor.popleft())
#         else:
#             if sig in self.subSigPlots:
#                 self.pwOI.removeItem(self.subSigPlots[sig])
#             self.subSigPlots[sig] = self.pwOI.plot()
#             self.subSigColor[sig] = self.allSubColor[0]
#             self.allSubColor.append(self.allSubColor.popleft())
#
#     # ----------------------------------------------------------------------
#     def showSig(self, datas, main=True, clear=False):
#         """刷新信号图"""
#         if clear:
#             self.clearSig(main)
#             if datas and not main:
#                 sigDatas = np.array(datas.values()[0])
#                 self.listOpenInterest = sigDatas
#                 self.datas['openInterest'] = sigDatas
#                 self.plotOI(0, len(sigDatas))
#         if main:
#             for sig in datas:
#                 self.addSig(sig, main)
#                 self.sigData[sig] = datas[sig]
#                 self.sigPlots[sig].setData(np.append(datas[sig], 0), pen=self.sigColor[sig][0], name=sig)
#         else:
#             for sig in datas:
#                 self.addSig(sig, main)
#                 self.subSigData[sig] = datas[sig]
#                 self.subSigPlots[sig].setData(np.append(datas[sig], 0), pen=self.subSigColor[sig][0], name=sig)
#
#     # ----------------------------------------------------------------------
#     def plotMA(self):
#         for curve, p in zip(self.curveMAs, DEFAULT_MA):
#             curve.setData(self.listMA[f'ma{p}'])
#
#     def plotTradeMark(self):
#         """显示交易信号"""
#         for arrow in self.tradeArrows:
#             self.pwKL.removeItem(arrow)
#
#         for t in self.listTrade:
#             if t.direction == '多':
#                 arrow = pg.ArrowItem(pos=(t.time_int, t.price), angle=90, brush=(255, 0, 0))
#                 self.pwKL.addItem(arrow)
#                 self.tradeArrows.append(arrow)
#             elif t.direction == '空':
#                 arrow = pg.ArrowItem(pos=(t.time_int, t.price), angle=-90, brush=(0, 255, 0))
#                 self.pwKL.addItem(arrow)
#                 self.tradeArrows.append(arrow)
#
#     def plotOrderMarkLine(self):
#         for o_id, o in self.dictOrder.items():
#             if o.vt_orderid in self.orderLines:
#                 if o.status in [Status.ALLTRADED, Status.REJECTED, Status.CANCELLED]:
#                     self.pwKL.removeItem(self.orderLines[o.vt_orderid])
#                 else:
#                     self.orderLines[o.vt_orderid].setPos(o.price)
#                     if o.direction == Direction.LONG:
#                         self.orderLines[o.vt_orderid].label.setFormat(f'BUY-{o.price}-{o.volume - o.traded}')
#                     elif o.direction == Direction.SHORT:
#                         self.orderLines[o.vt_orderid].label.setFormat(f'SELL-{o.price}-{o.volume - o.traded}')
#             else:
#                 if o.status in [Status.ALLTRADED, Status.REJECTED, Status.CANCELLED]:
#                     continue
#
#                 if o.direction == Direction.LONG:
#                     pen = pg.mkPen(color='b', width=min(o.volume - o.traded, 10) / 2)
#                     hoverPen = pg.mkPen(color='r', width=min(o.volume - o.traded, 10))
#                     line = pg.InfiniteLine(pos=o.price, angle=0, movable=False,
#                                            pen=pen, hoverPen=hoverPen,
#                                            label=f'BUY-{o.price}-{o.volume - o.traded}', labelOpts={'color':'r'})
#                     self.pwKL.addItem(line)
#                     self.orderLines[o.vt_orderid] = line
#                 elif o.direction == Direction.SHORT:
#                     pen = pg.mkPen(color='y', width=min(o.volume - o.traded, 10)/2)
#                     hoverPen = pg.mkPen(color='g', width=min(o.volume - o.traded, 10))
#                     line = pg.InfiniteLine(pos=o.price, angle=0, movable=False,
#                                            pen=pen, hoverPen=hoverPen,
#                                            label=f'SELL-{o.price}-{o.volume - o.traded}', labelOpts={'color':'g'})
#                     pg.BarGraphItem
#                     self.pwKL.addItem(line)
#                     self.orderLines[o.vt_orderid] = line
#
#     def plotMark(self):
#         """显示开平仓信号"""
#         # 检查是否有数据
#         if len(self.datas) == 0:
#             return
#         for arrow in self.arrows:
#             self.pwKL.removeItem(arrow)
#         # 画买卖信号
#         for i in range(len(self.listSig)):
#             # 无信号
#             if self.listSig[i] == 0:
#                 continue
#             # 买信号
#             elif self.listSig[i] > 0:
#                 arrow = pg.ArrowItem(pos=(i, self.datas[i]['low']), angle=90, brush=(255, 0, 0))
#             # 卖信号
#             elif self.listSig[i] < 0:
#                 arrow = pg.ArrowItem(pos=(i, self.datas[i]['high']), angle=-90, brush=(0, 255, 0))
#             self.pwKL.addItem(arrow)
#             self.arrows.append(arrow)
#
#     # ----------------------------------------------------------------------
#     def updateAll(self):
#         """
#         手动更新所有K线图形，K线播放模式下需要
#         """
#         datas = self.datas
#         self.volume.pictrue = None
#         self.candle.pictrue = None
#         self.volume.update()
#         self.candle.update()
#
#         def update(view, low, high):
#             vRange = view.viewRange()
#             xmin = max(0, int(vRange[0][0]))
#             xmax = max(0, int(vRange[0][1]))
#             try:
#                 xmax = min(xmax, len(datas) - 1)
#             except:
#                 xmax = xmax
#             if len(datas) > 0 and xmax > xmin:
#                 ymin = min(datas[xmin:xmax][low])
#                 ymax = max(datas[xmin:xmax][high])
#                 view.setRange(yRange=(ymin, ymax))
#             else:
#                 view.setRange(yRange=(0, 1))
#
#         update(self.pwKL.getViewBox(), 'low', 'high')
#         update(self.pwVol.getViewBox(), 'volume', 'volume')
#
#     # ----------------------------------------------------------------------
#     def plotAll(self, redraw=True, xMin=0, xMax=-1):
#         """
#         重画所有界面
#         redraw ：False=重画最后一根K线; True=重画所有
#         xMin,xMax : 数据范围
#         """
#         xMax = len(self.datas) - 1 if xMax < 0 else xMax
#         # self.countK = xMax-xMin
#         # self.index = int((xMax+xMin)/2)
#         self.pwOI.setLimits(xMin=xMin, xMax=xMax)
#         self.pwKL.setLimits(xMin=xMin, xMax=xMax)
#         self.pwVol.setLimits(xMin=xMin, xMax=xMax)
#         self.plotKline(redraw, xMin, xMax)  # K线图
#         self.plotVol(redraw, xMin, xMax)  # K线副图，成交量
#         self.plotOI(0, len(self.datas))  # K线副图，持仓量
#         self.refresh()
#
#     # ----------------------------------------------------------------------
#     def refresh(self):
#         """
#         刷新三个子图的现实范围
#         """
#         # datas = self.datas
#         minutes = int(self.countK / 2)
#         xmin = max(0, self.index - minutes)
#         try:
#             xmax = min(xmin + 2 * minutes, len(self.datas) - 1) if self.datas else xmin + 2 * minutes
#         except:
#             xmax = xmin + 2 * minutes
#         self.pwOI.setRange(xRange=(xmin, xmax))
#         self.pwKL.setRange(xRange=(xmin, xmax))
#         self.pwVol.setRange(xRange=(xmin, xmax))
#
#     # ----------------------------------------------------------------------
#     #  快捷键相关
#     # ----------------------------------------------------------------------
#     def onNxt(self):
#         """跳转到下一个开平仓点"""
#         if len(self.listSig) > 0 and not self.index is None:
#             datalen = len(self.listSig)
#             if self.index < datalen - 2: self.index += 1
#             while self.index < datalen - 2 and self.listSig[self.index] == 0:
#                 self.index += 1
#             self.refresh()
#             x = self.index
#             y = self.datas[x]['close']
#             self.crosshair.signal.emit((x, y))
#
#     # ----------------------------------------------------------------------
#     def onPre(self):
#         """跳转到上一个开平仓点"""
#         if len(self.listSig) > 0 and not self.index is None:
#             if self.index > 0: self.index -= 1
#             while self.index > 0 and self.listSig[self.index] == 0:
#                 self.index -= 1
#             self.refresh()
#             x = self.index
#             y = self.datas[x]['close']
#             self.crosshair.signal.emit((x, y))
#
#     # ----------------------------------------------------------------------
#     def onDown(self):
#         """放大显示区间"""
#         self.countK = min(len(self.datas), int(self.countK * 1.2) + 1)
#         self.refresh()
#         if len(self.datas) > 0:
#             x = self.index - self.countK / 2 + 2 if int(
#                 self.crosshair.xAxis) < self.index - self.countK / 2 + 2 else int(self.crosshair.xAxis)
#             x = self.index + self.countK / 2 - 2 if x > self.index + self.countK / 2 - 2 else x
#             x = len(self.datas) - 1 if x > len(self.datas) - 1 else int(x)
#             y = self.datas[x][2]
#             self.crosshair.signal.emit((x, y))
#
#     # ----------------------------------------------------------------------
#     def onUp(self):
#         """缩小显示区间"""
#         self.countK = max(3, int(self.countK / 1.2) - 1)
#         self.refresh()
#         if len(self.datas) > 0:
#             x = self.index - self.countK / 2 + 2 if int(
#                 self.crosshair.xAxis) < self.index - self.countK / 2 + 2 else int(self.crosshair.xAxis)
#             x = self.index + self.countK / 2 - 2 if x > self.index + self.countK / 2 - 2 else x
#             x = len(self.datas) - 1 if x > len(self.datas) - 1 else int(x)
#             y = self.datas[x]['close']
#             self.crosshair.signal.emit((x, y))
#
#     # ----------------------------------------------------------------------
#     def onLeft(self):
#         """向左移动"""
#         if len(self.datas) > 0 and int(self.crosshair.xAxis) > 2:
#             x = int(self.crosshair.xAxis) - 1
#             x = len(self.datas) - 1 if x > len(self.datas) - 1 else int(x)
#             y = self.datas[x]['close']
#             if x <= self.index - self.countK / 2 + 2 and self.index > 1:
#                 self.index -= 1
#                 self.refresh()
#             self.crosshair.signal.emit((x, y))
#
#     # ----------------------------------------------------------------------
#     def onRight(self):
#         """向右移动"""
#         if len(self.datas) > 0 and int(self.crosshair.xAxis) < len(self.datas) - 1:
#             x = int(self.crosshair.xAxis) + 1
#             x = len(self.datas) - 1 if x > len(self.datas) - 1 else int(x)
#             y = self.datas[x]['close']
#             if x >= self.index + int(self.countK / 2) - 2:
#                 self.index += 1
#                 self.refresh()
#             self.crosshair.signal.emit((x, y))
#
#     def wheelEvent(self, event):
#         """滚轮缩放"""
#         angle = event.angleDelta()
#         if angle.y() < 0:
#             self.onDown()
#         elif angle.y() > 0:
#             self.onUp()
#
#     # ----------------------------------------------------------------------
#     # 界面回调相关
#     # ----------------------------------------------------------------------
#     def onPaint(self):
#         """界面刷新回调"""
#         view = self.pwKL.getViewBox()
#         vRange = view.viewRange()
#         xmin = max(0, int(vRange[0][0]))
#         xmax = max(0, int(vRange[0][1]))
#         self.index = int((xmin + xmax) / 2) + 1
#
#     # ----------------------------------------------------------------------
#     def resignData(self, datas):
#         """更新数据，用于Y坐标自适应"""
#         self.crosshair.datas = datas
#
#         def viewXRangeChanged(low, high, self):
#             vRange = self.viewRange()
#             xmin = max(0, int(vRange[0][0]))
#             xmax = max(0, int(vRange[0][1]))
#             xmax = min(xmax, len(datas))
#             if len(datas) > 0 and xmax > xmin:
#                 ymin = min(datas[xmin:xmax][low])
#                 ymax = max(datas[xmin:xmax][high])
#                 ymin, ymax = (-1, 1) if ymin == ymax else (ymin, ymax)
#                 self.setRange(yRange=(ymin, ymax))
#             else:
#                 self.setRange(yRange=(0, 1))
#
#         view = self.pwKL.getViewBox()
#         view.sigXRangeChanged.connect(partial(viewXRangeChanged, 'low', 'high'))
#
#         view = self.pwVol.getViewBox()
#         view.sigXRangeChanged.connect(partial(viewXRangeChanged, 'volume', 'volume'))
#
#         view = self.pwOI.getViewBox()
#         view.sigXRangeChanged.connect(partial(viewXRangeChanged, 'openInterest', 'openInterest'))
#
#     # ----------------------------------------------------------------------
#     # 数据相关
#     # ----------------------------------------------------------------------
#     def clearData(self):
#         """清空数据"""
#         # 清空数据，重新画图
#         self.time_index = []
#         self.listBar = []
#         self.listVol = []
#         self.listLow = []
#         self.listHigh = []
#         self.listMA = []
#         self.listOpenInterest = []
#         self.listSig = []
#         self.sigData = {}
#         self.datas = []
#
#         self.listTrade = []
#         self.dictOrder = {}
#         self.tradeArrows = []
#         self.orderLines = {}
#
#     # ----------------------------------------------------------------------
#     def clearSig(self, main=True):
#         """清空信号图形"""
#         # 清空信号图
#         if main:
#             for sig in self.sigPlots:
#                 self.pwKL.removeItem(self.sigPlots[sig])
#             self.sigData = {}
#             self.sigPlots = {}
#         else:
#             for sig in self.subSigPlots:
#                 self.pwOI.removeItem(self.subSigPlots[sig])
#             self.subSigData = {}
#             self.subSigPlots = {}
#
#     # ----------------------------------------------------------------------
#     def updateSig(self, sig):
#         """刷新买卖信号"""
#         self.listSig = sig
#         self.plotMark()
#
#     # ----------------------------------------------------------------------
#     def onBar(self, bar):
#         """
#         新增K线数据,K线播放模式
#         """
#         # 是否需要更新K线
#         newBar = False if len(self.datas) > 0 and bar.datetime.replace(second=0) == self.datas[-1].datetime.item().replace(second=0) else True
#         nrecords = len(self.datas) if newBar else len(self.datas) - 1
#         # bar.openInterest = np.random.randint(0,
#         #                                      3) if bar.openInterest == np.inf or bar.openInterest == -np.inf else bar.openInterest
#         openInterest = 0
#         recordVol = (nrecords, abs(bar.volume), 0, 0, abs(bar.volume)) if bar.close_price < bar.open_price else (
#         nrecords, 0, abs(bar.volume), 0, abs(bar.volume))
#
#         if newBar and any(self.datas):
#             self.datas.resize(nrecords + 1, refcheck=0)
#             self.listBar.resize(nrecords + 1, refcheck=0)
#             self.listVol.resize(nrecords + 1, refcheck=0)
#             self.listMA.resize(nrecords + 1, refcheck=0)
#             self.listSig.append(0)
#         elif any(self.datas):
#             self.listLow.pop()
#             self.listHigh.pop()
#             self.listOpenInterest.pop()
#             self.listSig.pop()
#         if any(self.datas):
#             self.datas[-1] = (bar.datetime, bar.open_price, bar.close_price, bar.low_price, bar.high_price, bar.volume, bar.open_interest)
#             self.listBar[-1] = (nrecords, bar.open_price, bar.close_price, bar.low_price, bar.high_price)
#             self.listVol[-1] = recordVol
#             self.listSig[-1] = 0
#             self.listMA[-1] = tuple(sum(self.datas.close[-p:])/p for p in DEFAULT_MA)
#
#         else:
#             self.datas = np.rec.array(
#                 [(bar.datetime, bar.open_price, bar.close_price, bar.low_price, bar.high_price, bar.volume, bar.open_interest)], \
#                 names=('datetime', 'open', 'close', 'low', 'high', 'volume', 'openInterest'))
#             self.listBar = np.rec.array([(nrecords, bar.open_price, bar.close_price, bar.low_price, bar.high_price)], \
#                                         names=('time_int', 'open', 'close', 'low', 'high'))
#             self.listVol = np.rec.array([recordVol], names=('time_int', 'open', 'close', 'low', 'high'))
#             self.listSig = [0]
#             self.resignData(self.datas)
#
#         self.axisTime.update_xdict({nrecords: bar.datetime})
#         self.listLow.append(bar.low_price)
#         self.listHigh.append(bar.high_price)
#         self.listOpenInterest.append(bar.open_interest)
#         self.listSig.append(0)
#         self.resignData(self.datas)
#         return newBar
#
#     # ----------------------------------------------------------------------
#     def loadData(self, datas, trades=None, sigs=None):
#         """
#         载入pandas.DataFrame数据
#         datas : 数据格式，cols : datetime, open, close, low, high
#         """
#         # 设置中心点时间
#         # 绑定数据，更新横坐标映射，更新Y轴自适应函数，更新十字光标映射
#         datas = pd.DataFrame([[b.datetime, b.open_price, b.close_price, b.low_price, b.high_price, b.volume, getattr(b, 'open_interest', 0)] for b in datas],
#                              columns=['datetime', 'open', 'close', 'low', 'high', 'volume', 'openInterest']).set_index('datetime', drop=False)
#         for p in DEFAULT_MA:
#             datas[f'ma{p}'] = talib.MA(datas['close'].values, timeperiod=p)
#
#         datas['time_int'] = np.array(range(len(datas.index)))
#         self.datas = datas[['datetime', 'open', 'close', 'low', 'high', 'volume', 'openInterest']].to_records(False, column_dtypes={'datetime': '<M8[s]'})
#         self.axisTime.xdict = {}
#         xdict = dict(enumerate(datas.index.to_list()))
#         self.axisTime.update_xdict(xdict)
#         self.resignData(self.datas)
#         # 更新画图用到的数据
#         self.listBar = datas[['time_int', 'open', 'close', 'low', 'high']].to_records(False)
#         self.listHigh = list(datas['high'])
#         self.listLow = list(datas['low'])
#         self.listOpenInterest = list(datas['openInterest'])
#         self.listSig = [0] * (len(self.datas) - 1) if sigs is None else sigs
#         self.listMA = datas[[f'ma{p}' for p in DEFAULT_MA]].to_records(False)
#         if trades is not None:
#             trades = trades.merge(datas['time_int'], how='left', left_index=True, right_index=True)
#             self.listTrade = trades[['time_int', 'direction', 'price', 'volume']].to_records(False)
#         # 成交量颜色和涨跌同步，K线方向由涨跌决定
#         datas0 = pd.DataFrame()
#         datas0['open'] = datas.apply(lambda x: 0 if x['close'] >= x['open'] else x['volume'], axis=1)
#         datas0['close'] = datas.apply(lambda x: 0 if x['close'] < x['open'] else x['volume'], axis=1)
#         datas0['low'] = 0
#         datas0['high'] = datas['volume']
#         datas0['time_int'] = np.array(range(len(datas.index)))
#         self.listVol = datas0[['time_int', 'open', 'close', 'low', 'high']].to_records(False)
#
#     # ----------------------------------------------------------------------
#     def refreshAll(self, redraw=True, update=False):
#         """
#         更新所有界面
#         """
#         # 调用画图函数
#         self.index = len(self.datas)
#         self.plotAll(redraw, 0, len(self.datas))
#         if not update:
#             self.updateAll()
#         self.crosshair.signal.emit((None, None))


from .baseQtItems import MACurveItem, MACDItem
from vnpy.chart.base import UP_COLOR, DOWN_COLOR, CURSOR_COLOR, BLACK_COLOR, NORMAL_FONT, PEN_WIDTH
from collections import defaultdict
from vnpy.trader.object import OrderData
from vnpy.trader.constant import Status
from vnpy.trader.ui.widget import TickMonitor

class CandleChartWidget(QtWidgets.QWidget):
    """
    """
    signal_update_bar = QtCore.pyqtSignal(BarData)
    signal_update_trade = QtCore.pyqtSignal(TradeData)
    signal_update_order = QtCore.pyqtSignal(OrderData)
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.visual_engine = main_engine.get_engine(APP_NAME)
        self.bar_generator = BarGenerator(self.update_bar)
        self.dt_ix_map = {}
        self.last_ix = 0
        self.contract = {}
        self.trades = defaultdict(list)
        self.ix_pos_map = defaultdict(lambda :(0, 0))
        self.vt_symbol = None
        self.updated = False
        self.init_ui()
        self.register_event()

    def init_ui(self):
        """"""
        self.setWindowTitle("K线图表")
        self.resize(1400, 800)

        self.contract_combo = QtWidgets.QComboBox()
        self.contract = {c.vt_symbol:c for c in self.main_engine.get_all_contracts()}
        self.contract_combo.addItems(self.contract.keys())
        self.contract_combo.setCurrentIndex(-1)
        self.contract_combo.currentTextChanged.connect(self.change_contract)

        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItems([Interval.MINUTE.value])
        # self.tick_widget = TickMonitor(self.main_engine, self.event_engine)
        form = QtWidgets.QFormLayout()
        form.addRow("合约", self.contract_combo)
        form.addRow("周期", self.interval_combo)
        # form.addRow()


        # Create chart widget
        self.chart = ChartWidget()
        self.chart.add_plot("candle", hide_x_axis=True)
        self.chart.add_plot("indicator", hide_x_axis=True, maximum_height=120)
        self.chart.add_plot("volume", maximum_height=100)
        self.chart.add_item(CandleItem, "candle", "candle")
        self.chart.add_item(MACurveItem, 'ma', 'candle')
        self.chart.add_item(MACDItem, 'macd', 'indicator')
        self.chart.add_item(VolumeItem, "volume", "volume")
        self.chart.add_cursor()

        # Add scatter item for showing tradings
        self.trade_scatter = pg.ScatterPlotItem()
        self.last_tick_line = pg.InfiniteLine(angle=0, label='')
        candle_plot = self.chart.get_plot("candle")
        candle_plot.addItem(self.trade_scatter)
        candle_plot.addItem(self.last_tick_line)

        self.order_lines = defaultdict(pg.InfiniteLine)

        self.trade_info = trade_info = pg.TextItem(
                "info",
                anchor=(1, 0),
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                fill=BLACK_COLOR
            )
        trade_info.hide()
        trade_info.setZValue(2)
        trade_info.setFont(NORMAL_FONT)
        candle_plot.addItem(trade_info)  # , ignoreBounds=True)
        self.chart.scene().sigMouseMoved.connect(self.show_trade_info)

        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addWidget(self.chart)
        self.setLayout(vbox)

    def change_contract(self, vt_symbol):
        if self.vt_symbol is not None:
            self.event_engine.unregister(EVENT_TICK + self.vt_symbol, self.process_tick_event)
            self.event_engine.unregister(EVENT_TRADE + self.vt_symbol, self.process_trade_event)
            self.event_engine.unregister(EVENT_ORDER, self.process_order_event)

        self.clear_data()
        self.vt_symbol = vt_symbol
        contract: ContractData  = self.contract.get(vt_symbol)
        if contract:
            interval = Interval(self.interval_combo.currentText())
            total_minutes = {Interval.MINUTE: 1, Interval.HOUR: 60}[interval] * 600
            req = HistoryRequest(contract.symbol, contract.exchange, start=dt.datetime.now() - dt.timedelta(minutes=total_minutes), interval=interval)

            his_data = self.main_engine.query_history(req, contract.gateway_name)
            trade_data = [t for t in self.main_engine.get_all_trades() if t.vt_symbol == self.vt_symbol]
            order_data = [o for o in self.main_engine.get_all_orders() if o.vt_symbol == self.vt_symbol]
            self.bar_generator.bar = his_data[-1]

            self.event_engine.register(EVENT_TICK + self.vt_symbol, self.process_tick_event)
            self.event_engine.register(EVENT_TRADE + self.vt_symbol, self.process_trade_event)
            self.event_engine.register(EVENT_ORDER, self.process_order_event)
            self.update_history_bar(his_data)
            self.update_trades(trade_data)
            self.update_pos()

            for o in order_data:
                self.signal_update_order.emit(o)

    def add_contract(self, event: Event):
        c = event.data
        self.contract[c.vt_symbol] = c
        self.contract_combo.addItem(c.vt_symbol)

    def register_event(self):
        self.event_engine.register(EVENT_CONTRACT, self.add_contract)
        self.signal_update_bar.connect(self.chart.update_bar)
        self.signal_update_bar.connect(self.update_tick_line)
        self.signal_update_trade.connect(self.update_trade)
        self.signal_update_order.connect(self.update_order)

    def process_tick_event(self, event: Event):
        self.bar_generator.update_tick(event.data)
        bar = self.bar_generator.bar
        bar.datetime = bar.datetime.replace(
            second=0, microsecond=0
        )
        self.signal_update_bar.emit(bar)

    def process_trade_event(self, event: Event):
        trade = event.data

        self.signal_update_trade.emit(trade)

    def process_order_event(self, event: Event):
        order = event.data

        if order.vt_symbol == self.vt_symbol:
            self.signal_update_order.emit(order)

    def update_history_bar(self, history: list):
        """"""
        self.updated = True
        self.chart.update_history(history)

        for ix, bar in enumerate(history):
            self.dt_ix_map[bar.datetime] = ix
        else:
            self.last_ix = ix

    def update_bar(self, bar: BarData) -> None:
        if bar.datetime not in self.dt_ix_map:
            self.last_ix += 1
            self.dt_ix_map[bar.datetime] = self.last_ix
            self.ix_pos_map[self.last_ix] = self.ix_pos_map[self.last_ix - 1]
            # self.chart.update_bar(bar)

    def update_trades(self, trades: list):
        """"""
        trade_data = []

        for trade in trades:
            ix = self.dt_ix_map.get(trade.time.replace(second=0))

            if ix is not None:
                self.trades[ix].append(trade)
                scatter = {
                    "pos": (ix, trade.price),
                    "data": 1,
                    "size": 14,
                    "pen": pg.mkPen((255, 255, 255))
                }

                if trade.direction == Direction.LONG:
                    scatter["symbol"] = "t1"
                    scatter["brush"] = pg.mkBrush((255, 255, 0))
                else:
                    scatter["symbol"] = "t"
                    scatter["brush"] = pg.mkBrush((0, 0, 255))

                trade_data.append(scatter)

        self.trade_scatter.setData(trade_data)

    def update_trade(self, trade: TradeData):
        ix = self.dt_ix_map.get(trade.time.replace(second=0))
        if ix is not None:
            self.trades[ix].append(trade)
            scatter = {
                "pos": (ix, trade.price),
                "data": 1,
                "size": 14,
                "pen": pg.mkPen((255, 255, 255))
            }

            if trade.direction == Direction.LONG:
                scatter["symbol"] = "t1"
                scatter["brush"] = pg.mkBrush((255, 255, 0))
            else:
                scatter["symbol"] = "t"
                scatter["brush"] = pg.mkBrush((0, 0, 255))

            if trade.direction == Direction.LONG:
                p = trade.volume
                v = trade.volume * trade.price
            else:
                p = -trade.volume
                v = -trade.volume * trade.price
            self.ix_pos_map[ix] = (self.ix_pos_map[ix][0] + p,  self.ix_pos_map[ix][1] + v)

            self.trade_scatter.addPoints([scatter])

    def update_order(self, order: OrderData):
        if order.status in (Status.NOTTRADED, Status.PARTTRADED):
            line = self.order_lines[order.vt_orderid]
            line.setPos(order.price)
            line.setAngle(0)
            line.setPen(pg.mkPen(color=UP_COLOR if order.direction == Direction.LONG else DOWN_COLOR, width=PEN_WIDTH))
            line.setHoverPen(pg.mkPen(color=UP_COLOR if order.direction == Direction.LONG else DOWN_COLOR, width=PEN_WIDTH * 2))
            line.label = pg.InfLineLabel(line,
                                         text=f'{order.type.value}:{"↑" if order.direction == Direction.LONG else "↓"}{order.volume - order.traded}@{order.price}',
                                         color='r' if order.direction == Direction.LONG else 'g')
            candle_plot = self.chart.get_plot("candle")
            candle_plot.addItem(line)
        else:
            if order.vt_orderid in self.order_lines:
                line = self.order_lines[order.vt_orderid]
                candle_plot = self.chart.get_plot("candle")
                candle_plot.removeItem(line)

    def update_tick_line(self, bar: BarData):
        c = bar.close_price
        o = bar.open_price
        self.last_tick_line.setPos(bar.close_price)
        if c >= o:
            self.last_tick_line.setPen(pg.mkPen(color=UP_COLOR, width=PEN_WIDTH/2))
            self.last_tick_line.label.setText(str(c), color=(255, 69, 0))
        else:
            self.last_tick_line.setPen(pg.mkPen(color=DOWN_COLOR, width=PEN_WIDTH / 2))
            self.last_tick_line.label.setText(str(c), color=(173, 255, 47))

    def update_pos(self):
        net_p = 0
        net_value = 0
        for ix in self.dt_ix_map.values():
            trades = self.trades[ix]
            for t in trades:
                if t.direction == Direction.LONG:
                    net_p += t.volume
                    net_value += t.volume * t.price
                else:
                    net_p -= t.volume
                    net_value -= t.volume * t.price
            self.ix_pos_map[ix] = (net_p, net_value)

    def show_trade_info(self, evt: tuple) -> None:
        info = self.trade_info
        trades = self.trades[self.chart._cursor._x]
        pos = self.ix_pos_map[self.chart._cursor._x]
        pos_info_text = f'Pos: {pos[0]}@{pos[1]/pos[0] if pos[0] != 0 else pos[1]:.1f}\n'
        trade_info_text = '\n'.join(f'{t.time}: {"↑" if t.direction == Direction.LONG else "↓"}{t.volume}@{t.price:.1f}' for t in trades)
        info.setText(pos_info_text + trade_info_text)
        info.show()
        view = self.chart._cursor._views['candle']
        top_right = view.mapSceneToView(view.sceneBoundingRect().topRight())
        info.setPos(top_right)

    def clear_data(self):
        """"""
        self.updated = False
        self.chart.clear_all()
        self.vt_symbol = None
        self.dt_ix_map.clear()
        self.last_ix = 0
        self.trade_scatter.clear()
        self.trades = defaultdict(list)
        self.ix_pos_map = defaultdict(lambda :(0, 0))
        if self.bar_generator.bar:
            self.bar_generator.generate()

        candle_plot = self.chart.get_plot("candle")

        for l in self.order_lines:
            candle_plot.removeItem(l)

    def is_updated(self):
        """"""
        return self.updated

    def closeEvent(self, QCloseEvent):
        if self.vt_symbol is not None:
            self.event_engine.unregister(EVENT_TICK + self.vt_symbol, self.process_tick_event)
            self.event_engine.unregister(EVENT_TRADE + self.vt_symbol, self.process_trade_event)
            self.event_engine.unregister(EVENT_ORDER + self.vt_symbol, self.process_order_event)

        self.clear_data()
        self.contract_combo.setCurrentIndex(-1)