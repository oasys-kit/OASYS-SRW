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

from wofrysrw.storage_ring.srw_light_source import SourceWavefrontParameters, WavefrontPrecisionParameters, PowerDensityPrecisionParameters, SRWLightSource
from wofrysrw.beamline.srw_beamline import SRWBeamline

from orangecontrib.srw.util.srw_util import SRWPlot

class SRWSource(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

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

    spe_initial_UR_harmonic = Setting(1)
    spe_final_UR_harmonic = Setting(21)
    spe_longitudinal_integration_precision_parameter = Setting(1.5)
    spe_azimuthal_integration_precision_parameter = Setting(1.5)
    spe_calculation_type = Setting(2)

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

        left_box_1 = oasysgui.widgetBox(self.tab_source, "Electron Beam/Machine Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_h", "Horizontal Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_v", "Vertical Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_divergence_h", "Horizontal Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_divergence_v", "Vertical Beam Divergence", labelWidth=260, valueType=float, orientation="horizontal")

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

        tab_convolution = oasysgui.createTabPage(self.tabs_plots_setting, "Intensity/Power")

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

        tab_pow = oasysgui.createTabPage(tabs_precision, "Power")

        oasysgui.lineEdit(tab_pow, self, "pow_precision_factor", "Precision Factor", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(tab_pow, self, "pow_computation_method", label="Computation Method",
                     items=["Near Field", "Far Field"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(tab_pow, self, "pow_initial_longitudinal_position", "Initial longitudinal position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_pow, self, "pow_final_longitudinal_position", "Final longitudinal position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_pow, self, "pow_number_of_points_for_trajectory_calculation", "Number of points for trajectory calculation", labelWidth=260, valueType=int, orientation="horizontal")
    
        # FLUX -------------------------------------------

        tab_flux = oasysgui.createTabPage(self.tabs_plots_setting, "Spectral Flux")

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

        tab_flu = oasysgui.createTabPage(tabs_precision, "Spectral Flux")

        oasysgui.lineEdit(tab_flu, self, "spe_initial_UR_harmonic", "Initial Harmonic", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(tab_flu, self, "spe_final_UR_harmonic", "Final Harmonic", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(tab_flu, self, "spe_longitudinal_integration_precision_parameter", "Longitudinal integration precision param.", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_flu, self, "spe_azimuthal_integration_precision_parameter", "Azimuthal integration precision param.", labelWidth=260, valueType=int, orientation="horizontal")

    def build_wf_photon_energy_box(self, box):
        oasysgui.lineEdit(box, self, "wf_photon_energy", "Photon Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

    def runSRWSource(self):
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            srw_source = self.get_srw_source()

            self.progressBarSet(10)

            self.setStatusMessage("Running SRW")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            print(srw_source.get_electron_beam().get_electron_beam_geometrical_properties().to_info())

            self.print_specific_infos(srw_source)

            self.progressBarSet(20)

            tickets = []

            self.run_calculation_intensity_power(srw_source, tickets)
            self.run_calculation_flux(srw_source, tickets)

            self.setStatusMessage("Plotting Results")

            self.plot_results(tickets)

            self.setStatusMessage("")

            beamline = SRWBeamline(light_source=srw_source)
            wavefront = self.calculate_wavefront_propagation(srw_source)

            self.send("SRWData", SRWData(srw_beamline=beamline, srw_wavefront=wavefront))

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                       str(exception),
                QMessageBox.Ok)

            raise exception

        self.progressBarFinished()


    def checkFields(self):

        #TODO: checks

        self.checkSpecificFields()

    def checkSpecificFields(self):
        raise NotImplementedError()

    def run_calculation_intensity_power(self, srw_source, tickets, progress_bar_value=30):
        wf_parameters = SourceWavefrontParameters(photon_energy_min = self.int_photon_energy_min,
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

        e, h, v, i = srw_source.get_intensity(source_wavefront_parameters=wf_parameters)

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value)

        # POWER DENSITY

        wf_parameters = SourceWavefrontParameters(photon_energy_min = self.int_photon_energy_min,
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

        print(SRWLightSource.get_total_power_from_power_density(h, v, p))

        tickets.append(SRWPlot.get_ticket_2D(h, v, p))

        self.progressBarSet(progress_bar_value + 10)

    def get_automatic_sr_method(self):
        raise NotImplementedError()

    def run_calculation_flux(self, srw_source, tickets, progress_bar_value=50):
        raise NotImplementedError()

    def calculate_wavefront_propagation(self, srw_source):

        photon_energy = self.get_photon_energy_for_wavefront_propagation(srw_source)

        wf_parameters = SourceWavefrontParameters(photon_energy_min = photon_energy,
                                                  photon_energy_max = photon_energy,
                                                  photon_energy_points=1,
                                                  h_slit_gap = self.wf_h_slit_gap,
                                                  v_slit_gap = self.wf_v_slit_gap,
                                                  h_slit_points=self.wf_h_slit_points,
                                                  v_slit_points=self.wf_v_slit_points,
                                                  distance = self.get_source_length(srw_source)*1.01,
                                                  wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.wf_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                              relative_precision=self.wf_relative_precision,
                                                                                                              start_integration_longitudinal_position=self.wf_start_integration_longitudinal_position,
                                                                                                              end_integration_longitudinal_position=self.wf_end_integration_longitudinal_position,
                                                                                                              number_of_points_for_trajectory_calculation=self.wf_number_of_points_for_trajectory_calculation,
                                                                                                              use_terminating_terms=self.wf_use_terminating_terms,
                                                                                                              sampling_factor_for_adjusting_nx_ny=self.wf_sampling_factor_for_adjusting_nx_ny))


        wavefront = srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

        from srwlib import SRWLOptC, SRWLOptD, srwl

        opDrift = SRWLOptD(-self.get_source_length(srw_source)*1.01) #Drift space from lens to image plane
        ppDrift = [0, 0, 1., 1, 0, 1.0, 1.0, 1.0, 1.0, 0, 0, 0]

        srwl.PropagElecField(wavefront, SRWLOptC([opDrift], [ppDrift]))

        return wavefront

    def get_photon_energy_for_wavefront_propagation(self, srw_source):
        return self.wf_photon_energy

    def get_source_length(self):
        raise NotImplementedError()