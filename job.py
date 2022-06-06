#-*- coding:utf-8 -*-
import time
from matplotlib.pyplot import close
import numpy as np
import math
import requests
import json
from datetime import timedelta,datetime
from sendmail import mail
from stock_predict.stock_spider.config import config
import stock_predict.stock_spider.util as ut
from stock_predict.stock_spider.db import *
from publisher import publish_daily_update_etf

stock_pool = config["policy_stock_pool"]

# 动量轮动参数
stock_num = 1           # 买入评分最高的前 stock_num 只股票
momentum_day = 30       # 最新动量参考最近 momentum_day 的

ref_stock = '000300.XSHG' #用 ref_stock 做择时计算的基础数据
N = 18 # 计算最新斜率 slope，拟合度 r2 参考最近 N 天
M = 600 # 计算最新标准分 zscore，rsrs_score 参考最近 M 天
score_threshold = 0.7 # rsrs 标准分指标阈值
# ma 择时参数
mean_day = 20 # 计算结束 ma 收盘价，参考最近 mean_day
mean_diff_day = 3 # 计算初始 ma 收盘价，参考(mean_day + mean_diff_day)天前，窗口为 mean_diff_day 的一段时间


run_today_day = 1
day = 1

send_info = []

# 0-0 预测模块-使用人工智能模型对股价做出预测，指导投资
def predict(history,code,predict_type=''):
    base_url = "http://49.233.19.128:8080/index/"
    post_data = {
        "history_list":history,
        "stock_code":code,
        "predict_type":predict_type
    }
    #print(post_data)
    res = requests.post("http://49.233.19.128:8080/index/",data=post_data)
    #print(res.content.decode())
    d = json.loads(res.content.decode())
    return float(d["predict_value"])
    

# 1-1 选股模块-动量因子轮动
# 基于股票年化收益和判定系数打分,并按照分数从大到小排名
def get_rank(stock_pool, day):
    score_list = []
    global send_info
    for stock in stock_pool:
        current_dt = time.strftime("%Y-%m-%d", time.localtime())
        current_dt = datetime.strptime(current_dt, '%Y-%m-%d')
        previous_date  = current_dt - timedelta(days = day)
        data = ut.get_price(stock, end_date = previous_date, count = momentum_day, fields=['close'])
        close_price = [float('%.3f' % float(x)) for x in list(data.close)]
        # begin 预测代码
        pre_value = predict(close_price,stock)
        close_price.append(pre_value)
        close_price = close_price[-30:]
        print("[动量因子]今日预测值：{}".format(pre_value))
        # end 预测代码
        # 收盘价
        y = data['log'] = np.log(close_price)    # np.log 求对数
        # 分析的数据个数（天）
        x = data['num'] = np.arange(data.log.size)
        # 拟合 1 次多项式
        # y = kx + b, slope 为斜率 k，intercept 为截距 b
        slope, intercept = np.polyfit(x, y, 1)
        # (e ^ slope) ^ 250 - 1
        annualized_returns = math.pow(math.exp(slope), 250) - 1     # annualized_returns：年化收益率
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        score = annualized_returns * r_squared
        score_list.append(score)
    stock_dict = dict(zip(stock_pool, score_list))
    sort_list = sorted(stock_dict.items(), key = lambda item:item[1], reverse = True)
    print("#" * 30 + "候选" + "#" * 30)
    for stock in sort_list:
        stock_code = stock[0]
        stock_score = stock[1]
        security_info = ut.get_security_info(stock_code)
        stock_name = security_info.display_name
        send_info.append('{}({}):{}'.format(stock_name, stock_code, stock_score))
        print('{}({}):{}'.format(stock_name, stock_code, stock_score))
    print('#' * 64)
    code_list = []
    for i in range((len(stock_pool))):
        code_list.append(sort_list[i][0])
    rank_stock = code_list[0:stock_num]
    return rank_stock

# 2-1 择时模块-计算线性回归统计值
# 对输入的自变量每日最低价 x(series) 和因变量每日最高价 y(series) 建立 OLS 回归模型,返回元组(截距,斜率,拟合度)
# R2 统计学线性回归决定系数，也叫判定系数，拟合优度。
# R2 范围 0 ~ 1，拟合优度越大，自变量对因变量的解释程度越高，越接近 1 越好。
# 公式说明： https://blog.csdn.net/snowdroptulip/article/details/79022532
#           https://www.cnblogs.com/aviator999/p/10049646.html
def get_ols(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r2 = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
    return (intercept, slope, r2)

# 2-2 择时模块-设定初始斜率序列
# 通过前 M 日最高最低价的线性回归计算初始的斜率,返回斜率的列表
def initial_slope_series():
    current_dt = time.strftime("%Y-%m-%d", time.localtime())
    current_dt = datetime.strptime(current_dt, '%Y-%m-%d')
    previous_date  = current_dt - timedelta(days = day)
    data = ut.get_price(ref_stock, end_date = previous_date, count = N + M, fields=['high', 'low'])
    return [get_ols(data.low[i:i+N], data.high[i:i+N])[1] for i in range(M)]

# 2-3 择时模块-计算标准分
# 通过斜率列表计算并返回截至回测结束日的最新标准分
def get_zscore(slope_series):
    mean = np.mean(slope_series)
    std = np.std(slope_series)
    return (slope_series[-1] - mean) / std

# 2-4 择时模块-计算综合信号
# 1.获得 rsrs 与 MA 信号,rsrs 信号算法参考优化说明，MA 信号为一段时间两个端点的 MA 数值比较大小
# 2.信号同时为 True 时返回买入信号，同为 False 时返回卖出信号，其余情况返回持仓不变信号
# 解释：
#       MA 信号：MA 指标是英文(Moving average)的简写，叫移动平均线指标。
#       RSRS 择时信号：
#               https://www.joinquant.com/view/community/detail/32b60d05f16c7d719d7fb836687504d6?type=1
def get_timing_signal(stock):
    # 计算 MA 信号
    current_dt = time.strftime("%Y-%m-%d", time.localtime())
    current_dt = datetime.strptime(current_dt, '%Y-%m-%d')
    previous_date  = current_dt - timedelta(days = day)
    print(previous_date)
    # 预测代码
    close_data = ut.get_price(ref_stock, end_date = previous_date, count = mean_day + mean_diff_day, fields = ['close'])
    print(close_data)
    close_price = [float('%.3f' % float(x)) for x in list(close_data.close)]
    close_pre = predict(close_price,ref_stock,'close')
    print(close_price)
    print("[MA]今日预测值： close {}".format(close_pre))
    close_price.append(close_pre)
    close_price = np.array(close_price[-(mean_day + mean_diff_day):])
    today_MA = close_price[mean_diff_day:].mean()
    before_MA = close_price[:mean_diff_day].mean()

    # 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1，23 天，要后 20 天
    # today_MA = close_data.close[mean_diff_day:].mean()
    # # 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0，23 天，要前 20 天
    # before_MA = close_data.close[:-mean_diff_day].mean()
    # 计算 rsrs 信号
    high_low_data = ut.get_price(ref_stock, end_date = previous_date, count = N, fields = ['high', 'low'])
    intercept, slope, r2 = get_ols(high_low_data.low, high_low_data.high)
    slope_series.append(slope)
    rsrs_score = get_zscore(slope_series[-M:]) * r2   # 取最近600天的斜率时间序列
    # 综合判断所有信号
    if rsrs_score > score_threshold and today_MA > before_MA:
        return "BUY"
    elif rsrs_score < -score_threshold and today_MA < before_MA:
        return "SELL"
    else:
        return "KEEP"

slope_series = initial_slope_series()[:-1] # 除去回测第一天的 slope ，避免运行时重复加入


def run_today():
    policy_stock_pool = list(stock_pool).copy()
    policy_stock_pool.append(config['base'])
    #print(policy_stock_pool)
    etf_increment_update(policy_stock_pool)
    current_dt = time.strftime("%Y-%m-%d", time.localtime())
    current_dt = datetime.strptime(current_dt, '%Y-%m-%d')
    message = ""
    check_out_list = get_rank(stock_pool, run_today_day)
    for each_check_out in check_out_list:
        security_info = ut.get_security_info(each_check_out)
        stock_name = security_info.display_name
        stock_code = each_check_out
        # print('今日自选股:{}({})'.format(stock_name, stock_code))
    #获取综合择时信号
    timing_signal = get_timing_signal(ref_stock)
    if timing_signal == 'SELL':
        message = '清仓！卖卖卖！'
        # print('今日择时信号:{}'.format(timing_signal))
    else:
        message = "今日自选股:{}({})".format(stock_name, stock_code)
        # print('今日自选股:{}({})'.format(stock_name, stock_code))
    print(message)
    # print('*' * 100)
    message += "\r\n\r\n"
    message += "*" * 20 + "备选股" + "*" * 20
    message += "\r\n\r\n"
    message += "\r\n\r\n".join(send_info)
    ret = 0
    for _ in range(10):
        if ret:
            # 邮件发送成功推出
            break
        else:
            # 没有发送成功或失败继续
            ret = mail(message)
            time.sleep(1)

if __name__ == "__main__":
    run_today()