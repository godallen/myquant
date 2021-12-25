#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import wx
import wx.adv
import wx.grid
import wx.html2
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg  as NavigationToolbar
import matplotlib.gridspec as gridspec # 分割子图
import tushare as ts
import pandas as pd
import mpl_finance as mpf
import matplotlib.pyplot as plt
import datetime

from QTYX_ElementGui import StockPanel, SubGraphs, GroupPanel, CollegeTreeListCtrl, Sys_Panel
from QTYX_ApiData import bs_k_data_stock, Tspro_Backend, Tsorg_Backend
from QTYX_StrategyGath import Base_Strategy_Group
from QTYX_SysFile import Base_File_Oper

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class MainFrame(wx.Frame):

    def __init__(self):

        # hack to help on dual-screen, need something better XXX - idfah
        displaySize = wx.DisplaySize()  # (1920, 1080)
        displaySize = 0.85 * displaySize[0], 0.75 * displaySize[1]

        # call base class constructor
        wx.Frame.__init__(self, parent=None, title=u'量化软件', size=displaySize,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX)  # size=(1000,600)

        # 组合加入tushare数据
        self.ts_data = Tspro_Backend()
        self.filter = self.ts_data.filter
        self.tran_col = self.ts_data.tran_col
        self.datafame_join = self.ts_data.datafame_join

        # 加载配置文件
        self.firm_para = Base_File_Oper.load_sys_para("firm_para.json")
        self.back_para = Base_File_Oper.load_sys_para("back_para.json")

        self.backtPanel = wx.Panel(self, -1)
        self.backt_info_box = wx.StaticBox(self.backtPanel, -1, u'回测结果')
        self.backt_info_sizer = wx.StaticBoxSizer(self.backt_info_box, wx.VERTICAL)
        self.backt_info_Tinput = wx.TextCtrl(self.backtPanel, -1, "", size=(200, 300), style=wx.TE_MULTILINE)  # 多行|只读
        self.backt_info_sizer.Add(self.backt_info_Tinput, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        self.backtPanel.SetSizer(self.backt_info_sizer)

        # 创建wxGrid表格对象
        self.init_grid_pl()
        self.init_grid_pk()


        self.colleges = {
            u'经典策略': [
                {'名称': u'N日突破', '类型': u'趋势', '函数': u'CalNdaysSignal'},
                {'名称': u'动能转换', '类型': u'趋势','函数': u'未定义'},
                {'名称': u'KDJ峰谷', '类型': u'波动','函数': u'未定义'},
                {'名称': u'均线交叉', '类型': u'趋势','函数': u'未定义'}],
            u'自定义策略': [
                {'名称': u'yx-zl-1', '类型': u'综合','函数': u'未定义'},
                {'名称': u'yx-zl-2', '类型': u'趋势','函数': u'未定义'},
                {'名称': u'yx-zl-3', '类型': u'波动','函数': u'未定义'}]
        }
        # 创建一个 treeListCtrl object
        self.treeListCtrl = CollegeTreeListCtrl(parent=self, pos=(-1, 39), size=(150, 200))
        self.treeListCtrl.refDataShow(self.colleges) # treeListCtrl显示数据接口
        # self.treeListCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeListCtrlClickFunc, )

        self.vbox_sizer_a = wx.BoxSizer(wx.VERTICAL)  # 纵向box
        self.vbox_sizer_a.Add(self.treeListCtrl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)  # 添加行情参数布局
        self.vbox_sizer_a.Add(self.backtPanel, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)  # 添加行情参数布局
        self.vbox_sizer_a.Add(self.grid_pl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # 创建参数区面板
        self.ParaNoteb = wx.Notebook(self)
        self.ParaStPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaBtPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaPtPanel = wx.Panel(self.ParaNoteb, -1)

        # 创建显示区面板
        self.DispPanel = Sys_Panel(self, **self.firm_para['layout_dict']) # 自定义
        self.sw_panel_last = self.DispPanel

        # 第二层布局
        self.add_stock_para_lay()
        self.add_backt_para_lay()
        self.add_pick_para_lay()
        self.ParaNoteb.AddPage(self.ParaStPanel, "行情参数")
        self.ParaNoteb.AddPage(self.ParaBtPanel, "回测参数")
        self.ParaNoteb.AddPage(self.ParaPtPanel, "条件选股")

        self.vbox_sizer_b = wx.BoxSizer(wx.VERTICAL)  # 纵向box
        self.vbox_sizer_b.Add(self.ParaNoteb, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=5)  # 添加行情参数布局
        self.vbox_sizer_b.Add(self.DispPanel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # 第一层布局
        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_a, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_b, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # 使布局有效

    def add_stock_para_lay(self):

        # 行情参数
        stock_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 行情参数——日历控件时间周期
        self.dpc_end_time = wx.adv.DatePickerCtrl(self.ParaStPanel, -1,
                                                  style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#结束时间
        self.dpc_start_time = wx.adv.DatePickerCtrl(self.ParaStPanel, -1,
                                                    style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#起始时间

        self.start_date_box = wx.StaticBox(self.ParaStPanel, -1, u'开始日期(Start)')
        self.end_date_box = wx.StaticBox(self.ParaStPanel, -1, u'结束日期(End)')
        self.start_date_sizer = wx.StaticBoxSizer(self.start_date_box, wx.VERTICAL)
        self.end_date_sizer = wx.StaticBoxSizer(self.end_date_box, wx.VERTICAL)
        self.start_date_sizer.Add(self.dpc_start_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.end_date_sizer.Add(self.dpc_end_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.dpc_end_time.SetValue(date_time_now)
        self.dpc_start_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

        # 行情参数——输入股票代码
        self.stock_code_box = wx.StaticBox(self.ParaStPanel, -1, u'股票代码')
        self.stock_code_sizer = wx.StaticBoxSizer(self.stock_code_box, wx.VERTICAL)
        self.stock_code_input = wx.TextCtrl(self.ParaStPanel, -1, "sz.000876", style=wx.TE_PROCESS_ENTER)
        self.stock_code_sizer.Add(self.stock_code_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.stock_code_input.Bind(wx.EVT_TEXT_ENTER, self.enter_stcode)

        # 行情参数——股票周期选择
        self.stock_period_box = wx.StaticBox(self.ParaStPanel, -1, u'股票周期')
        self.stock_period_sizer = wx.StaticBoxSizer(self.stock_period_box, wx.VERTICAL)
        self.stock_period_cbox = wx.ComboBox(self.ParaStPanel, -1, u"", choices=[u"30分钟", u"60分钟", u"日线", u"周线"])
        self.stock_period_cbox.SetSelection(2)
        self.stock_period_sizer.Add(self.stock_period_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 行情参数——股票复权选择
        self.stock_authority_box = wx.StaticBox(self.ParaStPanel, -1, u'股票复权')
        self.stock_authority_sizer = wx.StaticBoxSizer(self.stock_authority_box, wx.VERTICAL)
        self.stock_authority_cbox = wx.ComboBox(self.ParaStPanel, -1, u"", choices=[u"前复权", u"后复权", u"不复权"])
        self.stock_authority_cbox.SetSelection(2)
        self.stock_authority_sizer.Add(self.stock_authority_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 行情参数——多子图显示
        self.pick_graph_box = wx.StaticBox(self.ParaStPanel, -1, u'多子图显示')
        self.pick_graph_sizer = wx.StaticBoxSizer(self.pick_graph_box, wx.VERTICAL)
        self.pick_graph_cbox = wx.ComboBox(self.ParaStPanel, -1, u"未开启", choices=[u"未开启", u"A股票走势", u"B股票走势", u"C股票走势", u"D股票走势"],
                                           style=wx.CB_READONLY | wx.CB_DROPDOWN)
        self.pick_graph_cbox.SetSelection(0)
        self.pick_graph_last = self.pick_graph_cbox.GetSelection()
        self.pick_graph_sizer.Add(self.pick_graph_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_graph_cbox.Bind(wx.EVT_COMBOBOX, self.select_graph)

        stock_para_sizer.Add(self.start_date_sizer, proportion=0, flag=wx.EXPAND | wx.CENTER | wx.ALL, border=10)
        stock_para_sizer.Add(self.end_date_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_code_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_period_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.stock_authority_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        stock_para_sizer.Add(self.pick_graph_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        self.ParaStPanel.SetSizer(stock_para_sizer)


    def add_backt_para_lay(self):

        # 回测参数
        back_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.init_cash_box = wx.StaticBox(self.ParaBtPanel, -1, u'初始资金')
        self.init_cash_sizer = wx.StaticBoxSizer(self.init_cash_box, wx.VERTICAL)
        self.init_cash_input = wx.TextCtrl(self.ParaBtPanel, -1, "100000", style=wx.TE_LEFT)
        self.init_cash_sizer.Add(self.init_cash_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_stake_box = wx.StaticBox(self.ParaBtPanel, -1, u'交易规模')
        self.init_stake_sizer = wx.StaticBoxSizer(self.init_stake_box, wx.VERTICAL)
        self.init_stake_input = wx.TextCtrl(self.ParaBtPanel, -1, "all", style=wx.TE_LEFT)
        self.init_stake_sizer.Add(self.init_stake_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_slippage_box = wx.StaticBox(self.ParaBtPanel, -1, u'滑点')
        self.init_slippage_sizer = wx.StaticBoxSizer(self.init_slippage_box, wx.VERTICAL)
        self.init_slippage_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.01", style=wx.TE_LEFT)
        self.init_slippage_sizer.Add(self.init_slippage_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_commission_box = wx.StaticBox(self.ParaBtPanel, -1, u'手续费')
        self.init_commission_sizer = wx.StaticBoxSizer(self.init_commission_box, wx.VERTICAL)
        self.init_commission_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.0005", style=wx.TE_LEFT)
        self.init_commission_sizer.Add(self.init_commission_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_tax_box = wx.StaticBox(self.ParaBtPanel, -1, u'印花税')
        self.init_tax_sizer = wx.StaticBoxSizer(self.init_tax_box, wx.VERTICAL)
        self.init_tax_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.001", style=wx.TE_LEFT)
        self.init_tax_sizer.Add(self.init_tax_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 回测按钮
        self.start_back_but = wx.Button(self.ParaBtPanel, -1, "开始回测")
        self.start_back_but.Bind(wx.EVT_BUTTON, self.start_run)  # 绑定按钮事件

        back_para_sizer.Add(self.init_cash_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_stake_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_slippage_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_commission_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_tax_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.start_back_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        self.ParaBtPanel.SetSizer(back_para_sizer)

    def add_pick_para_lay(self):

        # 选股参数
        pick_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 选股参数——日历控件时间周期
        self.dpc_cur_time = wx.adv.DatePickerCtrl(self.ParaPtPanel, -1,
                                                  style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE)  # 当前时间

        self.cur_date_box = wx.StaticBox(self.ParaPtPanel, -1, u'当前日期(Start)')
        self.cur_date_sizer = wx.StaticBoxSizer(self.cur_date_box, wx.VERTICAL)
        self.cur_date_sizer.Add(self.dpc_cur_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTime格式"03/03/18 00:00:00"
        self.dpc_cur_time.SetValue(date_time_now)
        # self.dpc_cur_time.SetValue(date_time_now.SetDay(9)) # 以9日为例 先不考虑周末的干扰

        # 选股参数——条件表达式分析
        self.pick_stock_box = wx.StaticBox(self.ParaPtPanel, -1, u'条件表达式选股')
        self.pick_stock_sizer = wx.StaticBoxSizer(self.pick_stock_box, wx.HORIZONTAL)
        self.pick_item_cmbo = wx.ComboBox(self.ParaPtPanel, -1, self.filter[0], choices=self.filter,
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股项
        self.pick_cond_cmbo = wx.ComboBox(self.ParaPtPanel, -1, u"大于",
                                          choices=[u"大于", u"等于", u"小于"],
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 选股条件
        self.pick_value_text = wx.TextCtrl(self.ParaPtPanel, -1, "0", style=wx.TE_LEFT)

        self.sort_values_cmbo = wx.ComboBox(self.ParaPtPanel, -1, u"不排列",
                                            choices=[u"不排列", u"升序", u"降序"],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # 排列条件

        self.pick_stock_sizer.Add(self.pick_item_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_cond_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_value_text, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.sort_values_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # 选股按钮
        self.start_pick_but = wx.Button(self.ParaPtPanel, -1, "开始选股")
        self.start_pick_but.Bind(wx.EVT_BUTTON, self.start_select)  # 绑定按钮事件

        # 复位按钮
        self.start_reset_but = wx.Button(self.ParaPtPanel, -1, "复位条件")
        self.start_reset_but.Bind(wx.EVT_BUTTON, self.start_reset)  # 绑定按钮事件

        # 保存按钮
        self.start_save_but = wx.Button(self.ParaPtPanel, -1, "保存结果")
        self.start_save_but.Bind(wx.EVT_BUTTON, self.start_save)  # 绑定按钮事件

        pick_para_sizer.Add(self.cur_date_sizer, proportion=0, flag=wx.EXPAND | wx.CENTER | wx.ALL, border=10)
        pick_para_sizer.Add(self.pick_stock_sizer, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER,
                             border=10)
        pick_para_sizer.Add(self.start_pick_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        pick_para_sizer.Add(self.start_reset_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        pick_para_sizer.Add(self.start_save_but, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=10)
        self.ParaPtPanel.SetSizer(pick_para_sizer)

    def data_pl_grid(self, basic):

        i = 0
        self.grid_pl = wx.grid.Grid(self, -1)
        self.grid_pl.CreateGrid(0, 2)
        self.grid_pl.SetColLabelValue(0, "代码")
        self.grid_pl.SetColLabelValue(1, "名称")

        for m_k, m_v in basic.items():
            st_name_code_dict = m_v
            for s_k, s_v in st_name_code_dict.items():
                self.grid_pl.InsertRows(i, 2)
                self.grid_pl.SetCellValue(i, 0, s_k)
                self.grid_pl.SetCellValue(i, 1, s_v)
                i = i + 1
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.click_stcode, self.grid_pl)

    def init_grid_pk(self):
        # 初始化选股表格
        self.grid_pk = wx.grid.Grid(self, -1)
        self.df_use = pd.DataFrame()
        self.filte_result = pd.DataFrame()

    def init_grid_pl(self):
        # 初始化股票池表格
        dict_basic = Base_File_Oper.load_sys_para("stock_self_pool.json")
        self.data_pl_grid(dict_basic)

    def get_stdat(self, st_code):
        # 获取股票数据
        sdate_obj = self.dpc_start_time.GetValue()
        sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)
        edate_obj = self.dpc_end_time.GetValue()
        edate_val = datetime.datetime(edate_obj.year, edate_obj.month + 1, edate_obj.day)

        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()

        if st_period == "30分钟":
            period_val = "30"
        elif st_period == "60分钟":
            period_val = "60"
        elif st_period == "日线":
            period_val = "d"
        elif st_period == "周线":
            period_val = "w"
        else:
            period_val = "d"

        if st_auth == "后复权":
            auth_val = "2"
        elif st_auth == "前复权":
            auth_val = "1"
        elif st_auth == "不复权":
            auth_val = "3"
        else:
            auth_val = "3"

        try:
            df = bs_k_data_stock(st_code, start_val=sdate_val.strftime('%Y-%m-%d'),
                                          end_val=edate_val.strftime('%Y-%m-%d'),
                                          freq_val=period_val, adjust_val=auth_val)

        except:
            self.MessageDiag("输入参数有误！")
            df = pd.DataFrame()

        return df

    def enter_stcode(self, event):

        st_code = self.stock_code_input.GetValue()

        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()

        df_stockDat = self.get_stdat(st_code)

        if self.pick_graph_cbox.GetSelection() != 0:
            self.clear_subgraph(0)  # 必须清理图形才能显示下一幅图
            self.draw_subgraph(df_stockDat, st_code, st_period + st_auth)
        else:

            self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.firm_para['layout_dict']))
            self.DispPanel = self.sw_panel_last
            self.firm_para['subplots_dict']['graph_fst']['title'] = st_code + st_period + st_auth
            self.DispPanel.firm_graph_run(df_stockDat,  **self.firm_para['subplots_dict'])

        self.update_subgraph(0)  # 必须刷新才能显示下一幅图


    def update_subgraph(self, sub):
        if sub == 0:
            self.DispPanel.FigureCanvas.draw()
        elif sub == 1:
            self.GroupPanel.FigureCanvas.draw()

    def clear_subgraph(self, sub):
        # 再次画图前,必须调用该命令清空原来的图形
        if sub == 0:
            self.ochl.clear()
            self.vol.clear()
        elif sub == 1:
            self.GroupPanel.relate.clear()

    def draw_subgraph(self, stockdat, st_name, st_kylabel):
        # 绘制多子图页面
        num_bars = np.arange(0, len(stockdat.index))

        # 绘制K线
        ohlc = list(zip(num_bars, stockdat.Open, stockdat.Close, stockdat.High, stockdat.Low))
        mpf.candlestick_ochl(self.ochl, ohlc, width=0.5, colorup='r', colordown='g')  # 绘制K线走势

        # 绘制成交量
        self.vol.bar(num_bars, stockdat.Volume, color=['g' if stockdat.Open[x] > stockdat.Close[x] else 'r' for x in
                                                    range(0, len(stockdat.index))])

        self.ochl.set_ylabel(st_kylabel)
        self.vol.set_ylabel(u"成交量")
        self.ochl.set_title(st_name + " 行情走势图")

        major_tick = len(num_bars)
        self.ochl.set_xlim(0, major_tick)  # 设置一下x轴的范围
        self.vol.set_xlim(0, major_tick)  # 设置一下x轴的范围

        self.ochl.set_xticks(range(0, major_tick, 15))  # 每五天标一个日期
        self.vol.set_xticks(range(0, major_tick, 15))  # 每五天标一个日期
        self.vol.set_xticklabels(
            [stockdat.index.strftime('%Y-%m-%d')[index] for index in self.vol.get_xticks()])  # 标签设置为日期

        for label in self.ochl.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
            label.set_visible(False)
        for label in self.vol.xaxis.get_ticklabels():  # X-轴每个ticker标签隐藏
            label.set_rotation(45)  # X-轴每个ticker标签都向右倾斜45度
            label.set_fontsize(10)  # 设置标签字体

        self.ochl.grid(True, color='k')
        self.vol.grid(True, color='k')

    def refresh_grid(self, df):

        self.grid_pk = wx.grid.Grid(self, -1)

        self.switch_main_panel(self.sw_panel_last, self.grid_pk)

        if df.empty != True:

            self.grid_pk.ClearGrid()
            self.grid_pk.CreateGrid(df.shape[0], df.shape[1])
            self.list_columns = df.columns.tolist()

            for col, series in df.iteritems():
                m = self.list_columns.index(col)
                self.grid_pk.SetColLabelValue(m, self.tran_col.get(col, ""))
                for n, val in enumerate(series):
                    self.grid_pk.SetCellValue(n, m, str(val))
                self.grid_pk.AutoSizeColumn(m, True)  # 自动调整列尺寸

    def MessageDiag(self, info):

        dlg_mesg = wx.MessageDialog(None, info, u"温馨提示",
                                    wx.YES_NO | wx.ICON_INFORMATION)
        if dlg_mesg.ShowModal() == wx.ID_YES:
            print("点击Yes")
        else:
            print("点击No")
        dlg_mesg.Destroy()

    def switch_main_panel(self, org_panel=None, new_panel=None):

        if id(org_panel) != id(new_panel):

            self.vbox_sizer_b.Hide(org_panel)
            # 方案一 先删除后添加
            self.vbox_sizer_b.Detach(org_panel)
            self.vbox_sizer_b.Add(new_panel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)
            # 方案二 等类型可替换
            #self.vbox_sizer_b.Replace(org_panel, new_panel)
            self.vbox_sizer_b.Show(new_panel)
            self.sw_panel_last = new_panel
            self.SetSizer(self.HBoxPanelSizer)
            self.HBoxPanelSizer.Layout()

    def click_stcode(self, event):

        st_code = self.grid_pl.GetCellValue(event.GetRow(), 1)
        st_name = self.grid_pl.GetCellValue(event.GetRow(), 0)

        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()

        df_stockDat = self.get_stdat(st_code)

        if self.pick_graph_cbox.GetSelection() != 0:
            self.clear_subgraph(0)  # 必须清理图形才能显示下一幅图
            self.draw_subgraph(df_stockDat, st_name, st_period + st_auth)
        else:

            self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.firm_para['layout_dict']))
            self.DispPanel = self.sw_panel_last
            self.firm_para['subplots_dict']['graph_fst']['title'] = st_name + st_period + st_auth
            self.DispPanel.firm_graph_run(df_stockDat,  **self.firm_para['subplots_dict'])

        self.update_subgraph(0)  # 必须刷新才能显示下一幅图

    def select_graph(self, event):

        item = event.GetSelection()

        if item != 0 and self.pick_graph_last == 0:

            self.pick_graph_last = item
            self.graphs_obj = SubGraphs(self)

            self.FlexGridSizer = self.graphs_obj.FlexGridSizer
            self.DispPanel0 = self.graphs_obj.DispPanel0
            self.DispPanel1 = self.graphs_obj.DispPanel1
            self.DispPanel2 = self.graphs_obj.DispPanel2
            self.DispPanel3 = self.graphs_obj.DispPanel3
            self.switch_main_panel(self.sw_panel_last, self.FlexGridSizer)

        elif item == 0 and self.pick_graph_last != 0:
            #print(self.vbox_sizer_b.GetItem(self.DispPanel))
            self.pick_graph_last = item
            self.switch_main_panel(self.FlexGridSizer, Sys_Panel(self, **self.firm_para['layout_dict']))

        if item == 1:
            self.DispPanel = self.DispPanel0
            self.ochl = self.DispPanel0.ochl
            self.vol = self.DispPanel0.vol
        elif item == 2:
            self.DispPanel = self.DispPanel1
            self.ochl = self.DispPanel1.ochl
            self.vol = self.DispPanel1.vol
        elif item == 3:
            self.DispPanel = self.DispPanel2
            self.ochl = self.DispPanel2.ochl
            self.vol = self.DispPanel2.vol
        elif item == 4:
            self.DispPanel = self.DispPanel3
            self.ochl = self.DispPanel3.ochl
            self.vol = self.DispPanel3.vol
        else:
            pass

    def start_run(self, event):
        # 点击运行回测
        cash_value = self.init_cash_input.GetValue()
        stake_value = self.init_stake_input.GetValue()
        slippage_value = self.init_slippage_input.GetValue()
        commission_value = self.init_commission_input.GetValue()
        tax_value = self.init_tax_input.GetValue()
        st_code = self.stock_code_input.GetValue()

        #self.backtrader_excetue(df_stockDat, sdate_val, edate_val, cash_value, trade_value, commission_value)

        # 更新GUI的回测参数 并且保存
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['cash_hold'] = cash_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['slippage'] = slippage_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['c_rate'] = commission_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['t_rate'] = tax_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['stake_size'] = stake_value
        self.back_para['subplots_dict']['graph_fst']['title'] = st_code + "-回测分析"

        Base_File_Oper.save_sys_para("back_para.json", self.back_para)

        self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.back_para['layout_dict']))
        self.DispPanel = self.sw_panel_last

        self.DispPanel.back_graph_run(Base_Strategy_Group.get_ndays_signal(self.get_stdat(st_code)), **self.back_para['subplots_dict'])
        # 修改图形的任何属性后都必须更新GUI界面
        self.DispPanel.FigureCanvas.draw()

        self.backt_info_Tinput.Clear()
        self.backt_info_Tinput.AppendText(Base_File_Oper.read_log_trade())

        # self.clear_subgraph() # 必须清理图形才能显示下一幅图
        # self.draw_backTest(df_recon, st_code)
        # self.update_subgraph() # 必须刷新才能显示下一幅图

    def start_select(self, event):

        if self.df_use.empty != True:
            for key, val in self.tran_col.items():
                if val == self.pick_item_cmbo.GetStringSelection():

                    para_value = float(self.pick_value_text.GetValue())

                    if self.pick_cond_cmbo.GetStringSelection() == u"大于":
                        self.filte_result = self.df_use[self.df_use[key] > para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"小于":
                        self.filte_result = self.df_use[self.df_use[key] < para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"等于":
                        self.filte_result = self.df_use[self.df_use[key] == para_value]
                    else:
                        pass

                    if self.sort_values_cmbo.GetStringSelection() == u"降序":
                        self.filte_result.sort_values(by=key, axis='index', ascending=False, inplace=True,
                                                      na_position='last')
                    elif self.sort_values_cmbo.GetStringSelection() == u"升序":
                        self.filte_result.sort_values(by=key, axis='index', ascending=True, inplace=True,
                                                      na_position='last')
                    else:
                        pass
                    self.refresh_grid(self.filte_result)
                    self.df_use = self.filte_result
                    break

    def start_reset(self, event):
        # 复位选股按钮事件
        sdate_obj = self.dpc_cur_time.GetValue()
        sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)

        self.df_join = self.datafame_join(sdate_val.strftime('%Y%m%d'))  # 刷新self.df_join

        if self.df_join.empty == True:
            self.MessageDiag("该日无数据")

        self.df_use = self.df_join
        self.refresh_grid(self.df_use)

    def start_save(self, event):
        # 保存选股按钮事件
        codes = self.df_use.ts_code.values
        names = self.df_use.name.values
        st_name_code_dict = dict(zip(names, codes))

        for k, v in st_name_code_dict.items():
            code_split = v.lower().split(".")
            st_name_code_dict[k] = code_split[1] + "." + code_split[0] # tushare转baostock

        dict_basic = Base_File_Oper.load_sys_para("stock_self_pool.json")
        dict_basic['股票'].clear()
        dict_basic['股票'].update(st_name_code_dict)

        Base_File_Oper.save_sys_para("stock_self_pool.json", dict_basic)

        self.grid_pl.Destroy()
        self.data_pl_grid(dict_basic)
        self.vbox_sizer_a.Add(self.grid_pl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)
        self.vbox_sizer_a.Show(self.grid_pl)
        self.SetSizer(self.HBoxPanelSizer)
        self.HBoxPanelSizer.Layout()
        #self.df_use.to_csv('table-stock.csv', columns=self.df_use.columns, index=True, encoding='GB18030')

class MainApp(wx.App):

    def OnInit(self):
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        self.frame = MainFrame()
        self.frame.Show()
        self.frame.Center()
        self.SetTopWindow(self.frame)
        return True


if __name__ == '__main__':
    app = MainApp()
    app.MainLoop()

