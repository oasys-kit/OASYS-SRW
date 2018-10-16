import os, numpy

from silx.gui.plot import Plot2D

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence

from oasys.widgets.exchange import DataExchangeObject

from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget
from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWReflectivityData

from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import ScaleType

class OWReflectivityGenerator(SRWWidget):
    name = "SRW Reflectivity Generator"
    description = "Utility: SRW Reflectivity Generator"
    icon = "icons/reflectivity.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 3
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 1

    file_name = Setting("")
    data_path = Setting("")

    inputs = []
    inputs = [("Reflectivity (Total/Unpol.)", DataExchangeObject, "set_input_1"),
              ("Reflectivity (\u03c3)", DataExchangeObject, "set_input_2"),
              ("Reflectivity (\u03c0)", DataExchangeObject, "set_input_3")]

    outputs = [{"name":"Reflectivity Data",
                "type":SRWPreProcessorData,
                "doc":"Reflectivity Data",
                "id":"data"}
               ]

    reflectivity_unpol_data = None
    reflectivity_p_data = None
    reflectivity_s_data = None

    data_file_name = Setting("reflectivity.dat")

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "reflectivity_generator_usage.png")

    def __init__(self):
        super().__init__(show_general_option_box=False, show_automatic_box=False)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)

        self.clear_tabs()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Generate Reflectivity File", callback=self.generate_reflectivity_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Reflectivity Generator Setting")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        file_box = oasysgui.widgetBox(tab_bas, "", addSpace=False, orientation="horizontal")

        self.le_data_file_name = oasysgui.lineEdit(file_box, self, "data_file_name", "Output File Name", labelWidth=150, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectDataFile)

    def selectDataFile(self):
        self.le_data_file_name.setText(oasysgui.selectFileFromDialog(self, self.data_file_name, "Output Data File"))

    def generate_reflectivity_file(self):
        file_name = congruence.checkFileName(self.data_file_name)

        output_data = SRWPreProcessorData(reflectivity_data=SRWReflectivityData(reflectivity_data_file=self.data_file_name))

        data_txt = ""

        if not self.reflectivity_unpol_data is None:
            try:
                reflectivity = self.reflectivity_unpol_data.get_content("data2D")
                energy = self.reflectivity_unpol_data.get_content("dataX")
                angle = self.reflectivity_unpol_data.get_content("dataY")

                output_data.reflectivity_data.energies_number = len(energy)
                output_data.reflectivity_data.angles_number = len(angle)
                output_data.reflectivity_data.components_number = 1
                output_data.reflectivity_data.energy_start = energy[0]
                output_data.reflectivity_data.energy_end = energy[-1]
                output_data.reflectivity_data.energy_scale_type = ScaleType.LINEAR
                output_data.reflectivity_data.angle_start = angle[0]
                output_data.reflectivity_data.angle_end = angle[-1]
                output_data.reflectivity_data.angle_scale_type = ScaleType.LINEAR

                data_txt = ""

                for i in range(0, len(angle)):
                    for j in range (0, len(energy)):
                        if i==0 and j==0: data_txt += "\n"

                        data_txt += str(reflectivity[j, i]) + "\n00"

            except:
                try:
                    reflectivity = self.reflectivity_unpol_data.get_content("xoppy_data")




                    output_data.reflectivity_data.energies_number = len(energy)
                    output_data.reflectivity_data.angles_number = len(angle)
                    output_data.reflectivity_data.components_number = 1
                    output_data.reflectivity_data.energy_start = energy[0]
                    output_data.reflectivity_data.energy_end = energy[-1]
                    output_data.reflectivity_data.energy_scale_type = ScaleType.LINEAR
                    output_data.reflectivity_data.angle_start = angle[0]
                    output_data.reflectivity_data.angle_end = angle[-1]
                    output_data.reflectivity_data.angle_scale_type = ScaleType.LINEAR

                    j = int(self.reflectivity_unpol_data.get_content("plot_y_col"))

                    for i in range(0, len(reflectivity)):
                        if i==0: data_txt += "\n"

                        data_txt += str(reflectivity[i, j]) + "\n00"

                except Exception as exception:
                    QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                    if self.IS_DEVELOP: raise exception

            if not data_txt == "":
                file = open(file_name, "w")

                file.write(data_txt)
                file.flush()
                file.close()

            self.send("Reflectivity Data", output_data)

        elif not self.reflectivity_s_data is None and not self.reflectivity_p_data is None:
            pass
        else:
            QMessageBox.critical(self, "Error", "Incomplete Data: connect Total Polarization Data or BOTH Polarizations Data", QMessageBox.Ok)


    def set_input_1(self, data):
        self.reflectivity_unpol_data = data

        if not self.reflectivity_unpol_data is None:
            self.reflectivity_p_data = None
            self.reflectivity_s_data = None

        self.plot_results()

    def set_input_2(self, data):
        self.reflectivity_s_data = data

        if not self.reflectivity_s_data is None:
            self.reflectivity_unpol_data = None

        self.plot_results()

    def set_input_3(self, data):
        self.reflectivity_p_data = data

        if not self.reflectivity_p_data is None:
            self.reflectivity_unpol_data = None

        self.plot_results()

    def plot_results(self):
        self.progressBarInit()

        self.clear_tabs()

        self.plot_data(self.reflectivity_unpol_data, 0, 0, "Reflectivity (Total/Unpol.)")

        self.progressBarSet(30)

        self.plot_data(self.reflectivity_s_data, 1, 1, "Reflectivity (\u03c3)")

        self.progressBarSet(60)

        self.plot_data(self.reflectivity_p_data, 2, 2, "Reflectivity (\u03c0)")

        self.progressBarSet(90)

        self.progressBarFinished()

    def clear_tabs(self):
        self.main_tabs.clear()

        self.tab = [oasysgui.createTabPage(self.main_tabs, "Total/Unpolarized Reflectivity"),
                    oasysgui.createTabPage(self.main_tabs, "\u03c3 Reflectivity"),
                    oasysgui.createTabPage(self.main_tabs, "\u03c0 Reflectivity")]

        self.plot_canvas = [None, None, None]

    def plot_data(self, data, tabs_canvas_index, plot_canvas_index, title):
        if not data is None:
            try:
                data2D = data.get_content("data2D")
                dataX = data.get_content("dataX")
                dataY = data.get_content("dataY")

                self.plot_data2D(data2D, dataX, dataY, tabs_canvas_index, plot_canvas_index,
                                 xtitle='Energy [eV]',
                                 ytitle='Theta [mrad]',
                                 title=title)

            except:
                try:
                    xoppy_data = data.get_content("xoppy_data")

                    x_col = int(data.get_content("plot_x_col"))
                    y_col = int(data.get_content("plot_y_col"))
                    labels = data.get_content("labels")

                    self.plot_histo(xoppy_data[:, x_col],
                                    xoppy_data[:, y_col],
                                    tabs_canvas_index=tabs_canvas_index,
                                    plot_canvas_index=plot_canvas_index,
                                    title=title,
                                    xtitle=labels[0],
                                    ytitle=labels[1])
                except Exception as exception:
                    QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                    if self.IS_DEVELOP: raise exception

    def plot_histo(self, x, y, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle="",
                   log_x=False, log_y=False, color='blue', replace=True, control=False):

        self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(parent=None,
                                                                  backend=None,
                                                                  resetzoom=True,
                                                                  autoScale=False,
                                                                  logScale=True,
                                                                  grid=True,
                                                                  curveStyle=True,
                                                                  colormap=False,
                                                                  aspectRatio=False,
                                                                  yInverted=False,
                                                                  copy=True,
                                                                  save=True,
                                                                  print_=True,
                                                                  control=control,
                                                                  position=True,
                                                                  roi=False,
                                                                  mask=False,
                                                                  fit=False)
        self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
        self.plot_canvas[plot_canvas_index].setActiveCurveColor(color="#00008B")
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)

        self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        import matplotlib

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        self.plot_canvas[plot_canvas_index].addCurve(x, y, title, symbol='', color=color, xlabel=xtitle, ylabel=ytitle, replace=replace) #'+', '^', ','

        self.plot_canvas[plot_canvas_index].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[plot_canvas_index].setInteractiveMode('zoom',color='orange')
        self.plot_canvas[plot_canvas_index].resetZoom()
        self.plot_canvas[plot_canvas_index].replot()

        self.plot_canvas[plot_canvas_index].setActiveCurve(title)

        self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(log_x)
        self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(log_y)

        if min(y) < 0:
            if log_y:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y)*1.2, max(y)*1.2)
            else:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y)*1.01, max(y)*1.01)
        else:
            if log_y:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y), max(y)*1.2)
            else:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y), max(y)*1.01)

    def plot_data2D(self, data2D, dataX, dataY, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle=""):
        origin = (dataX[0],dataY[0])
        scale = (dataX[1]-dataX[0],dataY[1]-dataY[0])

        data_to_plot = data2D.T

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[plot_canvas_index] = Plot2D()

        self.plot_canvas[plot_canvas_index].resetZoom()
        self.plot_canvas[plot_canvas_index].setXAxisAutoScale(True)
        self.plot_canvas[plot_canvas_index].setYAxisAutoScale(True)
        self.plot_canvas[plot_canvas_index].setGraphGrid(False)
        self.plot_canvas[plot_canvas_index].setKeepDataAspectRatio(True)
        self.plot_canvas[plot_canvas_index].yAxisInvertedAction.setVisible(False)

        self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
        self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)

        self.plot_canvas[plot_canvas_index].getMaskAction().setVisible(False)
        self.plot_canvas[plot_canvas_index].getRoiAction().setVisible(False)
        self.plot_canvas[plot_canvas_index].getColormapAction().setVisible(False)
        self.plot_canvas[plot_canvas_index].setKeepDataAspectRatio(False)



        self.plot_canvas[plot_canvas_index].addImage(numpy.array(data_to_plot),
                                                     legend="image1",
                                                     scale=scale,
                                                     origin=origin,
                                                     colormap=colormap,
                                                     replace=True)

        self.plot_canvas[plot_canvas_index].setActiveImage("image1")

        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)

        self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])
