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


class StrategyReviewer(QtWidgets.QWidget):
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
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

        data = self.calc()
        self.update_data(data)

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
                self.datas = datas

        l = []
        for n in strategies:
            datas = database_manager.load_trade_data(datetime(2000, 1, 1), datetime.now(), strategy=n)
            s = strategy(n, datas)
            s.start_date = datas[0].time.date()
            s.end_date = datas[-1].time.date()
            s.profit_days = 0
            s.loss_days = 0
            s.total_net_pnl = 0
            s.total_commission = 0
            s.total_trade_count = 0
            s.daily_net_pnl = 0
            s.daily_commission = 0
            s.daily_trade_count = 0
            l.append(s)

        return l

    def show_trade_chart(self, row, column):
        self.trade.clear_all()
        strategy_name = self.table.item(row, 0).text()
        self.trade.update_trades(strategy_name)

        self.trade.show()

class StrategyMonitor(BaseMonitor):
    headers = {
        "name": {"display": "策略名称", "cell": BaseCell, "update": False},
        "start_date": {"display": "首个交易日", "cell": BaseCell, "update": False},
        "end_date": {"display": "最后交易日", "cell": BaseCell, "update": False},

        "profit_days": {"display": "盈利交易日", "cell": BaseCell, "update": False},
        "loss_days": {"display": "亏损交易日", "cell": BaseCell, "update": False},

        "total_net_pnl": {"display": "总净盈亏", "cell": BaseCell, "update": False},
        "total_commission": {"display": "总手续", "cell": BaseCell, "update": False},
        "total_trade_count": {"display": "总盈利次数", "cell": BaseCell, "update": False},

        "daily_net_pnl": {"display": "日均盈亏", "cell": BaseCell, "update": False},
        "daily_commission": {"display": "日均手续费", "cell": BaseCell, "update": False},
        "daily_trade_count": {"display": "日均成交笔数", "cell": BaseCell, "update": False},
    }

class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """

    headers = {
        "tradeid": {"display": "成交号 ", "cell": BaseCell, "update": False},
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

class TradeChartDialog(QtWidgets.QDialog):
    def __init__(self, main_engine, event_engine):
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.strategy = ""
        self.trade_data = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("策略交易明细")
        self.resize(900, 600)

        self.tradeChart = TradeMonitor(self.main_engine, self.event_engine)
        self.candleChart = CandleChartDialog()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tradeChart)
        self.setLayout(vbox)

        self.tradeChart.cellDoubleClicked.connect(self.show_candle_chart)

    def update_trades(self, strategy):
        trade_data = database_manager.load_trade_data(datetime(2000, 1, 1), datetime.now(), strategy=strategy)
        self.strategy = strategy
        for t in trade_data:
            self.trade_data[t.tradeid] = t
            self.tradeChart.insert_new_row(t)

    def clear_all(self):
        self.strategy = ""
        self.trade_data = {}
        self.tradeChart.clearContents()

    def show_candle_chart(self, row, column):
        self.candleChart.clear_data()
        tradeid = self.tradeChart.item(row, 0).text()
        symbol = self.trade_data[tradeid].symbol
        exchange = self.trade_data[tradeid].exchange
        trade_data = [t for t in self.trade_data.values() if t.symbol == symbol and t.exchange == exchange]
        trade_data.sort(key=lambda t:t.time)
        start = trade_data[0].time.replace(hour=0, minute=0, second=0)
        end = trade_data[-1].time.replace(hour=23, minute=59, second=59)

        req = HistoryRequest(symbol, exchange, start, end, Interval.HOUR)
        gateway = self.main_engine.get_gateway('IB')
        if gateway and gateway.api.status:
            history_data = self.main_engine.get_gateway('IB').query_history(req)
            self.candleChart.update_history(history_data)
            self.candleChart.update_trades(trade_data)

        self.candleChart.show()


class CandleChartDialog(QtWidgets.QDialog):
    def __init__(self):
        """"""
        super().__init__()

        self.dt_ix_map = {}
        self.updated = False
        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("策略K线图表")
        self.resize(1400, 800)

        # Create chart widget
        self.chart = ChartWidget()
        self.chart.add_plot("candle", hide_x_axis=True)
        self.chart.add_plot("volume", maximum_height=200)
        self.chart.add_item(CandleItem, "candle", "candle")
        self.chart.add_item(VolumeItem, "volume", "volume")
        self.chart.add_cursor()

        # Add scatter item for showing tradings
        self.trade_scatter = pg.ScatterPlotItem()
        candle_plot = self.chart.get_plot("candle")
        candle_plot.addItem(self.trade_scatter)

        # Set layout
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.chart)
        self.setLayout(vbox)

    def update_history(self, history: list):
        """"""
        self.updated = True
        self.chart.update_history(history)

        for ix, bar in enumerate(history):
            self.dt_ix_map[bar.datetime] = ix

    def update_trades(self, trades: list):
        """"""
        trade_data = []

        for trade in trades:
            for _time in self.dt_ix_map.keys():
                if dt.timedelta(minutes=0) <= trade.time - _time < dt.timedelta(minutes=60):
                    _time = _time
                    ix = self.dt_ix_map[_time]

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

    def clear_data(self):
        """"""
        self.updated = False
        self.chart.clear_all()

        self.dt_ix_map.clear()
        self.trade_scatter.clear()

    def is_updated(self):
        """"""
        return self.updated