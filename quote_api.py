# encoding: UTF-8
import os
from time import sleep
from vnxtpquote import *





def printFuncName(*args):
    """"""
    print('*' * 50)
    print(args)
    print('*' * 50)


class QuoteApi(QuoteApi):

    def __init__(self, quote_queue):
        """Constructor"""
        super(QuoteApi, self).__init__()
        self.quote_queue = quote_queue
        print("QuoteApi initialized")

    # 当客户端与行情后台通信连接断开时，该方法被调用。
    # @param reason 错误原因，请与错误代码表对应
    # @remark api不会自动重连，当断线发生时，请用户自行选择后续操作。可以在此函数中调用Login重新登录。注意用户重新登录后，需要重新订阅行情
    def onDisconnected(self, reason):
        """"""
        printFuncName('onDisconnected', reason)

    # 错误应答
    # @param data 当服务器响应发生错误时的具体的错误代码和错误信息，当data为空，或者data.error_id为0时，表明没有错误
    # @remark 此函数只有在服务器发生错误时才会调用，一般无需用户处理
    def onError(self, data):
        """"""
        printFuncName('onError', data)

    # 订阅行情应答，包括股票、指数和期权
    # @param data 详细的合约订阅情况
    # @param error 订阅合约发生错误时的错误信息，当error为空，或者error.error_id为0时，表明没有错误
    # @param last 是否此次订阅的最后一个应答，当为最后一个的时候为true，如果为false，表示还有其他后续消息响应
    # @remark 每条订阅的合约均对应一条订阅应答，需要快速返回，否则会堵塞后续消息，当堵塞严重时，会触发断线
    def onSubMarketData(self, data, error, last):
        """"""
        if(error['error_id'] !=0 ):
            print("\n")
            print("\n")
            printFuncName('onSubMarketData', data, error)
            print("data['exchange_id']:", data['exchange_id'])  # 交易所代码
            print("data['ticker']:", data['ticker'])  # 合约代码（不包含交易所信息）例如"600000"
            print("error['error_id']):", error['error_id'])
            print("error['error_msg']):", error['error_msg'])
            print("\n")
            print("\n")

    def OnSubOrderBook(self, data, error, last):
        """"""
        printFuncName('OnSubOrderBook', data, error)
        print("data['exchange_id']:", data['exchange_id'])  # 交易所代码
        print("data['ticker']:", data['ticker'])  # 合约代码（不包含交易所信息）例如"600000"
        print("error['error_id']):", error['error_id'])
        print("error['error_msg']):", error['error_msg'])

    # 退订行情应答，包括股票、指数和期权
    # @param data 详细的合约取消订阅情况
    # @param error 取消订阅合约时发生错误时返回的错误信息，当error为空，或者error.error_id为0时，表明没有错误
    # @param last 是否此次取消订阅的最后一个应答，当为最后一个的时候为true，如果为false，表示还有其他后续消息响应
    # @remark 每条取消订阅的合约均对应一条取消订阅应答，需要快速返回，否则会堵塞后续消息，当堵塞严重时，会触发断线
    def onUnSubMarketData(self, data, error, last):
        """"""
        printFuncName('onUnSubMarketData', data, error, last)
        print("data['exchange_id']:", data['exchange_id'])  # 交易所代码
        print("data['ticker']:", data['ticker'])  # 合约代码（不包含交易所信息）例如"600000"
        print("error['error_id']):", error['error_id'])
        print("error['error_msg']):", error['error_msg'])

    # 深度行情通知，包含买一卖一队列
    # @param data 行情数据
    # @param bid1_qty_list 买一队列数据
    # @param bid1_counts 买一队列的有效委托笔数
    # @param max_bid1_count 买一队列总委托笔数
    # @param ask1_qty_list 卖一队列数据
    # @param ask1_count 卖一队列的有效委托笔数
    # @param max_ask1_count 卖一队列总委托笔数
    # @remark 需要快速返回，否则会堵塞后续消息，当堵塞严重时，会触发断线
    def onDepthMarketData(self, data, bid1_qty_list, bid1_counts, max_bid1_count, ask1_qty_list, ask1_count, max_ask1_count):
        """"""
        tick_data = {'data_time': data['data_time'],
                     'ticker': data['ticker'],
                     'ask_p': data['ask'],
                     'ask_v': data['ask_qty'],
                     'bid_p': data['bid'],
                     'bid_v': data['bid_qty'],
                     'high_price': data['high_price'],
                     'low_price': data['low_price'],
                     'upper_limit_price': data['upper_limit_price'],
                     'lower_limit_price': data['lower_limit_price']}
        self.quote_queue.put(tick_data)

    def onSubTickByTick(self, data, error, last):
        """"""
        printFuncName('onSubTickByTick', data, error, last)
        print("data['exchange_id']:",data['exchange_id'])#交易所代码
        print("data['ticker']:",data['ticker'])#合约代码
        print("error['error_id']):",error['error_id'])
        print("error['error_msg']):",error['error_msg'])

    #退订逐笔行情应答，包括股票、指数和期权
    #@param data 详细的合约取消订阅情况
    #@param error 取消订阅合约时发生错误时返回的错误信息，当error为空，或者error.error_id为0时，表明没有错误
    #@param last 是否此次取消订阅的最后一个应答，当为最后一个的时候为true，如果为false，表示还有其他后续消息响应
    #@remark 每条取消订阅的合约均对应一条取消订阅应答，需要快速返回，否则会堵塞后续消息，当堵塞严重时，会触发断线
    def onUnSubTickByTick(self, data, error, last):
        """"""
        printFuncName('onUnSubTickByTick', data, error, last)
        print("data['exchange_id']:",data['exchange_id'])#交易所代码
        print("data['ticker']:",data['ticker'])#合约代码
        print("error['error_id']):",error['error_id'])
        print("error['error_msg']):",error['error_msg'])

    #逐笔行情通知，包括股票、指数和期权
    #@param data 逐笔行情数据，包括逐笔委托和逐笔成交，此为共用结构体，需要根据type来区分是逐笔委托还是逐笔成交，需要快速返回，否则会堵塞后续消息，当堵塞严重时，会触发断线
    def onTickByTick(self, data):
        """"""
        trans_data = {'data_time': data['data_time'],
                      'ticker': data['ticker'],
                      'type': data['type']}
        self.quote_queue.put(trans_data)
