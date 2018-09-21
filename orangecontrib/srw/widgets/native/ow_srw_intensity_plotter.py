__author__ = 'labx'

import os, sys, numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

from orangecontrib.srw.widgets.native.util import native_util

class OWSRWIntensityPlotter(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Native"
    keywords = ["data", "file", "load", "read"]
    name = "Intensity Plot"
    description = "SRW Native: Intensity"
    icon = "icons/intensity.png"
    priority = 3

    want_main_area=1

    TABS_AREA_HEIGHT = 618

    intensity_file_name = Setting("<file_intensity>.dat")

    is_final_screen = True
    view_type = 1

    def __init__(self):
        super().__init__(show_automatic_box=False, show_view_box=False)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Load SRW File", callback=self.plot_intensity)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "Calculated Intensity Setting")

        gui.separator(self.tab_bas)

        file_box =  oasysgui.widgetBox(self.tab_bas, "", addSpace=False, orientation="horizontal")
        self.le_intensity_file_name = oasysgui.lineEdit(file_box, self, "intensity_file_name", "Intensity File", labelWidth=105, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectIntensityFile)


    def selectIntensityFile(self):
        self.le_intensity_file_name.setText(oasysgui.selectFileFromDialog(self, self.intensity_file_name, "Intensity File"))

    def plot_intensity(self):
        try:
            self.progressBarInit()

            tickets = []

            x, y, intensity = native_util.load_intensity_file(self.intensity_file_name)

            tickets.append(SRWPlot.get_ticket_2D(x*1000, y*1000, intensity))

            self.progressBarSet(50)

            self.plot_results(tickets, progressBarValue=50)

            self.progressBarFinished()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

    def getVariablesToPlot(self):
        return [[1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity [ph/s/.1%bw/mm\u00b2]"]
        else: return ["Intensity"]

    def getXTitles(self):
        return ["X [\u03bcm]"]

    def getYTitles(self):
        return ["Y [\u03bcm]"]

    def getXUM(self):
        return ["X [\u03bcm]"]

    def getYUM(self):
        return ["Y [\u03bcm]"]



