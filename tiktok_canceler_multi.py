import pandas as pd
import datetime
import os
import json
from queue import Queue
from quote_data_manager import QuoteDataManager
from trade_manager import TradeManager
import logging
from time import sleep

amt_threshold = 1000 * 10000
qty_threshold = 100 * 10000
buy1_ratio_threshold = 0.28


def __cal_time_delta(start, end) -> float:
    if not isinstance(start, int):
        start = int(start)
    if not isinstance(end, int):
        end = int(end)
    if start > 120000000:
        start = start - 17000000
    if end > 120000000:
        end = end - 17000000
    start_str = str(start)
    end_str = str(end)
    time_delta = (int(end_str[:~6]) - int(start_str[:~6])) * 3600000 + \
                 (int(end_str[~6:~4]) - int(start_str[~6:~4])) * 60000 + \
                 (int(end_str[~4:~2]) - int(start_str[~4:~2])) * 1000 + \
                 (int(end_str[~2:]) - int(start_str[~2:]))
    time_delta = time_delta / 1000 / 60
    return time_delta


def __qty_filter(qty_input: int) -> int:
    """股票数量，过滤至整百"""
    if qty_input < 100:
        ans = 0
    else:
        ans = int(divmod(qty_input, 100)[0] * 100)
    return ans


if __name__ == "__main__":
    with open(f"config_ttc.json", "r") as file:
        json_para = json.load(file)

    today = datetime.date.today().strftime('%Y%m%d')
    logging.basicConfig(filename=f"log_{today}.log", filemode="w",
                        format="%(asctime)s.%(msecs)03d %(name)s:%(levelname)s:%(message)s",
                        datefmt="%Y%m%d %H:%M:%S", level=logging.DEBUG)

    if today != str(json_para["trade_date"]):
        logging.info(f"ERROR: trade_date of config_ttc.json {json_para['trade_date']} != today {today}")
        exit()

    # 行情队列
    quote_queue = Queue()
    # 登录行情模块
    quote_manager = QuoteDataManager(quote_queue)

    # 登录交易模块
    trade_manager = TradeManager(json_para)
    logging.info("Try to log in trader_api")
    trade_manager.log_in_trader()
    trade_manager.run_process_trade_queue()

    stock_start_time = {}  # key为股票代码，初始值为0
    stock_qty_acc0 = {}  # key为股票代码，初始值从csv中读到，是acc0 （也就是本机）委托的数量
    stock_qty = {}  # key为股票代码，在stock_qty_acc0的基础上，加上其他账户的相同股票的委托数
    stock_price = {}  # key为股票代码，初始值根据csv中读到
    tiktok_orders_dic = {}  # key为股票代码，值为委托的内容

    # 每次while循环时重置pending_list, 如果读取到csv文件且有必要订阅行情, 就会放到pending_list中;
    # 为了减少不必要的行情订阅, 在检测pending_list之前会sleep 2秒, 根据未成交量和未成交金额是否真的需要订阅行情;
    # 如需要订阅行情，则订阅之并把股票加到subscription_list中
    subscription_list = []  # 订阅快照的股票列表

    tiktok_order_csv_dir = f'/home/zjtd/Insert_Trade_Info/'

    while True:
        pending_list = []

        tiktok_csv_files = os.listdir(tiktok_order_csv_dir)
        stock_list = [x[13:19] for x in tiktok_csv_files if x.endswith('.csv') and x[23:31] == today and
                      os.path.getsize(f'{tiktok_order_csv_dir}/{x}') > 0]
        new_stock_list = set(stock_list) - set(stock_qty)
        if len(new_stock_list) > 0:
            for stock in new_stock_list:
                logging.info(f"{stock} order loaded")
                if stock[0] == '6':
                    file_name = f'tiktok_order_{stock}.SH_{today}.csv'
                else:
                    file_name = f'tiktok_order_{stock}.SZ_{today}.csv'
                tiktok_order_df = pd.read_csv(f'{tiktok_order_csv_dir}/{file_name}', header=None,
                                              names=['session_id', 'xtp_ret_id', 'qty', 'price'],
                                              dtype={'session_id': int, 'xtp_id': int, 'qty': int, 'price': float})
                tiktok_orders_dic[stock] = tiktok_order_df
                stock_qty_acc0[stock] = tiktok_order_df['qty'].sum()
                logging.info(f"acc0 order loaded; stock = {stock}, order_qty_acc0 = {stock_qty_acc0[stock]}")
                flag_acc1 = False
                for t in range(3):
                    sleep(0.5)  # 本机读取到委托后等待一会、待其他账户下单完毕
                    order_other_accounts = trade_manager.get_order_qty_acc1(stock)
                    if order_other_accounts > 0:
                        stock_qty[stock] = stock_qty_acc0[stock] + order_other_accounts
                        flag_acc1 = True
                        logging.info(f"other accounts order loaded; stock = {stock}, qty = {order_other_accounts}")
                        break
                if not flag_acc1:  # 如果没有读取到其他账户的委托信息，那就用json文件中的比例来估算
                    order_other_accounts = __qty_filter(int(stock_qty_acc0[stock] * json_para["qty_acc1_to_acc0"]))
                    logging.info(f"cannot load other accounts' order via trade_manager; using parameter from config;"
                                 f"estimated order qty = {order_other_accounts}")
                    stock_qty[stock] = stock_qty_acc0[stock] + order_other_accounts
                stock_price[stock] = tiktok_order_df['price'].max()
                if stock_qty[stock] < qty_threshold and stock_qty[stock] * stock_price[stock] < amt_threshold:
                    logging.info(f"stock = {stock}, order_amt = {stock_qty[stock] * stock_price[stock]},"
                                 f"order_qty = {stock_qty[stock]}, CASE 0 continue")
                    continue
                else:
                    stock_start_time[stock] = 0
                    pending_list.append(stock)

        if quote_manager.quote_queue.empty():
            sleep(2)

        if len(pending_list) > 0:
            for stock in pending_list:
                traded_qty = trade_manager.get_traded_qty(stock)
                unfilled_qty = stock_qty[stock] - traded_qty
                unfilled_amt = unfilled_qty * stock_price[stock]
                if unfilled_qty < qty_threshold and unfilled_amt < amt_threshold:
                    logging.info(f"stock = {stock}, unfilled_qty = {unfilled_qty}, unfilled_amt = {unfilled_amt},"
                                 f"CASE 1 continue")
                    continue
                else:
                    quote_manager.subscribe_some_stock(stock)
                    logging.info(f"subscribed stock={stock}, unfilled_qty={unfilled_qty}, unfilled_amt={unfilled_amt}")
                    if stock not in subscription_list:
                        subscription_list.append(stock)

        if len(subscription_list) > 0:
            tick_data = quote_manager.quote_queue.get()

            stock = tick_data["ticker"]
            traded_qty = trade_manager.get_traded_qty(stock)
            unfilled_qty = stock_qty[stock] - traded_qty
            unfilled_amt = unfilled_qty * stock_price[stock]
            traded_qty_acc0 = trade_manager.get_traded_qty_acc0(stock)
            unfilled_qty_acc0 = stock_qty_acc0[stock] - traded_qty_acc0
            unfilled_amt_acc0 = unfilled_qty_acc0 * stock_price[stock]
            logging.info(f"tick time={tick_data['data_time']}, stock={stock}, traded_qty={traded_qty},"
                         f"unfilled_qty={unfilled_qty}, unfilled_amt={unfilled_amt}, bid0v={tick_data['bid_v'][0]},"
                         f"unfilled_qty_acc0={unfilled_qty_acc0}, unfilled_amt_acc0={unfilled_amt_acc0}")
            if unfilled_qty < qty_threshold and unfilled_amt < amt_threshold:
                logging.info(f'CASE 2: unsubscribe quote of {stock}')
                quote_manager.unsubscribe_some_stock(stock)
                if stock in subscription_list:
                    subscription_list.remove(stock)
                continue

            if unfilled_qty_acc0 <= 200:
                logging.info(f'CASE 3: unsubscribe quote of {stock}')
                quote_manager.unsubscribe_some_stock(stock)
                if stock in subscription_list:
                    subscription_list.remove(stock)
                continue

            time_now = str(tick_data["data_time"])[8:]
            if 1130 < int(time_now[0:4]) < 1300:
                # 中午时间跳过
                continue

            if int(time_now[0:4]) >= 1457:
                exit()

            if stock_start_time[stock] == 0 or unfilled_qty / tick_data["bid_v"][0] < buy1_ratio_threshold:
                stock_start_time[stock] = time_now
                continue

            if __cal_time_delta(stock_start_time[stock], time_now) > 9:
                while unfilled_qty > qty_threshold or unfilled_amt > amt_threshold:
                    # 根据下单委托，倒序撤单
                    if len(tiktok_orders_dic[stock]) > 0:
                        for order in tiktok_orders_dic[stock][::-1].iterrows():
                            logging.info(f"{stock} to cancel {order[1]['qty']}")
                            trade_manager.cancel_an_order(int(order[1]['xtp_ret_id']), int(order[1]['session_id']))
                            stock_qty[stock] -= int(order[1]['qty'])
                            unfilled_qty = stock_qty[stock] - traded_qty
                            unfilled_amt = unfilled_qty * stock_price[stock]
                            break
                        tiktok_orders_dic[stock] = tiktok_orders_dic[stock].drop(tiktok_orders_dic[stock].index[-1])
                    else:
                        break
                logging.info(f'CASE 4: unsubscribe quote of {stock}')
                quote_manager.unsubscribe_some_stock(stock)
                if stock in subscription_list:
                    subscription_list.remove(stock)
