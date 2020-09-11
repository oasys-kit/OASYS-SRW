#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2020. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

import sys, numpy
import os
import time

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

from oasys.util.scanning_gui import StatisticalDataCollection, HistogramDataCollection, DoublePlotWidget, write_histo_and_stats_file, write_histo_and_stats_file_hdf5
from orangecontrib.srw.util.scanning_gui import ScanHistoWidget, Scan3DHistoWidget, Column

from wofrysrw.propagator.wavefront2D.srw_wavefront import PolarizationComponent, TypeOfDependence

TO_UM = 1e6

class Histogram(SRWWidget):
    name = "Scanning Variable Histogram"
    description = "Display Data Tools: Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("SRWData", SRWData, "set_input")]

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    want_main_area=1
    plot_canvas_intensity=None
    plot_canvas_phase=None
    plot_scan_canvas=None

    input_srw_data = None

    x_column_index=Setting(0)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    polarization_component_to_be_extracted=Setting(0)
    multi_electron = Setting(0)

    title=Setting("Y")

    iterative_mode = Setting(0)

    last_ticket=None

    current_histo_data = None
    current_histo_data_phase = None
    current_stats = None
    last_histo_data = None
    last_histo_data_phase = None
    histo_index = -1

    plot_type = Setting(1)
    add_labels=Setting(0)
    has_colormap=Setting(1)
    plot_type_3D = Setting(0)
    stats_to_plot = Setting(0)
    stats_to_plot_2 = Setting(0)

    def __init__(self):
        super().__init__()

        self.refresh_button = gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=45, width=400)
        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Histogram Settings")

        general_box = oasysgui.widgetBox(tab_set, "General Settings", addSpace=True, orientation="vertical", height=250, width=390)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="Intensity Cut", labelWidth=250,
                                     items=["Horizontal", "Vertical"],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="Position Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "Min [\u03bcm]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "Max [\u03bcm]", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        gui.comboBox(general_box, self, "polarization_component_to_be_extracted", label="Polarization Component", labelWidth=250,
                                     items=["Total", "\u03c3", "\u03c0"],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "multi_electron", label="Multi Electron (Convolution)", labelWidth=250,
                                     items=["No", "Yes"],
                                     sendSelectedValue=False, orientation="horizontal")

        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="vertical", height=290)

        gui.button(incremental_box, self, "Clear Stored Data", callback=self.clearResults, height=30)
        gui.separator(incremental_box)

        gui.comboBox(incremental_box, self, "iterative_mode", label="Iterative Mode", labelWidth=250,
                                         items=["None", "Accumulating", "Scanning"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_IterativeMode)

        self.box_scan_empty = oasysgui.widgetBox(incremental_box, "", addSpace=False, orientation="vertical")
        self.box_scan = oasysgui.widgetBox(incremental_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_scan, self, "plot_type", label="Plot Type", labelWidth=310,
                     items=["2D", "3D"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_PlotType)

        self.box_pt_1 = oasysgui.widgetBox(self.box_scan, "", addSpace=False, orientation="vertical", height=25)

        gui.comboBox(self.box_pt_1, self, "add_labels", label="Add Labels (Variable Name/Value)", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.box_pt_2 = oasysgui.widgetBox(self.box_scan, "", addSpace=False, orientation="vertical", height=25)

        gui.comboBox(self.box_pt_2, self, "plot_type_3D", label="3D Plot Aspect", labelWidth=310,
                     items=["Lines", "Surface"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_scan, self, "has_colormap", label="Colormap", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.box_scan)

        gui.comboBox(self.box_scan, self, "stats_to_plot", label="Stats: Spot Dimension", labelWidth=310,
                     items=["Sigma", "FWHM"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.box_scan, self, "stats_to_plot_2", label="Stats: Intensity", labelWidth=310,
                     items=["Peak", "Integral"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.button(self.box_scan, self, "Export Scanning Results/Stats", callback=self.export_scanning_stats_analysis, height=30)

        self.set_IterativeMode()

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")

        plot_tabs = oasysgui.tabWidget(plot_tab)
        intensity_tab = oasysgui.createTabPage(plot_tabs, "Intensity")
        phase_tab     = oasysgui.createTabPage(plot_tabs, "Phase")

        self.image_box = gui.widgetBox(intensity_tab, "", addSpace=False, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

        self.image_box_2 = gui.widgetBox(phase_tab, "", addSpace=False, orientation="vertical")
        self.image_box_2.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box_2.setFixedWidth(self.IMAGE_WIDTH-20)

        plot_tab_stats = oasysgui.createTabPage(self.main_tabs, "Stats")

        self.image_box_stats = gui.widgetBox(plot_tab_stats, "Stats Result", addSpace=True, orientation="vertical")
        self.image_box_stats.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box_stats.setFixedWidth(self.IMAGE_WIDTH)

        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.srw_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.srw_output)

    def clearResults(self):
        if ConfirmDialog.confirmed(parent=self):
            self.clear_data()

    def clear_data(self):
        self.input_srw_data = None
        self.last_ticket = None
        self.current_stats = None
        self.current_histo_data = None
        self.current_histo_data_phase = None
        self.last_histo_data = None
        self.last_histo_data_phase = None

        self.histo_index = -1

        if not self.plot_canvas_intensity is None:
            self.main_tabs.removeTab(1)
            self.main_tabs.removeTab(0)

            plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

            plot_tabs = oasysgui.tabWidget(plot_tab)
            intensity_tab = oasysgui.createTabPage(plot_tabs, "Intensity")
            phase_tab     = oasysgui.createTabPage(plot_tabs, "Phase")

            self.image_box = gui.widgetBox(intensity_tab, "", addSpace=False, orientation="vertical")
            self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
            self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

            self.image_box_2 = gui.widgetBox(phase_tab, "", addSpace=False, orientation="vertical")
            self.image_box_2.setFixedHeight(self.IMAGE_HEIGHT-30)
            self.image_box_2.setFixedWidth(self.IMAGE_WIDTH-20)

            plot_tab_stats = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

            self.image_box_stats = gui.widgetBox(plot_tab_stats, "Stats Result", addSpace=True, orientation="vertical")
            self.image_box_stats.setFixedHeight(self.IMAGE_HEIGHT)
            self.image_box_stats.setFixedWidth(self.IMAGE_WIDTH)

            self.main_tabs.insertTab(0, plot_tab_stats, "TEMP")
            self.main_tabs.setTabText(0, "Stats")
            self.main_tabs.insertTab(0, plot_tab, "TEMP")
            self.main_tabs.setTabText(0, "Plots")
            self.main_tabs.setCurrentIndex(0)

            self.plot_canvas_intensity = None
            self.plot_canvas_phase = None
            self.plot_canvas_stats = None

    def set_IterativeMode(self):
        self.box_scan_empty.setVisible(self.iterative_mode<2)
        if self.iterative_mode==2:
            self.box_scan.setVisible(True)
            self.refresh_button.setEnabled(False)
            self.set_PlotType()
        else:
            self.box_scan.setVisible(False)
            self.refresh_button.setEnabled(True)

        self.clear_data()

    def set_PlotType(self):
        self.plot_canvas_intensity = None
        self.plot_canvas_phase = None
        self.plot_canvas_stats = None

        self.box_pt_1.setVisible(self.plot_type==0)
        self.box_pt_2.setVisible(self.plot_type==1)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def replace_fig(self, wavefront, var, xrange, title, xtitle, ytitle, xum):
        if self.plot_canvas_intensity is None:
            if self.iterative_mode < 2:
                self.plot_canvas_intensity = SRWPlot.Detailed1DWidget(y_scale_factor=1.14)
            else:
                if self.plot_type == 0:
                    self.plot_canvas_intensity = ScanHistoWidget()
                    self.plot_canvas_phase = ScanHistoWidget()
                elif self.plot_type==1:
                    self.plot_canvas_intensity = Scan3DHistoWidget(type=Scan3DHistoWidget.PlotType.LINES if self.plot_type_3D == 0 else Scan3DHistoWidget.PlotType.SURFACE)
                    self.plot_canvas_phase     = Scan3DHistoWidget(type=Scan3DHistoWidget.PlotType.LINES if self.plot_type_3D == 0 else Scan3DHistoWidget.PlotType.SURFACE)

                self.plot_canvas_stats = DoublePlotWidget(parent=None)
                self.image_box_stats.layout().addWidget(self.plot_canvas_stats)

            self.image_box.layout().addWidget(self.plot_canvas_intensity)
            self.image_box_2.layout().addWidget(self.plot_canvas_phase)

        if self.polarization_component_to_be_extracted == 0:
            polarization_component_to_be_extracted = PolarizationComponent.TOTAL
        elif self.polarization_component_to_be_extracted == 1:
            polarization_component_to_be_extracted = PolarizationComponent.LINEAR_HORIZONTAL
        elif self.polarization_component_to_be_extracted == 2:
            polarization_component_to_be_extracted = PolarizationComponent.LINEAR_VERTICAL

        if self.multi_electron==0 and self.iterative_mode==2:
            e, h, v, p = wavefront.get_phase(polarization_component_to_be_extracted=polarization_component_to_be_extracted)

            if len(e) <= 1: ticket2D_Phase = SRWPlot.get_ticket_2D(h, v, p[int(e.size / 2)])
            else:           ticket2D_Phase = SRWPlot.get_ticket_2D(h, v, numpy.average(p, axis=0), is_multi_energy=True)

            ticket_phase = {}
            if var == Column.X:
                ticket_phase["histogram"] = ticket2D_Phase["histogram"][:, int(e.size/2)]
                ticket_phase["bins"] = ticket2D_Phase["bin_h"]*TO_UM
                ticket_phase["xrange"] = ticket2D_Phase["xrange"]
                ticket_phase["fwhm"] = ticket2D_Phase["fwhm_h"]*TO_UM
                ticket_phase["fwhm_coordinates"] = ticket2D_Phase["fwhm_coordinates_h"]
            elif var == Column.Y:
                ticket_phase["histogram"] = ticket2D_Phase["histogram"][int(e.size/2), :]
                ticket_phase["bins"] = ticket2D_Phase["bin_v"]*TO_UM
                ticket_phase["xrange"] = ticket2D_Phase["yrange"]
                ticket_phase["fwhm"] = ticket2D_Phase["fwhm_v"]*TO_UM
                ticket_phase["fwhm_coordinates"] = ticket2D_Phase["fwhm_coordinates_v"]
    
            ticket_phase["xrange"] = (ticket_phase["xrange"][0]*TO_UM, ticket_phase["xrange"][1]*TO_UM)
    
            if not ticket_phase["fwhm"] is None and not ticket_phase["fwhm"] == 0.0:
                ticket_phase["fwhm_coordinates"] = (ticket_phase["fwhm_coordinates"][0]*TO_UM, ticket_phase["fwhm_coordinates"][1]*TO_UM)


        e, h, v, i = wavefront.get_intensity(multi_electron=self.multi_electron==1,
                                            polarization_component_to_be_extracted=polarization_component_to_be_extracted,
                                            type_of_dependence=TypeOfDependence.VS_XY)

        if len(e) <= 1:
            ticket2D_Intensity = SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)])
        else:
            delta_e = e[1] - e[0]
            for j in range(len(e)): i[j, :, :] *= delta_e / (e[j] * 1e-3)  # change to fixed bw for integration
            ticket2D_Intensity = SRWPlot.get_ticket_2D(h, v, numpy.sum(i, axis=0), is_multi_energy=True)

        ticket_intensity = {}
        if var == Column.X:
            ticket_intensity["histogram"] = ticket2D_Intensity["histogram_h"]
            ticket_intensity["bins"] = ticket2D_Intensity["bin_h"]*TO_UM
            ticket_intensity["xrange"] = ticket2D_Intensity["xrange"]
            ticket_intensity["fwhm"] = ticket2D_Intensity["fwhm_h"]*TO_UM
            ticket_intensity["fwhm_coordinates"] = ticket2D_Intensity["fwhm_coordinates_h"]
        elif var == Column.Y:
            ticket_intensity["histogram"] = ticket2D_Intensity["histogram_v"]
            ticket_intensity["bins"] = ticket2D_Intensity["bin_v"]*TO_UM
            ticket_intensity["xrange"] = ticket2D_Intensity["yrange"]
            ticket_intensity["fwhm"] = ticket2D_Intensity["fwhm_v"]*TO_UM
            ticket_intensity["fwhm_coordinates"] = ticket2D_Intensity["fwhm_coordinates_v"]

        ticket_intensity["xrange"] = (ticket_intensity["xrange"][0]*TO_UM, ticket_intensity["xrange"][1]*TO_UM)

        if not ticket_intensity["fwhm"] is None and not ticket_intensity["fwhm"] == 0.0:
            ticket_intensity["fwhm_coordinates"] = (ticket_intensity["fwhm_coordinates"][0]*TO_UM, ticket_intensity["fwhm_coordinates"][1]*TO_UM)

        if self.iterative_mode==0:
            self.last_ticket = None
            self.current_histo_data = None
            self.current_stats = None
            self.last_histo_data = None
            self.current_histo_data_phase = None
            self.last_histo_data_phase = None
            self.histo_index = -1

            self.plot_canvas_intensity.plot_1D(ticket_intensity, var, title, xtitle, ytitle, xum, xrange, use_default_factor=False)
        elif self.iterative_mode == 1:
            self.current_histo_data = None
            self.current_stats = None
            self.last_histo_data = None
            self.current_histo_data_phase = None
            self.last_histo_data_phase = None
            self.histo_index = -1

            ticket_intensity['histogram'] += self.last_ticket['histogram']

            self.plot_canvas_intensity.plot_1D(ticket_intensity, var, title, xtitle, ytitle, xum, xrange, use_default_factor=False)

            self.last_ticket = ticket_intensity
        else:
            if not wavefront.scanned_variable_data is None:
                self.last_ticket = None
                self.histo_index += 1

                um = wavefront.scanned_variable_data.get_scanned_variable_um()
                um = " " + um if um.strip() == "" else " [" + um + "]"

                if self.multi_electron==0:
                    histo_data_phase = self.plot_canvas_phase.plot_histo(ticket_phase,
                                                                         col=var,
                                                                         title="Phase [rad]",
                                                                         xtitle=xtitle,
                                                                         ytitle=ytitle,
                                                                         histo_index=self.histo_index,
                                                                         scan_variable_name=wavefront.scanned_variable_data.get_scanned_variable_display_name() + um,
                                                                         scan_variable_value=wavefront.scanned_variable_data.get_scanned_variable_value(),
                                                                         offset=0.0 if self.last_histo_data_phase is None else self.last_histo_data_phase.offset,
                                                                         xrange=xrange,
                                                                         show_reference=False,
                                                                         add_labels=self.add_labels==1,
                                                                         has_colormap=self.has_colormap==1,
                                                                         use_default_factor=False
                                                                         )

                histo_data = self.plot_canvas_intensity.plot_histo(ticket_intensity,
                                                                   col=var,
                                                                   title=title,
                                                                   xtitle=xtitle,
                                                                   ytitle=ytitle,
                                                                   histo_index=self.histo_index,
                                                                   scan_variable_name=wavefront.scanned_variable_data.get_scanned_variable_display_name() + um,
                                                                   scan_variable_value=wavefront.scanned_variable_data.get_scanned_variable_value(),
                                                                   offset=0.0 if self.last_histo_data is None else self.last_histo_data.offset,
                                                                   xrange=xrange,
                                                                   show_reference=False,
                                                                   add_labels=self.add_labels==1,
                                                                   has_colormap=self.has_colormap==1,
                                                                   use_default_factor=False
                                                                   )

                scanned_variable_value = wavefront.scanned_variable_data.get_scanned_variable_value()

                if isinstance(scanned_variable_value, str):
                    histo_data.scan_value = self.histo_index + 1
                else:
                    histo_data.scan_value=wavefront.scanned_variable_data.get_scanned_variable_value()

                if not histo_data.bins is None:
                    if self.current_histo_data is None:
                        self.current_histo_data = HistogramDataCollection(histo_data)
                    else:
                        self.current_histo_data.add_histogram_data(histo_data)

                if self.multi_electron==0:
                    if isinstance(scanned_variable_value, str):
                        histo_data_phase.scan_value = self.histo_index + 1
                    else:
                        histo_data_phase.scan_value=wavefront.scanned_variable_data.get_scanned_variable_value()

                    if not histo_data_phase.bins is None:
                        if self.current_histo_data_phase is None:
                            self.current_histo_data_phase = HistogramDataCollection(histo_data_phase)
                        else:
                            self.current_histo_data_phase.add_histogram_data(histo_data_phase)

                if self.current_stats is None:
                    self.current_stats = StatisticalDataCollection(histo_data)
                else:
                    self.current_stats.add_statistical_data(histo_data)

                self.last_histo_data = histo_data
                if self.multi_electron==0: self.last_histo_data_phase = histo_data_phase

                self.plot_canvas_stats.plotCurves(self.current_stats.get_scan_values(),
                                                  self.current_stats.get_sigmas() if self.stats_to_plot==0 else self.current_stats.get_fwhms(),
                                                  self.current_stats.get_relative_peak_intensities() if self.stats_to_plot_2==0 else self.current_stats.get_relative_integral_intensities(),
                                                  "Statistics",
                                                  wavefront.scanned_variable_data.get_scanned_variable_display_name() + um,
                                                  "Sigma " + xum if self.stats_to_plot==0 else "FWHM " + xum,
                                                  "Relative Peak Intensity" if self.stats_to_plot_2==0 else "Relative Integral Intensity")


    def plot_histo(self, var_x, title, xtitle, ytitle, xum):
        wavefront_to_plot = self.input_srw_data.get_srw_wavefront()

        xrange = self.get_range(wavefront_to_plot, var_x)

        self.replace_fig(wavefront_to_plot, var_x, xrange, title, xtitle, ytitle, xum)

    def get_range(self, wavefront_to_plot, var_x):
        if self.x_range == 0 :
            if var_x == 1: # horizontal
                x_max = wavefront_to_plot.mesh.xFin
                x_min = wavefront_to_plot.mesh.xStart
            else:
                x_max = wavefront_to_plot.mesh.yFin
                x_min = wavefront_to_plot.mesh.yStart

            xrange = [x_min*TO_UM, x_max*TO_UM]
        else:
            congruence.checkLessThan(self.x_range_min, self.x_range_max, "Range min", "Range max")

            xrange = [self.x_range_min, self.x_range_max]

        return xrange

    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if not self.input_srw_data is None:
                x, title, x_title, y_title, xum = self.get_titles()

                self.plot_histo(x, title=title, xtitle=x_title, ytitle=y_title, xum=xum)

                plotted = True

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def get_titles(self):
        auto_title = self.x_column.currentText()

        xum = "[\u03bcm]"
        x_title = auto_title + " Position " + xum
        title = auto_title + " Cut"
        x = self.x_column_index + 1

        me = " ME " if self.multi_electron else " SE "

        if self.polarization_component_to_be_extracted == 0:
            y_title = "Intensity" + me + "[ph/s/.1%bw/mm\u00b2]"
        elif self.polarization_component_to_be_extracted == 1:
            y_title = "Intensity" + me + "\u03c3 [ph/s/.1%bw/mm\u00b2]"
        else:
            y_title = "Intensity" + me + "\u03c0 [ph/s/.1%bw/mm\u00b2]"

        return x, title, x_title, y_title, xum

    def set_input(self, srw_data):
        if not srw_data is None:
            self.input_srw_data = srw_data

            if self.is_automatic_run:
                self.plot_results()
        else:
            QMessageBox.critical(self, "Error", "Data not displayable: no input data", QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.srw_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.srw_output.setTextCursor(cursor)
        self.srw_output.ensureCursorVisible()


    def export_scanning_stats_analysis(self):
        output_folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", directory=os.curdir)

        if output_folder:
            if not self.current_histo_data is None:
                items = ("Hdf5 only", "Text only", "Hdf5 and Text")

                item, ok = QInputDialog.getItem(self, "Select Output Format", "Formats: ", items, 2, False)

                if ok and item:
                    if item == "Hdf5 only" or item == "Hdf5 and Text":
                            write_histo_and_stats_file_hdf5(histo_data=self.current_histo_data,
                                                        stats=self.current_stats,
                                                        suffix="_intensity",
                                                        output_folder=output_folder)
                    if item == "Text only" or item == "Hdf5 and Text":
                        write_histo_and_stats_file(histo_data=self.current_histo_data,
                                                   stats=self.current_stats,
                                                   suffix="_intensity",
                                                   output_folder=output_folder)

                    if self.multi_electron==0 and not self.current_histo_data_phase is None:
                        if item == "Hdf5 only" or item == "Hdf5 and Text":
                            write_histo_and_stats_file_hdf5(histo_data=self.current_histo_data_phase,
                                                            stats=None,
                                                            suffix="_phase",
                                                            output_folder=output_folder)
                        if item == "Text only" or item == "Hdf5 and Text":
                            write_histo_and_stats_file(histo_data=self.current_histo_data_phase,
                                                       stats=None,
                                                       suffix="_phase",
                                                       output_folder=output_folder)


                QMessageBox.information(self, "Export Scanning Results & Stats", "Data saved into directory: " + output_folder, QMessageBox.Ok)
