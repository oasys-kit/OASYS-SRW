__author__ = 'labx'

import os, sys

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

from syned.storage_ring.light_source import ElectronBeam, LightSource

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters
from wofrysrw.storage_ring.srw_light_source import PowerDensityPrecisionParameters, SRWLightSource
from wofrysrw.storage_ring.srw_electron_beam import SRWElectronBeam
from wofrysrw.beamline.srw_beamline import SRWBeamline

from orangecontrib.srw.util.srw_util import SRWPlot

from syned.widget.widget_decorator import WidgetDecorator

class OWSRWSource(SRWWavefrontViewer, WidgetDecorator):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = WidgetDecorator.syned_input_data()

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRW Source Data",
                "id":"data"}]

    want_main_area=1

    source_name = Setting("SRW Source")

    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.0007)
    ring_current = Setting(0.4)
    electron_beam_size_h = Setting(0.05545e-3)
    electron_beam_size_v = Setting(2.784e-6)
    electron_beam_divergence_h = Setting(0.2525e-9)
    electron_beam_divergence_v = Setting(0.8352e-11)

    moment_xx           = Setting(0.0)
    moment_xxp          = Setting(0.0)
    moment_xpxp         = Setting(0.0)
    moment_yy           = Setting(0.0)
    moment_yyp          = Setting(0.0)
    moment_ypyp         = Setting(0.0)

    electron_beam_drift_distance = Setting(0.0)

    type_of_properties = Setting(0)

    wf_photon_energy = Setting(0.0)
    wf_h_slit_gap = Setting(0.0001)
    wf_v_slit_gap =Setting( 0.0001)
    wf_h_slit_points=Setting(100)
    wf_v_slit_points=Setting(100)
    wf_distance = Setting(1.0)

    wf_sr_method = Setting(1)
    wf_relative_precision = Setting(0.01)
    wf_start_integration_longitudinal_position = Setting(0.0) 
    wf_end_integration_longitudinal_position = Setting(0.0) 
    wf_number_of_points_for_trajectory_calculation = Setting(50000)
    wf_use_terminating_terms = Setting(1)
    wf_sampling_factor_for_adjusting_nx_ny = Setting(0.0) 

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


    pow_precision_factor = Setting(1.5)  
    pow_computation_method = Setting(1) 
    pow_initial_longitudinal_position = Setting(0.0)
    pow_final_longitudinal_position = Setting(0.0) 
    pow_number_of_points_for_trajectory_calculation = Setting(20000)

    spe_photon_energy_min = Setting(100.0)
    spe_photon_energy_max = Setting(100100.0)
    spe_photon_energy_points=Setting(10000)
    spe_h_slit_gap = Setting(0.0001)
    spe_v_slit_gap =Setting( 0.0001)
    spe_distance = Setting(1.0)

    spe_sr_method = Setting(1)  
    spe_relative_precision = Setting(0.01) 
    spe_start_integration_longitudinal_position = Setting(0.0) 
    spe_end_integration_longitudinal_position = Setting(0.0) 
    spe_number_of_points_for_trajectory_calculation = Setting(50000)
    spe_use_terminating_terms = Setting(1)
    spe_sampling_factor_for_adjusting_nx_ny = Setting(0.0)

    calculated_total_power = 0.0

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run SRW", self)
        self.runaction.triggered.connect(self.runSRWSource)
        self.addAction(self.runaction)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run SRW Source", callback=self.runSRWSource)
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

        self.tab_source = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        oasysgui.lineEdit(self.tab_source, self, "source_name", "Light Source Name", labelWidth=260, valueType=str, orientation="horizontal")

        left_box_1 = oasysgui.widgetBox(self.tab_source, "Electron Beam/Machine Parameters", addSpace=True, orientation="vertical", height=350)

        oasysgui.lineEdit(left_box_1, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_1, self, "type_of_properties", label="Electron Beam Properties", labelWidth=350,
                     items=["From 2nd Moments", "From Size/Divergence"],
                     callback=self.set_TypeOfProperties,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_2_1 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=160)

        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xx", "Moment xx   [m^2]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xxp", "Moment xxp  [m.rad]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_xpxp", "Moment xpxp [rad^2]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yy", "Moment yy   [m^2]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_yyp", "Moment yyp  [m.rad]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_1, self, "moment_ypyp", "Moment ypyp [rad^2]", labelWidth=200, valueType=float, orientation="horizontal")


        self.left_box_2_2 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=160)

        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_h",       "Horizontal Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_size_v",       "Vertical Beam Size [m]",  labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_h", "Horizontal Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.left_box_2_2, self, "electron_beam_divergence_v", "Vertical Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_TypeOfProperties()

        oasysgui.lineEdit(left_box_1, self, "electron_beam_drift_distance", "Beam propagation distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.tab_plots = oasysgui.createTabPage(self.tabs_setting, "Wavefront Setting")

        self.tabs_plots_setting = oasysgui.tabWidget(self.tab_plots)
        
        # PROPAGATION -------------------------------------------
        
        tab_wav = oasysgui.createTabPage(self.tabs_plots_setting, "Propagation")

        wav_box = oasysgui.widgetBox(tab_wav, "Wavefront Parameters", addSpace=True, orientation="vertical")

        self.build_wf_photon_energy_box(wav_box)
        oasysgui.lineEdit(wav_box, self, "wf_h_slit_gap", "H Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_v_slit_gap", "V Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_h_slit_points", "H Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_v_slit_points", "V Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        pre_box = oasysgui.widgetBox(tab_wav, "Precision Parameters", addSpace=False, orientation="vertical")

        gui.comboBox(pre_box, self, "wf_sr_method", label="Calculation Method",
                     items=["Manual", "Auto"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(pre_box, self, "wf_relative_precision", "Relative Precision", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_start_integration_longitudinal_position", "Longitudinal position to start integration\n(effective if < zEndInteg) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_end_integration_longitudinal_position", "Longitudinal position to finish integration\n(effective if > zStartInteg) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(pre_box, self, "wf_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")

        gui.comboBox(pre_box, self, "wf_use_terminating_terms", label="Use \"terminating terms\"\n(i.e. asymptotic expansions at zStartInteg\nand zEndInteg) or not",
                     items=["No", "Yes"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(pre_box, self, "wf_sampling_factor_for_adjusting_nx_ny", "Sampling factor for adjusting nx/ny\n(effective if > 0)", labelWidth=260, valueType=int, orientation="horizontal")

        # INTENSITY/POWER  -------------------------------------------

        tab_convolution = oasysgui.createTabPage(self.tabs_plots_setting, "Intensity/Power Density")

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

        tab_pow = oasysgui.createTabPage(tabs_precision, "Power Density")

        oasysgui.lineEdit(tab_pow, self, "pow_precision_factor", "Precision Factor", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(tab_pow, self, "pow_computation_method", label="Computation Method",
                     items=["Near Field", "Far Field"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_pow, self, "pow_initial_longitudinal_position", "Initial longitudinal position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_pow, self, "pow_final_longitudinal_position", "Final longitudinal position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_pow, self, "pow_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")
    
        # FLUX -------------------------------------------

        tab_flux = oasysgui.createTabPage(self.tabs_plots_setting, "Flux")

        spe_box = oasysgui.widgetBox(tab_flux, "Wavefront Parameters", addSpace=True, orientation="vertical")
    
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_min", "Photon Energy Min [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_max", "Photon Energy Max [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_points", "Photon Energy Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_h_slit_gap", "H Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_v_slit_gap", "V Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        pre_box = oasysgui.widgetBox(tab_flux, "Precision Parameters", addSpace=False, orientation="vertical")

        tabs_precision = oasysgui.tabWidget(pre_box)

        tab_prop = oasysgui.createTabPage(tabs_precision, "Propagation")

        gui.comboBox(tab_prop, self, "spe_sr_method", label="Calculation Method",
                     items=["Manual", "Auto"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_prop, self, "spe_relative_precision", "Relative Precision", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "spe_start_integration_longitudinal_position", "Longitudinal pos. to start integration [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "spe_end_integration_longitudinal_position", "Longitudinal pos. to finish integration [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_prop, self, "spe_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")

        gui.comboBox(tab_prop, self, "spe_use_terminating_terms", label="Use \"terminating terms\"or not",
                     items=["No", "Yes"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_prop, self, "spe_sampling_factor_for_adjusting_nx_ny", "Sampling factor for adjusting nx/ny", labelWidth=260, valueType=int, orientation="horizontal")

        # FLUX  -------------------------------------------

        self.build_flux_precision_tab(tabs_precision)

        gui.rubber(self.controlArea)

    def set_TypeOfProperties(self):
        self.left_box_2_1.setVisible(self.type_of_properties==0)
        self.left_box_2_2.setVisible(self.type_of_properties==1)

    def build_wf_photon_energy_box(self, box):
        oasysgui.lineEdit(box, self, "wf_photon_energy", "Photon Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

    def build_flux_precision_tab(self, tabs_precision):
        pass

    def runSRWSource(self):
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

            if self.is_do_plots():
                self.run_calculation_intensity_power(srw_source, tickets)
                self.run_calculation_flux(srw_source, tickets)

            self.setStatusMessage("Plotting Results")

            self.plot_results(tickets)

            self.setStatusMessage("")

            beamline = SRWBeamline(light_source=srw_source)
            wavefront = self.calculate_wavefront_propagation(srw_source)

            self.send("SRWData", SRWData(srw_beamline=beamline, srw_wavefront=wavefront))

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            #raise exception

        self.progressBarFinished()

    def get_electron_beam(self):
        electron_beam = SRWElectronBeam(energy_in_GeV=self.electron_energy_in_GeV,
                                        energy_spread=self.electron_energy_spread,
                                        current=self.ring_current,
                                        drift_distance=self.electron_beam_drift_distance)
        if self.type_of_properties == 0:
            electron_beam._moment_xx = self.moment_xx
            electron_beam._moment_xxp = self.moment_xxp
            electron_beam._moment_xpxp = self.moment_xpxp
            electron_beam._moment_yy = self.moment_yy
            electron_beam._moment_yyp = self.moment_yyp
            electron_beam._moment_ypyp = self.moment_ypyp

            x, xp, y, yp = electron_beam.get_sigmas_all()

            self.electron_beam_size_h = x
            self.electron_beam_size_v = y
            self.electron_beam_divergence_h = xp
            self.electron_beam_divergence_v = yp
        else:
            electron_beam.set_sigmas_all(sigma_x=self.electron_beam_size_h,
                                         sigma_y=self.electron_beam_size_v,
                                         sigma_xp=self.electron_beam_divergence_h,
                                         sigma_yp=self.electron_beam_divergence_v)

            self.moment_xx = electron_beam._moment_xx
            self.moment_xpxp = electron_beam._moment_xpxp
            self.moment_yy = electron_beam._moment_yy
            self.moment_ypyp = electron_beam._moment_ypyp

        return electron_beam

    def get_srw_source(self, electron_beam=ElectronBeam()):
        raise NotImplementedError()

    def getCalculatedTotalPowerString(self):
        if self.calculated_total_power == 0:
            return ""
        else:
            return "Total: " + str(int(self.calculated_total_power)) + " W"

    def checkFields(self):

        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        congruence.checkPositiveNumber(self.electron_energy_spread, "Energy Spread")
        congruence.checkStrictlyPositiveNumber(self.ring_current, "Ring Current")

        if self.type_of_properties == 0:
            congruence.checkPositiveNumber(self.moment_xx   , "Moment xx")
            congruence.checkPositiveNumber(self.moment_xxp  , "Moment xxp")
            congruence.checkPositiveNumber(self.moment_xpxp , "Moment xpxp")
            congruence.checkPositiveNumber(self.moment_yy   , "Moment yy")
            congruence.checkPositiveNumber(self.moment_yyp  , "Moment yyp")
            congruence.checkPositiveNumber(self.moment_ypyp , "Moment ypyp")
        else:
            congruence.checkPositiveNumber(self.electron_beam_size_h       , "Horizontal Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_divergence_h , "Vertical Beam Size")
            congruence.checkPositiveNumber(self.electron_beam_size_v       , "Horizontal Beam Divergence")
            congruence.checkPositiveNumber(self.electron_beam_divergence_v , "Vertical Beam Divergence")

        self.checkLightSourceSpecificFields()

        # WAVEFRONT

        self.checkWavefrontPhotonenergy()

        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_gap, "Wavefront Propagation H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_gap, "Wavefront Propagation V Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_points, "Wavefront Propagation H Slit Points")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_points, "Wavefront Propagation V Slit Points")
        congruence.checkGreaterOrEqualThan(self.wf_distance, self.get_minimum_propagation_distance(),
                                           "Wavefront Propagation Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.wf_relative_precision, "Wavefront Propagation Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.wf_number_of_points_for_trajectory_calculation, "Wavefront Propagation Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.wf_sampling_factor_for_adjusting_nx_ny, "Wavefront Propagation Sampling Factor for adjusting nx/ny")


        # INTENSITY/POWER

        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_min, "Intensity/Power Density Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_max, "Intensity/Power Density Photon Energy Max")
        congruence.checkGreaterOrEqualThan(self.int_photon_energy_max, self.int_photon_energy_min, "Intensity/Power Density Photon Energy Max", "Intensity/Power Density Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.int_photon_energy_points, "Intensity/Power Density Photon Energy Points")
        
        congruence.checkStrictlyPositiveNumber(self.int_h_slit_gap, "Intensity/Power Density H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.int_v_slit_gap, "Intensity/Power Density V Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.int_h_slit_points, "Intensity/Power Density H Slit Points")
        congruence.checkStrictlyPositiveNumber(self.int_v_slit_points, "Intensity/Power Density V Slit Points")
        congruence.checkGreaterOrEqualThan(self.int_distance, self.get_minimum_propagation_distance(),
                                           "Intensity/Power Density Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.int_relative_precision, "Intensity/Power Density Propagation - Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.int_number_of_points_for_trajectory_calculation, "Intensity/Power Density Propagation - Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.int_sampling_factor_for_adjusting_nx_ny, " Intensity/Power Density Propagation - Sampling Factor for adjusting nx/ny")

        congruence.checkStrictlyPositiveNumber(self.pow_precision_factor, "Intensity/Power Density Power - Precision Factor")
        congruence.checkStrictlyPositiveNumber(self.pow_number_of_points_for_trajectory_calculation, "Intensity/Power Density Power - Number of points for trajectory calculation")


        # FLUX
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_min, "Flux Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_max, "Flux Photon Energy Max")
        congruence.checkGreaterOrEqualThan(self.spe_photon_energy_max, self.spe_photon_energy_min, "Flux Photon Energy Max", "Flux Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_points, "Flux Photon Energy Points")
        
        congruence.checkStrictlyPositiveNumber(self.spe_h_slit_gap, "Flux H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.spe_v_slit_gap, "Flux V Slit Gap")
        congruence.checkGreaterOrEqualThan(self.spe_distance, self.get_minimum_propagation_distance(),
                                           "Flux Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.spe_relative_precision, "Flux Propagation - Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.spe_number_of_points_for_trajectory_calculation, "Flux Propagation - Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.spe_sampling_factor_for_adjusting_nx_ny, "Flux Propagation - Sampling Factor for adjusting nx/ny")

        self.checkFluxSpecificFields()


    def checkLightSourceSpecificFields(self):
        raise NotImplementedError()


    def checkWavefrontPhotonenergy(self):
        congruence.checkStrictlyPositiveNumber(self.wf_photon_energy, "Wavefront Propagation Photon Energy")

    def checkFluxSpecificFields(self):
        pass

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

        e, h, v, i = srw_wavefront.get_intensity(multi_electron=False)

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value)

        e, h, v, i = srw_wavefront.get_phase()

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value + 5)

        e, h, v, i = srw_wavefront.get_intensity(multi_electron=True)

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value + 5)

        # POWER DENSITY

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

        h, v, p = srw_source.get_power_density(source_wavefront_parameters=wf_parameters,
                                               power_density_precision_parameters=PowerDensityPrecisionParameters(precision_factor=self.pow_precision_factor,
                                                                                                                  computation_method=self.pow_computation_method,
                                                                                                                  initial_longitudinal_position=self.pow_initial_longitudinal_position,
                                                                                                                  final_longitudinal_position=self.pow_final_longitudinal_position,
                                                                                                                  number_of_points_for_trajectory_calculation=self.pow_number_of_points_for_trajectory_calculation))

        self.calculated_total_power = SRWLightSource.get_total_power_from_power_density(h, v, p)

        print("TOTAL POWER: ", self.calculated_total_power, " W")

        tickets.append(SRWPlot.get_ticket_2D(h, v, p))

        self.progressBarSet(progress_bar_value + 10)

    def get_automatic_sr_method(self):
        raise NotImplementedError()

    def run_calculation_flux(self, srw_source, tickets, progress_bar_value=50):
        raise NotImplementedError()

    def calculate_wavefront_propagation(self, srw_source):

        photon_energy = self.get_photon_energy_for_wavefront_propagation(srw_source)

        wf_parameters = WavefrontParameters(photon_energy_min = photon_energy,
                                            photon_energy_max = photon_energy,
                                            photon_energy_points=1,
                                            h_slit_gap = self.wf_h_slit_gap,
                                            v_slit_gap = self.wf_v_slit_gap,
                                            h_slit_points=self.wf_h_slit_points,
                                            v_slit_points=self.wf_v_slit_points,
                                            distance = self.wf_distance,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.wf_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                        relative_precision=self.wf_relative_precision,
                                                                                                        start_integration_longitudinal_position=self.wf_start_integration_longitudinal_position,
                                                                                                        end_integration_longitudinal_position=self.wf_end_integration_longitudinal_position,
                                                                                                        number_of_points_for_trajectory_calculation=self.wf_number_of_points_for_trajectory_calculation,
                                                                                                        use_terminating_terms=self.wf_use_terminating_terms,
                                                                                                        sampling_factor_for_adjusting_nx_ny=self.wf_sampling_factor_for_adjusting_nx_ny))

        return srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

    def get_photon_energy_for_wavefront_propagation(self, srw_source):
        return self.wf_photon_energy

    def get_minimum_propagation_distance(self):
        return round(self.get_source_length()*1.01, 6)

    def get_source_length(self):
        raise NotImplementedError()

    def receive_syned_data(self, data):
        if not data is None:
            if not data._light_source is None and isinstance(data._light_source, LightSource):
                light_source = data._light_source

                self.source_name = light_source._name
                self.electron_energy_in_GeV = light_source._electron_beam._energy_in_GeV
                self.electron_energy_spread = light_source._electron_beam._energy_spread
                self.ring_current = light_source._electron_beam._current

                self.moment_xx = light_source._electron_beam._moment_xx
                self.moment_xxp = light_source._electron_beam._moment_xxp
                self.moment_xpxp = light_source._electron_beam._moment_xpxp
                self.moment_yy = light_source._electron_beam._moment_yy
                self.moment_yyp = light_source._electron_beam._moment_yyp
                self.moment_ypyp = light_source._electron_beam._moment_ypyp

                x, xp, y, yp = light_source._electron_beam.get_sigmas_all()

                self.electron_beam_size_h = x
                self.electron_beam_size_v = y
                self.electron_beam_divergence_h = xp
                self.electron_beam_divergence_v = yp

                self.type_of_properties = 0

                self.set_TypeOfProperties()

                self.receive_specific_syned_data(data)
            else:
                raise ValueError("Syned data not correct")

    def receive_specific_syned_data(self, data):
        raise NotImplementedError()