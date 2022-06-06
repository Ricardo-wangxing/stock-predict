
config = {
    'f_params': {
        #成分股接口适用
        '实时股价': 'f2',
        '实时涨跌幅': 'f3',
        '实时涨跌额': 'f4',
        '实时成交量（手）': 'f5', 
        '实时成交额': 'f6', 
        '实时振幅': 'f7', 
        '实时换手率': 'f8', 
        '实时市盈率': 'f9', 
        '股票代码': 'f12', 
        '股票所在市场': 'f13', 
        '股票中文名': 'f14', 
        '实时最高': 'f15', 
        '实时最低': 'f16', 
        '今开': 'f17', 
        '昨收': 'f18', 
        '上市时间':'f26',
        #k线接口适用
        '日期':'f51',
        '开盘价': 'f52', 
        '收盘价': 'f53', 
        '最高价': 'f54', 
        '最低价': 'f55', 
        '成交量': 'f56',
        '成交额': 'f57', 
        '振幅': 'f58', 
        '涨跌幅': 'f59', 
        '涨跌额': 'f60', 
        '换手率': 'f61'},
    'db_user':'root',
    'db_password':'123456',
    'jqdata_user':'',
    'jqdata_password':'',
    'RABBITMQ_HOST':'',
    'RABBITMQ_PORT':'5672',
    'RABBITMQ_QUEUE':'downloader',
    'routing_key':'downloader',
    'default_db':'stock_info',
    "policy_stock_pool":[
        '159915.XSHE', # 易方达创业板ETF
        '510300.XSHG', # 华泰柏瑞沪深300ETF
        '510500.XSHG', # 南方中证500ETF
    ],
    "base":"000300.XSHG" #沪深300指数作为基准
    }
