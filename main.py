#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
from PySide import QtGui, QtCore
import pandas as pd
import inspect
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib as mpl
import matplotlib.dates as mdates
import time



class Data(object):


    def __init__(self):
        self.filename = None
        self.df = pd.DataFrame()
        self.edit_df = pd.DataFrame()
        self.xrange = []
        self.operation_sender = ""
        self.nto = ""
        self.selected_col = ""
        self.freq = None

    def Read(self, fname):
        self.filename = fname
        self.df = pd.read_csv(fname)
        self.edit_df = self.df.copy()
        self.log = {col: {"normalise" : None, "cal" : [], "bg" : [], "NaN" : []} for col in self.df.columns}

    def Save(self, filepath):

        self.edit_df.to_csv(filepath, index=False)
        # save log too
        pd.DataFrame(self.log).transpose().to_csv(filepath[:filepath.find(".")]+"_log"+filepath[filepath.find("."):])


    def SetDatetimeIndex(self, column):
        self.edit_df.set_index(pd.DatetimeIndex(self.edit_df[column]), inplace=True)
        del self.edit_df.index.name

    def Reset(self):
        for c in self.selected_col:
            self.log[c]["normalise"] = None
            self.log[c]["NaN"] = []
            self.log[c]["bg"] = []
            self.log[c]["cal"] = []
        self.edit_df[self.selected_col] = self.df[self.selected_col].copy().values

    def GetStartEnd(self, s, e):
        """
        Get entries between (s)tart and (e)nd time. df requires datetime index. Default values of
        s and e take first and last entries of the df. Threshold changed where the value is made null.
        """
        # check whether the index is datetime or not and adjust the index accordingly
        print "s: ",s, type(s)
        print "e: ",e, type(e)

        if isinstance(self.edit_df.index, pd.DatetimeIndex):
            print "datetime index"
            s, e = mdates.num2date(s).replace(microsecond=0), mdates.num2date(e).replace(microsecond=0)
        elif isinstance(self.edit_df.index, pd.PeriodIndex):
            print "PERIOD INDEX YOU IDIOT"
        else:
            s, e = int(s), int(e)
        print "s: ",s
        print "e: ",e
        return s, e

    def Stats(self, s=None, e=None):
        """Provides descriptive statistics between S and E if provided or entire dataframe if not."""
        if not s and not e:
            return self.edit_df[self.selected_col].describe()
        else:
            return self.edit_df.loc[(self.edit_df.index > s) & (self.edit_df.index < e), self.selected_col].describe()

    def nan_points(self, s, e):
        """NaN points between S and E."""
        # if self.threshold:
        #     threshold = self.threshold
        # else:
        threshold=1e20
        self.edit_df.loc[(self.edit_df.index > s) & (self.edit_df.index < e), self.selected_col] = np.nan

    def Resample(self, freq):
        """Average up dataframe."""
        self.edit_df = self.edit_df.resample(freq).mean()

    def RemoveBackground(self, bg, s, e):
        """Remove bg from points between S and E."""
        self.edit_df.loc[(self.edit_df.index > s) & (self.edit_df.index < e), self.selected_col] -= bg

    def Calibrate(self, cf, s, e):
        """Calibrate points between S and E."""
        self.edit_df.loc[(self.edit_df.index > s) & (self.edit_df.index < e), self.selected_col] /= cf

    def Normalise(self, operation):

        col = self.selected_col
        nto = self.nto
        denominator = (np.nanmean(self.df[nto]) / self.df[self.nto]).values

        if operation == "/":
            print "{} normalised to {}".format(col, nto)
            self.edit_df[col] = self.edit_df[col].multiply(denominator, axis=0)
            for c in col:
                self.log[c]["normalise"] = nto

        elif operation == "*":
            print "{} unnormalised to {}".format(col, nto)
            self.edit_df[col] = self.edit_df[col].div(denominator, axis=0)
            for c in col:
                self.log[c]["normalise"] = None
        else:
            print "incorrect operation"



class LoadButton(QtGui.QWidget):

    dataLoaded = QtCore.Signal()

    def __init__(self):
        super(LoadButton, self).__init__() #Initialise parent
        self.button = QtGui.QPushButton("Load", self) #Initalse button
        self.button.pressed.connect(self.Open) #Connect pressed button to Open method
        self.filepath = ""
        self.filename = ""

    def Open(self):
        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', "../")
        if not self.filename:
            return

        self.filepath = os.path.normpath(str(self.filename[0]))
        print 'Path file :', self.filepath


        self.dataLoaded.emit()




class ExportButton(QtGui.QWidget):

    dataSaved = QtCore.Signal()

    def __init__(self):
        super(ExportButton, self).__init__() #Initialise parent
        self.button = QtGui.QPushButton("Export", self) #Initalse button
        self.button.pressed.connect(self.Save) #Connect pressed button to Open method
        self.filepath = "nothing"

    def Save(self):
        filename = QtGui.QFileDialog.getSaveFileName(self)
        if not filename:
            return

        self.filepath = os.path.normpath(str(filename[0]))
        print 'Path file :', self.filepath
        self.dataSaved.emit()


class TimeSeriesList(QtGui.QWidget):

    def __init__(self):
        super(TimeSeriesList, self).__init__()
        self.list = QtGui.QListWidget(self)
        self.list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # extra interaction

    def PopulateList(self, ls):
        self.list.clear()
        self.list.insertItems(len(ls), ls)
        for index in range(self.list.count()):  # make list editable
            item = self.list.item(index)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)


class clicker_class(object):
    def __init__(self, ax):
        self.ax = ax
        if isinstance(self.ax, np.ndarray):
            self.canvas = ax[0].get_figure().canvas
        else:
            self.canvas = ax.get_figure().canvas
        self.cid = None
        self.pt_lst_x = []
        self.axis_variable_name = ""
        self.connect_sf()

    def clear(self):
        '''Clears the points'''
        self.pt_lst_x = []

    def connect_sf(self):
        if self.cid is None:
            self.cid = self.canvas.mpl_connect('button_press_event',
                                               self.click_event)

    def disconnect_sf(self):
        if self.cid is not None:
            self.canvas.mpl_disconnect(self.cid)
            self.cid = None

    def click_event(self, event):
        """Extracts locations from the user"""

        self.axis_variable_name = event.inaxes.get_legend().texts # returns column name of df where data in the axis is from
        if event.xdata is None or event.ydata is None:
            return
        if event.button == 1:
            print event.xdata, type(event.xdata)
            self.pt_lst_x.append((event.xdata, event.ydata))
        elif (event.button == 3):
            self.RemoveAXVline()
            self.clear()

        if len(self.pt_lst_x) > 2:
            self.RemoveAXVline()
            self.clear()

        self.DrawAXVline()

    def RemoveAXVline(self):
        """Removes axv lines from plot."""
        # delete the last two lines which should be the markers to nan
        for i in range(10):
            if isinstance(self.ax, np.ndarray):
                [ax.lines.remove(l) for ax in self.ax for l in ax.lines if l._gid == "axvline"]
            else:
                [self.ax.lines.remove(l) for l in self.ax.lines if l._gid == "axvline"]

        self.canvas.draw()

    def DrawAXVline(self):
        if isinstance(self.ax, np.ndarray):
            for axis in self.ax:
                 [axis.axvline(x[0], color="k", linestyle="--", linewidth=0.5, gid="axvline") for x in self.pt_lst_x]
        else:
            [self.ax.axvline(x[0], color="k", linestyle="--", linewidth=0.5, gid="axvline") for x in self.pt_lst_x]
        self.canvas.draw()

    def return_points(self):
        '''Returns the clicked points in the format the rest of the code expects.'''
        print np.vstack(self.pt_lst_x).T
        return np.vstack(self.pt_lst_x).T


class MessageWindow(QtGui.QWidget):

    def __init__(self):
        super(MessageWindow, self).__init__()
        self.window = QtGui.QTextEdit()
        self.window.setReadOnly(True)

    # def CreateEntry(self, text):
    #     """Inserts text into window."""
    #     self.data.log[self.selected_col]["log"].append(text)

    # def ReadAllEntries(self):
    #     return self.data.log[self.selected_col]["log"]

    # def DeleteAllEntries(self, text):
    #     """Deletes all text in window."""
    #     self.data.log[self.selected_col]["log"] = []



class MainWindow(QtGui.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.color_active = "#4286f4"
        self.initUI()
        self.subplots = False
        self.legend = False

    @QtCore.Slot()
    def readData(self):
        """Read data into dataobj and populate list widget."""
        self.data.Read(self.load_button.filepath)
        self.trace_list.PopulateList(self.data.df.columns)
        self.export_button.button.setEnabled(True) # default is off

    @QtCore.Slot()
    def saveData(self):
        """Read data into dataobj and populate list widget."""
        self.data.Save(self.export_button.filepath)

    @QtCore.Slot()
    def DisplayData(self, **kwargs):
        """Plot data onto canvas"""
        self.canvas.figure.clear()
        self.ax = self.canvas.figure.subplots()

        if hasattr(self, "cc"):
            self.cc.ax = self.ax # update the clicker class with new axis
        self.data.selected_col = [str(x.text()) for x in self.trace_list.list.selectedItems()]

        
        if self.subplots:
            kwargs = {"subplots":True, "sharex":True}
        


        # actually plot
        self.ax = self.data.edit_df[self.data.selected_col].plot(ax=self.ax, **kwargs)

        # takes care of legend y axis label switching
        if not self.subplots:
            self.ax.set_ylabel(self.data.selected_col[0])
            if self.legend:
                self.ax.legend().set_visible(True)
            else:
                self.ax.legend().set_visible(False)
        else:
            for i in range(len(self.ax)):
                self.ax[i].set_ylabel(self.data.selected_col[i])
                if self.legend:
                    self.ax[i].legend().set_visible(True)
                else:
                    self.ax[i].legend().set_visible(False)

        if hasattr(self, "cc"):
            self.cc.ax = self.ax # update the clicker class with new axis

        self.canvas.figure.autofmt_xdate()
        self.canvas.draw_idle()
        self.canvas.figure.tight_layout()
        self.ReadMessages()
        self.GetStats()
        print "selected columns:", self.data.selected_col


    @QtCore.Slot()
    def SetTimeAxis(self):
        """Set x axis on dataframe to datetime"""
        self.data.SetDatetimeIndex(str(self.trace_list.list.currentItem().text()))
        self.time_axis_button.setStyleSheet("background-color: "+self.color_active)
        self.average_button.setEnabled(True)

    @QtCore.Slot()
    def SeparateAxes(self):
        """toggle multiple traces to subplots"""
        if not self.sep_axes_button.isChecked():
            self.subplots=True # set flag
            self.sep_axes_button.setStyleSheet("background-color: "+self.color_active)
        else:
            self.subplots=False # set flag
            self.sep_axes_button.setStyleSheet("background-color: None")
            self.nan_mode_button.setEnabled(True)
        self.DisplayData()


    @QtCore.Slot()
    def ToggleLegend(self):

        if not self.legend_button.isChecked():
            self.legend=True # set flag
            self.legend_button.setStyleSheet("background-color: "+self.color_active)
        else:
            self.legend=False # set flag
            self.legend_button.setStyleSheet("background-color: None")
            self.legend_button.setEnabled(True)
        self.DisplayData()





    @QtCore.Slot()
    def RemoveColumn(self):
        """Remove column from dataframe."""
        col = [str(x.text()) for x in self.trace_list.list.selectedItems()]
        self.data.edit_df.drop(col, inplace=True, axis=1)
        self.trace_list.PopulateList(self.data.edit_df.columns)


    @QtCore.Slot()
    def Rename(self):
        """Rename dataframe col from list widget."""
        if self.trace_list.list.currentItem() is None:
            return

        new = unicode(self.trace_list.list.currentItem().text())
        old = self.data.selected_col[0]

        self.data.edit_df.rename(columns={old:new}, inplace=True)
        self.data.df.rename(columns={old:new}, inplace=True)
        self.data.log[new] = self.data.log.pop(old)

    @QtCore.Slot()
    def ResetDF(self):
        """Undo all changes to dataframe and redraw."""
        # Reset Widgets
        self.nan_mode_button.setStyleSheet("background-color: None")
        self.bg_mode_button.setStyleSheet("background-color: None")
        self.normalise_button.setStyleSheet("background-color: None")
        self.cal_mode_button.setStyleSheet("background-color: None")

        self.nan_mode_button.setChecked(False)
        self.nan_mode_button.setEnabled(True)
        self.NaN_button.setEnabled(False) # when the points are collected, enable the button

        self.bg_mode_button.setChecked(False) # when the points are collected, enable the button
        self.bg_mode_button.setEnabled(True)
        self.set_bg_val_button.setEnabled(False) # when the points are collected, enable the button
        self.get_bg_val_button.setEnabled(False) # when the points are collected, enable the button
        self.bg_text_field.setEnabled(False) # when the points are collected, enable the button

        self.normalise_button.setChecked(False)

        self.cal_mode_button.setChecked(False) # when the points are collected, enable the button
        self.cal_mode_button.setEnabled(True)
        self.cal_text_field.setEnabled(False) # when the points are collected, enable the button
        self.set_cal_val_button.setEnabled(False) # when the points are collected, enable the button

        # Reset data
        self.data.Reset()
        self.DisplayData()
        self.freq = None

    @QtCore.Slot()
    def NanMode(self):
        """Activates extra buttons and functionality to allow nanning."""
        if hasattr(self, "ax"):
            self.cc = clicker_class(ax=self.ax)

            self.cc.disconnect_sf()
            self.nan_mode_button.setStyleSheet("background-color: None")
            self.nan_mode_annotation = ""
            self.NaN_button.setEnabled(False) # when the points are collected, enable the button
            self.bg_mode_button.setEnabled(True) # when the points are collected, enable the button
            self.cal_mode_button.setEnabled(True) # when the points are collected, enable the button
            self.cal_text_field.setEnabled(False) # when the points are collected, enable the button
            self.set_cal_val_button.setEnabled(False) # when the points are collected, enable the button

            if not self.nan_mode_button.isChecked():
                self.cc.connect_sf()
                self.nan_mode_button.setStyleSheet("background-color: "+self.color_active)
                self.nan_mode_annotation = "NaN mode On. Click and drag to make selection.\nPress NaN button to remove data between selection.\nRight click to remove selection"
                self.NaN_button.setEnabled(True) # when the points are collected, enable the button
                self.bg_mode_button.setEnabled(False) # when the points are collected, enable the button
                self.set_bg_val_button.setEnabled(False) # when the points are collected, enable the button
                self.get_bg_val_button.setEnabled(False) # when the points are collected, enable the button
                self.bg_text_field.setEnabled(False) # when the points are collected, enable the button
                self.cal_mode_button.setEnabled(False) # when the points are collected, enable the button


    @QtCore.Slot()
    def Nan_points(self):
        """Extract points and nans them."""
        if len(self.cc.pt_lst_x) == 2:
            xrang = self.cc.return_points()[0]
            s, e = self.data.GetStartEnd(xrang[0], xrang[1])
            for col in self.data.selected_col:
                self.data.log[col]["NaN"].append("{} to {}".format(s, e))

            self.data.nan_points(s, e)
            self.cc.clear()
            self.DisplayData()

    @QtCore.Slot()
    def BgMode(self):
        """Activates extra buttons and functionality to allow nanning."""
        if hasattr(self, "ax"):
            self.cc = clicker_class(ax=self.ax)

            self.cc.disconnect_sf()
            self.bg_mode_button.setStyleSheet("background-color: None")
            self.bg_mode_annotation = ""
            self.get_bg_val_button.setEnabled(False) # when the points are collected, enable the button
            self.set_bg_val_button.setEnabled(False) # when the points are collected, enable the button
            self.bg_text_field.setEnabled(False) # when the points are collected, enable the button
            self.cal_mode_button.setEnabled(True) # when the points are collected, enable the button
            self.cal_text_field.setEnabled(False) # when the points are collected, enable the button
            self.set_cal_val_button.setEnabled(False) # when the points are collected, enable the button
            self.nan_mode_button.setEnabled(True)

            if not self.bg_mode_button.isChecked():
                self.cc.connect_sf()
                self.bg_mode_button.setStyleSheet("background-color: "+self.color_active)
                self.bg_mode_annotation = "NaN mode On. Click and drag to make selection.\nPress NaN button to remove data between selection.\nRight click to remove selection"
                self.get_bg_val_button.setEnabled(True) # when the points are collected, enable the button
                self.set_bg_val_button.setEnabled(True) # when the points are collected, enable the button
                self.bg_text_field.setEnabled(True) # when the points are collected, enable the button
                self.nan_mode_button.setEnabled(False)
                self.cal_mode_button.setEnabled(False) # when the points are collected, enable the button


    @QtCore.Slot()
    def GetBg(self):
        """retrieve mean of selected area and sets widget."""
        # extract points and nan
        if len(self.cc.pt_lst_x) == 2:
            xrang = self.cc.return_points()[0]
            s, e = self.data.GetStartEnd(xrang[0], xrang[1])
            print "VARIABLE NAME", self.cc.axis_variable_name
            if self.subplots:
                axis_variable_name = str(self.cc.axis_variable_name[0])
                print str(axis_variable_name[2])

            mean = np.round(self.data.Stats(s=s, e=e).loc["mean"].values, 2)[0]
            print mean
            self.bg_text_field.setText(unicode(mean))
            self.cc.clear()
            self.DisplayData()


    @QtCore.Slot()
    def SetBg(self):
        """removes stored value from selected points."""
        # extract points and nan
        if (len(self.cc.pt_lst_x) == 2) and len(self.bg_text_field.text()) > 0:
            xrang = self.cc.return_points()[0]
            s, e = self.data.GetStartEnd(xrang[0], xrang[1])
            mean = float(self.bg_text_field.text())
            self.data.RemoveBackground(mean, s=s, e=e)
            for col in self.data.selected_col:
                self.data.log[col]["bg"].append("{} {} to {}".format(mean, s, e))
            self.cc.clear()
            self.DisplayData()


    @QtCore.Slot()
    def CalMode(self):
        """Activates extra buttons and functionality to allow nanning."""
        if hasattr(self, "ax"):
            self.cc = clicker_class(ax=self.ax)

            self.cc.disconnect_sf()
            self.cal_mode_button.setStyleSheet("background-color: None")
            self.cal_mode_annotation = ""
            self.set_cal_val_button.setEnabled(False) # when the points are collected, enable the button
            self.cal_text_field.setEnabled(False) # when the points are collected, enable the button
            self.nan_mode_button.setEnabled(True)
            self.bg_mode_button.setEnabled(True)

            if not self.cal_mode_button.isChecked():
                self.cc.connect_sf()
                self.cal_mode_button.setStyleSheet("background-color: "+self.color_active)
                self.cal_mode_annotation = "NaN mode On. Click and drag to make selection.\nPress NaN button to remove data between selection.\nRight click to remove selection"
                self.set_cal_val_button.setEnabled(True) # when the points are collected, enable the button
                self.cal_text_field.setEnabled(True) # when the points are collected, enable the button
                self.nan_mode_button.setEnabled(False)
                self.bg_mode_button.setEnabled(False)


    @QtCore.Slot()
    def SetCalibrate(self):
        """removes stored value from selected points."""
        # extract points and nan
        if (len(self.cc.pt_lst_x) == 2):
            xrang = self.cc.return_points()[0]
            s, e = self.data.GetStartEnd(xrang[0], xrang[1])
            cf = float(self.cal_text_field.text())
            for col in self.data.selected_col:
                self.data.log[col]["cal"].append("{} {} to {}".format(cf, s, e))

            self.data.Calibrate(cf, s=s, e=e)
            self.cc.clear()
            self.DisplayData()


    @QtCore.Slot()
    def GetStats(self):
        """Returns descriptive statistics."""
        
        stats = self.data.Stats()
        start = self.data.edit_df[self.data.selected_col[0]].first_valid_index()
        end = self.data.edit_df[self.data.selected_col[0]].last_valid_index()

        self.stats_box.clear()
        self.stats_box.insertHtml("<b>Range:</b> " + str(start) + " - " + str(end) + "<br><br>")

        for col in self.data.selected_col:
            displayStats = "<b>" + col + "</b><br>"
            for row in stats[col].index:
                displayStats += "{} = {}".format(row, str(round(stats[col].loc[row],2)) + "<br>")
            displayStats += "<br>\r\n"
            self.stats_box.insertHtml(displayStats)



    @QtCore.Slot()
    def SetNormalise(self, perform):
        """Normalise trace. Toggles so can be undone."""
        # Check to see whether the operation has been performed before
        # This information is stored in the data log
        has_normalised_to = np.array([self.data.log[x]["normalise"] for x in self.data.selected_col])
        norm_cols = self.data.selected_col

        # First check if has_normalised_to is populated with one unique element
        # If not, this function cannot be performed.
        if len(np.unique(has_normalised_to)) != 1:
            print "More than 1 unique normalisation factor"
            state = self.normalise_button.isChecked()
            self.normalise_button.setChecked(~state)
        else:
            # Check to see whether it is a None or a string.
            if has_normalised_to[0] is None:
                 # get normalisation column
                 self.data.nto = unicode(self.normalise_text_field.text())
                 # change checked state of button
                 self.normalise_button.setChecked(False)
                 self.normalise_button.setStyleSheet("background-color: None")
                 # perform normalisation
                 if perform:
                    self.data.Normalise("/")
                    self.normalise_button.setChecked(True)
                    self.normalise_button.setStyleSheet("background-color: "+self.color_active)
                    self.DisplayData()
            else:
                 self.data.nto = unicode(has_normalised_to[0])
                 self.normalise_text_field.setText(self.data.nto)
                 # change checked state of button
                 self.normalise_button.setChecked(True)
                 self.normalise_button.setStyleSheet("background-color: "+self.color_active)
                 # perform reverse normalisation
                 if perform:
                    self.data.Normalise("*")
                    self.normalise_button.setChecked(False)
                    self.normalise_button.setStyleSheet("background-color: None")
                    self.DisplayData()

    @QtCore.Slot()
    def ReplaceData(self):
        """Replaces the data in the data object with the unbound data."""
        self.data.df[self.data.edit_df.columns] = self.data.edit_df

    @QtCore.Slot()
    def ReadMessages(self):
        """Shows contents of message in message area."""
        self.message_window.window.clear()

        for col in self.data.selected_col:

            norm_html="<br>Normalised:<br>"
            nan_html="<br>NaN:<br>"
            bg_html="<br>Background:<br>"
            cal_html="<br>Calibrated:<br>"
            msg_html = ""

            try:
                norm_text = self.data.log[col]["normalise"]
            except TypeError:
                norm_text = ""
                print "No normalisation factor"
            try:
                nan_list = self.data.log[col]["NaN"]
            except IndexError:
                nan_list = ""
                print "No message text"
            try:
                bg_list = self.data.log[col]["bg"]
            except IndexError:
                bg_list = ""
                print "No message text"
            try:
                cal_list = self.data.log[col]["cal"]
            except IndexError:
                cal_list = ""
                print "No message text"


            norm_html += "{}<br>".format(norm_text)
            nan_html += "{}<br>".format(nan_list)
            bg_html += "{}<br>".format(bg_list)
            cal_html += "{}<br>".format(cal_list)

            # if hasattr(self, "freq"):
            #     resample_text =.insert(0, "Resampled to {} min".format(self.freq))

            for html in [norm_html, nan_html, bg_html, cal_html]:
                msg_html += html
            msg_html = msg_html.replace("[","").replace("]","").replace("'","").replace(",",",<br>") + "<br>"

            self.message_window.window.insertHtml("<b>" + col + "<b><br>")
            self.message_window.window.insertHtml(msg_html)


    @QtCore.Slot()
    def AverageUp(self):
        """Average up data"""
        self.freq = str(QtGui.QInputDialog.getText(self, 'Average', 'Enter minute averaging period:')[0])
        self.data.Resample(self.freq+"T")

        self.DisplayData()

    @QtCore.Slot()
    def Toggle_bg_functionality(self):
        """disable background when more than one trace is selected."""
        if len(self.data.selected_col) == 1:
            self.bg_mode_button.setEnabled(True)
            self.set_bg_val_button.setEnabled(True)
            self.get_bg_val_button.setEnabled(True)
            self.bg_text_field.setEnabled(True)
        else:
            self.bg_mode_button.setEnabled(False)
            self.set_bg_val_button.setEnabled(False)
            self.get_bg_val_button.setEnabled(False)
            self.bg_text_field.setEnabled(False)




    def initUI(self):

        """Initialise GUI."""

        # Initialise objects and widgets
        self.data = Data()
        self.load_button = LoadButton()
        self.trace_list = TimeSeriesList()
        self.trace_list.list.setMaximumWidth(250)
        self.remove_button = QtGui.QPushButton("Remove", self)
        self.time_axis_button = QtGui.QPushButton("Set time axis", self)
        self.average_button = QtGui.QPushButton("Time average", self)
        self.average_button.setEnabled(False)
        self.sep_axes_button = QtGui.QPushButton("Multiple axes", self)
        self.sep_axes_button.setCheckable(True)
        self.sep_axes_button.setDefault(False) # stop auto highlighting
        self.sep_axes_button.setAutoDefault(False)
        self.legend_button = QtGui.QPushButton("Legend", self)
        self.legend_button.setCheckable(True)
        self.legend_button.setDefault(False) # stop auto highlighting
        self.legend_button.setAutoDefault(False)
        self.reset_button = QtGui.QPushButton("Undo changes", self)
        self.nan_mode_button = QtGui.QPushButton("NaN mode", self)
        self.nan_mode_button.setCheckable(True)
        self.NaN_button = QtGui.QPushButton("NaN", self)
        self.NaN_button.setEnabled(False)
        self.normalise_button = QtGui.QPushButton("Normalise", self)
        self.normalise_button.setCheckable(True)
        self.normalise_text_field = QtGui.QLineEdit()
        self.bg_mode_button = QtGui.QPushButton("Background mode", self)
        self.bg_mode_button.setCheckable(True)
        self.get_bg_val_button = QtGui.QPushButton("Get Background", self)
        self.get_bg_val_button.setEnabled(False) # default is off
        self.bg_text_field = QtGui.QLineEdit()
        self.bg_text_field.setEnabled(False) # default is off
        self.set_bg_val_button = QtGui.QPushButton("Set background", self)
        self.set_bg_val_button.setEnabled(False) # default is off
        self.cal_mode_button = QtGui.QPushButton("Calibrate mode", self)
        self.cal_mode_button.setCheckable(True)
        self.cal_text_field = QtGui.QLineEdit()
        self.cal_text_field.setEnabled(False) # default is off
        self.set_cal_val_button = QtGui.QPushButton("Calibrate", self)
        self.set_cal_val_button.setEnabled(False) # default is off
        self.figure = mpl.figure.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.stats_box = QtGui.QTextEdit()
        self.stats_box.setReadOnly(True)
        self.stats_box.setMaximumWidth(350)
        self.message_window = MessageWindow()
        self.message_window.window.setMaximumWidth(350)
        self.export_button = ExportButton()
        self.export_button.button.setEnabled(False) # default is off
        

        # Bindings
        self.load_button.dataLoaded.connect(self.readData) #read data into object
        self.time_axis_button.pressed.connect(self.SetTimeAxis) # set the time axis for the data
        self.sep_axes_button.pressed.connect(self.SeparateAxes) # multiplot button
        self.legend_button.pressed.connect(self.ToggleLegend) # multiplot button
        self.average_button.pressed.connect(self.AverageUp)
        self.remove_button.pressed.connect(self.RemoveColumn) # delete dataframe column
        self.trace_list.list.itemSelectionChanged.connect(self.DisplayData) # plot different data
        self.trace_list.list.itemSelectionChanged.connect(lambda nto=False : self.SetNormalise(nto)) # toggle normalise widget
        self.trace_list.list.itemSelectionChanged.connect(self.ReadMessages) # plot different data
        self.trace_list.list.itemSelectionChanged.connect(self.Toggle_bg_functionality)
        self.trace_list.list.itemSelectionChanged.connect(self.GetStats)
        self.trace_list.list.itemChanged.connect(self.Rename) # rename dataframe column
        self.nan_mode_button.pressed.connect(self.NanMode) # activate nan mode
        self.NaN_button.released.connect(self.Nan_points) # Execute the NaN
        self.bg_mode_button.pressed.connect(self.BgMode) # activate bg mode
        self.get_bg_val_button.pressed.connect(self.GetBg) # get background value
        self.set_bg_val_button.pressed.connect(self.SetBg) # get background value
        self.reset_button.pressed.connect(self.ResetDF) # reset dataframe
        self.normalise_button.pressed.connect(lambda nto=True : self.SetNormalise(nto)) # normalise trace
        self.cal_mode_button.pressed.connect(self.CalMode) # activate bg mode
        self.set_cal_val_button.pressed.connect(self.SetCalibrate) # calibrate
        self.export_button.button.pressed.connect(self.saveData) # Export data

        # Layout


        # action = QtGui.QAction("do something", self)
        # def p(self):
        #     print "text"
        # action.triggered.connect(p)

        self.load_vbox = QtGui.QVBoxLayout()
        self.load_vbox.addWidget(self.load_button.button)
        self.load_vbox.addWidget(self.trace_list.list)
        self.load_vbox.addWidget(self.remove_button)
        self.plotoptions_hbox = QtGui.QHBoxLayout()
        self.plotoptions_hbox.addWidget(self.time_axis_button)
        self.plotoptions_hbox.addWidget(self.average_button)
        self.plotoptions_hbox.addWidget(self.sep_axes_button)
        self.plotoptions_hbox.addWidget(self.legend_button)
        self.plotoptions_hbox.addWidget(self.reset_button)
        self.nan_hbox = QtGui.QHBoxLayout()
        self.nan_hbox.addWidget(self.nan_mode_button)
        self.nan_hbox.addWidget(self.NaN_button)
        self.bg_hbox = QtGui.QHBoxLayout()
        self.bg_hbox.addWidget(self.bg_mode_button)
        self.bg_hbox.addWidget(self.get_bg_val_button)
        self.bg_hbox.addWidget(self.bg_text_field)
        self.bg_hbox.addWidget(self.set_bg_val_button)
        self.normalise_hbox = QtGui.QHBoxLayout()
        self.normalise_hbox.addWidget(self.normalise_button)
        self.normalise_hbox.addWidget(self.normalise_text_field)
        self.calibrate_hbox = QtGui.QHBoxLayout()
        self.calibrate_hbox.addWidget(self.cal_mode_button)
        self.calibrate_hbox.addWidget(self.cal_text_field)
        self.calibrate_hbox.addWidget(self.set_cal_val_button)
        self.plot_vbox = QtGui.QVBoxLayout()
        self.plot_vbox.addWidget(self.canvas)
        self.plot_vbox.addWidget(self.toolbar)
        self.plot_vbox.addLayout(self.plotoptions_hbox)
        self.plot_vbox.addLayout(self.nan_hbox)
        self.plot_vbox.addLayout(self.bg_hbox)
        self.plot_vbox.addLayout(self.normalise_hbox)
        self.plot_vbox.addLayout(self.calibrate_hbox)
        self.output_vbox = QtGui.QVBoxLayout()
        self.output_vbox.addWidget(self.stats_box)
        self.output_vbox.addWidget(self.message_window.window)
        self.output_vbox.addWidget(self.export_button.button)
        self.main_hbox = QtGui.QHBoxLayout()
        self.main_hbox.addLayout(self.load_vbox)
        self.main_hbox.addLayout(self.plot_vbox)
        self.main_hbox.addLayout(self.output_vbox)
        self.setLayout(self.main_hbox)
        self.setGeometry(50, 50, 1200, 600)
        self.setWindowTitle('Time Series Cleaner')
        self.show()




def Run():

    app = QtGui.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    Run()
