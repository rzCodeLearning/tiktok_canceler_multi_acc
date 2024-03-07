import os
import time
import datetime as dt
from vnxtptrader import *
import logging


def printFuncName(*args):
    """"""
    print('*' * 50)
    print(args)
    print('*' * 50)


class TraderApi(TraderApi):
    def __init__(self, trade_queue):
        super(TraderApi, self).__init__()
        self.trade_queue = trade_queue

    @staticmethod
    def __convert_trade_event_info(data, session) -> dict:
        trade_info = dict()
        trade_info["type"] = "trade_info"
        trade_info["ticker"] = data["ticker"]
        trade_info["order_xtp_id"] = data["order_xtp_id"]
        trade_info["order_client_id"] = data["order_client_id"]
        trade_info["quantity"] = data["quantity"]
        trade_info["trade_amount"] = data["trade_amount"]
        trade_info["price"] = data["price"]
        trade_info["side"] = data["side"]
        trade_info["session"] = session
        return trade_info

    @staticmethod
    def __convert_order_event_info(data, session) -> dict:
        trade_info = dict()
        trade_info["type"] = "order_info"
        trade_info["ticker"] = data["ticker"]
        trade_info["order_xtp_id"] = data["order_xtp_id"]
        trade_info["order_client_id"] = data["order_client_id"]
        trade_info["quantity"] = data["quantity"]
        trade_info["price"] = data["price"]
        trade_info["side"] = data["side"]
        trade_info["session"] = session
        return trade_info

    def onDisconnected(self, session_id, reason):
        printFuncName("onDisconnected", session_id, reason)

    def onCancelOrderError(self, data, error, session):
        printFuncName('onCancelOrderError', data, error, session)

    def onTradeEvent(self, data, session):
        trade_info = self.__convert_trade_event_info(data, session)
        self.trade_queue.put(trade_info)

    def onOrderEvent(self, data, error, session):
        if data['side'] == 1 and data['order_status'] == 4:  # 买入且状态为"已报"的委托
            order_info = self.__convert_order_event_info(data, session)
            self.trade_queue.put(order_info)
