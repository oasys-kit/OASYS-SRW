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

class OWSRWDegCohPlotter(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Native"
    keywords = ["data", "file", "load", "read"]
    name = "Degree of Coherence Plot"
    description = "SRW Native: Degree of Coherence Plot"
    icon = "icons/degcoh.png"
    priority = 4

    want_main_area=1

    TABS_AREA_HEIGHT = 618

    calculation = Setting(0)
    
    horizontal_cut_file_name = Setting("<file_me_degcoh>.1")
    vertical_cut_file_name = Setting("<file_me_degcoh>.2")
    mode = Setting(0)

    is_final_screen = True
    view_type = 1

    last_tickets=None

    def __init__(self):
        super().__init__(show_automatic_box=False, show_view_box=False)

        self.do_average=True

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Load SRW Files", callback=self.plot_degcoh)
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

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "ME Degree of Coherence Setting")

        view_box_1 = oasysgui.widgetBox(self.tab_bas, "Calculation Setting", addSpace=False, orientation="vertical")

        gui.comboBox(view_box_1, self, "calculation", label="M.E. Output File", items=["Mutual Intensity", "Degree of Coherence"], orientation="horizontal", callback=self.set_calculation)

        self.box_1 = oasysgui.widgetBox(view_box_1, "", addSpace=False, orientation="vertical")
        self.box_2 = oasysgui.widgetBox(view_box_1, "", addSpace=False, orientation="vertical")

        gui.label(self.box_1, self, "Mutual Intensity Files:")
        
        file_box =  oasysgui.widgetBox(self.box_1, "", addSpace=False, orientation="horizontal")
        self.le_horizontal_cut_file_name = oasysgui.lineEdit(file_box, self, "horizontal_cut_file_name", "Horizontal Cut ", labelWidth=105, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectHorizontalCutFile)

        file_box =  oasysgui.widgetBox(self.box_1, "", addSpace=False, orientation="horizontal")
        self.le_vertical_cut_file_name = oasysgui.lineEdit(file_box, self, "vertical_cut_file_name", "Vertical Cut ", labelWidth=105, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectVerticalCutFile)

        gui.separator(self.box_1)

        gui.comboBox(self.box_1, self, "mode", label="Calculation type:", items=["by using Numpy/Scipy (Faster)", "As Original Igor Macro (Slower)"], orientation="horizontal")

        gui.label(self.box_2, self, "Degree of Coherence Files:")

        file_box = oasysgui.widgetBox(self.box_2, "", addSpace=False, orientation="horizontal")
        self.le_horizontal_cut_file_name = oasysgui.lineEdit(file_box, self, "horizontal_cut_file_name", "Horizontal Cut ", labelWidth=105, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectHorizontalCutFile)

        file_box = oasysgui.widgetBox(self.box_2, "", addSpace=False, orientation="horizontal")
        self.le_vertical_cut_file_name = oasysgui.lineEdit(file_box, self, "vertical_cut_file_name", "Vertical Cut ", labelWidth=105, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectVerticalCutFile)

        self.set_calculation()

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

    def set_calculation(self):
        self.box_1.setVisible(self.calculation == 0)
        self.box_2.setVisible(self.calculation == 1)

    def selectHorizontalCutFile(self):
        self.le_horizontal_cut_file_name.setText(oasysgui.selectFileFromDialog(self, self.horizontal_cut_file_name, "Mutual Intensity Horizontal Cut File", file_extension_filter="*.1"))

    def selectVerticalCutFile(self):
        self.le_vertical_cut_file_name.setText(oasysgui.selectFileFromDialog(self, self.vertical_cut_file_name, "Mutual Intensity Horizontal Cut File", file_extension_filter="*.2"))

    def plot_degcoh(self):
        try:
            self.progressBarInit()

            tickets = []

            if self.calculation == 0:
                mode = "Igor" if self.mode == 1 else "Scipy"

                sum_x, difference_x, degree_of_coherence_x = native_util.calculate_degree_of_coherence_vs_sum_and_difference_from_file(self.horizontal_cut_file_name, mode=mode)

                self.progressBarSet(40)

                sum_y, difference_y, degree_of_coherence_y = native_util.calculate_degree_of_coherence_vs_sum_and_difference_from_file(self.vertical_cut_file_name, mode=mode)

            else:
                sum_x, difference_x, degree_of_coherence_x = native_util.load_mutual_intensity_file(self.horizontal_cut_file_name)

                self.progressBarSet(40)

                sum_y, difference_y, degree_of_coherence_y = native_util.load_mutual_intensity_file(self.vertical_cut_file_name)

            tickets.append(SRWPlot.get_ticket_2D(sum_x*1000, difference_x*1000, degree_of_coherence_x))
            tickets.append(SRWPlot.get_ticket_2D(sum_y*1000, difference_y*1000, degree_of_coherence_y))

            self.plot_results(tickets, progressBarValue=80)

            self.last_tickets = tickets

            self.progressBarFinished()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

    def replot(self):
        if self.last_tickets is None:
            self.plot_degcoh()
        else:
            self.progressBarInit()

            self.progressBarSet(50)

            self.plot_results(self.last_tickets, progressBarValue=50)

            self.progressBarFinished()

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2]]

    def getWeightedPlots(self):
        return [False, False]

    def getWeightTickets(self):
        return [nan, nan]

    def getTitles(self, with_um=False):
        if with_um: return ["Degree Of Coherence (H)", "Degree Of Coherence (V)"]
        else: return ["Degree Of Coherence (H)", "Degree Of Coherence (V)"]

    def getXTitles(self):
        return ["(X\u2081 + X\u2082)/2 [\u03bcm]", "(Y\u2081 + Y\u2082)/2 [\u03bcm]"]

    def getYTitles(self):
        return ["(X\u2081 - X\u2082)/2 [\u03bcm]", "(Y\u2081 - Y\u2082)/2 [\u03bcm]"]

    def getXUM(self):
        return ["X [\u03bcm]", "X [\u03bcm]"]

    def getYUM(self):
        return ["Y [\u03bcm]", "Y [\u03bcm]"]



