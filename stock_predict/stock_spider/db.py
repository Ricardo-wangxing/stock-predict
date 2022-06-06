
import pymysql
from datetime import date
from tqdm import tqdm
from .config import config
from .spider import *
from loguru import logger
from .util import get_trade_day_num



f_params = config["f_params"]


def write_normal_stock_price_pool(data:list,code,name):
    '''
    将获取到的股价信息写入到数据库中(非沪深300成分)
    需要写入的字段：(code, name, date, open, close, high, low, volume, money)
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    execute_data = []
    for d in data:
        infos = d.split(',')
        date = infos[0]
        open = infos[1]
        close = infos[2]
        high = infos[3]
        low = infos[4]
        volume = infos[5]
        money = infos[6]
        execute_data.append((code,name,date,open,close,high,low,volume,money))
        
    cursor = db.cursor()
    sql = "insert into stock_price_pool(code, name, date, open, close, high, low, volume, money) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    cursor.executemany(sql,execute_data)
    db.commit()    
    db.close()



def write_hs300_stock_price_pool(data:list,code,name):
    '''
    将获取到的股价信息写入到数据库中
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    execute_data = []
    for d in data:
        infos = d.split(',')
        date = infos[0]
        open = infos[1]
        close = infos[2]
        high = infos[3]
        low = infos[4]
        execute_data.append((code,name,date,open,close,high,low))
    cursor = db.cursor()
    sql = "insert into hs300_stock_price_pool(code, name, date, open, close, high, low) values(%s,%s,%s,%s,%s,%s,%s);"
    cursor.executemany(sql,execute_data)
    db.commit()
    db.close()

def write_hs300_details(data):
    '''
    检查沪深300成分股变化情况，如有不同就改变
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    cursor = db.cursor()
    cursor.execute('select code,name,date from hs300_details where is_exist = 1;')
    sql = "insert into hs300_details(code, name, date, is_exist) values(%s,%s,%s,%s);"
    old_data = cursor.fetchall()
    #print(old_data)
    execute_data = []
    if old_data == ():
        # 表中还没有数据，直接将data全部写入
        for d in data:
            date = d[f_params['上市时间']]
            name = d[f_params['股票中文名']]
            area = d[f_params['股票所在市场']]
            code = d[f_params['股票代码']]
            if area == 1:
                code += '.XSHG' # 1代表上海交易所
            else:
                code += '.XSHE' # 0代表深圳交易所
            execute_data.append((code,name,date,1))
    else:
        #提取所有的old_data里的股票代码
        old_data_code = [i[0] for i in old_data]
        #然后遍历新一天的data，判断是否有新增的
        need_update = []    #需要更新的项目（股票代码元组）
        need_insert = []    #需要新增的项目（股票信息字典）

        for i in range(len(data)):
            current_code = data[i][f_params['股票代码']]
            area = data[i][f_params['股票所在市场']]
            if area == 1:
                current_code += '.XSHG' # 1代表上海交易所
            else:
                current_code += '.XSHE' # 0代表深圳交易所
            flag = False
            for j in range(len(old_data_code)):
                if current_code == old_data_code[j]:
                    flag = True
                    old_data_code[j] = ''
                    pass
            if flag is False:
                need_insert.append(data[i])
        for old_code in old_data_code:
            if old_code != '':
                need_update.append((old_code))
        # 将data里还剩余的数据进行写入
        for d in need_insert:
            date = d[f_params['上市时间']]
            name = d[f_params['股票中文名']]
            area = d[f_params['股票所在市场']]
            code = d[f_params['股票代码']]
            if area == 1:
                code += '.XSHG' # 1代表上海交易所
            else:
                code += '.XSHE' # 0代表深圳交易所
            execute_data.append((code,name,date,1))
        
        # 修改已经不在沪深300的名单
        sql_update = "update hs300_details set is_exist=0 where code=%s;"
        cursor.executemany(sql_update,need_update)

    cursor.executemany(sql,execute_data)
    db.commit()
    db.close()

    
def hs300_price_daily_update():
    '''
    将每日的沪深300成分股价格写入hs300_stock_price_pool中
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    def _covert_code(code):
        if code[-5:] == '.XSHG':
            return "1."+code[:-5]
        else:
            return "0."+code[:-5]
    cursor = db.cursor()
    cursor.execute('select * from hs300_details where is_exist=1;')
    hs300_list = cursor.fetchall()
    query_date = str(date.today()).replace('-','')
    for item in tqdm(hs300_list):
        history = stock_histroy_info(_covert_code(item[1]),query_date,1)['klines']
        write_hs300_stock_price_pool(history,item[1],item[2])
    db.close()

def hs300_price_all_update():
    '''
    将当前的沪深300成分股所有历史价格写入hs300_stock_price_pool中
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    def _covert_code(code):
        if code[-5:] == '.XSHG':
            return "1."+code[:-5]
        else:
            return "0."+code[:-5]
    cursor = db.cursor()
    cursor.execute('select * from hs300_details where is_exist=1;')
    hs300_list = cursor.fetchall()
    query_date = str(date.today()).replace('-','')
    for item in tqdm(hs300_list):
        history = stock_histroy_info(_covert_code(item[1]),query_date)['klines']
        write_hs300_stock_price_pool(history,item[1],item[2])
    db.close()

def hs300_increment_update():
    '''
    将当前的沪深300成分股的未更新的价格更新
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    def _covert_code(code):
        if code[-5:] == '.XSHG':
            return "1."+code[:-5]
        else:
            return "0."+code[:-5]
    cursor = db.cursor()
    cursor.execute('select * from hs300_details where is_exist=1;')
    hs300_list = cursor.fetchall()
    # 需要根据hs300_details表来遍历，因为不确定股票池中的数据是否是已经调仓的
    for stock in hs300_list:
        # 查询数据库内每只股票的最新日期
        sql = "select code,max(date),name from hs300_stock_price_pool where code='%s';" % stock[1]
        cursor.execute(sql)
        stock_date_list = cursor.fetchall()
        for stock_info in stock_date_list:
            #计算天数
            stock_date = stock_info[1]
            today = date.today()
            if stock_date == today:
                continue
            else:
                limit = get_trade_day_num(stock_date,today)
                if limit == -1:
                    continue
                if limit == 0:
                    logger.info("{} already latest.".format(stock_info[0],str(stock_date),str(today)))
                    continue
                query_date = str(date.today()).replace('-','')
                history = stock_histroy_info(_covert_code(stock_info[0]),query_date,limit=limit)['klines']
                write_hs300_stock_price_pool(history,stock[1],stock[2])
                logger.info("{} from {} update to {}.".format(stock[1],str(stock_date),str(today)))
    logger.info('hs300 increment update done.')
    db.close()
    
#hs300_increment_update()

def etf_update(etf_code_list:list):
    '''
    更新ETF指数的全部历史股价到stock_price_pool中
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    def _covert_code(code):
        if code[-5:] == '.XSHG':
            return "1."+code[:-5]
        else:
            return "0."+code[:-5]
    for code in etf_code_list:
        query_date = str(date.today()).replace('-','')
        history = stock_histroy_info(_covert_code(code),query_date)
        write_normal_stock_price_pool(history['klines'],code,history['name'])
        logger.info('[etf_update] {}:{} over'.format(code,history['name']))
    db.close()

def etf_increment_update(etf_code_list:list):
    '''
    更新ETF指数的增量股价到stock_price_pool中
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    def _covert_code(code):
        if code[-5:] == '.XSHG':
            return "1."+code[:-5]
        else:
            return "0."+code[:-5]
    # 查询最新日期
    cursor = db.cursor()
    for code in etf_code_list:
        sql = "select code,max(date),name from stock_price_pool where code='{}';".format(code)
        cursor.execute(sql)
        stock_date_list = cursor.fetchall()
        for stock_info in stock_date_list:
            #计算天数
            stock_date = stock_info[1]
            today = date.today()
            if stock_date == today:
                continue
            else:
                limit = get_trade_day_num(stock_date,today)
                if limit == -1:
                    continue
                if limit == 0:
                    logger.info("{} already latest.".format(code,str(stock_date),str(today)))
                    continue
                query_date = str(date.today()).replace('-','')
                history = stock_histroy_info(_covert_code(stock_info[0]),query_date,limit=limit)['klines']
                write_normal_stock_price_pool(history,code,stock_info[2])
                logger.info("{} from {} update to {}.".format(code,str(stock_date),str(today)))

        logger.info('[etf_update] increment update done.')
    db.close()



