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

        self.table = StrategyMonitor(self.main_engine, self.event_engine)
        self.table.cellDoubleClicked.connect(self.show_trade_chart)
        self.table.setSortingEnabled(True)

        self.trade = TradeChartDialog(self.main_engine, self.event_engine)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.table)

        self.setLayout(vbox)

        self.strategies = self.calc()
        self.update_data(self.strategies)

    def clear_data(self):
        """"""
        self.updated = False
        self.table.setRowCount(0)

    def update_data(self, data: list):
        """"""
        self.updated = True

        data.reverse()
        for obj in data:
            self.table.insert_new_row(obj)

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
            def start_date(self):
                return self.raw_data[0].time

            @property
            def end_date(self):
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
        for n in strategies:
            datas = database_manager.load_trade_data(datetime(2000, 1, 1), datetime.now(), strategy=n)
            s = strategy(n, datas)
            l.append(s)

        return l

    def show_trade_chart(self, row, column):
        self.trade.clear_all()
        strategy_name = self.table.item(row, 0).text()
        self.trade.update_trades(strategy_name)
        self.trade.show()

    # def show_daily_pnl(self, row, column):
    #     strategy_name = self.table.item(row, 0).text()
    #     strategy = self.strategies[strategy_name]
    #     for vt_symbol, datas in strategy.datas.items():
    #         start = datas[0].time
    #         end = datas[-1].time
    #         symbol, exchange = vt_symbol.split('.')
    #         his_data = self.review_engine.get_daily_history(symbol, exchange, start, end)
    #         for bar in his_data:
    #             for trade in datas:
    #             if bar.datetime.date()



class StrategyMonitor(BaseMonitor):
    headers = {
        "name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "start_date": {"display": "首个交易日", "cell": BaseCell, "update": False},
        "end_date": {"display": "最后交易日", "cell": BaseCell, "update": False},
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

class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """
    data_key = 'tradeid'
    sorting = True
    headers = {
        # "check": {"display": "包含", "cell": CheckCell, "update": False},
        "tradeid": {"display": "成交号 ", "cell": CheckCell, "update": False},
        "orderid": {"display": "委托号", "cell": BaseCell, "update": False},
        "symbol": {"display": "代码", "cell": BaseCell, "update": False},
        "exchange": {"display": "交易所", "cell": EnumCell, "update": False},
        "direction": {"display": "方向", "cell": DirectionCell, "update": False},
        "offset": {"display": "开平", "cell": EnumCell, "update": False},
        "price": {"display": "价格", "cell": BaseCell, "update": False},
        "volume": {"display": "数量", "cell": BaseCell, "update": False},
        "time": {"display": "时间", "cell": BaseCell, "update": False},
        "gateway_name": {"display": "接口", "cell": BaseCell, "update": False},
    }

from vnpy.app.realtime_monitor.ui.baseQtItems import MarketDataChartWidget
class TradeChartDialog(QtWidgets.QDialog):
    def __init__(self, main_engine, event_engine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
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

    def update_trades(self, strategy):
        trade_data = database_manager.load_trade_data(datetime(2000, 1, 1), datetime.now(), strategy=strategy)
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
                history_data = gateway.query_history(req)
                self.candleChart.update_all(history_data, trade_data, [])
            database_manager.save_bar_data(history_data)

        self.candleChart.show()


class CandleChartDialog(QtWidgets.QDialog):
    def __init__(self):
        """"""
        super().__init__()
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

