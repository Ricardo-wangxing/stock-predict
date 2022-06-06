from .config import config
import jqdatasdk as jq
import pymysql
import pandas as pd
import datetime
import six


def is_str(s):
    return isinstance(s, six.string_types)

def to_date(date):
    """
    >>> convert_date('2015-1-1')
    datetime.date(2015, 1, 1)

    >>> convert_date('2015-01-01 00:00:00')
    datetime.date(2015, 1, 1)

    >>> convert_date(datetime.datetime(2015, 1, 1))
    datetime.date(2015, 1, 1)

    >>> convert_date(datetime.date(2015, 1, 1))
    datetime.date(2015, 1, 1)
    """
    if is_str(date):
        if ':' in date:
            date = date[:10]
        return datetime.datetime.strptime(date, '%Y-%m-%d').date()
    elif isinstance(date, datetime.datetime):
        return date.date()
    elif isinstance(date, datetime.date):
        return date
    elif date is None:
        return None
    raise ParamsError("type error")

class ParamsError(Exception):
    pass

class Security(object):
    code = None
    display_name = None
    name = None
    start_date = None
    end_date = None

    def __init__(self, **kwargs):
        self.code = kwargs.get("code", None)
        self.display_name = kwargs.get("display_name", None)
        self.name = kwargs.get("name", None)
        self.start_date = to_date(kwargs.get("start_date", None))
        self.end_date = to_date(kwargs.get("end_date", None))

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.code


def is_st(stock_list:list):
    '''
    code需要是聚宽格式
    '''
    query_day = str(datetime.date.today())
    history = jq.get_extras('is_st',stock_list,end_date=query_day,count=1,df=False)
    result = []
    for k,v in history.items():
        if True in v:
            result.append(k)
    return result

def get_trade_day_num(start_day,end_day):
    '''
    获取到增量更新所需的limit值
    '''
    jq.auth(config['jqdata_user'],config['jqdata_password'])
    history = jq.get_trade_days(start_date=start_day,end_date=end_day)
    return len(history) - 1

def get_price(security:str, start_date=None, end_date=None, fields=None,count=None):
    '''
    模仿jq的get_price接口，需要先把数据写入到数据库中
    仅支持返回单只股票的日度数据
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    cursor = db.cursor()
    fields_str = ""
    for f in fields:
        fields_str += f + ','
    fields_str = fields_str.rstrip(',')
    # 写一个判断逻辑，判断是使用count还是start_date
    if count == None:
        sql_a = "select %s from stock_price_pool where code = '%s' and (date between %s and %s);" % (fields_str,security,str(start_date),str(end_date))
        cursor.execute(sql_a)
        data = cursor.fetchall()
    else:
        #print(fields_str,security,count)
        sql_b = "select %s from stock_price_pool where code = '%s' and date <= '%s' order by date desc limit %d" % (fields_str,security,str(end_date),count)
        cursor.execute(sql_b)
        data = list(cursor.fetchall())
        data = data[::-1]
        #reversed(list(data))

    df = pd.DataFrame(data)
    rename_mapper = { i:fields[i] for i in range(len(fields))}
    df.rename(columns=rename_mapper,inplace=True)
    db.close()
    return df

def get_security_info(code):
    '''
    模拟jqdata的get_security_info接口
    '''
    db = pymysql.connect(host="127.0.0.1",user=config['db_user'],passwd=config['db_password'],database='stock_info')
    cursor = db.cursor()
    sql = "select code, display_name, name, start_date, end_date from all_securities where code='%s';" % (code)
    cursor.execute(sql)
    data = cursor.fetchall()
    # print(data)
    obj = {
        "code":data[0][0],
        "display_name":data[0][1],
        "name":data[0][2],
        "start_date":data[0][3],
        "end_date":data[0][4],
    }
    db.close()
    return Security(**obj)
