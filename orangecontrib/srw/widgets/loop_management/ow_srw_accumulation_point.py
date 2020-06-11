__author__ = 'labx'

import numpy
from numpy import nan

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
    is_final_screen = True

    accumulated_intensity = None
    last_tickets = None

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box, show_view_box=False)

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

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "Accumulation Point Setting")

        gui.separator(self.tab_bas)

        view_box_1 = oasysgui.widgetBox(self.tab_bas, "Plot Setting", addSpace=False, orientation="vertical")

        view_box_2 = oasysgui.widgetBox(view_box_1, "", addSpace=False, orientation="horizontal")

        self.range_combo = gui.comboBox(view_box_2, self, "use_range", label="Plotting Range",
                                        labelWidth=120,
                                        items=["No", "Yes"],
                                        callback=self.set_PlottingRange, sendSelectedValue=False, orientation="horizontal")

        self.refresh_button = gui.button(view_box_2, self, "Refresh", callback=self.replot)

        self.plot_range_box_1 = oasysgui.widgetBox(view_box_1, "", addSpace=False, orientation="vertical", height=50)
        self.plot_range_box_2 = oasysgui.widgetBox(view_box_1, "", addSpace=False, orientation="vertical", height=50)

        view_box_2 = oasysgui.widgetBox(self.plot_range_box_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(view_box_2, self, "range_x_min", "Plotting Range X min [\u03bcm]", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(view_box_2, self, "range_x_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")

        view_box_3 = oasysgui.widgetBox(self.plot_range_box_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(view_box_3, self, "range_y_min", "Plotting Range Y min [\u03bcm]", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(view_box_3, self, "range_y_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")

        self.set_PlottingRange()


    def replot(self):
        if not self.last_tickets is None:
            self.progressBarInit()

            self.progressBarSet(50)

            self.plot_results(self.last_tickets, progressBarValue=50)

            self.progressBarFinished()

    def receive_srw_data(self, data):
        if not data is None:
            if isinstance(data, SRWData):
                if not data.get_srw_wavefront() is None:
                    try:
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

                        tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, self.accumulated_intensity[int(e.size/2)]))

                        self.plot_results(tickets, progressBarValue=90)

                        self.last_tickets = tickets

                        self.progressBarFinished()

                    except Exception as e:
                        QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

                        self.setStatusMessage("")
                        self.progressBarFinished()

                        if self.IS_DEVELOP: raise e


    def reset_accumulation(self):
        try:
            self.progressBarInit()

            self.accumulated_intensity = None

            self.plot_results([SRWPlot.get_ticket_2D(numpy.array([0, 0.001]),
                                                     numpy.array([0, 0.001]),
                                                     numpy.zeros((2, 2)))], ignore_range=True)
            self.progressBarFinished()
        except:
            pass

    def getVariablesToPlot(self):
        return [[1, 2]]

    def getWeightedPlots(self):
        return [False]

    def getWeightTickets(self):
        return [nan]

    def getTitles(self, with_um=False):
        if with_um: return ["Accumulated Intensity [ph/s/.1%bw/mm\u00b2]"]
        else: return ["Accumulated Intensity"]

    def getXTitles(self):
        return ["X [\u03bcm]"]

    def getYTitles(self):
        return ["Y [\u03bcm]"]

    def getXUM(self):
        return ["X [\u03bcm]"]

    def getYUM(self):
        return ["Y [\u03bcm]"]
