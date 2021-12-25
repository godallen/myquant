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
import wx.gizmos

from QTYX_MultiGraphs import Sys_MultiGraph

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class StockPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=-1)

        # 分割子图实现代码
        self.figure = Figure(figsize=(8, 5))
        gs = gridspec.GridSpec(2, 1, left=0.1, bottom=0.15, right=0.95, top=0.90, wspace=None, hspace=0.1,
                               height_ratios=[3.5, 1])
        self.ochl = self.figure.add_subplot(gs[0, :])
        self.vol = self.figure.add_subplot(gs[1, :])

        self.FigureCanvas = FigureCanvas(self, -1, self.figure)  # figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas, proportion=10, border=2, flag=wx.ALL | wx.EXPAND)

        self.SetSizer(self.TopBoxSizer)

class SubGraphs(wx.Panel):
    def __init__(self, parent):

        # 创建FlexGridSizer布局网格 vgap定义垂直方向上行间距/hgap定义水平方向上列间距
        self.FlexGridSizer = wx.FlexGridSizer(rows=2, cols=2, vgap=1, hgap=1)
        self.DispPanel0 = StockPanel(parent)  # 自定义
        self.DispPanel1 = StockPanel(parent)  # 自定义
        self.DispPanel2 = StockPanel(parent)  # 自定义
        self.DispPanel3 = StockPanel(parent)  # 自定义

        # 加入Sizer中
        self.FlexGridSizer.Add(self.DispPanel0, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel1, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel2, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.Add(self.DispPanel3, proportion=1, border=2,
                               flag=wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        self.FlexGridSizer.SetFlexibleDirection(wx.BOTH)

class GroupPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=-1)

        # 分割子图实现代码
        self.figure = Figure(figsize=(8, 8))

        self.relate = self.figure.add_subplot(1, 1, 1)

        self.FigureCanvas = FigureCanvas(self, -1, self.figure)  # figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas, proportion=10, border=2, flag=wx.ALL | wx.EXPAND)

        self.SetSizer(self.TopBoxSizer)

class Sys_Panel(Sys_MultiGraph, wx.Panel):
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent=parent, id=-1)
        Sys_MultiGraph.__init__(self, **kwargs)

        self.FigureCanvas = FigureCanvas(self, -1, self.fig)#figure加到FigureCanvas
        self.TopBoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.TopBoxSizer.Add(self.FigureCanvas,proportion = -1, border = 2,flag = wx.ALL | wx.EXPAND)
        self.SetSizer(self.TopBoxSizer)

class CollegeTreeListCtrl(wx.gizmos.TreeListCtrl):

    def __init__(self, parent=None, id=-1, pos=(0, 0), size=wx.DefaultSize,
                 style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT):

        wx.gizmos.TreeListCtrl.__init__(self, parent, id, pos, size, style)

        self.root = None
        self.InitUI()
        pass

    def InitUI(self):
        self.il = wx.ImageList(16, 16, True)
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16)))
        self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        self.SetImageList(self.il)
        self.AddColumn(u'名称')
        self.AddColumn(u'类型')
        self.AddColumn(u'函数')
        self.SetColumnWidth(0, 150)
        self.SetColumnWidth(1, 60)
        self.SetColumnWidth(2, 140)
        pass

    def refDataShow(self, newDatas):
        # if self.root != None:
        #    self.DeleteAllItems()

        if newDatas != None:
            self.root = self.AddRoot(u'择时策略')
            self.SetItemText(self.root, "", 1) # 第1列上添加
            self.SetItemText(self.root, "", 2) # 第2列上添加

            for cityID in newDatas.keys():# 填充整个树
                child = self.AppendItem(self.root, cityID)
                lastList = newDatas.get(cityID, [])
                self.SetItemText(child, cityID + u" (共" + str(len(lastList)) + u"个)", 0)
                self.SetItemImage(child, 0, which=wx.TreeItemIcon_Normal) # wx.TreeItemIcon_Expanded

                for index in range(len(lastList)):
                    college = lastList[index]  # TreeItemData是每一个ChildItem的唯一标示
                    # 以便在点击事件中获得点击项的位置信息
                    # "The TreeItemData class no longer exists, just pass your object directly to the tree instead
                    # data = wx.TreeItemData(cityID + "|" + str(index))
                    last = self.AppendItem(child, str(index), data=cityID + "|" + str(index))
                    self.SetItemText(last, college.get('名称', ''), 0)
                    self.SetItemText(last, college.get('类型', ''), 1)
                    self.SetItemText(last, str(college.get('函数', '')), 2)
                    self.SetItemImage(last, 0, which=wx.TreeItemIcon_Normal) # wx.TreeItemIcon_Expanded
                    self.Expand(self.root)
                    pass
