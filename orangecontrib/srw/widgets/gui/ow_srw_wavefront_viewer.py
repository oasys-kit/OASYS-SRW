import sys
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from silx.gui.plot.StackView import StackViewMainWindow

from wofry.propagator.propagator import PropagationManager, WavefrontDimension
from wofrysrw.propagator.propagators2D.srw_fresnel_native import FresnelSRWNative, SRW_APPLICATION
from wofrysrw.propagator.propagators2D.srw_fresnel_wofry import FresnelSRWWofry
from wofrysrw.propagator.propagators2D.srw_propagation_mode import SRWPropagationMode

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

def initialize_propagator_2D():
    propagation_manager = PropagationManager.Instance()

    if not propagation_manager.is_initialized(SRW_APPLICATION):
        if not propagation_manager.has_propagator(FresnelSRWNative.HANDLER_NAME, WavefrontDimension.TWO): propagation_manager.add_propagator(FresnelSRWNative())
        if not propagation_manager.has_propagator(FresnelSRWWofry.HANDLER_NAME, WavefrontDimension.TWO): propagation_manager.add_propagator(FresnelSRWWofry())

        propagation_manager.set_propagation_mode(SRW_APPLICATION, SRWPropagationMode.STEP_BY_STEP)

        propagation_manager.set_initialized(True)
try:
    initialize_propagator_2D()
except Exception as e:
    print("Error while initializing propagators", str(e))

    raise e


class SRWWavefrontViewer(SRWWidget):

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    want_main_area=1
    view_type=Setting(1)

    output_wavefront=None

    def __init__(self, show_general_option_box=True, show_automatic_box=True, show_view_box=True):
        super().__init__(show_general_option_box=show_general_option_box, show_automatic_box=show_automatic_box)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.view_box = oasysgui.widgetBox(plot_tab, "Plotting", addSpace=False, orientation="horizontal")

        if show_view_box:
            view_box_1 = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical", width=350)

            self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Plot Results",
                                                labelWidth=120,
                                                items=["No", "Yes (Total Polarization)", "Yes (Polarization Components)"],
                                                callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")
        else:
            self.view_type = 1
            self.view_type_combo = QtWidgets.QWidget()

        self.show_view_box = show_view_box

        #* -------------------------------------------------------------------------------------------------------------
        propagation_box = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical")

        self.le_srw_live_propagation_mode = gui.lineEdit(propagation_box, self, "srw_live_propagation_mode", "Propagation Mode", labelWidth=150, valueType=str, orientation="horizontal")
        self.le_srw_live_propagation_mode.setAlignment(Qt.AlignCenter)
        self.le_srw_live_propagation_mode.setReadOnly(True)
        font = QFont(self.le_srw_live_propagation_mode.font())
        font.setBold(True)
        self.le_srw_live_propagation_mode.setFont(font)

        self.set_srw_live_propagation_mode()

        #* -------------------------------------------------------------------------------------------------------------

        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self.initializeTabs()

        self.srw_output = oasysgui.textArea(600, 600)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.srw_output)

        self.set_PlotQuality()

    def set_srw_live_propagation_mode(self):
        propagation_mode = PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION)

        self.srw_live_propagation_mode = "Element by Element (Native)" if              propagation_mode == SRWPropagationMode.STEP_BY_STEP  else \
                                          "Whole beamline at Final Screen (Native)" if propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE else \
                                          "Element by Element (Wofry)" if              propagation_mode == SRWPropagationMode.STEP_BY_STEP_WOFRY else \
                                          "Unknown"

        palette = QPalette(self.le_srw_live_propagation_mode.palette())

        color = 'dark green' if propagation_mode == SRWPropagationMode.STEP_BY_STEP  else \
                'dark red' if   propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE else \
                'dark blue' if  propagation_mode == SRWPropagationMode.STEP_BY_STEP_WOFRY else \
                'black'

        palette.setColor(QPalette.Text, QColor(color))
        palette.setColor(QPalette.Base, QColor(243, 240, 140))
        self.le_srw_live_propagation_mode.setPalette(palette)

        if propagation_mode==SRWPropagationMode.WHOLE_BEAMLINE: self.view_type = 0

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

        if self.is_do_plots():
            try:
                self.initializeTabs()

                if not self.output_wavefront is None:
                    tickets = []

                    self.run_calculation_for_plots(tickets, 50)

                    self.plot_results(tickets, 80)

            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception
        else:
            self.initializeTabs()

        self.progressBarFinished()

    def run_calculation_for_plots(self, tickets, progress_bar_value):
        raise NotImplementedError("to be implemented")

    def plot_1D(self, ticket, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed1DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_1D(ticket, var, title, xtitle, ytitle, xum=xum)

        self.progressBarSet(progressBarValue)


    def plot_2D(self, ticket, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed2DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_2D(ticket, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum)

        self.progressBarSet(progressBarValue)

    def plot_3D(self, data3D, dataE, dataX, dataY, progressBarValue, plot_canvas_index,  title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = StackViewMainWindow()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        xmin = numpy.min(dataX)
        xmax = numpy.max(dataX)
        ymin = numpy.min(dataY)
        ymax = numpy.max(dataY)

        stepX = dataX[1]-dataX[0]
        stepY = dataY[1]-dataY[0]
        if len(dataE) > 1: stepE = dataE[1]-dataE[0]
        else: stepE = 1.0

        if stepE == 0.0: stepE = 1.0
        if stepX == 0.0: stepX = 1.0
        if stepY == 0.0: stepY = 1.0

        dim0_calib = (dataE[0],stepE)
        dim1_calib = (ymin, stepY)
        dim2_calib = (xmin, stepX)

        data_to_plot = numpy.swapaxes(data3D, 1, 2)

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.plot_canvas[plot_canvas_index].setLabels(["Photon Energy [eV]",ytitle,xtitle])
        self.plot_canvas[plot_canvas_index].setColormap(colormap=colormap)
        self.plot_canvas[plot_canvas_index].setStack(numpy.array(data_to_plot),
                                                     calibrations=[dim0_calib, dim1_calib, dim2_calib] )


    def show_power_density(self):
        return True

    def is_do_plots(self):
        return self.view_type == 1 or self.view_type == 2

    def plot_results(self, tickets = [], progressBarValue=80):
        if self.is_do_plots():
            if not tickets is None:
                if not len(tickets) == 0:
                    self.view_type_combo.setEnabled(False)

                    SRWPlot.set_conversion_active(self.getConversionActive())

                    variables = self.getVariablesToPlot()
                    titles = self.getTitles(with_um=True)
                    xtitles = self.getXTitles()
                    ytitles = self.getYTitles()
                    xums = self.getXUM()
                    yums = self.getYUM()

                    progress = (100 - progressBarValue) / len(tickets)

                    try:
                        for i in range(0, len(tickets)):
                            if type(tickets[i]) is tuple:
                                if len(tickets[i]) == 4:
                                    self.plot_3D(tickets[i][0], tickets[i][1], tickets[i][2], tickets[i][3], progressBarValue + (i+1)*progress, plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i], yum=yums[i])
                            else:
                                if len(variables[i]) == 1:
                                    self.plot_1D(tickets[i], progressBarValue + (i+1)*progress, variables[i],                     plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i])
                                else:
                                    self.plot_2D(tickets[i], progressBarValue + (i+1)*progress, variables[i][0], variables[i][1], plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i], yum=yums[i])
                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\nexception: " + str(e))

                    self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Nothing to Plot")

    def writeStdOut(self, text):
        cursor = self.srw_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.srw_output.setTextCursor(cursor)
        self.srw_output.ensureCursorVisible()

    def onReceivingInput(self):
        self.initializeTabs()

    def getVariablesToPlot(self):
        if self.view_type == 2:
            return [[1, 2], [1, 2], [1, 2], [1, 2], [1, 2], [1, 2]]
        else:
            return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if self.view_type == 2:
            if with_um: return ["Intensity SE \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity SE \u03c3 [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE \u03c0 [rad]",
                                "Phase SE \u03c3 [rad]",
                                "Intensity ME \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity ME \u03c3 [ph/s/.1%bw/mm\u00b2]"]
            else: return ["Intensity SE \u03c0",
                          "Intensity SE \u03c3",
                          "Phase SE \u03c0",
                          "Phase SE \u03c3",
                          "Intensity ME \u03c0 (Convolution)",
                          "Intensity ME \u03c3 (Convolution)"]
        else:
            if with_um: return ["Intensity SE [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE [rad]",
                                "Intensity ME [ph/s/.1%bw/mm\u00b2]"]
            else: return ["Intensity SE",
                          "Phase SE",
                          "Intensity ME (Convolution)"]

    def getXTitles(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]

    def getYTitles(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]

    def getXUM(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]

    def getYUM(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]

    def getConversionActive(self):
        return True

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWWavefrontViewer()
    ow.show()
    a.exec_()
    ow.saveSettings()
