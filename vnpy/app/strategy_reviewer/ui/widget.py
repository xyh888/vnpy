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
from vnpy.trader.constant import Interval, Direction
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
        # self.query_btn = QtWidgets.QPushButton("查询")
        self.skip_checkbox = QtWidgets.QCheckBox('AutoSkip')
        self.skip_checkbox.setToolTip('自动过滤未平仓订单')
        self.skip_checkbox.clicked.connect(lambda : self.update_strategy_data(self.skip_checkbox.checkState()))
        self.datetime_from.editingFinished.connect(lambda : self.update_strategy_data(self.skip_checkbox.checkState()))
        self.datetime_to.editingFinished.connect(lambda: self.update_strategy_data(self.skip_checkbox.checkState()))
        # self.query_btn.clicked.connect(self.update_strategy_data)

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
        time_hbox.addWidget(self.skip_checkbox, 1)
        # time_hbox.addWidget(self.query_btn, 1)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(time_hbox)
        vbox.addWidget(self.tab)
        self.setLayout(vbox)

        self.update_strategy_data(False)

    def clear_data(self):
        """"""
        self.updated = False
        self.strategy_monitor.setRowCount(0)

    def update_strategy_data(self, skip):
        self.strategy_monitor.clearContents()
        self.strategy_monitor.setRowCount(0)
        self.strategies = self.calc(skip)
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

    def update_data(self, data: dict):
        """"""
        self.updated = True

        # data.reverse()
        for n, s in data.items():
            self.strategy_monitor.insert_new_row(s)

    def is_updated(self):
        """"""
        return self.updated

    def calc(self, skip):
        strategies = database_manager.get_all_strategy()
        class strategy:
            def __init__(self, name, datas, auto_skip_daily_opentrade=False):
                self.name = name
                self.raw_data = datas
                self._skip = auto_skip_daily_opentrade
                self.raw_data.sort(key=lambda d: d.time)
                self.datas = defaultdict(lambda :defaultdict(list))
                self.init_data(auto_skip_daily_opentrade)


            def init_data(self, skip):
                for d in self.raw_data:
                    self.datas[d.vt_symbol][d.time.date()].append(d)

                if skip:
                    for symbol, trades_groupby_date in self.datas.items():
                        for date in list(trades_groupby_date.keys()):
                            trades = trades_groupby_date[date]
                            daily_pos = 0
                            daily_value = 0
                            for t in trades:
                                if t.direction == Direction.LONG:
                                    daily_pos += t.volume
                                    daily_value += t.price * t.volume
                                else:
                                    daily_pos -= t.volume
                                    daily_value -= t.price * t.volume
                            else:
                                if daily_pos != 0:
                                    tls=trades_groupby_date.pop(date)

                                    for t in tls:
                                        self.raw_data.remove(t)

            @property
            def start_datetime(self):
                if len(self.raw_data) == 0:
                    return

                return self.raw_data[0].time

            @property
            def end_datetime(self):
                if len(self.raw_data) == 0:
                    return

                return self.raw_data[-1].time

            @property
            def trade_count(self):
                return len(self.raw_data)

            @property
            def cost(self):
                all_cost = []
                for vt_symbol, daily_trades in self.datas.items():
                    net_pos = 0
                    net_value = 0
                    for date, tl in daily_trades.items():
                        daily_pos = 0
                        daily_value = 0
                        for t in tl:
                            if t.direction == Direction.SHORT:
                                daily_pos -= t.volume
                                daily_value -= t.volume * t.price
                            else:
                                daily_pos += t.volume
                                daily_value += t.volume * t.price
                        else:
                            net_pos += daily_pos
                            net_value += daily_value
                    else:
                        all_cost.append(f'#<{vt_symbol}>:{net_pos}@{net_value/net_pos if net_pos != 0 else net_value:.1f}  ')

                return '\n'.join(all_cost)

        strategy_dict = {}
        start = self.datetime_from.dateTime().toPyDateTime()
        end = self.datetime_to.dateTime().toPyDateTime()
        all_datas = []
        for n in strategies:
            datas = database_manager.load_trade_data(start, end, strategy=n)
            if datas:
                s = strategy(n, datas, skip)
                all_datas.extend(s.raw_data)
                strategy_dict[n] = s
        else:
            # datas = database_manager.load_trade_data(start, end)
            s = strategy('TOTAL', all_datas, skip)
            strategy_dict['TOTAL'] = s

        return strategy_dict

    def show_trade_chart(self, row, column):
        self.trade.clear_all()
        strategy_name = self.strategy_monitor.item(row, 0).text()
        # if strategy_name == 'TOTAL':
        #     strategy_name=None
        strategy = self.strategies[strategy_name]

        self.trade.update_trades(strategy.raw_data, strategy_name)
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
    def __init__(self, main_engine, event_engine, skip_opentrade=False):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.history_data = None
        self._skip = skip_opentrade
        self.strategy = ""
        self.trade_datas = defaultdict(list)
        self.available_tradeid = set()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("策略交易明细")
        self.resize(900, 600)

        self.tradeChart = TradeMonitor(self.main_engine, self.event_engine)
        self.cost_text = QtWidgets.QTextEdit()
        self.candleChart = CandleChartDialog(self.main_engine, self.event_engine)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tradeChart)
        vbox.addWidget(self.cost_text)
        vbox.setStretchFactor(self.tradeChart, 8)
        vbox.setStretchFactor(self.cost_text, 2)
        self.setLayout(vbox)

        self.tradeChart.cellDoubleClicked.connect(self.show_candle_chart)
        self.tradeChart.cellClicked.connect(self.check_tradeid)

    # def update_trades(self, start, end, strategy=None):
    #     trade_data = database_manager.load_trade_data(start, end, strategy=strategy)
    #     self.strategy = strategy
    #     self.available_tradeid = set()
    #     for t in trade_data:
    #         self.trade_data[t.tradeid] = t
    #         self.tradeChart.insert_new_row(t)
    #         self.available_tradeid.add(t.tradeid)
    #
    #     self.show_cost()

    def update_trades(self, trade_datas, strategy):
        self.strategy = strategy
        self.available_tradeid = set()
        for t in trade_datas:
            self.trade_datas[t.tradeid] = t
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
            t = self.trade_datas[t_id]
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
        self.trade_datas = {}
        self.tradeChart.clearContents()

    def show_candle_chart(self, row, column):
        self.candleChart.clear_all()
        tradeid = self.tradeChart.item(row, 0).text()
        symbol = self.trade_datas[tradeid].symbol
        exchange = self.trade_datas[tradeid].exchange
        trade_datas = [t for t in self.trade_datas.values() if t.symbol == symbol and t.exchange == exchange]
        trade_datas.sort(key=lambda t:t.time)
        time = self.trade_datas[tradeid].time
        start = time.replace(hour=0, minute=0, second=0) - dt.timedelta(minutes=120)
        # end = min(time.replace(hour=23, minute=59, second=59) + dt.timedelta(minutes=120),
        #           dt.datetime.now())

        self.candleChart.update_all(symbol, exchange, trade_datas, start)

        self.candleChart.show()


class CandleChartDialog(QtWidgets.QDialog):
    def __init__(self,  main_engine, event_engine,):
        """"""
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.last_end = dt.datetime(1970, 1, 1)
        self._interval = Interval.HOUR
        self._symbol = None
        self._exchange = None
        self._start = None
        self._end = None
        self.trade_datas = []
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

        self.interval_combo = QtWidgets.QComboBox()
        for i in Interval:
            self.interval_combo.addItem(i.value, i)
        self.interval_combo.setCurrentText(Interval.HOUR.value)

        self.forward_btn = QtWidgets.QPushButton('←')

        self.interval_combo.currentIndexChanged.connect(self.change_interval)
        self.forward_btn.clicked.connect(self.forward)
        self.chart.signal_new_bar_request.connect(self.update_backward_bars)

        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.indicator_combo)
        vbox.addWidget(self.interval_combo)
        vbox.addWidget(self.forward_btn)
        vbox.addWidget(self.chart)
        self.setLayout(vbox)

    def change_interval(self, interval):
        old_tp = self.interval2timdelta(self._interval)
        self._interval = self.interval_combo.itemData(interval)
        new_tp = self.interval2timdelta(self._interval)
        symbol = self._symbol
        exchange = self._exchange
        trade_datas = self.trade_datas
        if new_tp > old_tp:
            start = self._start
            end = self._end
        else:
            cur_bar = self.chart._manager.get_bar(self.chart._cursor._x)
            start = cur_bar.datetime
            end=None

        self.clear_all()
        self.update_all(symbol, exchange, trade_datas, start, end)

    def update_all(self, symbol, exchange, trade_datas, start, end=None):
        self._symbol = symbol
        self._exchange = exchange
        self._start = start
        interval = self._interval
        tp = self.interval2timdelta(self._interval)

        backward_n = max(60 * tp, dt.timedelta(hours=25))
        end = start + backward_n if end is None else end
        history_data = database_manager.load_bar_data(symbol, exchange, interval, start=start, end=end)
        self.trade_datas = trade_datas

        if len(history_data) > 0 and len(history_data)/ ((end - start).total_seconds() / 60) > 0.7:
            self.chart.update_all(history_data, trade_datas, [])
        else:
            req = HistoryRequest(symbol, exchange, start, end, interval)
            gateway = self.main_engine.get_gateway('IB')
            if gateway and gateway.api.status:
                self.history_data = history_data = gateway.query_history(req)
                self.chart.update_all(history_data, trade_datas, [])
            database_manager.save_bar_data(history_data)

        if len(self.history_data) >0:
            self._end = self.history_data[-1].datetime

    def forward(self):
        start = self._start
        symbol = self._symbol
        exchange = self._exchange
        interval = self._interval
        end = self._end

        if all([symbol, exchange, interval, start, end]):
            tp = self.interval2timdelta(interval)
            forward_n = max(60 * tp, dt.timedelta(hours=25))
            self._start = start - forward_n
            self.chart.clear_all()
            self.update_all(symbol, exchange, self.trade_datas, self._start, end)

    def clear_all(self):
        self._symbol = None
        self._exchange = None
        self._start = None
        self._end = None
        self.trade_datas = []
        self.chart.clear_all()

    def update_backward_bars(self, n):
        chart = self.chart
        last_bar = chart._manager.get_bar(chart.last_ix)
        if last_bar:
            symbol = last_bar.symbol
            exchange = last_bar.exchange
            if self._end:
                start = max(last_bar.datetime, self._end)
            else:
                start = last_bar.datetime


            if start >= dt.datetime.now():
                return

            tp = self.interval2timdelta(self._interval)
            backward_n = max(tp * n, dt.timedelta(minutes=60))
            end = start + backward_n
            if not self.checkTradeTime(end.time()):
                history_data = database_manager.load_bar_data(symbol, exchange, self._interval, start=start, end=end)

                if len(history_data) == 0 or len(history_data) / ((end - start).total_seconds() / 60) < 0.7:
                    req = HistoryRequest(symbol, exchange, start, end, self._interval)
                    gateway = self.main_engine.get_gateway('IB')
                    if gateway and gateway.api.status:
                        history_data = gateway.query_history(req)
                    database_manager.save_bar_data(history_data)

                for bar in history_data:
                    self.chart.update_bar(bar)

            self._end = end

    @staticmethod
    def checkTradeTime(t):
        TRADINGHOURS = [(dt.time(3, 0), dt.time(9, 15)),
                        (dt.time(12, 0), dt.time(13, 0)),
                        (dt.time(16, 30), dt.time(17, 15))]
        for tp in TRADINGHOURS:
            if tp[0] <= t < tp[1]:
                return True

        return False

    @staticmethod
    def interval2timdelta(interval):
        return {Interval.MINUTE: dt.timedelta(minutes=1), Interval.HOUR: dt.timedelta(hours=1),
                  Interval.DAILY: dt.timedelta(days=1), Interval.WEEKLY: dt.timedelta(weeks=1)}[interval]

    # def update_all(self, history, trades, orders):
    #     self.chart.update_all(history, trades, orders)


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

