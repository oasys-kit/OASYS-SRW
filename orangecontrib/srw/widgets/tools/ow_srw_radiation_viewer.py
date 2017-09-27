import sys


from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.srw.util.srw_util import SRWPlot

from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

class SRWWavefrontViewer(SRWWidget):

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    want_main_area=1
    view_type=Setting(1)

    plotted_tickets=None

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        view_box = oasysgui.widgetBox(plot_tab, "Plotting", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Plot Results",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")
        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self.initializeTabs()

        self.srw_output = QtWidgets.QTextEdit()
        self.srw_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.srw_output)

        self.srw_output.setFixedHeight(600)
        self.srw_output.setFixedWidth(600)


    def initializeTabs(self):
        current_tab = self.tabs.currentIndex()

        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = self.getTitles()
        self.tab = []
        self.plot_canvas = []

        for title in self.getTitles():
            self.tab.append(oasysgui.createTabPage(self.tabs, title))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.tabs.setCurrentIndex(current_tab)


    def set_PlotQuality(self):
        self.progressBarInit()

        if not self.plotted_tickets==None:
            try:
                self.initializeTabs()

                self.plot_results(self.plotted_tickets, 80)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

                #raise exception
                
        self.progressBarFinished()

    def plot_2D(self, ticket, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed2DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_2D(ticket, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum)

        self.progressBarSet(progressBarValue)


    def plot_1D(self, ticket, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed1DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_1D(ticket, var, title, xtitle, ytitle, xum=xum)

        self.progressBarSet(progressBarValue)

    def show_power_density(self):
        return True

    def is_do_plots(self):
        return self.view_type == 1


    def plot_results(self, tickets = [], progressBarValue=80):
        if self.is_do_plots():
            if not tickets is None:
                self.view_type_combo.setEnabled(False)

                SRWPlot.set_conversion_active(self.getConversionActive())

                variables = self.getVariablesToPlot()
                titles = self.getTitles(with_um=True)
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()
                xums = self.getXUM()
                yums = self.getYUM()

                try:
                    self.plot_2D(tickets[0], progressBarValue + 4,  variables[0][0], variables[0][1], plot_canvas_index=0, title=titles[0], xtitle=xtitles[0], ytitle=ytitles[0], xum=xums[0], yum=yums[0])
                    self.plot_2D(tickets[1], progressBarValue + 4,  variables[1][0], variables[1][1], plot_canvas_index=1, title=titles[1], xtitle=xtitles[1], ytitle=ytitles[1], xum=xums[1], yum=yums[1])
                    self.plot_2D(tickets[2], progressBarValue + 4,  variables[2][0], variables[2][1], plot_canvas_index=2, title=titles[2], xtitle=xtitles[2], ytitle=ytitles[2], xum=xums[2], yum=yums[2])

                    if (len(tickets)) >= 4:
                        self.plot_2D(tickets[3], progressBarValue + 4,  variables[3][0], variables[3][1], plot_canvas_index=3, title=titles[3], xtitle=xtitles[3], ytitle=ytitles[3], xum=xums[3], yum=yums[3])
                    if (len(tickets)) == 5:
                        self.plot_1D(tickets[4], progressBarValue + 16, variables[4],                  plot_canvas_index=4, title=titles[4], xtitle=xtitles[4], ytitle=ytitles[4], xum=xums[4] )


                except Exception as e:
                    self.view_type_combo.setEnabled(True)

                    raise Exception("Data not plottable: bad content\nexception: " + str(e))

                self.view_type_combo.setEnabled(True)

            else:
                raise Exception("Nothing to Plot")

        self.plotted_tickets = tickets

    def writeStdOut(self, text):
        cursor = self.srw_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.srw_output.setTextCursor(cursor)
        self.srw_output.ensureCursorVisible()

    def onReceivingInput(self):
        self.initializeTabs()

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2], [1, 2], [1, 2], -1]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity SE [ph/s/.1%bw/mm^2]",
                            "Phase SE [rad]",
                            "Intensity ME [ph/s/.1%bw/mm^2]",
                            "Power Density [W/mm^2], " + self.getCalculatedTotalPowerString(),
                            "Flux [ph/s/.1%bw]"]
        else: return ["Intensity SE", "Phase SE", "Intensity ME (Convolution)", "Power Density", "Flux"]

    def getXTitles(self):
        return ["X [mm]", "X [mm]", "X [mm]", "X [mm]", "Energy [eV]"]

    def getYTitles(self):
        return ["Y [mm]", "Y [mm]", "Y [mm]", "Y [mm]", "Flux [ph/s/.1%bw]"]

    def getXUM(self):
        return ["X [mm]", "X [mm]", "X [mm]", "X [mm]", "Energy [eV]"]

    def getYUM(self):
        return ["Y [mm]", "Y [mm]", "Y [mm]", "Y [mm]", "Flux [ph/s/.1%bw]"]

    def getConversionActive(self):
        return True

    def getCalculatedTotalPowerString(self):
        return ""

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWWavefrontViewer()
    ow.show()
    a.exec_()
    ow.saveSettings()