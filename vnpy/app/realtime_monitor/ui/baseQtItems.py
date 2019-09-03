#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl
THANKS FOR th github project https://github.com/moonnejs/uiKLine
"""


import numpy as np
import pandas as pd
import pyqtgraph as pg
import datetime as dt

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtCore
from pyqtgraph.Point import Point

# DEFAULT_MA = [5, 10, 30, 60]

from vnpy.chart.item import ChartItem, CandleItem, VolumeItem
from vnpy.chart.manager import BarManager
from vnpy.chart.widget import ChartWidget
from vnpy.trader.object import BarData, TickData, TradeData, OrderData
from vnpy.trader.constant import Direction, Status, Interval
from vnpy.chart.base import BAR_WIDTH, PEN_WIDTH, UP_COLOR, DOWN_COLOR, CURSOR_COLOR, BLACK_COLOR, NORMAL_FONT
from vnpy.trader.utility import ArrayManager, BarGenerator
from typing import Tuple, Callable
from collections import defaultdict
from vnpy.trader.ui.widget import BaseMonitor, TimeCell, BaseCell
from vnpy.app.realtime_monitor.ui.indicatorQtItems import INDICATOR
import talib


class TickSaleMonitor(BaseMonitor):
    headers = {
        "datetime": {"display": "时间", "cell": TimeCell, "update": False},
        "last_price": {"display": "价格", "cell": BaseCell, "update": False},
        "last_volume": {"display": "现手", "cell": BaseCell, "update": False},
    }

    def unregister_event(self):
        self.signal.disconnect(self.process_event)
        self.event_engine.unregister(self.event_type, self.signal.emit)

    def clear_all(self):
        self.cells = {}
        self.clearContents()


class InfoWidget(QFormLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.symbol_line = QLabel(" " * 30)
        self.symbol_line.setStyleSheet('color: rgb(255, 6, 10)')


        self.ask_line = QLabel(" " * 20)
        self.ask_line.setStyleSheet('color: rgb(255, 255, 255);\nbackground-color: rgb(0, 255, 50);')
        self.bid_line = QLabel(" " * 20)
        self.bid_line.setStyleSheet('color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 0);')

        self.addRow(self.symbol_line)
        self.addRow("卖出", self.ask_line)
        self.addRow("买入", self.bid_line)

    def update_tick(self, tick: TickData):
        self.symbol_line.setText(tick.vt_symbol)
        self.ask_line.setText(f'{tick.ask_volume_1}@{tick.ask_price_1}')
        self.bid_line.setText(f'{tick.bid_volume_1}@{tick.bid_price_1}')

    def clear_all(self):
        self.symbol_line.setText("")
        self.ask_line.setText("")
        self.bid_line.setText("")

class MarketDataChartWidget(ChartWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.dt_ix_map = {}
        self.last_ix = 0
        self.trades = defaultdict(list)
        self.ix_pos_map = defaultdict(lambda :(0, 0))
        self.vt_symbol = None
        self.bar = None
        self.last_tick = None
        self.indicators = {i.name: i for i in INDICATOR if i.plot_name == 'indicator'}
        self.current_indicator = list(self.indicators.keys())[0]
        self.init_chart_ui()

    def init_chart_ui(self):
        self.add_plot("candle", hide_x_axis=True, minimum_height=200)
        self.add_plot("indicator", hide_x_axis=True, maximum_height=120)
        self.add_plot("volume", maximum_height=100)

        self.add_item(CandleItem, "candle", "candle")

        for i in INDICATOR:
            if i.plot_name == 'candle':
                self.add_item(i, i.name, i.plot_name)
                break

        ind = self.indicators[self.current_indicator]
        self.add_item(ind, ind.name, ind.plot_name)

        self.add_item(VolumeItem, "volume", "volume")
        self.add_cursor()

        self.init_trade_scatter()
        self.init_last_tick_line()
        self.init_order_lines()
        self.init_trade_info()

    def init_trade_scatter(self):
        self.trade_scatter = pg.ScatterPlotItem()
        candle_plot = self.get_plot("candle")
        candle_plot.addItem(self.trade_scatter)

    def init_last_tick_line(self):
        self.last_tick_line = pg.InfiniteLine(angle=0, label='')
        candle_plot = self.get_plot("candle")
        candle_plot.addItem(self.last_tick_line)

    def init_order_lines(self):
        self.order_lines = defaultdict(pg.InfiniteLine)

    def init_trade_info(self):
        self.trade_info = pg.TextItem(
                "info",
                anchor=(1, 0),
                color=CURSOR_COLOR,
                border=CURSOR_COLOR,
                fill=BLACK_COLOR
            )
        self.trade_info.hide()
        self.trade_info.setZValue(2)
        self.trade_info.setFont(NORMAL_FONT)

        candle_plot = self.get_plot("candle")
        candle_plot.addItem(self.trade_info)

        self.scene().sigMouseMoved.connect(self.show_trade_info)

    def change_indicator(self, indicator):
        indicator_plot = self.get_plot("indicator")
        if self.current_indicator:
            for item in indicator_plot.items:
                if isinstance(item, ChartItem):
                    indicator_plot.removeItem(item)
                    self._items.pop(self.current_indicator)
                    self._item_plot_map.pop(item)

        self.current_indicator = indicator
        self.add_item(self.indicators[indicator], indicator, "indicator")

        self._items[self.current_indicator].update_history(self._manager.get_all_bars())

    def show_trade_info(self, evt: tuple) -> None:
        info = self.trade_info
        trades = self.trades[self._cursor._x]
        pos = self.ix_pos_map[self._cursor._x]
        pos_info_text = f'Pos: {pos[0]}@{pos[1]/pos[0] if pos[0] != 0 else pos[1]:.1f}\n'
        trade_info_text = '\n'.join(f'{t.time}: {"↑" if t.direction == Direction.LONG else "↓"}{t.volume}@{t.price:.1f}' for t in trades)
        info.setText(pos_info_text + trade_info_text)
        info.show()
        view = self._cursor._views['candle']
        top_right = view.mapSceneToView(view.sceneBoundingRect().topRight())
        info.setPos(top_right)

    def update_all(self, history, trades, orders):
        self.update_history(history)
        self.update_trades(trades)
        self.update_orders(orders)
        self.update_pos()

    def update_history(self, history: list):
        """"""
        super().update_history(history)

        for ix, bar in enumerate(history):
            self.dt_ix_map[bar.datetime] = ix
        else:
            self.last_ix = ix

    def update_tick(self, tick: TickData):
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return

        if not self.bar or self.bar.datetime.minute != tick.datetime.minute:
            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime.replace(second=0),
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            self.bar.close_price = tick.last_price
            self.bar.open_interest = tick.open_interest
            # self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        self.last_tick = tick
        self.update_bar(self.bar)

    def update_bar(self, bar: BarData) -> None:
        if bar.datetime not in self.dt_ix_map:
            self.last_ix += 1
            self.dt_ix_map[bar.datetime] = self.last_ix
            self.ix_pos_map[self.last_ix] = self.ix_pos_map[self.last_ix - 1]
            super().update_bar(bar)
        else:
            candle = self._items.get('candle')
            volume = self._items.get('volume')
            if candle:
                candle.update_bar(bar)

            if volume:
                volume.update_bar(bar)

    def update_trades(self, trades: list):
        """"""
        trade_scatters = []
        for trade in trades:
            ix = self.dt_ix_map.get(trade.time.replace(second=0))

            if ix is not None:
                self.trades[ix].append(trade)
                scatter = self.__trade2scatter(ix, trade)
                trade_scatters.append(scatter)

        self.trade_scatter.setData(trade_scatters)

    def update_trade(self, trade: TradeData):
        ix = self.dt_ix_map.get(trade.time.replace(second=0))
        if ix is not None:
            self.trades[ix].append(trade)
            scatter = self.__trade2scatter(ix, trade)
            self.__trade2pos(ix, trade)
            self.trade_scatter.addPoints([scatter])

    def update_orders(self, orders: list):
        for o in orders:
            self.update_order(o)

    def __trade2scatter(self, ix, trade: TradeData):
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

        return scatter

    def __trade2pos(self, ix, trade: TradeData):
        if trade.direction == Direction.LONG:
            p = trade.volume
            v = trade.volume * trade.price
        else:
            p = -trade.volume
            v = -trade.volume * trade.price
        self.ix_pos_map[ix] = (self.ix_pos_map[ix][0] + p, self.ix_pos_map[ix][1] + v)


    def update_order(self, order: OrderData):
        if order.status in (Status.NOTTRADED, Status.PARTTRADED):
            line = self.order_lines[order.vt_orderid]
            candle_plot = self.get_plot("candle")

            if line not in candle_plot.items:
                candle_plot.addItem(line)
            line.setPos(order.price)
            line.setAngle(0)
            line.setPen(pg.mkPen(color=UP_COLOR if order.direction == Direction.LONG else DOWN_COLOR, width=PEN_WIDTH))
            line.setHoverPen(pg.mkPen(color=UP_COLOR if order.direction == Direction.LONG else DOWN_COLOR, width=PEN_WIDTH * 2))
            line.label = pg.InfLineLabel(line,
                                         text=f'{order.type.value}:{"↑" if order.direction == Direction.LONG else "↓"}{order.volume - order.traded}@{order.price}',
                                         color='r' if order.direction == Direction.LONG else 'g')

        elif order.status in (Status.ALLTRADED, Status.CANCELLED, Status.REJECTED):
            if order.vt_orderid in self.order_lines:
                line = self.order_lines[order.vt_orderid]
                candle_plot = self.get_plot("candle")
                candle_plot.removeItem(line)

    def update_tick_line(self, tick: TickData):
        c = tick.last_price
        o = self.bar.close_price if self.bar else c
        self.last_tick_line.setPos(c)
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

    def clear_all(self) -> None:
        """"""
        super().clear_all()
        self.vt_symbol = None
        self.dt_ix_map.clear()
        self.last_ix = 0
        self.trade_scatter.clear()
        self.trades = defaultdict(list)
        self.ix_pos_map = defaultdict(lambda :(0, 0))

        candle_plot = self.get_plot("candle")
        for _, l in self.order_lines.items():
            candle_plot.removeItem(l)

        self.order_lines.clear()

        self.last_tick_line.setPos(0)