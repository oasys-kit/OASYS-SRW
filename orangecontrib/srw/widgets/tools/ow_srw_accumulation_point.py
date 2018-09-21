__author__ = 'labx'

import os, sys, numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from oasys.widgets import gui as oasysgui

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

class OWSRWAccumulationPoint(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Tools"
    keywords = ["data", "file", "load", "read"]
    name = "Accumulation Point"
    description = "SRW Tools: Accumulation Point"
    icon = "icons/accumulation.png"
    priority = 4

    inputs = [("SRWData", SRWData, "receive_srw_data")]

    want_main_area=1

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 255

    accumulated_intensity = None

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Reset Accumulated Wavefronts", callback=self.reset_accumulation)
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

    def receive_srw_data(self, data):
        if not data is None:
            if isinstance(data, SRWData):
                if not data.get_srw_wavefront() is None:
                    self.progressBarInit()

                    self.progressBarSet(30)

                    e, h, v, i = data.get_srw_wavefront().get_intensity(multi_electron=False)

                    tickets = []

                    if self.accumulated_intensity is None:
                        self.accumulated_intensity = i
                    else:
                        if i.shape != self.accumulated_intensity.shape:
                            raise ValueError("Accumulated Intensity Shape is different from received one")

                        self.accumulated_intensity += i

                    self.progressBarSet(60)

                    tickets.append(SRWPlot.get_ticket_2D(h, v, self.accumulated_intensity[int(e.size/2)]))

                    self.plot_results(tickets, progressBarValue=90)

                    self.progressBarFinished()

    def reset_accumulation(self):
        try:
            self.progressBarInit()

            self.accumulated_intensity = None

            self.plot_results([SRWPlot.get_ticket_2D(numpy.array([0, 0.001]),
                                                     numpy.array([0, 0.001]),
                                                     numpy.zeros((2, 2)))])
            self.progressBarFinished()
        except:
            pass

    def getVariablesToPlot(self):
        return [[1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Accumulated Intensity [ph/s/.1%bw/mm\u00b2]"]
        else: return ["Accumulated Intensity"]

    def getXTitles(self):
        return ["X [mm]"]

    def getYTitles(self):
        return ["Y [mm]"]

    def getXUM(self):
        return ["X [mm]"]

    def getYUM(self):
        return ["Y [mm]"]
