#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author åå®µå¤§å¸ æ¬ä¾ç¨ä»ç¨äºæå­¦ç®çï¼ä¸¥ç¦è½¬ååç¨äºçå©ç®çï¼è¿èå¿ç©¶

import wx
import wx.adv
import wx.grid
import wx.html2
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg  as NavigationToolbar
import matplotlib.gridspec as gridspec # åå²å­å¾
import tushare as ts
import pandas as pd
import mpl_finance as mpf
import matplotlib.pyplot as plt
import datetime

from QTYX_ElementGui import StockPanel, SubGraphs, GroupPanel, CollegeTreeListCtrl, Sys_Panel
from QTYX_ApiData import bs_k_data_stock, Tspro_Backend, Tsorg_Backend
from QTYX_StrategyGath import Base_Strategy_Group
from QTYX_SysFile import Base_File_Oper

plt.rcParams['font.sans-serif'] = ['SimHei']  # ç¨æ¥æ­£å¸¸æ¾ç¤ºä¸­ææ ç­¾
plt.rcParams['axes.unicode_minus'] = False  # ç¨æ¥æ­£å¸¸æ¾ç¤ºè´å·

class MainFrame(wx.Frame):

    def __init__(self):

        # hack to help on dual-screen, need something better XXX - idfah
        displaySize = wx.DisplaySize()  # (1920, 1080)
        displaySize = 0.85 * displaySize[0], 0.75 * displaySize[1]

        # call base class constructor
        wx.Frame.__init__(self, parent=None, title=u'éåè½¯ä»¶', size=displaySize,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX)  # size=(1000,600)

        # ç»åå å¥tushareæ°æ®
        self.ts_data = Tspro_Backend()
        self.filter = self.ts_data.filter
        self.tran_col = self.ts_data.tran_col
        self.datafame_join = self.ts_data.datafame_join

        # å è½½éç½®æä»¶
        self.firm_para = Base_File_Oper.load_sys_para("firm_para.json")
        self.back_para = Base_File_Oper.load_sys_para("back_para.json")

        self.backtPanel = wx.Panel(self, -1)
        self.backt_info_box = wx.StaticBox(self.backtPanel, -1, u'åæµç»æ')
        self.backt_info_sizer = wx.StaticBoxSizer(self.backt_info_box, wx.VERTICAL)
        self.backt_info_Tinput = wx.TextCtrl(self.backtPanel, -1, "", size=(200, 300), style=wx.TE_MULTILINE)  # å¤è¡|åªè¯»
        self.backt_info_sizer.Add(self.backt_info_Tinput, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        self.backtPanel.SetSizer(self.backt_info_sizer)

        # åå»ºwxGridè¡¨æ ¼å¯¹è±¡
        self.init_grid_pl()
        self.init_grid_pk()


        self.colleges = {
            u'ç»å¸ç­ç¥': [
                {'åç§°': u'Næ¥çªç ´', 'ç±»å': u'è¶å¿', 'å½æ°': u'CalNdaysSignal'},
                {'åç§°': u'å¨è½è½¬æ¢', 'ç±»å': u'è¶å¿','å½æ°': u'æªå®ä¹'},
                {'åç§°': u'KDJå³°è°·', 'ç±»å': u'æ³¢å¨','å½æ°': u'æªå®ä¹'},
                {'åç§°': u'åçº¿äº¤å', 'ç±»å': u'è¶å¿','å½æ°': u'æªå®ä¹'}],
            u'èªå®ä¹ç­ç¥': [
                {'åç§°': u'yx-zl-1', 'ç±»å': u'ç»¼å','å½æ°': u'æªå®ä¹'},
                {'åç§°': u'yx-zl-2', 'ç±»å': u'è¶å¿','å½æ°': u'æªå®ä¹'},
                {'åç§°': u'yx-zl-3', 'ç±»å': u'æ³¢å¨','å½æ°': u'æªå®ä¹'}]
        }
        # åå»ºä¸ä¸ª treeListCtrl object
        self.treeListCtrl = CollegeTreeListCtrl(parent=self, pos=(-1, 39), size=(150, 200))
        self.treeListCtrl.refDataShow(self.colleges) # treeListCtrlæ¾ç¤ºæ°æ®æ¥å£
        # self.treeListCtrl.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeListCtrlClickFunc, )

        self.vbox_sizer_a = wx.BoxSizer(wx.VERTICAL)  # çºµåbox
        self.vbox_sizer_a.Add(self.treeListCtrl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)  # æ·»å è¡æåæ°å¸å±
        self.vbox_sizer_a.Add(self.backtPanel, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)  # æ·»å è¡æåæ°å¸å±
        self.vbox_sizer_a.Add(self.grid_pl, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # åå»ºåæ°åºé¢æ¿
        self.ParaNoteb = wx.Notebook(self)
        self.ParaStPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaBtPanel = wx.Panel(self.ParaNoteb, -1)
        self.ParaPtPanel = wx.Panel(self.ParaNoteb, -1)

        # åå»ºæ¾ç¤ºåºé¢æ¿
        self.DispPanel = Sys_Panel(self, **self.firm_para['layout_dict']) # èªå®ä¹
        self.sw_panel_last = self.DispPanel

        # ç¬¬äºå±å¸å±
        self.add_stock_para_lay()
        self.add_backt_para_lay()
        self.add_pick_para_lay()
        self.ParaNoteb.AddPage(self.ParaStPanel, "è¡æåæ°")
        self.ParaNoteb.AddPage(self.ParaBtPanel, "åæµåæ°")
        self.ParaNoteb.AddPage(self.ParaPtPanel, "æ¡ä»¶éè¡")

        self.vbox_sizer_b = wx.BoxSizer(wx.VERTICAL)  # çºµåbox
        self.vbox_sizer_b.Add(self.ParaNoteb, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=5)  # æ·»å è¡æåæ°å¸å±
        self.vbox_sizer_b.Add(self.DispPanel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)

        # ç¬¬ä¸å±å¸å±
        self.HBoxPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_a, proportion=1, border=2, flag=wx.EXPAND | wx.ALL)
        self.HBoxPanelSizer.Add(self.vbox_sizer_b, proportion=10, border=2, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(self.HBoxPanelSizer)  # ä½¿å¸å±ææ

    def add_stock_para_lay(self):

        # è¡æåæ°
        stock_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # è¡æåæ°ââæ¥åæ§ä»¶æ¶é´å¨æ
        self.dpc_end_time = wx.adv.DatePickerCtrl(self.ParaStPanel, -1,
                                                  style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#ç»ææ¶é´
        self.dpc_start_time = wx.adv.DatePickerCtrl(self.ParaStPanel, -1,
                                                    style = wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE)#èµ·å§æ¶é´

        self.start_date_box = wx.StaticBox(self.ParaStPanel, -1, u'å¼å§æ¥æ(Start)')
        self.end_date_box = wx.StaticBox(self.ParaStPanel, -1, u'ç»ææ¥æ(End)')
        self.start_date_sizer = wx.StaticBoxSizer(self.start_date_box, wx.VERTICAL)
        self.end_date_sizer = wx.StaticBoxSizer(self.end_date_box, wx.VERTICAL)
        self.start_date_sizer.Add(self.dpc_start_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.end_date_sizer.Add(self.dpc_end_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTimeæ ¼å¼"03/03/18 00:00:00"
        self.dpc_end_time.SetValue(date_time_now)
        self.dpc_start_time.SetValue(date_time_now.SetYear(date_time_now.year - 1))

        # è¡æåæ°ââè¾å¥è¡ç¥¨ä»£ç 
        self.stock_code_box = wx.StaticBox(self.ParaStPanel, -1, u'è¡ç¥¨ä»£ç ')
        self.stock_code_sizer = wx.StaticBoxSizer(self.stock_code_box, wx.VERTICAL)
        self.stock_code_input = wx.TextCtrl(self.ParaStPanel, -1, "sz.000876", style=wx.TE_PROCESS_ENTER)
        self.stock_code_sizer.Add(self.stock_code_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.stock_code_input.Bind(wx.EVT_TEXT_ENTER, self.enter_stcode)

        # è¡æåæ°ââè¡ç¥¨å¨æéæ©
        self.stock_period_box = wx.StaticBox(self.ParaStPanel, -1, u'è¡ç¥¨å¨æ')
        self.stock_period_sizer = wx.StaticBoxSizer(self.stock_period_box, wx.VERTICAL)
        self.stock_period_cbox = wx.ComboBox(self.ParaStPanel, -1, u"", choices=[u"30åé", u"60åé", u"æ¥çº¿", u"å¨çº¿"])
        self.stock_period_cbox.SetSelection(2)
        self.stock_period_sizer.Add(self.stock_period_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # è¡æåæ°ââè¡ç¥¨å¤æéæ©
        self.stock_authority_box = wx.StaticBox(self.ParaStPanel, -1, u'è¡ç¥¨å¤æ')
        self.stock_authority_sizer = wx.StaticBoxSizer(self.stock_authority_box, wx.VERTICAL)
        self.stock_authority_cbox = wx.ComboBox(self.ParaStPanel, -1, u"", choices=[u"åå¤æ", u"åå¤æ", u"ä¸å¤æ"])
        self.stock_authority_cbox.SetSelection(2)
        self.stock_authority_sizer.Add(self.stock_authority_cbox, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # è¡æåæ°ââå¤å­å¾æ¾ç¤º
        self.pick_graph_box = wx.StaticBox(self.ParaStPanel, -1, u'å¤å­å¾æ¾ç¤º')
        self.pick_graph_sizer = wx.StaticBoxSizer(self.pick_graph_box, wx.VERTICAL)
        self.pick_graph_cbox = wx.ComboBox(self.ParaStPanel, -1, u"æªå¼å¯", choices=[u"æªå¼å¯", u"Aè¡ç¥¨èµ°å¿", u"Bè¡ç¥¨èµ°å¿", u"Cè¡ç¥¨èµ°å¿", u"Dè¡ç¥¨èµ°å¿"],
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

        # åæµåæ°
        back_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.init_cash_box = wx.StaticBox(self.ParaBtPanel, -1, u'åå§èµé')
        self.init_cash_sizer = wx.StaticBoxSizer(self.init_cash_box, wx.VERTICAL)
        self.init_cash_input = wx.TextCtrl(self.ParaBtPanel, -1, "100000", style=wx.TE_LEFT)
        self.init_cash_sizer.Add(self.init_cash_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_stake_box = wx.StaticBox(self.ParaBtPanel, -1, u'äº¤æè§æ¨¡')
        self.init_stake_sizer = wx.StaticBoxSizer(self.init_stake_box, wx.VERTICAL)
        self.init_stake_input = wx.TextCtrl(self.ParaBtPanel, -1, "all", style=wx.TE_LEFT)
        self.init_stake_sizer.Add(self.init_stake_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_slippage_box = wx.StaticBox(self.ParaBtPanel, -1, u'æ»ç¹')
        self.init_slippage_sizer = wx.StaticBoxSizer(self.init_slippage_box, wx.VERTICAL)
        self.init_slippage_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.01", style=wx.TE_LEFT)
        self.init_slippage_sizer.Add(self.init_slippage_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_commission_box = wx.StaticBox(self.ParaBtPanel, -1, u'æç»­è´¹')
        self.init_commission_sizer = wx.StaticBoxSizer(self.init_commission_box, wx.VERTICAL)
        self.init_commission_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.0005", style=wx.TE_LEFT)
        self.init_commission_sizer.Add(self.init_commission_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        self.init_tax_box = wx.StaticBox(self.ParaBtPanel, -1, u'å°è±ç¨')
        self.init_tax_sizer = wx.StaticBoxSizer(self.init_tax_box, wx.VERTICAL)
        self.init_tax_input = wx.TextCtrl(self.ParaBtPanel, -1, "0.001", style=wx.TE_LEFT)
        self.init_tax_sizer.Add(self.init_tax_input, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # åæµæé®
        self.start_back_but = wx.Button(self.ParaBtPanel, -1, "å¼å§åæµ")
        self.start_back_but.Bind(wx.EVT_BUTTON, self.start_run)  # ç»å®æé®äºä»¶

        back_para_sizer.Add(self.init_cash_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_stake_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_slippage_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_commission_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.init_tax_sizer, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        back_para_sizer.Add(self.start_back_but, proportion=0, flag=wx.EXPAND|wx.ALL|wx.CENTER, border=10)
        self.ParaBtPanel.SetSizer(back_para_sizer)

    def add_pick_para_lay(self):

        # éè¡åæ°
        pick_para_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # éè¡åæ°ââæ¥åæ§ä»¶æ¶é´å¨æ
        self.dpc_cur_time = wx.adv.DatePickerCtrl(self.ParaPtPanel, -1,
                                                  style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY | wx.adv.DP_ALLOWNONE)  # å½åæ¶é´

        self.cur_date_box = wx.StaticBox(self.ParaPtPanel, -1, u'å½åæ¥æ(Start)')
        self.cur_date_sizer = wx.StaticBoxSizer(self.cur_date_box, wx.VERTICAL)
        self.cur_date_sizer.Add(self.dpc_cur_time, proportion=0, flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        date_time_now = wx.DateTime.Now()  # wx.DateTimeæ ¼å¼"03/03/18 00:00:00"
        self.dpc_cur_time.SetValue(date_time_now)
        # self.dpc_cur_time.SetValue(date_time_now.SetDay(9)) # ä»¥9æ¥ä¸ºä¾ åä¸èèå¨æ«çå¹²æ°

        # éè¡åæ°ââæ¡ä»¶è¡¨è¾¾å¼åæ
        self.pick_stock_box = wx.StaticBox(self.ParaPtPanel, -1, u'æ¡ä»¶è¡¨è¾¾å¼éè¡')
        self.pick_stock_sizer = wx.StaticBoxSizer(self.pick_stock_box, wx.HORIZONTAL)
        self.pick_item_cmbo = wx.ComboBox(self.ParaPtPanel, -1, self.filter[0], choices=self.filter,
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)  # éè¡é¡¹
        self.pick_cond_cmbo = wx.ComboBox(self.ParaPtPanel, -1, u"å¤§äº",
                                          choices=[u"å¤§äº", u"ç­äº", u"å°äº"],
                                          style=wx.CB_READONLY | wx.CB_DROPDOWN)  # éè¡æ¡ä»¶
        self.pick_value_text = wx.TextCtrl(self.ParaPtPanel, -1, "0", style=wx.TE_LEFT)

        self.sort_values_cmbo = wx.ComboBox(self.ParaPtPanel, -1, u"ä¸æå",
                                            choices=[u"ä¸æå", u"ååº", u"éåº"],
                                            style=wx.CB_READONLY | wx.CB_DROPDOWN)  # æåæ¡ä»¶

        self.pick_stock_sizer.Add(self.pick_item_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_cond_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.pick_value_text, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)
        self.pick_stock_sizer.Add(self.sort_values_cmbo, proportion=0,
                                  flag=wx.EXPAND | wx.ALL | wx.CENTER, border=2)

        # éè¡æé®
        self.start_pick_but = wx.Button(self.ParaPtPanel, -1, "å¼å§éè¡")
        self.start_pick_but.Bind(wx.EVT_BUTTON, self.start_select)  # ç»å®æé®äºä»¶

        # å¤ä½æé®
        self.start_reset_but = wx.Button(self.ParaPtPanel, -1, "å¤ä½æ¡ä»¶")
        self.start_reset_but.Bind(wx.EVT_BUTTON, self.start_reset)  # ç»å®æé®äºä»¶

        # ä¿å­æé®
        self.start_save_but = wx.Button(self.ParaPtPanel, -1, "ä¿å­ç»æ")
        self.start_save_but.Bind(wx.EVT_BUTTON, self.start_save)  # ç»å®æé®äºä»¶

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
        self.grid_pl.SetColLabelValue(0, "ä»£ç ")
        self.grid_pl.SetColLabelValue(1, "åç§°")

        for m_k, m_v in basic.items():
            st_name_code_dict = m_v
            for s_k, s_v in st_name_code_dict.items():
                self.grid_pl.InsertRows(i, 2)
                self.grid_pl.SetCellValue(i, 0, s_k)
                self.grid_pl.SetCellValue(i, 1, s_v)
                i = i + 1
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.click_stcode, self.grid_pl)

    def init_grid_pk(self):
        # åå§åéè¡è¡¨æ ¼
        self.grid_pk = wx.grid.Grid(self, -1)
        self.df_use = pd.DataFrame()
        self.filte_result = pd.DataFrame()

    def init_grid_pl(self):
        # åå§åè¡ç¥¨æ± è¡¨æ ¼
        dict_basic = Base_File_Oper.load_sys_para("stock_self_pool.json")
        self.data_pl_grid(dict_basic)

    def get_stdat(self, st_code):
        # è·åè¡ç¥¨æ°æ®
        sdate_obj = self.dpc_start_time.GetValue()
        sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)
        edate_obj = self.dpc_end_time.GetValue()
        edate_val = datetime.datetime(edate_obj.year, edate_obj.month + 1, edate_obj.day)

        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()

        if st_period == "30åé":
            period_val = "30"
        elif st_period == "60åé":
            period_val = "60"
        elif st_period == "æ¥çº¿":
            period_val = "d"
        elif st_period == "å¨çº¿":
            period_val = "w"
        else:
            period_val = "d"

        if st_auth == "åå¤æ":
            auth_val = "2"
        elif st_auth == "åå¤æ":
            auth_val = "1"
        elif st_auth == "ä¸å¤æ":
            auth_val = "3"
        else:
            auth_val = "3"

        try:
            df = bs_k_data_stock(st_code, start_val=sdate_val.strftime('%Y-%m-%d'),
                                          end_val=edate_val.strftime('%Y-%m-%d'),
                                          freq_val=period_val, adjust_val=auth_val)

        except:
            self.MessageDiag("è¾å¥åæ°æè¯¯ï¼")
            df = pd.DataFrame()

        return df

    def enter_stcode(self, event):

        st_code = self.stock_code_input.GetValue()

        st_period = self.stock_period_cbox.GetStringSelection()
        st_auth = self.stock_authority_cbox.GetStringSelection()

        df_stockDat = self.get_stdat(st_code)

        if self.pick_graph_cbox.GetSelection() != 0:
            self.clear_subgraph(0)  # å¿é¡»æ¸çå¾å½¢æè½æ¾ç¤ºä¸ä¸å¹å¾
            self.draw_subgraph(df_stockDat, st_code, st_period + st_auth)
        else:

            self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.firm_para['layout_dict']))
            self.DispPanel = self.sw_panel_last
            self.firm_para['subplots_dict']['graph_fst']['title'] = st_code + st_period + st_auth
            self.DispPanel.firm_graph_run(df_stockDat,  **self.firm_para['subplots_dict'])

        self.update_subgraph(0)  # å¿é¡»å·æ°æè½æ¾ç¤ºä¸ä¸å¹å¾


    def update_subgraph(self, sub):
        if sub == 0:
            self.DispPanel.FigureCanvas.draw()
        elif sub == 1:
            self.GroupPanel.FigureCanvas.draw()

    def clear_subgraph(self, sub):
        # åæ¬¡ç»å¾å,å¿é¡»è°ç¨è¯¥å½ä»¤æ¸ç©ºåæ¥çå¾å½¢
        if sub == 0:
            self.ochl.clear()
            self.vol.clear()
        elif sub == 1:
            self.GroupPanel.relate.clear()

    def draw_subgraph(self, stockdat, st_name, st_kylabel):
        # ç»å¶å¤å­å¾é¡µé¢
        num_bars = np.arange(0, len(stockdat.index))

        # ç»å¶Kçº¿
        ohlc = list(zip(num_bars, stockdat.Open, stockdat.Close, stockdat.High, stockdat.Low))
        mpf.candlestick_ochl(self.ochl, ohlc, width=0.5, colorup='r', colordown='g')  # ç»å¶Kçº¿èµ°å¿

        # ç»å¶æäº¤é
        self.vol.bar(num_bars, stockdat.Volume, color=['g' if stockdat.Open[x] > stockdat.Close[x] else 'r' for x in
                                                    range(0, len(stockdat.index))])

        self.ochl.set_ylabel(st_kylabel)
        self.vol.set_ylabel(u"æäº¤é")
        self.ochl.set_title(st_name + " è¡æèµ°å¿å¾")

        major_tick = len(num_bars)
        self.ochl.set_xlim(0, major_tick)  # è®¾ç½®ä¸ä¸xè½´çèå´
        self.vol.set_xlim(0, major_tick)  # è®¾ç½®ä¸ä¸xè½´çèå´

        self.ochl.set_xticks(range(0, major_tick, 15))  # æ¯äºå¤©æ ä¸ä¸ªæ¥æ
        self.vol.set_xticks(range(0, major_tick, 15))  # æ¯äºå¤©æ ä¸ä¸ªæ¥æ
        self.vol.set_xticklabels(
            [stockdat.index.strftime('%Y-%m-%d')[index] for index in self.vol.get_xticks()])  # æ ç­¾è®¾ç½®ä¸ºæ¥æ

        for label in self.ochl.xaxis.get_ticklabels():  # X-è½´æ¯ä¸ªtickeræ ç­¾éè
            label.set_visible(False)
        for label in self.vol.xaxis.get_ticklabels():  # X-è½´æ¯ä¸ªtickeræ ç­¾éè
            label.set_rotation(45)  # X-è½´æ¯ä¸ªtickeræ ç­¾é½åå³å¾æ45åº¦
            label.set_fontsize(10)  # è®¾ç½®æ ç­¾å­ä½

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
                self.grid_pk.AutoSizeColumn(m, True)  # èªå¨è°æ´åå°ºå¯¸

    def MessageDiag(self, info):

        dlg_mesg = wx.MessageDialog(None, info, u"æ¸©é¦¨æç¤º",
                                    wx.YES_NO | wx.ICON_INFORMATION)
        if dlg_mesg.ShowModal() == wx.ID_YES:
            print("ç¹å»Yes")
        else:
            print("ç¹å»No")
        dlg_mesg.Destroy()

    def switch_main_panel(self, org_panel=None, new_panel=None):

        if id(org_panel) != id(new_panel):

            self.vbox_sizer_b.Hide(org_panel)
            # æ¹æ¡ä¸ åå é¤åæ·»å 
            self.vbox_sizer_b.Detach(org_panel)
            self.vbox_sizer_b.Add(new_panel, proportion=10, flag=wx.EXPAND | wx.BOTTOM, border=5)
            # æ¹æ¡äº ç­ç±»åå¯æ¿æ¢
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
            self.clear_subgraph(0)  # å¿é¡»æ¸çå¾å½¢æè½æ¾ç¤ºä¸ä¸å¹å¾
            self.draw_subgraph(df_stockDat, st_name, st_period + st_auth)
        else:

            self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.firm_para['layout_dict']))
            self.DispPanel = self.sw_panel_last
            self.firm_para['subplots_dict']['graph_fst']['title'] = st_name + st_period + st_auth
            self.DispPanel.firm_graph_run(df_stockDat,  **self.firm_para['subplots_dict'])

        self.update_subgraph(0)  # å¿é¡»å·æ°æè½æ¾ç¤ºä¸ä¸å¹å¾

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
        # ç¹å»è¿è¡åæµ
        cash_value = self.init_cash_input.GetValue()
        stake_value = self.init_stake_input.GetValue()
        slippage_value = self.init_slippage_input.GetValue()
        commission_value = self.init_commission_input.GetValue()
        tax_value = self.init_tax_input.GetValue()
        st_code = self.stock_code_input.GetValue()

        #self.backtrader_excetue(df_stockDat, sdate_val, edate_val, cash_value, trade_value, commission_value)

        # æ´æ°GUIçåæµåæ° å¹¶ä¸ä¿å­
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['cash_hold'] = cash_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['slippage'] = slippage_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['c_rate'] = commission_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['t_rate'] = tax_value
        self.back_para['subplots_dict']['graph_sec']['graph_type']['cash_profit']['stake_size'] = stake_value
        self.back_para['subplots_dict']['graph_fst']['title'] = st_code + "-åæµåæ"

        Base_File_Oper.save_sys_para("back_para.json", self.back_para)

        self.switch_main_panel(self.sw_panel_last, Sys_Panel(self, **self.back_para['layout_dict']))
        self.DispPanel = self.sw_panel_last

        self.DispPanel.back_graph_run(Base_Strategy_Group.get_ndays_signal(self.get_stdat(st_code)), **self.back_para['subplots_dict'])
        # ä¿®æ¹å¾å½¢çä»»ä½å±æ§åé½å¿é¡»æ´æ°GUIçé¢
        self.DispPanel.FigureCanvas.draw()

        self.backt_info_Tinput.Clear()
        self.backt_info_Tinput.AppendText(Base_File_Oper.read_log_trade())

        # self.clear_subgraph() # å¿é¡»æ¸çå¾å½¢æè½æ¾ç¤ºä¸ä¸å¹å¾
        # self.draw_backTest(df_recon, st_code)
        # self.update_subgraph() # å¿é¡»å·æ°æè½æ¾ç¤ºä¸ä¸å¹å¾

    def start_select(self, event):

        if self.df_use.empty != True:
            for key, val in self.tran_col.items():
                if val == self.pick_item_cmbo.GetStringSelection():

                    para_value = float(self.pick_value_text.GetValue())

                    if self.pick_cond_cmbo.GetStringSelection() == u"å¤§äº":
                        self.filte_result = self.df_use[self.df_use[key] > para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"å°äº":
                        self.filte_result = self.df_use[self.df_use[key] <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
< para_value]
                    elif self.pick_cond_cmbo.GetStringSelection() == u"ç­äº":
                        self.filte_result = self.df_use[self.df_use[key] == para_value]
                    else:
                        pass

                    if self.sort_values_cmbo.GetStringSelection() == u"éåº":
                        self.filte_result.sort_values(by=key, axis='index', ascending=False, inplace=True,
                                                      na_position='last')
                    elif self.sort_values_cmbo.GetStringSelection() == u"ååº":
                        self.filte_result.sort_values(by=key, axis='index', ascending=True, inplace=True,
                                                      na_position='last')
                    else:
                        pass
                    self.refresh_grid(self.filte_result)
                    self.df_use = self.filte_result
                    break

    def start_reset(self, event):
        # å¤ä½éè¡æé®äºä»¶
        sdate_obj = self.dpc_cur_time.GetValue()
        sdate_val = datetime.datetime(sdate_obj.year, sdate_obj.month + 1, sdate_obj.day)

        self.df_join = self.datafame_join(sdate_val.strftime('%Y%m%d'))  # å·æ°self.df_join

        if self.df_join.empty == True:
            self.MessageDiag("è¯¥æ¥æ æ°æ®")

        self.df_use = self.df_join
        self.refresh_grid(self.df_use)

    def start_save(self, event):
        # ä¿å­éè¡æé®äºä»¶
        codes = self.df_use.ts_code.values
        names = self.df_use.name.values
        st_name_code_dict = dict(zip(names, codes))

        for k, v in st_name_code_dict.items():
            code_split = v.lower().split(".")
            st_name_code_dict[k] = code_split[1] + "." + code_split[0] # tushareè½¬baostock

        dict_basic = Base_File_Oper.load_sys_para("stock_self_pool.json")
        dict_basic['è¡ç¥¨'].clear()
        dict_basic['è¡ç¥¨'].update(st_name_code_dict)

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

