import requests 
import json
from retrying import retry
from lxml import etree
from .config import config

f_params = config["f_params"]

@retry(stop_max_attempt_number=3)
def get_method(url:str)->etree:
    '''
    对网页进行请求，返回一个可以用于xpath语法查询的etree对象
    '''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
        "Cookie": "qgqp_b_id=82327231dd2c0544d1df0af437e5e00e; em_hq_fls=old; em-quote-version=topspeed; emshistory=%5B%22%E4%B8%8A%E8%AF%81300%22%2C%22%E4%B8%8A%E8%AF%81300%E5%9F%BA%E9%87%91%22%5D; intellpositionL=1215.35px; intellpositionT=792.6px; st_si=98696548744226; cowCookie=true; st_asi=delete; HAList=ty-1-000300-%u6CAA%u6DF1300%2Ca-sh-600989-%u5B9D%u4E30%u80FD%u6E90%2Ca-sz-000001-%u5E73%u5B89%u94F6%u884C%2Ca-sz-000063-%u4E2D%u5174%u901A%u8BAF%2Ca-sz-001308-N%u5EB7%u51A0; st_pvi=49113268979202; st_sp=2022-03-18%2019%3A43%3A26; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=63; st_psi=20220427123714698-113200301324-8862990645"
    }
    session = requests.session()
    response = session.get(url, headers=headers, timeout=5)
    html_str = response.content.decode()
    html = etree.HTML(html_str)
    return html

@retry(stop_max_attempt_number=3)
def json_method(url:str):
    '''
    对网页进行请求，json模块将请求内容反序列化后交给上层
    '''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
        "Cookie": "qgqp_b_id=82327231dd2c0544d1df0af437e5e00e; em_hq_fls=old; em-quote-version=topspeed; emshistory=%5B%22%E4%B8%8A%E8%AF%81300%22%2C%22%E4%B8%8A%E8%AF%81300%E5%9F%BA%E9%87%91%22%5D; intellpositionL=1215.35px; intellpositionT=792.6px; st_si=98696548744226; cowCookie=true; st_asi=delete; HAList=ty-1-000300-%u6CAA%u6DF1300%2Ca-sh-600989-%u5B9D%u4E30%u80FD%u6E90%2Ca-sz-000001-%u5E73%u5B89%u94F6%u884C%2Ca-sz-000063-%u4E2D%u5174%u901A%u8BAF%2Ca-sz-001308-N%u5EB7%u51A0; st_pvi=49113268979202; st_sp=2022-03-18%2019%3A43%3A26; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=63; st_psi=20220427123714698-113200301324-8862990645"
    }
    session = requests.session()
    response = session.get(url, headers=headers, timeout=5)
    html_str = response.content.decode()
    return json.loads(html_str)


def stock_histroy_info(code:str,enddate:str,limit=100000):
    '''
    请求某一只股票的历史数据
    code: 股票代码，格式如：1.000300,前缀码1代表沪A,前缀码0代表深A
    enddate: 日期格式应如：20220427，代表查询的最后一个日期
    limit: 从enddate向前查询多少个交易日

    返回的数据结构(以沪深300为例)
    ['日期','开盘价','收盘价','最高价','最低价']
    '''
    kline_api = "http://62.push2his.eastmoney.com/api/qt/stock/kline/get?"
    params = {
        "secid": code,
        "fields1": "f1,f2,f3,f4,f5,f6", #注意，这里的f参数和config里的不一样，不要混用！
        "fields2": "{},{},{},{},{},{},{}".format(f_params['日期'],f_params['开盘价'],f_params['收盘价'],f_params['最高价'],f_params['最低价'],f_params['成交量'],f_params['成交额']),
        "klt": 101, #101代表以每日为频度进行查询。102是每周的最后一个交易日，103是每月的最后一个交易日
        "fqt": 1, # 1代表前复权，2代表后复权，0代表不复权
        "end": enddate,
        "lmt": limit, #默认10w天，表示查询从该股票发行以来的所有交易信息
    }
    for k,v in params.items():
        kline_api += "{}={}&".format(k,v)

    data = json_method(kline_api)["data"]
    return data

def get_hs300_namelist():
    '''
    获取当前沪深300的成分股列表

    返回数据格式
    "data": {
    "total": 300,
    "diff": [
        {
            "f1": 2,
            "f2": 11643,
            "f3": -1000,
            "f4": -1294,
            "f12": "600763",
            "f13": 1,
            "f14": "通策医疗",
            "f152": 2
        }...]
    '''
    clist_api = "http://push2.eastmoney.com/api/qt/clist/get?"
    params = {
        "np":1
        ,"fltt":1
        ,"invt":2
        ,"fs":"b:BK0500+f:!50"
        ,"fields":"{},{},{},{}".format(f_params['上市时间'],f_params["股票中文名"],f_params["股票代码"],f_params["股票所在市场"])
        ,"fid":"f3"
        ,"pn":1
        ,"pz":300
    }
    for k,v in params.items():
        clist_api += "{}={}&".format(k,v)
    
    data = json_method(clist_api)["data"]
    return data["diff"]
