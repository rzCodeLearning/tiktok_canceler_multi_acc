
from trade_api import *
from queue import Queue
import threading
import pandas as pd


def printFuncName(*args):
    """"""
    print('*' * 50)
    print(args)
    print('*' * 50)


class TradeManager(object):
    def __init__(self, para: dict):
        self.para = para

        self.session_id_0 = None
        self.session_id_1 = None

        self.order_client_id = para["init_order_client_id"]
        self.order_client_id_step = para["order_client_id_step"]

        print("init_order_client_id = ", self.order_client_id)

        self.trade_queue = Queue()
        self.trader_api = TraderApi(self.trade_queue)

        self.traded_qty_all = {}
        self.traded_qty_0 = {}

        self.order_qty_1 = {}

    def log_in_trader(self):
        self.trader_api.createTraderApi(self.para["client_id"], os.getcwd(), 4)
        # 订阅公共流
        # 0: 从本交易日开始重传
        # 1: (保留字段，此方式暂未支持)从上次收到的续传
        # 2: 只传送登录后公共流的内容
        subscribe_public_topic = self.trader_api.subscribePublicTopic(0)
        printFuncName('subscribePublicTopic', subscribe_public_topic)
        self.trader_api.setSoftwareKey(self.para["account_key"])
        self.trader_api.setSoftwareVersion("sell_version1")
        self.session_id_0 = self.trader_api.login(self.para["trade_ip_0"], self.para["trade_port_0"],
                                                  self.para["trade_user_0"], self.para["trade_password_0"], 1,
                                                  self.para["local_ip"])
        # session id不为0表示登录成功，为0则登录失败
        if self.session_id_0 == 0:
            ret_get_api_last_error = self.trader_api.getApiLastError()
            printFuncName('Failed to login the account_0! getApiLastError:', ret_get_api_last_error)
            exit()
        else:
            printFuncName('Trader_api-account_0 successfully logged in; the session id is', self.session_id_0)

        self.session_id_1 = self.trader_api.login(self.para["trade_ip_1"], self.para["trade_port_1"],
                                                  self.para["trade_user_1"], self.para["trade_password_1"], 1,
                                                  self.para["local_ip"])

        if self.session_id_1 == 0:
            ret_get_api_last_error = self.trader_api.getApiLastError()
            printFuncName('Failed to login the account_1! getApiLastError:', ret_get_api_last_error)
            exit()
        else:
            printFuncName('Trader_api-account_1 successfully logged in; the session id is', self.session_id_1)

        ret_get_trading_day = self.trader_api.getTradingDay()
        printFuncName('getTradingDay', ret_get_trading_day)
        ret_get_api_version = self.trader_api.getApiVersion()
        printFuncName('getApiVersion', ret_get_api_version)

    def process_trade_queue(self):
        while True:
            trade_info = self.trade_queue.get()

            if trade_info["type"] == "trade_info":
                if trade_info["side"] == 1:
                    ticker = trade_info["ticker"]
                    if ticker not in self.traded_qty_all:
                        self.traded_qty_all[ticker] = trade_info["quantity"]
                    else:
                        self.traded_qty_all[ticker] += trade_info["quantity"]
                    if trade_info["session"] == self.session_id_0:
                        if ticker not in self.traded_qty_0:
                            self.traded_qty_0[ticker] = trade_info["quantity"]
                        else:
                            self.traded_qty_0[ticker] += trade_info["quantity"]

            if trade_info["type"] == "order_info":
                if trade_info["session"] == self.session_id_1:  # 只处理其他账户的委托
                    ticker = trade_info["ticker"]
                    if ticker not in self.order_qty_1:
                        self.order_qty_1[ticker] = trade_info["quantity"]
                    else:
                        self.order_qty_1[ticker] += trade_info["quantity"]

    def run_process_trade_queue(self):
        run_trade_queue = threading.Thread(target=self.process_trade_queue, args=())
        run_trade_queue.start()

    def cancel_an_order(self, order_xtp_id, session_id):
        print(f'to cancel a tiktok order {order_xtp_id} with session_id {session_id}')
        order_xtp_cancel_id = self.trader_api.cancelOrder(order_xtp_id, session_id)
        if order_xtp_cancel_id == 0:
            print(f'---WARNING: cancel order with xtp_order_id {order_xtp_id} failed')

    def get_traded_qty(self, ticker) -> int:
        if ticker in self.traded_qty_all:
            return self.traded_qty_all.get(ticker)
        else:
            return 0

    def get_traded_qty_acc0(self, ticker) -> int:
        if ticker in self.traded_qty_0:
            return self.traded_qty_0.get(ticker)
        else:
            return 0

    def get_order_qty_acc1(self, ticker) -> int:
        if ticker in self.order_qty_1:
            return self.order_qty_1.get(ticker)
        else:
            return 0
