#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/20 0020 16:50
# @Author  : Hadrianl 
# @File    : widget


from vnpy.chart import ChartWidget, CandleItem, VolumeItem
from vnpy.trader.constant import Direction
from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.ui.widget import BaseMonitor, BaseCell, DirectionCell, EnumCell
from vnpy.trader.database import database_manager
import datetime as dt
from datetime import datetime
import pyqtgraph as pg
from vnpy.trader.engine import MainEngine
from vnpy.event import EventEngine
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Interval
from vnpy.chart.base import BLACK_COLOR, CURSOR_COLOR, NORMAL_FONT
from collections import defaultdict
from ..engine import APP_NAME


class StrategyReviewer(QtWidgets.QWidget):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.review_engine = main_engine.get_engine(APP_NAME)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("策略执行回顾")
        self.resize(1100, 600)

        self.datetime_from = QtWidgets.QDateTimeEdit()
        self.datetime_to = QtWidgets.QDateTimeEdit()
        today = dt.date.today()
        self.datetime_from.setDateTime(dt.datetime(year=today.year, month=today.month, day=today.day))
        self.datetime_to.setDateTime(dt.datetime(year=today.year, month=today.month, day=today.day, hour=23, minute=59))
        self.query_btn = QtWidgets.QPushButton("查询")
        self.query_btn.clicked.connect(self.update_strategy_data)

        self.tab = QtWidgets.QTabWidget()
        self.strategy_monitor = StrategyMonitor(self.main_engine, self.event_engine)
        self.strategy_monitor.cellDoubleClicked.connect(self.show_trade_chart)
        # self.strategy_monitor.cellClicked.connect(self.check_strategies)
        self.strategy_monitor.resize(1000, 600)
        self.tab.addTab(self.strategy_monitor, '策略统计')

        self.trade = TradeChartDialog(self.main_engine, self.event_engine)

        time_hbox = QtWidgets.QHBoxLayout()
        time_hbox.addWidget(self.datetime_from, 3)
        time_hbox.addWidget(self.datetime_to, 3)
        time_hbox.addWidget(self.query_btn, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(time_hbox)
        vbox.addWidget(self.tab)
        self.setLayout(vbox)

        self.update_strategy_data()

    def clear_data(self):
        """"""
        self.updated = False
        self.strategy_monitor.setRowCount(0)

    def update_strategy_data(self):
        self.strategy_monitor.clearContents()
        self.strategy_monitor.setRowCount(0)
        self.strategies = self.calc()
        self.update_data(self.strategies)
        self.strategy_monitor.resize_columns()

    # def check_strategies(self, r, c):
    #     if c == 0:
    #         cell = self.strategy_monitor.item(r, c)
    #         if cell.checkState():
    #             cell.setCheckState(QtCore.Qt.Unchecked)
    #             self.available_strategies.remove(cell.text())
    #         else:
    #             cell.setCheckState(QtCore.Qt.Checked)
    #             self.available_strategies.add(cell.text())

    def update_data(self, data: list):
        """"""
        self.updated = True

        data.reverse()
        for obj in data:
            self.strategy_monitor.insert_new_row(obj)

    def is_updated(self):
        """"""
        return self.updated

    def calc(self):
        strategies = database_manager.get_all_strategy()
        class strategy:
            def __init__(self, name, datas):
                self.name = name
                self.raw_data = datas
                self.raw_data.sort(key=lambda d: d.time)
                self.datas = defaultdict(list)
                for d in self.raw_data:
                    self.datas[d.vt_symbol].append(d)

            @property
            def start_datetime(self):
                return self.raw_data[0].time

            @property
            def end_datetime(self):
                return self.raw_data[-1].time

            @property
            def trade_count(self):
                return len(self.raw_data)

            @property
            def cost(self):
                all_cost = []
                for vt_symbol, trades in self.datas.items():
                    net_pos = 0
                    net_value = 0
                    for t in trades:
                        if t.direction == Direction.SHORT:
                            net_pos -= t.volume
                            net_value -= t.volume * t.price
                        else:
                            net_pos += t.volume
                            net_value += t.volume * t.price
                    else:
                        all_cost.append(f'#<{vt_symbol}>:{net_pos}@{net_value/net_pos if net_pos != 0 else net_value:.1f}  ')

                return '\n'.join(all_cost)

        l = []
        start = self.datetime_from.dateTime().toPyDateTime()
        end = self.datetime_to.dateTime().toPyDateTime()
        for n in strategies:
            datas = database_manager.load_trade_data(start, end, strategy=n)
            if datas:
                s = strategy(n, datas)
                l.append(s)
        else:
            datas = database_manager.load_trade_data(start, end)
            s = strategy('TOTAL', datas)
            l.append(s)

        return l

    def show_trade_chart(self, row, column):
        self.trade.clear_all()
        strategy_name = self.strategy_monitor.item(row, 0).text()
        if strategy_name == 'TOTAL':
            strategy_name=None

        start = self.datetime_from.dateTime().toPyDateTime()
        end = self.datetime_to.dateTime().toPyDateTime()
        self.trade.update_trades(start, end, strategy_name)
        self.trade.show()

class CheckCell(BaseCell):
    def __init__(self, content, data):
        super().__init__(content, data)

    def set_content(self, content, data):
        self.setText(str(content))
        self._data = data
        # if self._data:
        self.setCheckState(QtCore.Qt.Checked)
        # else:
        #     self.setCheckState(QtCore.Qt.Unchecked)

class StrategyMonitor(BaseMonitor):
    sorting = True
    headers = {
        "name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "start_datetime": {"display": "首次交易时间", "cell": BaseCell, "update": False},
        "end_datetime": {"display": "最后交易时间", "cell": BaseCell, "update": False},
        "trade_count": {"display": "交易次数", "cell": BaseCell, "update": False},
        "cost": {"display": "持仓成本", "cell": BaseCell, "update": False},

        # "profit_days": {"display": "盈利交易日", "cell": BaseCell, "update": False},
        # "loss_days": {"display": "亏损交易日", "cell": BaseCell, "update": False},

        # "total_net_pnl": {"display": "总净盈亏", "cell": BaseCell, "update": False},
        # "total_commission": {"display": "总手续", "cell": BaseCell, "update": False},
        # "total_trade_count": {"display": "总盈利次数", "cell": BaseCell, "update": False},

        # "daily_net_pnl": {"display": "日均盈亏", "cell": BaseCell, "update": False},
        # "daily_commission": {"display": "日均手续费", "cell": BaseCell, "update": False},
        # "daily_trade_count": {"display": "日均成交笔数", "cell": BaseCell, "update": False},
    }

class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """
    data_key = 'tradeid'
    sorting = True
    headers = {
        "tradeid": {"display": "成交号 ", "cell": CheckCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        # "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "time": {"display": "时间", "cell": BaseCell, "update": False},
        "strategy": {"display": "策略", "cell": BaseCell, "update": False},
        # "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

from vnpy.app.realtime_monitor.ui.baseQtItems import MarketDataChartWidget
class TradeChartDialog(QtWidgets.QDialog):
    def __init__(self, main_engine, event_engine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.history_data = None
        self.strategy = ""
        self.trade_data = {}
        self.available_tradeid = set()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("策略交易明细")
        self.resize(900, 600)

        self.tradeChart = TradeMonitor(self.main_engine, self.event_engine)
        self.cost_text = QtWidgets.QTextEdit()
        self.candleChart = CandleChartDialog()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tradeChart)
        vbox.addWidget(self.cost_text)
        vbox.setStretchFactor(self.tradeChart, 8)
        vbox.setStretchFactor(self.cost_text, 2)
        self.setLayout(vbox)

        self.tradeChart.cellDoubleClicked.connect(self.show_candle_chart)
        self.tradeChart.cellClicked.connect(self.check_tradeid)
        self.candleChart.chart.signal_new_bar_request.connect(self.update_backwark_bars)

    def update_trades(self, start, end, strategy=None):
        trade_data = database_manager.load_trade_data(start, end, strategy=strategy)
        self.strategy = strategy
        self.available_tradeid = set()
        for t in trade_data:
            self.trade_data[t.tradeid] = t
            self.tradeChart.insert_new_row(t)
            self.available_tradeid.add(t.tradeid)

        self.show_cost()

    def check_tradeid(self, r, c):
        if c == 0:
            cell = self.tradeChart.item(r, c)
            if cell.checkState():
                cell.setCheckState(QtCore.Qt.Unchecked)
                self.available_tradeid.remove(cell.text())
            else:
                cell.setCheckState(QtCore.Qt.Checked)
                self.available_tradeid.add(cell.text())

            self.show_cost()

    def show_cost(self):
        all_cost = defaultdict(lambda: [0, 0, 0])
        for t_id in self.available_tradeid:
            t = self.trade_data[t_id]
            all_cost[t.vt_symbol][2] += 1
            if t.direction == Direction.SHORT:
                all_cost[t.vt_symbol][0] -= t.volume
                all_cost[t.vt_symbol][1] -= t.volume * t.price
            else:
                all_cost[t.vt_symbol][0] += t.volume
                all_cost[t.vt_symbol][1] += t.volume * t.price

        result = '\n'.join([f'#<{s}>:{p[0]}@{p[1] / p[0] if p[0] != 0 else p[1]:.1f} Total:{p[2]}' for s, p in all_cost.items()])
        self.cost_text.setText(result)

    def clear_all(self):
        self.strategy = ""
        self.trade_data = {}
        self.tradeChart.clearContents()

    def show_candle_chart(self, row, column):
        self.candleChart.clear_all()
        tradeid = self.tradeChart.item(row, 0).text()
        symbol = self.trade_data[tradeid].symbol
        exchange = self.trade_data[tradeid].exchange
        trade_data = [t for t in self.trade_data.values() if t.symbol == symbol and t.exchange == exchange]
        trade_data.sort(key=lambda t:t.time)
        time = self.trade_data[tradeid].time
        start = time.replace(hour=0, minute=0, second=0) - dt.timedelta(minutes=120)
        end = min(time.replace(hour=23, minute=59, second=59) + dt.timedelta(minutes=120),
                  dt.datetime.now())

        history_data = database_manager.load_bar_data(symbol, exchange, Interval.MINUTE, start=start, end=end)

        if len(history_data) > 0 and len(history_data)/ ((end - start).total_seconds() / 60) > 0.7:
            self.candleChart.update_all(history_data, trade_data, [])
        else:
            req = HistoryRequest(symbol, exchange, start, end, Interval.MINUTE)
            gateway = self.main_engine.get_gateway('IB')
            if gateway and gateway.api.status:
                self.history_data = history_data = gateway.query_history(req)
                self.candleChart.update_all(history_data, trade_data, [])
            database_manager.save_bar_data(history_data)

        self.candleChart.show()

    def update_backwark_bars(self, n):
        chart = self.candleChart.chart
        last_bar = chart._manager.get_bar(chart.last_ix)
        if last_bar:
            n = min(n, 60)
            symbol = last_bar.symbol
            exchange = last_bar.exchange
            print(last_bar.datetime, self.candleChart.last_end)
            start = max(last_bar.datetime, self.candleChart.last_end)

            if start >= dt.datetime.now():
                return

            end = start + n * dt.timedelta(minutes=1)
            if not self.checkTradeTime(end.time()):
                history_data = database_manager.load_bar_data(symbol, exchange, Interval.MINUTE, start=start, end=end)

                if len(history_data) == 0 or len(history_data) / ((end - start).total_seconds() / 60) < 0.7:
                    req = HistoryRequest(symbol, exchange, start, end, Interval.MINUTE)
                    gateway = self.main_engine.get_gateway('IB')
                    if gateway and gateway.api.status:
                        history_data = gateway.query_history(req)
                    database_manager.save_bar_data(history_data)

                for bar in history_data:
                    self.candleChart.chart.update_bar(bar)

            self.candleChart.last_end = end

    @staticmethod
    def checkTradeTime(t):
        TRADINGHOURS = [(dt.time(3, 0), dt.time(9, 15)),
                        (dt.time(12, 0), dt.time(13, 0)),
                        (dt.time(16, 30), dt.time(17, 15))]
        for tp in TRADINGHOURS:
            if tp[0] <= t < tp[1]:
                return True

        return False


class CandleChartDialog(QtWidgets.QDialog):
    def __init__(self):
        """"""
        super().__init__()
        self.last_end = dt.datetime(1970, 1, 1)
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("策略K线图表")
        self.resize(1400, 800)

        # Create chart widget
        self.chart = MarketDataChartWidget()
        self.indicator_combo = QtWidgets.QComboBox()
        self.indicator_combo.addItems(self.chart.indicators.keys())
        self.indicator_combo.currentTextChanged.connect(self.chart.change_indicator)

        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.indicator_combo)
        vbox.addWidget(self.chart)
        self.setLayout(vbox)

    def clear_all(self):
        self.chart.clear_all()

    def update_all(self, history, trades, orders):
        self.chart.update_all(history, trades, orders)


class DailyResultChart(QtWidgets.QDialog):
    def __init__(self):
        """"""
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("策略K线图表")
        self.resize(1400, 800)

        # Create chart widget
        self.pnlChart = pg.PlotCurveItem()
        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.pnlChart)
        self.setLayout(vbox)

    def clear_all(self):
        self.pnlChart.clear()

    # def update_all(self, history, trades, orders):
    #     self.chart.update_all(history, trades, orders)

