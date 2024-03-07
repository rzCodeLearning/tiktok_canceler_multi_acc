from quote_api import QuoteApi
import json
import os


def printFuncName(*args):
    """"""
    print('*' * 50)
    print(args)
    print('*' * 50)


class QuoteDataManager(object):
    def __init__(self, quote_queue):
        self.api = None
        self.quote_queue = quote_queue
        with open(f"config_ttc.json", "r") as file:
            self.config = json.load(file)
        self.ticker_list_sh = []
        self.ticker_list_sz = []
        self.init_quote_api()

    def init_quote_api(self):
        self.api = QuoteApi(self.quote_queue)
        self.api.createQuoteApi(self.config["client_id"], os.getcwd(), 4)
        self.api.setHeartBeatInterval(2)
        self.api.setUDPBufferSize(256)

        ret_login = self.api.login(self.config["quote_ip"], self.config["quote_port"], self.config["quote_user"],
                                   self.config["quote_password"], self.config["quote_protocol"], self.config["local_ip"])
        if ret_login == 0:
            printFuncName('QuoteApi successfully logged in')
        else:
            print('Failed to log in QuoteApi, and the ret_value of is', ret_login)
            exit()

        get_trading_day = self.api.getTradingDay()
        printFuncName("getTradingDay", get_trading_day)

    def unsubscribe_some_stock(self, ticker):
        if ticker in self.ticker_list_sz:
            ret_unsubscribe_market_data_sz = self.api.unSubscribeMarketData([{'ticker': ticker}], 1, 2)
            printFuncName(ticker, 'unsubscribeMarketData_SZ', ret_unsubscribe_market_data_sz)
        if ticker in self.ticker_list_sh:
            ret_unsubscribe_market_data_sh = self.api.unSubscribeMarketData([{'ticker': ticker}], 1, 1)
            printFuncName(ticker, 'unsubscribeMarketData_SH', ret_unsubscribe_market_data_sh)

    def subscribe_some_stock(self, ticker):
        if ticker[0] == '6':
            ret_subscribe_market_data_sh = self.api.subscribeMarketData([{'ticker': ticker}], 1, 1)
            self.ticker_list_sh.append(ticker)
            printFuncName(ticker, 'subscribeMarketData_SH', ret_subscribe_market_data_sh)
        else:
            ret_subscribe_market_data_sz = self.api.subscribeMarketData([{'ticker': ticker}], 1, 2)
            self.ticker_list_sz.append(ticker)
            printFuncName(ticker, 'subscribeMarketData_SZ', ret_subscribe_market_data_sz)
