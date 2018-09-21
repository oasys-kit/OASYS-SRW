__author__ = 'labx'

import os, sys, numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from syned.storage_ring.light_source import ElectronBeam

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters
from wofrysrw.storage_ring.srw_light_source import SRWLightSource
from wofrysrw.storage_ring.srw_electron_beam import SRWElectronBeam

from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

class OWSRWRadiation(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Source"
    keywords = ["data", "file", "load", "read"]
    name = "Source Radiation"
    description = "SRW Source: Radiation"
    icon = "icons/radiation.png"
    priority = 3

    inputs = [("SRWData", SRWData, "receive_srw_data")]

    want_main_area=1

    source_name = "SRW Source"
    electron_energy_in_GeV = 0.0
    electron_energy_spread = 0.0
    ring_current = 0.0
    electron_beam_size_h = 0.0
    electron_beam_size_v = 0.0
    electron_beam_divergence_h = 0.0
    electron_beam_divergence_v = 0.0
    moment_x = 0.0
    moment_y = 0.0
    moment_z = 0.0
    moment_xp = 0.0
    moment_yp = 0.0
    moment_xx           = 0.0
    moment_xxp          = 0.0
    moment_xpxp         = 0.0
    moment_yy           = 0.0
    moment_yyp          = 0.0
    moment_ypyp         = 0.0

    int_photon_energy_min = Setting(0.0)
    int_photon_energy_max = Setting(0.0)
    int_photon_energy_points=Setting(1)
    int_h_slit_gap = Setting(0.0001)
    int_v_slit_gap =Setting( 0.0001)
    int_h_slit_points=Setting(100)
    int_v_slit_points=Setting(100)
    int_distance = Setting(1.0)

    int_sr_method = Setting(1)  
    int_relative_precision = Setting(0.01) 
    int_start_integration_longitudinal_position = Setting(0.0) 
    int_end_integration_longitudinal_position = Setting(0.0) 
    int_number_of_points_for_trajectory_calculation = Setting(50000)
    int_use_terminating_terms = Setting(1)
    int_sampling_factor_for_adjusting_nx_ny = Setting(0.0)

    calculated_total_power = 0.0

    received_light_source = None

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box, show_view_box=False)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Radiation", callback=self.calculateRadiation)
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

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # INTENSITY/POWER  -------------------------------------------

        tab_convolution = oasysgui.createTabPage(self.tabs_setting, "Radiation")

        int_box = oasysgui.widgetBox(tab_convolution, "Wavefront Parameters", addSpace=True, orientation="vertical")
    
        oasysgui.lineEdit(int_box, self, "int_photon_energy_min", "Photon Energy Min [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_photon_energy_max", "Photon Energy Max [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_photon_energy_points", "Photon Energy Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_h_slit_gap", "H Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_v_slit_gap", "V Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_h_slit_points", "H Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_v_slit_points", "V Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(int_box, self, "int_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        pre_box = oasysgui.widgetBox(tab_convolution, "Precision Parameters", addSpace=False, orientation="vertical")

        tabs_precision = oasysgui.tabWidget(pre_box)

        tab_prop = oasysgui.createTabPage(tabs_precision, "Propagation")

        gui.comboBox(tab_prop, self, "int_sr_method", label="Calculation Method",
                     items=["Manual", "Auto"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_prop, self, "int_relative_precision", "Relative Precision", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "int_start_integration_longitudinal_position", "Longitudinal pos. to start integration [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "int_end_integration_longitudinal_position", "Longitudinal pos. to finish integration [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "int_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")

        gui.comboBox(tab_prop, self, "int_use_terminating_terms", label="Use \"terminating terms\"or not",
                     items=["No", "Yes"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_prop, self, "int_sampling_factor_for_adjusting_nx_ny", "Sampling factor for adjusting nx/ny", labelWidth=260, valueType=int, orientation="horizontal")

        gui.rubber(self.controlArea)

    def calculateRadiation(self):
        if not self.received_light_source is None:

            self.setStatusMessage("")
            self.progressBarInit()

            try:
                self.checkFields()

                srw_source = self.get_srw_source(self.get_electron_beam())

                self.progressBarSet(10)

                self.setStatusMessage("Running SRW")

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                print(srw_source.get_electron_beam().get_electron_beam_geometrical_properties().to_info())

                self.print_specific_infos(srw_source)

                self.progressBarSet(20)

                tickets = []

                self.run_calculation_intensity_power(srw_source, tickets)

                self.setStatusMessage("Plotting Results")

                self.plot_results(tickets)

                self.setStatusMessage("")

            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

            self.progressBarFinished()

    def get_electron_beam(self):
        received_electron_beam = self.received_light_source.get_electron_beam()

        electron_beam = SRWElectronBeam(energy_in_GeV=received_electron_beam._energy_in_GeV,
                                        energy_spread=received_electron_beam._energy_spread,
                                        current=received_electron_beam._current)

        electron_beam._moment_x = 0.0
        electron_beam._moment_y = 0.0
        electron_beam._moment_z = self.get_default_initial_z()
        electron_beam._moment_xp = 0.0
        electron_beam._moment_yp = 0.0
        electron_beam._moment_xx = received_electron_beam._moment_xx
        electron_beam._moment_xxp = received_electron_beam._moment_xxp
        electron_beam._moment_xpxp = received_electron_beam._moment_xpxp
        electron_beam._moment_yy = received_electron_beam._moment_yy
        electron_beam._moment_yyp = received_electron_beam._moment_yyp
        electron_beam._moment_ypyp = received_electron_beam._moment_ypyp

        return electron_beam

    def print_specific_infos(self, srw_source):
        if isinstance(self.received_light_source, SRWUndulatorLightSource):
            print("1st Harmonic Energy", srw_source.get_resonance_energy())
            print(srw_source.get_photon_source_properties(harmonic=1).to_info())

    def get_default_initial_z(self):
        if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return -0.5*self.received_light_source._magnetic_structure._length
        elif isinstance(self.received_light_source, SRWUndulatorLightSource):
            return -0.5*self.received_light_source._magnetic_structure._period_length*(self.received_light_source._magnetic_structure._number_of_periods + 4) # initial Longitudinal Coordinate (set before the ID)

    def get_srw_source(self, electron_beam=ElectronBeam()):
        if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return SRWBendingMagnetLightSource(name=self.received_light_source._name,
                                               electron_beam=electron_beam,
                                               bending_magnet_magnetic_structure=self.received_light_source._magnetic_structure
                                               )
        elif isinstance(self.received_light_source, SRWUndulatorLightSource):
            return SRWUndulatorLightSource(name=self.received_light_source._name,
                                           electron_beam=electron_beam,
                                           undulator_magnetic_structure=self.received_light_source._magnetic_structure
                                           )

    def getCalculatedTotalPowerString(self):
        if self.calculated_total_power == 0:
            return ""
        else:
            return "Total: " + str(int(self.calculated_total_power)) + " W"

    def get_automatic_sr_method(self):
        if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return 2
        elif isinstance(self.received_light_source, SRWUndulatorLightSource):
            return 1

    def get_minimum_propagation_distance(self):
        return round(self.get_source_length()*1.01, 6)

    def get_source_length(self):
        if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return self.received_light_source._magnetic_structure._length
        elif isinstance(self.received_light_source, SRWUndulatorLightSource):
            return self.received_light_source._magnetic_structure._period_length*self.received_light_source._magnetic_structure._number_of_periods

    def checkFields(self):

        # INTENSITY/POWER

        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_min, "Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_max, "Photon Energy Max")
        congruence.checkGreaterOrEqualThan(self.int_photon_energy_max, self.int_photon_energy_min, "Photon Energy Max", "Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_points, "Photon Energy Points")
        
        congruence.checkStrictlyPositiveNumber(self.int_h_slit_gap, "H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.int_v_slit_gap, "V Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.int_h_slit_points, "H Slit Points")
        congruence.checkStrictlyPositiveNumber(self.int_v_slit_points, "V Slit Points")
        congruence.checkGreaterOrEqualThan(self.int_distance, self.get_minimum_propagation_distance(),
                                           "Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.int_relative_precision, "Propagation - Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.int_number_of_points_for_trajectory_calculation, "Propagation - Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.int_sampling_factor_for_adjusting_nx_ny, " Propagation - Sampling Factor for adjusting nx/ny")

    def run_calculation_intensity_power(self, srw_source, tickets, progress_bar_value=30):
        wf_parameters = WavefrontParameters(photon_energy_min = self.int_photon_energy_min,
                                            photon_energy_max = self.int_photon_energy_max,
                                            photon_energy_points=self.int_photon_energy_points,
                                            h_slit_gap = self.int_h_slit_gap,
                                            v_slit_gap = self.int_v_slit_gap,
                                            h_slit_points=self.int_h_slit_points,
                                            v_slit_points=self.int_v_slit_points,
                                            distance = self.int_distance,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.int_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                        relative_precision=self.int_relative_precision,
                                                                                                        start_integration_longitudinal_position=self.int_start_integration_longitudinal_position,
                                                                                                        end_integration_longitudinal_position=self.int_end_integration_longitudinal_position,
                                                                                                        number_of_points_for_trajectory_calculation=self.int_number_of_points_for_trajectory_calculation,
                                                                                                        use_terminating_terms=self.int_use_terminating_terms,
                                                                                                        sampling_factor_for_adjusting_nx_ny=self.int_sampling_factor_for_adjusting_nx_ny))

        srw_wavefront = srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

        e, h, v, i_se = srw_wavefront.get_intensity(multi_electron=False)

        tickets.append((i_se, e, h*1e3, v*1e3))

        e, h, v, i_me = srw_wavefront.get_intensity(multi_electron=True)

        tickets.append((i_me, e, h*1e3, v*1e3))

        if len(e) > 1: energy_step = e[1]-e[0]
        else: energy_step = 1.0

        import scipy.constants as codata
        pd = i_se.sum(axis=0)*energy_step*codata.e*1e3

        self.calculated_total_power = SRWLightSource.get_total_power_from_power_density(h, v, pd)

        print("TOTAL POWER: ", self.calculated_total_power, " W")
        
        tickets.append(SRWPlot.get_ticket_2D(h, v, pd))

        self.progressBarSet(progress_bar_value + 10)

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity SE vs E,X,Y [ph/s/.1%bw/mm\u00b2]",
                            "Intensity ME vs E,X,Y [ph/s/.1%bw/mm\u00b2]",
                            "Power Density vs X,Y [W/mm\u00b2]"]
        else: return ["Intensity SE vs E,X,Y", "Intensity ME vs E,X,Y", "Power Density vs X,Y"]

    def getXTitles(self):
        return ["X [mm]", "X [mm]", "X [mm]"]

    def getYTitles(self):
        return ["Y [mm]", "Y [mm]", "Y [mm]"]

    def getXUM(self):
        return ["X [mm]", "X [mm]", "X [mm]"]

    def getYUM(self):
        return ["Y [mm]", "Y [mm]", "X [mm]"]

    def receive_srw_data(self, data):
        if not data is None:
            try:
                if isinstance(data, SRWData):
                    self.received_light_source = data.get_srw_beamline().get_light_source()

                    if not (isinstance(self.received_light_source, SRWBendingMagnetLightSource) or isinstance(self.received_light_source, SRWUndulatorLightSource)):
                        raise ValueError("This source is not supported")

                    received_wavefront = data.get_srw_wavefront()

                    if not received_wavefront is None:
                        if self.int_photon_energy_min == 0.0 and self.int_photon_energy_max == 0.0:
                            self.int_photon_energy_min = received_wavefront.mesh.eStart
                            self.int_photon_energy_max = received_wavefront.mesh.eFin
                            self.int_photon_energy_points=received_wavefront.mesh.ne
                        self.int_h_slit_gap = received_wavefront.mesh.xFin - received_wavefront.mesh.xStart
                        self.int_v_slit_gap = received_wavefront.mesh.yFin - received_wavefront.mesh.yStart
                        self.int_h_slit_points=received_wavefront.mesh.nx
                        self.int_v_slit_points=received_wavefront.mesh.ny
                        self.int_distance = received_wavefront.mesh.zStart
                else:
                    raise ValueError("SRW data not correct")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

