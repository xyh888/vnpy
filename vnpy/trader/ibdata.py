#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/6 0006 15:27
# @Author  : Hadrianl 
# @File    : ibdata



import datetime as dt

from typing import List, Dict

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.gateway.ib import IbGateway
from vnpy.trader.utility import load_json
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import ibapi.common as ibcommon
import ibapi.contract as ibcontract
from queue import Queue, Empty
from threading import Thread
from dateutil import parser
from vnpy.trader.object import SubscribeRequest
from vnpy.gateway.ib.ib_gateway import EXCHANGE_IB2VT, EXCHANGE_VT2IB
# from ibapi.contract import Contract
import re
from vnpy.trader.setting import get_settings



class IBDataClient(EClient, EWrapper):
    """
    Client for querying history data from Interactive Brokers.
    """

    def __init__(self):
        super(IBDataClient, self).__init__(self)
        settings = IbGateway.default_setting
        settings.update(load_json(f'connect_IB.json'))
        self.host = settings['TWS地址']
        self.port = settings['TWS端口']
        self.clientId = settings['客户号'] + 30


        self.inited = False
        self.thread = Thread(target=self.run)
        self.result_queues: Dict[int, Queue] = {}
        self.reqId2subscription = {}
        self.reqId = 1


    def init(self):
        if self.inited:
            return True

        if not self.host or not self.port:
            return False

        self.connect(self.host, self.port, self.clientId)
        self.thread.start()

        self.inited = True
        return True

    def deinit(self):
        if not self.inited:
            return True

        self.disconnect()
        self.thread.join()

        self.inited = False
        return True

    # def error(self, reqId, errorCode:int, errorString:str):
    #     print(reqId, errorCode, errorString)

    def historicalData(self, reqId: int, bar: ibcommon.BarData):
        self.result_queues[reqId].put(bar)

    def historicalDataUpdate(self, reqId: int, bar: BarData):
        self.result_queues[reqId].put(bar)

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.endReq(reqId)

    def contractDetails(self, reqId: int, contractDetails: ibcontract.ContractDetails):
        self.result_queues[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId:int):
        self.endReq(reqId)

    def startReq(self) -> int:
        self.reqId += 1
        self.result_queues[self.reqId] = Queue()
        return self.reqId

    def endReq(self, reqId: int):
        if reqId in self.result_queues and reqId not in self.reqId2subscription:
            q = self.result_queues.pop(reqId)
            q.put(reqId)

        # if reqId in self.reqId2subscription:
        #     subscription = self.reqId2subscription.pop(reqId)
        #     print(f'{subscription[0]}-{subscription[1]}取消订阅')

    def query_bar(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: dt.datetime,
        end: dt.datetime
    ):
        """
        Query bar data from IB.
        """
        if not symbol.isdigit():
            return self._query_bar_from_KRData(symbol, exchange, interval, start, end)

        barSizeSetting = {Interval.MINUTE: '1 min',
                          Interval.HOUR : '1 hour',
                          Interval.DAILY: '1 day',
                          Interval.WEEKLY: '1 week',
                          }[interval]

        if barSizeSetting == '1 week':
            raise ValueError('1 week barSizeSetting is not support!')

        delta = (end - start)
        durationStr = self.timedelta2durationStr(delta)

        endDateTime = end.strftime('%Y%m%d %H:%M:%S')  # yyyymmdd HH:mm:ss

        contract = ibcontract.Contract()
        contract.exchange = exchange.value
        contract.conId = int(symbol)
        symbol_reqId = self.startReq()
        symbol_queue = self.result_queues[symbol_reqId]
        self.reqContractDetails(symbol_reqId, contract)

        data: List[BarData] = []
        try:
            while True:
                contractDetail = symbol_queue.get(timeout=30)
                if isinstance(contract, int):
                    break

                mkdata_reqId = self.startReq()
                mkData_queue = self.result_queues[mkdata_reqId]
                self.reqHistoricalData(self.reqId, contractDetail.contract, endDateTime, durationStr, barSizeSetting, 'TRADES', False, 1, False, None)
                while True:
                    ibBar: ibcommon.BarData = mkData_queue.get(timeout=60*10)
                    if isinstance(ibBar, int):
                        break

                    bar = BarData(
                        symbol=str(contract.conId),
                        exchange=exchange,
                        interval=interval,
                        datetime=parser.parse(ibBar.date),
                        open_price=ibBar.open,
                        high_price=ibBar.high,
                        low_price=ibBar.low,
                        close_price=ibBar.close,
                        volume=ibBar.volume,
                        gateway_name="IB"
                    )
                    data.append(bar)
        except Empty:
            raise ConnectionError('请检查IB配置是否正确或IB ClientId是否被占用')
        except Exception as e:
            raise e
        finally:
            return data

    def query_history(self, req: HistoryRequest):
        """
        Query history bar data from RQData.
        """
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        return self.query_bar(symbol, exchange, interval, start, end)

    def _query_bar_from_KRData(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: dt.datetime,
        end: dt.datetime):

        if interval != Interval.MINUTE:
            print('暂不支持{interval}')

        from KRData.HKData import HKFuture
        db_setting = get_settings('database.')
        if db_setting['driver'] != 'mongodb':
            print('请先设置database为mongodb')
            return []

        hf = HKFuture(db_setting['user'], db_setting['password'], db_setting['host'], db_setting['port'])
        start = dt.datetime.fromordinal(start.toordinal())
        end = dt.datetime.fromordinal(end.toordinal())
        if re.match(r'([A-Z]+)', symbol):
            df = hf.get_main_contract_bars(symbol, start=start, end=end, ktype='1min')
        elif re.match(r'([A-Z]+)(\d{2,})', symbol):
            df = hf.get_bars(symbol, start=start, end=end, ktype='1min')
        else:
            print(f'不支持symbol{symbol}')
            return []

        data: List[BarData] = []
        for d, bar in df.iterrows():
            vt_bar = BarData(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime=d,
                open_price=bar.open,
                high_price=bar.high,
                low_price=bar.low,
                close_price=bar.close,
                volume=bar.volume,
                gateway_name="IB"
            )

            data.append(vt_bar)

        return data


    def subscribe_bar(self, req: SubscribeRequest, interval: Interval, barCount: int):
        """
        Subscribe tick data update.
        """
        # if not self.status:
        #     return

        # if req.vt_symbol in self.reqId2contract.values():
        #     return

        for reqId, subcription in self.reqId2subscription.items():
            if subcription == (req.vt_symbol, interval):
                print(f'{req.vt_symbol}-{interval}已在订阅中')
                return self.result_queues[reqId]

        if req.exchange not in EXCHANGE_VT2IB:
            self.gateway.write_log(f"不支持的交易所{req.exchange}")
            return

        ib_contract = ibcontract.Contract()
        ib_contract.conId = int(req.symbol)
        ib_contract.exchange = req.exchange.value

        # Subscribe tick data and create tick object buffer.

        barSizeSetting = {Interval.MINUTE: '1 min',
                          Interval.HOUR: '1 hour',
                          Interval.DAILY: '1 day',
                          Interval.WEEKLY: '1 week',
                          }[interval]

        if barSizeSetting == '1 week':
            raise ValueError('1 week barSizeSetting is not support!')

        delta = {Interval.MINUTE: dt.timedelta(minutes=1) * barCount,
                          Interval.HOUR: dt.timedelta(hours=1) * barCount,
                          Interval.DAILY: dt.timedelta(days=1) * barCount,
                          Interval.WEEKLY: dt.timedelta(weeks=1) * barCount,
                          }[interval]

        durationStr = self.timedelta2durationStr(delta)

        endDateTime = ''  # yyyymmdd HH:mm:ss  '' mean up to date

        reqId = self.startReq()
        self.reqId2subscription[reqId] = (req.vt_symbol, interval)
        print(reqId, ib_contract, endDateTime, durationStr, barSizeSetting)
        self.reqHistoricalData(reqId, ib_contract, endDateTime, durationStr, barSizeSetting, 'TRADES', False, 1,
                               True, None)

    def unsubscribe_bar(self, req: SubscribeRequest, interval: Interval):
        for reqId, subcription in self.reqId2subscription.items():
            if subcription == (req.vt_symbol, interval):
                self.cancelHistoricalData(reqId)
                self.reqId2subscription.pop(reqId)
                return
            else:
                print(f'{req.vt_symbol}-{interval}不在订阅列表中')

    def subscription2reqId(self, subcription):
        for k, v in self.reqId2subscription.items():
            if subcription == v:
                return k


    @staticmethod
    def timedelta2durationStr(delta: dt.timedelta):
        total_seconds = delta.total_seconds()
        if total_seconds < 86400:
            durationStr = f'{int(total_seconds //60 * 60  + 60)} S'
        elif total_seconds <= 86400 * 30:
            durationStr = f'{int(min(delta.days + 1, 30))} D'
        elif total_seconds < 86400 * 30 * 6:
            durationStr = f'{int(min(delta.days // 30 + 1, 6))} M'
        else:
            durationStr = f'{int(delta.days // (30 * 12) + 1)} Y'

        return durationStr

ibdata_client = IBDataClient()