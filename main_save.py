#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
# from PyQt4 import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from time_series_tools import *
import pandas as pd


class QDataViewer(QtGui.QPushButton):
    def __init__(self):
        super(QDataViewer, self).__init__()
        self.loadButton = QtGui.QPushButton('Load', self)
        self.connect(self.loadButton, QtCore.SIGNAL('Clicked()'), self.Open)

    def Open(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', '.')
        print 'Path file :', filename
        data = pd.read_csv(str(filename))
        return data

class DfColumnListWidget(QtGui.QListWidget):

    def __init__(self):
        QtGui.QListWidget.__init__(self)
        self.addItem("Item 1")
        self.addItem("Item 2")
        # self.connect(loadButton, QtCore.SIGNAL('clicked()'), self.Open)

    # def Clicked(self,item):
    #     QtGui.QMessageBox.information(self, "ListWidget", "You clicked: "+item.text())

    def Populate(self, ls):

        [self.addItem(item) for item in ls]

# class TSViewWidget(pg.GraphicsWindow):
#
#     def __init__(self):
#         super(TSViewWidget, self).__init__()
#         self.addPlot(title="Basic array plotting", y=np.random.normal(size=100))



class MainWindow(QtGui.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
        self.data = []



    def initUI(self):

        # Load data button
        LoadDataWidg = QDataViewer()
        # SpeciesNames list
        DfColListWidg = DfColumnListWidget()
        # Time series View port
        # TSWidg = TSViewWidget()




        # Time series Controls
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(LoadDataWidg, 1, 1, 1, 2)
        grid.addWidget(DfColListWidg, 2, 1, 10, 2)
        # grid.addWidget(TSWidg, 2, 3, 1, 1)


        # Layout
        self.setLayout(grid)
        self.setGeometry(0, 0, 700, 500)
        self.show()


def main():

    app = QtGui.QApplication(sys.argv)
    time_series_gui = MainWindow()

    # Connect Widgets

    # WIDGET.SIGNAL.CONNNECT(FUNCTION)
    data = MainWindow.LoadDataWidg.Open()
    MainWindow.DfColListWidg.Populate(data)


    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
