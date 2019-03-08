import os, numpy

from silx.gui.plot import Plot2D

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap

import orangecanvas.resources as resources

from orangewidget import gui
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
    energy_single_value = Setting(0.0)
    angle_single_value = Setting(0.0)

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

        self.energy_box = oasysgui.widgetBox(tab_bas, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.energy_box, self, "energy_single_value", "Energy Single Value [eV]", labelWidth=250, valueType=float, orientation="horizontal")

        self.angle_box = oasysgui.widgetBox(tab_bas, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.angle_box, self, "angle_single_value", "Angle Single Value [rad]", labelWidth=250, valueType=float, orientation="horizontal")

        self.energy_box.setVisible(False)
        self.angle_box.setVisible(False)

    def selectDataFile(self):
        self.le_data_file_name.setText(oasysgui.selectFileFromDialog(self, self.data_file_name, "Output Data File"))

    def generate_reflectivity_file(self):
        file_name = congruence.checkFileName(self.data_file_name)

        output_data = SRWPreProcessorData(reflectivity_data=SRWReflectivityData(reflectivity_data_file=self.data_file_name))

        data_txt = ""

        if not self.reflectivity_unpol_data is None:
            try:
                reflectivity_data = self.reflectivity_unpol_data.get_content("data2D")
                energy = self.reflectivity_unpol_data.get_content("dataX")
                angle = self.reflectivity_unpol_data.get_content("dataY")*0.001 #to rad

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
                        if not (i==0 and j==0): data_txt += "\n"

                        data_txt += str(reflectivity_data[j, i]) + "\n0.0"

            except:
                try:
                    reflectivity_data = self.reflectivity_unpol_data.get_content("xoppy_data")
                    labels = self.reflectivity_unpol_data.get_content("labels")
                    x_col = int(self.reflectivity_unpol_data.get_content("plot_x_col"))
                    y_col = int(self.reflectivity_unpol_data.get_content("plot_y_col"))

                    if "Energy" in labels[0]:
                        congruence.checkStrictlyPositiveNumber(self.angle_single_value, "Angle Single Value")

                        output_data.reflectivity_data.energies_number = len(reflectivity_data)
                        output_data.reflectivity_data.angles_number = 1
                        output_data.reflectivity_data.energy_start = reflectivity_data[0, x_col]
                        output_data.reflectivity_data.energy_end = reflectivity_data[-1, x_col]
                        output_data.reflectivity_data.angle_start = self.angle_single_value
                        output_data.reflectivity_data.angle_end = self.angle_single_value

                    elif "Theta" in labels[0]:
                        congruence.checkStrictlyPositiveNumber(self.energy_single_value, "Energy Single Value")

                        output_data.reflectivity_data.energies_number = 1
                        output_data.reflectivity_data.angles_number = len(reflectivity_data)
                        output_data.reflectivity_data.energy_start = self.energy_single_value
                        output_data.reflectivity_data.energy_end = self.energy_single_value
                        output_data.reflectivity_data.angle_start = reflectivity_data[0, x_col]*0.001 #to rad
                        output_data.reflectivity_data.angle_end = reflectivity_data[-1, x_col]*0.001 #to rad

                    output_data.reflectivity_data.components_number = 1
                    output_data.reflectivity_data.energy_scale_type = ScaleType.LINEAR
                    output_data.reflectivity_data.angle_scale_type = ScaleType.LINEAR

                    for i in range(0, len(reflectivity_data)):
                        if i!=0: data_txt += "\n"

                        data_txt += str(reflectivity_data[i, y_col]) + "\n0.0"

                except Exception as exception:
                    QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                    if self.IS_DEVELOP: raise exception

                    return

            if not data_txt == "":
                file = open(file_name, "w")

                file.write(data_txt)
                file.flush()
                file.close()

            self.send("Reflectivity Data", output_data)

        elif not self.reflectivity_s_data is None and not self.reflectivity_p_data is None:
            try:
                reflectivity_s = self.reflectivity_s_data.get_content("data2D")
                energy_s = self.reflectivity_s_data.get_content("dataX")
                angle_s = self.reflectivity_s_data.get_content("dataY")*0.001 #to rad

                try:
                    reflectivity_p = self.reflectivity_p_data.get_content("data2D")
                    energy_p = self.reflectivity_p_data.get_content("dataX")
                    angle_p = self.reflectivity_p_data.get_content("dataY")*0.001 #to rad

                    if (len(energy_s) != len(energy_p)) or \
                            (energy_p[0] != energy_s[0]) or \
                            (energy_p[-1] != energy_s[-1]) or \
                            (len(angle_s) != len(angle_p)) or \
                            (angle_p[0] != angle_s[0]) or \
                            (angle_p[-1] != angle_s[-1]):
                        QMessageBox.critical(self, "Error", "Reflectivity data have different dimension or different range of Energy/Angle values", QMessageBox.Ok)

                        return

                    output_data.reflectivity_data.energies_number = len(energy_s)
                    output_data.reflectivity_data.angles_number = len(angle_s)
                    output_data.reflectivity_data.components_number = 2
                    output_data.reflectivity_data.energy_start = energy_s[0]
                    output_data.reflectivity_data.energy_end = energy_s[-1]
                    output_data.reflectivity_data.energy_scale_type = ScaleType.LINEAR
                    output_data.reflectivity_data.angle_start = angle_s[0]
                    output_data.reflectivity_data.angle_end = angle_s[-1]
                    output_data.reflectivity_data.angle_scale_type = ScaleType.LINEAR

                    data_txt = ""

                    for i in range(0, len(angle_s)):
                        for j in range (0, len(energy_s)):
                            if not (i==0 and j==0): data_txt += "\n"

                            data_txt += str(reflectivity_s[j, i]) + "\n0.0"

                    for i in range(0, len(angle_p)):
                        for j in range (0, len(energy_p)):
                            data_txt += "\n" + str(reflectivity_p[j, i]) + "\n0.0"

                except:
                    QMessageBox.critical(self, "Error", "Reflectivity data have different dimension", QMessageBox.Ok)

                    return
            except:
               try:
                    reflectivity_s = self.reflectivity_s_data.get_content("xoppy_data")
                    labels_s = self.reflectivity_s_data.get_content("labels")
                    x_col = int(self.reflectivity_s_data.get_content("plot_x_col"))
                    y_col = int(self.reflectivity_s_data.get_content("plot_y_col"))

                    try:
                        reflectivity_p = self.reflectivity_p_data.get_content("xoppy_data")
                        labels_p = self.reflectivity_p_data.get_content("labels")

                        if (len(reflectivity_p) != len(reflectivity_s)) or \
                                (reflectivity_s[0, x_col] != reflectivity_p[0, x_col]) or \
                                (reflectivity_s[-1, x_col] != reflectivity_p[-1, x_col]) or \
                                (labels_s[0] != labels_p[0]):
                            QMessageBox.critical(self, "Error", "Reflectivity data have different dimension or different range of Energy/Angle values", QMessageBox.Ok)

                            return

                        try:
                            if "Energy" in labels_s[0]:
                                congruence.checkStrictlyPositiveNumber(self.angle_single_value, "Angle Single Value")

                                output_data.reflectivity_data.energies_number = len(reflectivity_s)
                                output_data.reflectivity_data.angles_number = 1
                                output_data.reflectivity_data.energy_start = reflectivity_s[0, x_col]
                                output_data.reflectivity_data.energy_end = reflectivity_s[-1, x_col]
                                output_data.reflectivity_data.angle_start = self.angle_single_value
                                output_data.reflectivity_data.angle_end = self.angle_single_value

                            elif "Theta" in labels_s[0]:
                                congruence.checkStrictlyPositiveNumber(self.energy_single_value, "Energy Single Value")

                                output_data.reflectivity_data.energies_number = 1
                                output_data.reflectivity_data.angles_number = len(reflectivity_s)
                                output_data.reflectivity_data.energy_start = self.energy_single_value
                                output_data.reflectivity_data.energy_end = self.energy_single_value
                                output_data.reflectivity_data.angle_start = reflectivity_s[0, x_col]*0.001 #to rad
                                output_data.reflectivity_data.angle_end = reflectivity_s[-1, x_col]*0.001 #to rad
                        except Exception as exception:
                            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                            if self.IS_DEVELOP: raise exception

                            return

                        output_data.reflectivity_data.components_number = 2
                        output_data.reflectivity_data.energy_scale_type = ScaleType.LINEAR
                        output_data.reflectivity_data.angle_scale_type = ScaleType.LINEAR

                        for i in range(0, len(reflectivity_s)):
                            if i!=0: data_txt += "\n"

                            data_txt += str(reflectivity_s[i, y_col]) + "\n0.0"

                        for i in range(0, len(reflectivity_p)):
                            data_txt += "\n" + str(reflectivity_p[i, y_col]) + "\n0.0"
                    except:
                        QMessageBox.critical(self, "Error", "Reflectivity data have different dimension", QMessageBox.Ok)

                        return

               except Exception as exception:
                    QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                    if self.IS_DEVELOP: raise exception

                    return

            if not data_txt == "":
                file = open(file_name, "w")

                file.write(data_txt)
                file.flush()
                file.close()

            self.send("Reflectivity Data", output_data)

        else:
            QMessageBox.critical(self, "Error", "Incomplete Data: connect Total Polarization Data or BOTH Polarizations Data", QMessageBox.Ok)


    def set_input_1(self, data):
        self.reflectivity_unpol_data = data

        if not self.reflectivity_unpol_data is None:
            self.reflectivity_p_data = None
            self.reflectivity_s_data = None

            try:
                self.reflectivity_unpol_data.get_content("xoppy_data")
                labels = self.reflectivity_unpol_data.get_content("labels")

                if "Energy" in labels[0]:
                    self.angle_box.setVisible(True)
                    self.energy_box.setVisible(False)
                elif "Theta" in labels[0]:
                    self.angle_box.setVisible(False)
                    self.energy_box.setVisible(True)
            except:
                self.angle_box.setVisible(False)
                self.energy_box.setVisible(False)

        self.plot_results()

        self.main_tabs.setCurrentIndex(0)

    def set_input_2(self, data):
        self.reflectivity_s_data = data

        if not self.reflectivity_s_data is None:
            self.reflectivity_unpol_data = None

            try:
                self.reflectivity_s_data.get_content("xoppy_data")
                labels = self.reflectivity_s_data.get_content("labels")

                if "Energy" in labels[0]:
                    self.angle_box.setVisible(True)
                    self.energy_box.setVisible(False)
                elif "Theta" in labels[0]:
                    self.angle_box.setVisible(False)
                    self.energy_box.setVisible(True)
            except: #2D
                if not self.reflectivity_p_data is None:
                    try:
                        self.reflectivity_p_data.get_content("xoppy_data")
                    except:
                        self.angle_box.setVisible(False)
                        self.energy_box.setVisible(False)


        self.plot_results()

        self.main_tabs.setCurrentIndex(1)

    def set_input_3(self, data):
        self.reflectivity_p_data = data

        if not self.reflectivity_p_data is None:
            self.reflectivity_unpol_data = None

            try:
                self.reflectivity_p_data.get_content("xoppy_data")
                labels = self.reflectivity_p_data.get_content("labels")

                if "Energy" in labels[0]:
                    self.angle_box.setVisible(True)
                    self.energy_box.setVisible(False)
                elif "Theta" in labels[0]:
                    self.angle_box.setVisible(False)
                    self.energy_box.setVisible(True)
            except: #2D
                if not self.reflectivity_s_data is None:
                    try:
                        self.reflectivity_s_data.get_content("xoppy_data")
                    except:
                        self.angle_box.setVisible(False)
                        self.energy_box.setVisible(False)

        self.plot_results()

        self.main_tabs.setCurrentIndex(2)

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
