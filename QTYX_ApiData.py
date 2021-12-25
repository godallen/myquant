#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import baostock as bs
import numpy as np
import pandas as pd
import sqlite3
import tushare as ts

from QTYX_SysFile import Base_File_Oper

pro = ts.pro_api(Base_File_Oper.read_tushare_token())  # 初始化pro接口

def bs_k_data_stock(code_val='sz.000651', start_val='2009-01-01', end_val='2019-06-01',
                    freq_val='d', adjust_val='3'):

    # 登陆系统
    lg = bs.login()

    # 获取历史行情数据
    fields= "date,open,high,low,close,volume"

    df_bs = bs.query_history_k_data_plus(code_val, fields, start_date=start_val, end_date=end_val,
                                 frequency=freq_val, adjustflag=adjust_val) # <class 'baostock.data.resultset.ResultData'>
    # frequency="d"取日k线，adjustflag="3"默认不复权，1：后复权；2：前复权

    data_list = []

    while (df_bs.error_code == '0') & df_bs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(df_bs.get_row_data())

    result = pd.DataFrame(data_list, columns=df_bs.fields)

    result.close = result.close.astype('float64')
    result.open = result.open.astype('float64')
    result.low = result.low.astype('float64')
    result.high = result.high.astype('float64')
    result.volume = result.volume.astype('float64')
    result.volume = result.volume/100 # 单位转换：股-手
    result.date = pd.DatetimeIndex(result.date)
    result.set_index("date", drop=True, inplace=True)
    result.index = result.index.set_names('Date')

    recon_data = {'High': result.high, 'Low': result.low, 'Open': result.open, 'Close': result.close,\
                  'Volume': result.volume}
    df_recon = pd.DataFrame(recon_data)

    # 登出系统
    bs.logout()
    return df_recon

def bs_profit_data_stock(code_val='sh.600000', year_val='2017', quarter_val=2):

    # 登陆系统
    lg = bs.login()
    # 显示登陆返回信息
    print('login respond error_code:'+lg.error_code)
    print('login respond  error_msg:'+lg.error_msg)

    # 查询季频估值指标盈利能力
    profit_list = []
    rs_profit = bs.query_profit_data(code=code_val, year=year_val, quarter=quarter_val)
    while (rs_profit.error_code == '0') & rs_profit.next():
        profit_list.append(rs_profit.get_row_data())
    result_profit = pd.DataFrame(profit_list, columns=rs_profit.fields)

    # 登出系统
    bs.logout()
    return result_profit


# 使用Python3自带的sqlite数据库
class DataBase_Sqlite(object):

    def __init__(self):
        self.conn = sqlite3.connect('stock-data.db')

    def get_codes(self):
        # 获取股票代码列表
        dict_basic = Base_File_Oper.load_sys_para("stock_self_pool.json")
        return dict_basic['股票'].values()

    def update_table(self):

        for code in self.get_codes():
            try:
                data = bs_profit_data_stock(code_val=code, year_val='2017', quarter_val=2)
                data.to_sql('stock_profit_stock', self.conn, index=False, if_exists='append')
                print("right code is %s" % code)
            except:
                print("error code is %s" % code)

    def read_table(self):
        # 读取整张表数据
        df = pd.read_sql_query("select * from 'stock_profit_stock';", self.conn)
        return df

    def drop_table(self, table_name):
        # 删除一个表
        c = self.conn.cursor()
        c.execute("drop table "+ table_name)
        self.conn.commit()

    def close_base(self):
        # 关闭数据库
        self.conn.close()


class Tspro_Backend():

    def __init__(self):

        self.tran_col = {"ts_code": u"股票代码", "close": u"当日收盘价",
                    # "turnover_rate": u"换手率%",
                    "turnover_rate_f": u"换手率%",  # 自由流通股
                    "volume_ratio": u"量比", "pe": u"市盈率(总市值/净利润)",
                    "pe_ttm": u"市盈率TTM",
                    "pb": u"市净率(总市值/净资产)",
                    "ps": u"市销率", "ps_ttm": u"市销率TTM",
                    "dv_ratio": u"股息率%",
                    "dv_ttm": u"股息率TTM%",
                    "total_share": u"总股本(万股)",
                    "float_share": u"流通股本(万股)",
                    "free_share": u"自由流通股本(万股)",
                    "total_mv": u"总市值(万元)",
                    "circ_mv": u"流通市值(万元)",
                    "name": u"股票名称",
                    "area": u"所在地域",
                    "list_date": u"上市日期",
                    "industry": u"所属行业"}

        self.filter = [u"换手率%", u"量比", u"市盈率(总市值/净利润)", u"市盈率TTM",
                  u"市净率(总市值/净资产)", u"市销率", u"市销率TTM", u"股息率%",
                  u"股息率TTM%", u"总股本(万股)", u"流通股本(万股)", u"自由流通股本(万股)",
                  u"总市值(万元)", u"流通市值(万元)"]

    def datafame_join(self, date_val):

        df_stbasic = pro.stock_basic(exchange='', list_status='L',
                                     fields='ts_code,name,area,industry,list_date')
        df_dybasic = pro.daily_basic(trade_date=date_val)  # "20200614"
        # cols_to_use = df_dybasic.columns.difference(df_stbasic.columns) # pandas版本0.15及之上 找出两个表不同列，然后merge

        if df_dybasic.empty == True:
            df_join = pd.DataFrame()
        else:
            df_join = pd.merge(df_stbasic, df_dybasic, on='ts_code', left_index=False, right_index=False,
                         how='outer')
            df_join.drop(['trade_date', 'turnover_rate'], axis=1, inplace=True)

        return df_join


class Tsorg_Backend():

    def __init__(self):

        self.tran_col = {"ts_code": u"股票代码",
                    "name": u"股票名称",
                    "area": u"所在地域",
                    "list_date": u"上市日期",
                    "industry": u"所属行业",

                    "pe": u"市盈率",
                    "outstanding": u"流通股本(亿)",
                    "totals": u"总股本(亿)",
                    "totalAssets": u"总资产(万)",
                    "liquidAssets": u"流动资产",
                    "fixedAssets": u"固定资产",
                    "reserved": u"公积金",
                    "reservedPerShare": u"每股公积金",

                    "pb": u"市净率",
                    "timeToMarket": u"上市日期",
                    "undp": u"未分利润",
                    "perundp": u"每股未分配",
                    "rev": u"收入同比(%)",
                    "profit": u"利润同比(%)",
                    "gpr": u"毛利率(%)",
                    "npr": u"净利润率(%)",
                    "holders": u"股东人数",

                    "esp": u"每股收益",
                    "eps_yoy": u"每股收益同比( %)",
                    "bvps": u"每股净资产",
                    "roe": u"净资产收益率(%)",
                    "epcf": u"每股现金流量(元)",
                    "net_profits": u"净利润(万元)",
                    "profits_yoy": u"净利润同比(%)",
                    "distrib": u"分配方案",
                    "report_date": u"发布日期",
        }

        self.filter = [u"每股收益", u"流通股本(亿)", u"净利润(万元)", u"每股净资产"]

    def datafame_join(self, date_val):

        try:
            df_stbasic = pro.stock_basic(exchange='', list_status='L',
                                         fields='ts_code,name,area,industry,list_date')
            df_dybasic = ts.get_stock_basics()
            # cols_to_use = df_dybasic.columns.difference(df_stbasic.columns) # pandas版本0.15及之上 找出两个表不同列，然后merge
            df_dybasic.drop(['industry', 'area', 'timeToMarket'], axis=1, inplace=True)

            df_rpbasic = ts.get_report_data(int(date_val[0:4]), int(date_val[4:6])//4+1)
            df_rpbasic.drop(['eps', 'bvps', 'code'], axis=1, inplace=True)

            df_temp = pd.merge(df_stbasic, df_dybasic, on='name', left_index=False, right_index=False,
                         how='inner') # suffixes 可设置重名列
            df_join = pd.merge(df_temp, df_rpbasic, on='name', left_index=False, right_index=False,
                               how='inner')  # suffixes 可设置重名列
            df_join.drop_duplicates(subset=['name'], keep='first', inplace=True)

        except:
            df_join = pd.DataFrame()

        return df_join

