#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/6 0006 15:27
# @Author  : Hadrianl 
# @File    : ibdata



from datetime import datetime
from typing import List, Dict

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
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
from ibapi.contract import Contract

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
        self.clientId = 20


        self.inited = False
        self.thread = Thread(target=self.run)
        self.data_queues: Dict[int, Queue] = {}
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

    def __del__(self):
        self.disconnect()

    def historicalData(self, reqId: int, bar: ibcommon.BarData):
        self.data_queues[reqId].put(bar)

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.endReq(reqId)

    def contractDetails(self, reqId: int, contractDetails: ibcontract.ContractDetails):
        self.data_queues[reqId].put(contractDetails.contract)

    def contractDetailsEnd(self, reqId:int):
        self.endReq(reqId)

    def startReq(self, reqId: int):
        self.reqId = reqId
        self.data_queues[self.reqId] = Queue()

    def endReq(self, reqId: int):
        q = self.data_queues.pop(reqId)
        q.put(reqId)

    def query_bar(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ):
        """
        Query bar data from IB.
        """
        barSizeSetting = {Interval.MINUTE: '1 min',
                          Interval.HOUR : '1 hour',
                          Interval.DAILY: '1 day',
                          Interval.WEEKLY: '1 week',
                          }[interval]

        if barSizeSetting == '1 week':
            raise ValueError('1 week barSizeSetting is not support!')

        delta = (end - start)
        total_seconds = delta.total_seconds()
        if total_seconds <= 86400:
            durationStr = f'{int(delta.total_seconds() //60 * 60  + 60)} S'
        elif total_seconds <= 86400 * 30:
            durationStr = f'{int(min(delta.days + 1, 30))} D'
        elif total_seconds < 86400 * 30 * 6:
            durationStr = f'{int(min(delta.days // 30 + 1, 6))} M'
        else:
            durationStr = f'{int(delta.days // (30 * 12) + 1)} Y'

        endDateTime = end.strftime('%Y%m%d %H:%M:%S')  # yyyymmdd HH:mm:ss

        contract = ibcontract.Contract()
        contract.exchange = exchange.value
        contract.conId = int(symbol)
        self.reqId += 1
        symbol_reqId = self.reqId
        self.startReq(symbol_reqId)
        symbol_queue = self.data_queues[symbol_reqId]
        self.reqContractDetails(symbol_reqId, contract)

        data: List[BarData] = []
        try:
            while True:
                contract = symbol_queue.get(timeout=30)
                print(contract)
                if isinstance(contract, int):
                    break

                self.reqId += 1
                self.startReq(self.reqId)
                mkData_queue = self.data_queues[self.reqId]
                self.reqHistoricalData(self.reqId, contract, endDateTime, durationStr, barSizeSetting, 'TRADES', False, 1, False, None)
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


    def subscribe_bar(self, req: SubscribeRequest, interval: Interval, barCount: int):
        """
        Subscribe tick data update.
        """
        if not self.status:
            return

        if req.exchange not in EXCHANGE_VT2IB:
            self.gateway.write_log(f"不支持的交易所{req.exchange}")
            return

        ib_contract = Contract()
        ib_contract.conId = str(req.symbol)
        ib_contract.exchange = EXCHANGE_VT2IB[req.exchange]

        # Get contract data from TWS.
        self.reqid += 1
        self.client.reqContractDetails(self.reqid, ib_contract)

        # Subscribe tick data and create tick object buffer.
        self.reqid += 1

        barSizeSetting = {Interval.MINUTE: '1 min',
                          Interval.HOUR: '1 hour',
                          Interval.DAILY: '1 day',
                          Interval.WEEKLY: '1 week',
                          }[interval]

        if barSizeSetting == '1 week':
            raise ValueError('1 week barSizeSetting is not support!')

        total_seconds = {Interval.MINUTE: 60 * barCount,
                          Interval.HOUR: 60 * 60 * barCount,
                          Interval.DAILY: 60 * 60 * 24 * barCount,
                          Interval.WEEKLY: 60 * 60 * 24 * 7 * barCount,
                          }[interval]

        if total_seconds <= 86400:
            durationStr = f'{int(delta.total_seconds() //60 * 60  + 60)} S'
        elif total_seconds <= 86400 * 30:
            durationStr = f'{int(min(delta.days + 1, 30))} D'
        elif total_seconds < 86400 * 30 * 6:
            durationStr = f'{int(min(delta.days // 30 + 1, 6))} M'
        else:
            durationStr = f'{int(delta.days // (30 * 12) + 1)} Y'

        endDateTime = ''  # yyyymmdd HH:mm:ss  '' mean up to date

        self.reqHistoricalData(self.reqId, ib_contract, '', durationStr, barSizeSetting, 'TRADES', False, 1,
                               False, None)


ibdata_client = IBDataClient()