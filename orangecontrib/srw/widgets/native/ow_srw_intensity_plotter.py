__author__ = 'labx'

from numpy import nan

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

    last_tickets=None

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

        oasysgui.lineEdit(view_box_2, self, "range_x_min", "Plotting Range X min [\u03bcm]", labelWidth=150, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(view_box_2, self, "range_x_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")

        view_box_3 = oasysgui.widgetBox(self.plot_range_box_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(view_box_3, self, "range_y_min", "Plotting Range Y min [\u03bcm]", labelWidth=150, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(view_box_3, self, "range_y_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")

        self.set_PlottingRange()

    def replot(self):
        if self.last_tickets is None:
            self.plot_intensity()
        else:
            self.progressBarInit()

            self.progressBarSet(50)

            self.plot_results(self.last_tickets, progressBarValue=50)

            self.progressBarFinished()

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

            self.last_tickets = tickets

            self.progressBarFinished()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

    def getVariablesToPlot(self):
        return [[1, 2]]

    def getWeightedPlots(self):
        return [False]

    def getWeightTickets(self):
        return [nan]

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



