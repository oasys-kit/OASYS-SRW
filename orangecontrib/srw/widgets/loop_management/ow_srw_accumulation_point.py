__author__ = 'labx'

import os
import numpy
from numpy import nan
from scipy.interpolate import RectBivariateSpline

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox, QInputDialog

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, Normalize

cdict_temperature = {'red': ((0.0, 0.0, 0.0),
                             (0.5, 0.0, 0.0),
                             (0.75, 1.0, 1.0),
                             (1.0, 1.0, 1.0)),
                     'green': ((0.0, 0.0, 0.0),
                               (0.25, 1.0, 1.0),
                               (0.75, 1.0, 1.0),
                               (1.0, 0.0, 0.0)),
                     'blue': ((0.0, 1.0, 1.0),
                              (0.25, 1.0, 1.0),
                              (0.5, 0.0, 0.0),
                              (1.0, 0.0, 0.0))}

cmap_temperature = LinearSegmentedColormap('temperature', cdict_temperature, 256)

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

    last_tickets = None

    use_merging_range = Setting(0)

    merging_range_x_min = Setting(-10.0)
    merging_range_x_max = Setting(10.0)
    merging_range_y_min = Setting(-10.0)
    merging_range_y_max = Setting(10.0)

    merging_nr_points_x = Setting(100)
    merging_nr_points_y = Setting(100)

    autosave = Setting(0)
    autosave_file_name = Setting("autosave_total_intensity.hdf5")

    autosave_file = None

    current_number_of_wavefronts       = 0
    last_number_of_wavefronts  = 0
    total_number_of_wavefronts = 0

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box, show_view_box=False)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Save Accumulated Data", callback=self.save_cumulated_data, height=45)
        gui.button(button_box, self, "Load Accumulated Data", callback=self.load_cumulated_data, height=45)

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
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT-50)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "Accumulation Point Setting")

        gui.separator(self.tab_bas)

        view_box_1 = oasysgui.widgetBox(self.tab_bas, "Plot Setting", addSpace=False, orientation="vertical", width=self.CONTROL_AREA_WIDTH-20)

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

        merge_box_1 = oasysgui.widgetBox(self.tab_bas, "Accumulation Setting", addSpace=False, orientation="vertical")

        merge_box_2 = oasysgui.widgetBox(merge_box_1, "", addSpace=False, orientation="horizontal")

        self.range_combo = gui.comboBox(merge_box_2, self, "use_merging_range", label="Merging Range",
                                        labelWidth=300,
                                        items=["No", "Yes"],
                                        callback=self.set_MergingRange, sendSelectedValue=False, orientation="horizontal")

        self.merge_range_box_1 = oasysgui.widgetBox(merge_box_1, "", addSpace=False, orientation="vertical", height=100)
        self.merge_range_box_2 = oasysgui.widgetBox(merge_box_1, "", addSpace=False, orientation="vertical", height=100)

        merge_box_2 = oasysgui.widgetBox(self.merge_range_box_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(merge_box_2, self, "merging_range_x_min", "Merging Range X min [\u03bcm]", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(merge_box_2, self, "merging_range_x_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.merge_range_box_1, self, "merging_nr_points_x", "Nr. Points X", labelWidth=160, valueType=int, orientation="horizontal")

        merge_box_3 = oasysgui.widgetBox(self.merge_range_box_1, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(merge_box_3, self, "merging_range_y_min", "Merging Range Y min [\u03bcm]", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(merge_box_3, self, "merging_range_y_max", "max [\u03bcm]", labelWidth=60, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.merge_range_box_1, self, "merging_nr_points_y", "Nr. Points Y", labelWidth=160, valueType=int, orientation="horizontal")

        self.set_MergingRange()

        autosave_box = oasysgui.widgetBox(self.tab_bas, "Autosave", addSpace=True, orientation="vertical", height=95)

        gui.comboBox(autosave_box, self, "autosave", label="Save automatically plot into file", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_autosave)

        self.autosave_box_1 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)
        self.autosave_box_2 = oasysgui.widgetBox(autosave_box, "", addSpace=False, orientation="horizontal", height=25)

        self.le_autosave_file_name = oasysgui.lineEdit(self.autosave_box_1, self, "autosave_file_name", "File Name", labelWidth=70,  valueType=str, orientation="horizontal")

        gui.button(self.autosave_box_1, self, "...", callback=self.selectAutosaveFile, width=30)
        gui.button(self.autosave_box_1, self, "\u21a9", callback=self.reload_autosave_file, width=30)

        self.set_autosave()

        oasysgui.lineEdit(self.tab_bas, self, "last_number_of_wavefronts", "Previous Nr. of Wavefronts", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.tab_bas, self, "current_number_of_wavefronts", "Current Nr. of Wavefronts", labelWidth=260, valueType=int, orientation="horizontal")
        le = oasysgui.lineEdit(self.tab_bas, self, "total_number_of_wavefronts", "Total Nr. of Wavefronts", labelWidth=260, valueType=int, orientation="horizontal")
        font = QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QPalette(le.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        le.setPalette(palette) # assign new palette

    def set_MergingRange(self):
        self.merge_range_box_1.setVisible(self.use_merging_range == 1)
        self.merge_range_box_2.setVisible(self.use_merging_range == 0)

    def set_autosave(self):
        self.autosave_box_1.setVisible(self.autosave==1)
        self.autosave_box_2.setVisible(self.autosave==0)

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

                        self.current_number_of_wavefronts += 1
                        self.total_number_of_wavefronts = self.last_number_of_wavefronts + self.current_number_of_wavefronts

                        self.progressBarSet(30)

                        e, h, v, current_intensity = data.get_srw_wavefront().get_intensity(multi_electron=False)

                        if self.use_merging_range == 0:
                            self.progressBarSet(60)

                            tickets = []
                            SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, current_intensity, tickets)
                        else:
                            new_h = numpy.linspace(self.merging_range_x_min*1e-6, self.merging_range_x_max*1e-6, self.merging_nr_points_x)
                            new_v = numpy.linspace(self.merging_range_y_min*1e-6, self.merging_range_y_max*1e-6, self.merging_nr_points_y)

                            new_current_intensity = numpy.zeros((len(e), len(new_h), len(new_v)))

                            for index in range(len(e)):
                                interpolator = RectBivariateSpline(x=h, y=v, z=current_intensity[index, :, :], bbox=[None, None, None, None], kx=2, ky=2, s=0)

                                new_current_intensity[index, :, :] = interpolator(new_h, new_v)

                            self.progressBarSet(60)

                            tickets = []
                            SRWWavefrontViewer.add_2D_wavefront_plot(e, new_h, new_v, new_current_intensity, tickets)

                        self.rinormalize(tickets[-1])

                        if self.autosave == 1:
                            if self.autosave_file is None:
                                self.autosave_file = SRWPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))
                            elif self.autosave_file.filename != congruence.checkFileName(self.autosave_file_name):
                                self.autosave_file.close()
                                self.autosave_file = SRWPlot.PlotXYHdf5File(congruence.checkDir(self.autosave_file_name))

                            self.autosave_file.write_coordinates(tickets[-1])
                            self.autosave_file.add_plot_xy(tickets[-1])
                            self.autosave_file.write_additional_data(tickets[-1])
                            self.autosave_file.add_attribute("number_of_wavefronts", self.total_number_of_wavefronts)
                            self.autosave_file.flush()

                        self.plot_results(tickets, progressBarValue=90)
                        self.last_tickets = tickets

                        self.progressBarFinished()

                    except Exception as e:
                        QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

                        self.setStatusMessage("")
                        self.progressBarFinished()

                        if self.IS_DEVELOP: raise e

    def rinormalize(self, ticket):
        if not self.last_tickets is None:
            if ticket["histogram"].shape != self.last_tickets[-1]["histogram"].shape: raise ValueError("Accumulated Intensity Shape is different from received one")

            ticket["histogram"]   = ((self.last_tickets[-1]["histogram"]   * (self.total_number_of_wavefronts - 1)) + ticket["histogram"])   / self.total_number_of_wavefronts  # average
            ticket["histogram_h"] = ((self.last_tickets[-1]["histogram_h"] * (self.total_number_of_wavefronts - 1)) + ticket["histogram_h"]) / self.total_number_of_wavefronts  # average
            ticket["histogram_v"] = ((self.last_tickets[-1]["histogram_v"] * (self.total_number_of_wavefronts - 1)) + ticket["histogram_v"]) / self.total_number_of_wavefronts  # average

    def reset_accumulation(self):
        try:
            self.progressBarInit()

            if not self.autosave_file is None:
                self.autosave_file.close()
                self.autosave_file = None

            self.plot_results([SRWPlot.get_ticket_2D(numpy.array([0, 0.001]),
                                                     numpy.array([0, 0.001]),
                                                     numpy.zeros((2, 2)))], ignore_range=True)
            self.last_tickets = None
            self.current_number_of_wavefronts = 0
            self.last_number_of_wavefronts    = 0
            self.total_number_of_wavefronts   = 0

            self.progressBarFinished()
        except:
            pass

    def selectAutosaveFile(self):
        file_name = oasysgui.selectSaveFileFromDialog(self, "Select File", default_file_name="", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)")
        self.le_autosave_file_name.setText("" if file_name is None else file_name)

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

    def save_cumulated_data(self):
        file_name = oasysgui.selectSaveFileFromDialog(self, "Save Current Plot", default_file_name=("" if self.autosave==0 else self.autosave_file_name),
                                                      file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf);;Text Files (*.dat *.txt);;Images (*.png)")

        if not file_name is None and not file_name.strip()=="":
            format, ok = QInputDialog.getItem(self, "Select Output Format", "Formats: ", ("Hdf5", "Text", "Image", "Hdf5 & Image", "All"), 3, False)

            if ok and format:
                if format == "Hdf5" or format == "All":  self.save_cumulated_data_hdf5(file_name)
                if format == "Text" or format == "All":  self.save_cumulated_data_txt(file_name)
                if format == "Image" or format == "All": self.save_cumulated_data_image(file_name)
                if format == "Hdf5 & Image":
                    self.save_cumulated_data_hdf5(file_name)
                    self.save_cumulated_data_image(file_name)

    def save_cumulated_data_hdf5(self, file_name):
        if not self.last_tickets is None:
            try:
                save_file = SRWPlot.PlotXYHdf5File(congruence.checkDir(os.path.splitext(file_name)[0] + ".hdf5"))

                save_file.write_coordinates(self.last_tickets[-1])
                save_file.add_plot_xy(self.last_tickets[-1])
                save_file.write_additional_data(self.last_tickets[-1])
                save_file.add_attribute("number_of_wavefronts", self.total_number_of_wavefronts)

                save_file.close()
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

    def save_cumulated_data_txt(self, file_name):
        if not self.last_tickets is None:
            try:
                save_file = open(os.path.splitext(file_name)[0] + ".dat", "w")

                x_values = self.last_tickets[-1]["bin_h"]
                y_values = self.last_tickets[-1]["bin_v"]
                z_values = self.last_tickets[-1]["histogram"]

                for i in range(len(x_values)):
                    for j in range(len(y_values)):
                        row = str(x_values[i]) + " " + str(y_values[j]) + " " + str(z_values[i, j])

                        if i+j > 0: row = "\n" + row

                        save_file.write(row)

                save_file.flush()
                save_file.close()
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

    def save_cumulated_data_image(self, file_name):
        if not self.last_tickets is None:
            try:
                def duplicate(obj):
                    import io, pickle
                    buf = io.BytesIO()
                    pickle.dump(obj, buf)
                    buf.seek(0)
                    return pickle.load(buf)

                fig = duplicate(self.plot_canvas[0].plot_canvas._backend.fig)
                fig.set_size_inches(10, 8)

                vmin = numpy.min(self.last_tickets[-1]["histogram"])
                vmax = numpy.max(self.last_tickets[-1]["histogram"])

                cbar = fig.colorbar(cm.ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap_temperature), ax=fig.gca())
                cbar.ax.set_ylabel('Intensity [ph/s/.1%BW/mm\u00b2]', fontsize=14)
                ticks = cbar.get_ticks()
                cbar.set_ticks([vmax] + list(ticks))
                cbar.set_ticklabels(["{:.1e}".format(vmax)] + ["{:.1e}".format(t) for t in ticks])

                fig.savefig(os.path.splitext(file_name)[0] + ".png")

            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

    def __load_file(self, file_name):
        if not file_name is None:
            plot_file = SRWPlot.PlotXYHdf5File(congruence.checkDir(file_name), mode="r")

            ticket = {}

            plot_file.get_plot(ticket)
            plot_file.get_coordinates(ticket)
            plot_file.get_additional_data(ticket)

            tickets = [ticket]

            try:
                self.current_number_of_wavefronts = 0
                self.last_number_of_wavefronts    = plot_file.get_attribute("number_of_wavefronts")
                self.total_number_of_wavefronts   = self.last_number_of_wavefronts
            except:
                self.current_number_of_wavefronts = 0
                self.last_number_of_wavefronts    = 0
                self.total_number_of_wavefronts   = 0

            self.plot_results(tickets, progressBarValue=90)
            self.last_tickets = tickets

            self.progressBarFinished()

    def reload_autosave_file(self):
        try:
            self.__load_file(self.autosave_file_name)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

    def load_cumulated_data(self):
        try:
            file_name = oasysgui.selectFileFromDialog(self, None, "Select File", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)")

            self.__load_file(file_name)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

