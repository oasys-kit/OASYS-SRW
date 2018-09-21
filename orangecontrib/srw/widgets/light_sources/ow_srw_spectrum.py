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

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters, PolarizationComponent
from wofrysrw.storage_ring.srw_electron_beam import SRWElectronBeam

from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource

from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import FluxPrecisionParameters, SRWUndulatorLightSource

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

class OWSRWSpectrum(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Source"
    keywords = ["data", "file", "load", "read"]
    name = "Source Spectrum"
    description = "SRW Source: Source Spectrum"
    icon = "icons/spectrum.png"
    priority = 5

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

    spe_photon_energy_min = Setting(100.0)
    spe_photon_energy_max = Setting(100100.0)
    spe_photon_energy_points=Setting(10000)
    spe_h_slit_gap = Setting(0.0001)
    spe_v_slit_gap =Setting( 0.0001)
    spe_h_slit_points=Setting(1)
    spe_v_slit_points=Setting(1)
    spe_distance = Setting(1.0)
    spe_on_axis_x = Setting(0.0)
    spe_on_axis_y =Setting( 0.0)
    spe_polarization_component_to_be_extracted = Setting(6)

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

    calculated_total_power = 0.0

    received_light_source = None

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box, show_view_box=False)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Spectrum", callback=self.calculateRadiation)
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

        # FLUX -------------------------------------------

        spe_box = oasysgui.widgetBox(self.controlArea, "Wavefront Parameters", addSpace=False, orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)
    
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_min", "Photon Energy Min [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_max", "Photon Energy Max [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_photon_energy_points", "Photon Energy Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_h_slit_gap", "H Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_v_slit_gap", "V Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.box_points = oasysgui.widgetBox(spe_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_points, self, "spe_h_slit_points", "H Slit Points", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_points, self, "spe_v_slit_points", "V Slit Points", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(spe_box, self, "spe_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(spe_box, self, "spe_polarization_component_to_be_extracted", label="Polarization Component",
                     items=PolarizationComponent.tuple(), labelWidth=150,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(spe_box, self, "spe_on_axis_x", "H On-Axis Position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(spe_box, self, "spe_on_axis_y", "V On-Axis Position [m]", labelWidth=260, valueType=float, orientation="horizontal")

        pre_box = oasysgui.widgetBox(self.controlArea, "Precision Parameters", addSpace=False, orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        self.tabs_precision = oasysgui.tabWidget(pre_box)

        tab_prop = oasysgui.createTabPage(self.tabs_precision, "Propagation")

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

                self.run_calculation_flux(srw_source, tickets)

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

       # FLUX
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_min, "Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_max, "Photon Energy Max")
        congruence.checkGreaterOrEqualThan(self.spe_photon_energy_max, self.spe_photon_energy_min, "Photon Energy Max", "Photon Energy Min")
        congruence.checkStrictlyPositiveNumber(self.spe_photon_energy_points, "Photon Energy Points")

        congruence.checkStrictlyPositiveNumber(self.spe_h_slit_gap, "H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.spe_v_slit_gap, "V Slit Gap")
        congruence.checkGreaterOrEqualThan(self.spe_distance, self.get_minimum_propagation_distance(),
                                           "Distance", "Minimum Distance out of the Source: " + str(self.get_minimum_propagation_distance()))

        congruence.checkStrictlyPositiveNumber(self.spe_relative_precision, "Relative Precision")
        congruence.checkStrictlyPositiveNumber(self.spe_number_of_points_for_trajectory_calculation, "Number of points for trajectory calculation")
        congruence.checkPositiveNumber(self.spe_sampling_factor_for_adjusting_nx_ny, "Sampling Factor for adjusting nx/ny")

        self.checkFluxSpecificFields()


    def checkFluxSpecificFields(self):
        if isinstance(self.received_light_source, SRWUndulatorLightSource):
            congruence.checkStrictlyPositiveNumber(self.spe_initial_UR_harmonic, "Flux Initial Harmonic")
            congruence.checkStrictlyPositiveNumber(self.spe_final_UR_harmonic, "Flux Final Harmonic")
            congruence.checkGreaterOrEqualThan(self.spe_final_UR_harmonic, self.spe_initial_UR_harmonic, "Flux Final Harmonic", "Flux Initial Harmonic")
            congruence.checkStrictlyPositiveNumber(self.spe_longitudinal_integration_precision_parameter, "Flux Longitudinal integration precision parameter")
            congruence.checkStrictlyPositiveNumber(self.spe_azimuthal_integration_precision_parameter, "Flux Azimuthal integration precision parameter")

    def run_calculation_flux(self, srw_source, tickets, progress_bar_value=50):
        wf_parameters = WavefrontParameters(photon_energy_min = self.spe_photon_energy_min,
                                            photon_energy_max = self.spe_photon_energy_max,
                                            photon_energy_points=self.spe_photon_energy_points,
                                            h_slit_gap = self.spe_h_slit_gap,
                                            v_slit_gap = self.spe_v_slit_gap,
                                            h_slit_points = self.spe_h_slit_points,
                                            v_slit_points = self.spe_v_slit_points,
                                            distance = self.spe_distance,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.spe_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                        relative_precision=self.spe_relative_precision,
                                                                                                        start_integration_longitudinal_position=self.spe_start_integration_longitudinal_position,
                                                                                                        end_integration_longitudinal_position=self.spe_end_integration_longitudinal_position,
                                                                                                        number_of_points_for_trajectory_calculation=self.spe_number_of_points_for_trajectory_calculation,
                                                                                                        use_terminating_terms=self.spe_use_terminating_terms,
                                                                                                        sampling_factor_for_adjusting_nx_ny=self.spe_sampling_factor_for_adjusting_nx_ny))


        srw_wavefront = srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

        if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            e, i = srw_wavefront.get_flux(multi_electron=True, polarization_component_to_be_extracted=self.spe_polarization_component_to_be_extracted)
        elif isinstance(self.received_light_source, SRWUndulatorLightSource):
            e, i = srw_source.get_undulator_flux(source_wavefront_parameters=wf_parameters,
                                                 flux_precision_parameters=FluxPrecisionParameters(initial_UR_harmonic=self.spe_initial_UR_harmonic,
                                                                                                   final_UR_harmonic=self.spe_final_UR_harmonic,
                                                                                                   longitudinal_integration_precision_parameter=self.spe_longitudinal_integration_precision_parameter,
                                                                                                   azimuthal_integration_precision_parameter=self.spe_azimuthal_integration_precision_parameter))

        tickets.append(SRWPlot.get_ticket_1D(e, i))

        wf_parameters = WavefrontParameters(photon_energy_min = self.spe_photon_energy_min,
                                            photon_energy_max = self.spe_photon_energy_max,
                                            photon_energy_points=self.spe_photon_energy_points,
                                            h_slit_gap = 0.0,
                                            v_slit_gap = 0.0,
                                            h_slit_points = 1,
                                            v_slit_points = 1,
                                            h_position=self.spe_on_axis_x,
                                            v_position=self.spe_on_axis_y,
                                            distance = self.spe_distance,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.spe_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                        relative_precision=self.spe_relative_precision,
                                                                                                        start_integration_longitudinal_position=self.spe_start_integration_longitudinal_position,
                                                                                                        end_integration_longitudinal_position=self.spe_end_integration_longitudinal_position,
                                                                                                        number_of_points_for_trajectory_calculation=self.spe_number_of_points_for_trajectory_calculation,
                                                                                                        use_terminating_terms=self.spe_use_terminating_terms,
                                                                                                        sampling_factor_for_adjusting_nx_ny=self.spe_sampling_factor_for_adjusting_nx_ny))

        srw_wavefront = srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

        e, i = srw_wavefront.get_flux(multi_electron=False, polarization_component_to_be_extracted=self.spe_polarization_component_to_be_extracted)

        tickets.append(SRWPlot.get_ticket_1D(e, i))

        self.progressBarSet(progress_bar_value)


    def getVariablesToPlot(self):
        return [[1], [1]]

    def getTitles(self, with_um=False):
        if with_um: return ["Flux Through Finite Aperture", "On Axis Spectrum from 0-Emittance Beam"]
        else: return ["Spectral Flux Density (ME) vs E", "Spectral Spatial Flux Density (SE) vs E"]

    def getXTitles(self):
        return ["E [eV]", "E [eV]"]

    def getYTitles(self):
        if not self.received_light_source  is None and isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return ["Spectral Flux Density [ph/s/.1%bw/mm\u00b2]", "Spectral Spatial Flux Density [ph/s/.1%bw/mm\u00b2]"]
        else:
            return ["Spectral Flux Density [ph/s/.1%bw]", "Spectral Spatial Flux Density [ph/s/.1%bw/mm\u00b2]"]

    def getXUM(self):
        return ["E [eV]", "E [eV]"]

    def getYUM(self):
        if not self.received_light_source  is None and isinstance(self.received_light_source, SRWBendingMagnetLightSource):
            return ["Spectral Flux Density [ph/s/.1%bw/mm\u00b2]", "Spectral Spatial Flux Density [ph/s/.1%bw/mm\u00b2]"]
        else:
            return ["Spectral Flux Density [ph/s/.1%bw]", "Spectral Spatial Flux Density [ph/s/.1%bw/mm\u00b2]"]

    def receive_srw_data(self, data):
        if not data is None:
            try:
                if isinstance(data, SRWData):
                    self.received_light_source = data.get_srw_beamline().get_light_source()
                    received_wavefront = data.get_srw_wavefront()

                    if not received_wavefront is None:
                        if self.spe_photon_energy_min == 0.0 and self.spe_photon_energy_max == 0.0:
                            self.spe_photon_energy_min = received_wavefront.mesh.eStart
                            self.spe_photon_energy_max = received_wavefront.mesh.eFin
                            self.spe_photon_energy_points=received_wavefront.mesh.ne
                        self.spe_h_slit_gap = received_wavefront.mesh.xFin - received_wavefront.mesh.xStart
                        self.spe_v_slit_gap = received_wavefront.mesh.yFin - received_wavefront.mesh.yStart
                        self.spe_distance = received_wavefront.mesh.zStart

                    n_tab = len(self.tabs_precision)

                    if isinstance(self.received_light_source, SRWBendingMagnetLightSource):
                        self.spe_h_slit_points = received_wavefront.mesh.nx
                        self.spe_v_slit_points = received_wavefront.mesh.ny
                        self.box_points.setVisible(True)

                        if n_tab > 1: self.tabs_precision.removeTab(n_tab-1)
                    elif isinstance(self.received_light_source, SRWUndulatorLightSource):
                        self.spe_h_slit_points = 1
                        self.spe_v_slit_points = 1
                        self.box_points.setVisible(False)

                        if n_tab == 1:
                            tab_flu = oasysgui.createTabPage(self.tabs_precision, "Flux")

                            oasysgui.lineEdit(tab_flu, self, "spe_initial_UR_harmonic", "Initial Harmonic", labelWidth=260, valueType=int, orientation="horizontal")
                            oasysgui.lineEdit(tab_flu, self, "spe_final_UR_harmonic", "Final Harmonic", labelWidth=260, valueType=int, orientation="horizontal")
                            oasysgui.lineEdit(tab_flu, self, "spe_longitudinal_integration_precision_parameter", "Longitudinal integration precision param.", labelWidth=260, valueType=float, orientation="horizontal")
                            oasysgui.lineEdit(tab_flu, self, "spe_azimuthal_integration_precision_parameter", "Azimuthal integration precision param.", labelWidth=260, valueType=int, orientation="horizontal")
                    else:
                        raise ValueError("This source is not supported")
                else:
                    raise ValueError("SRW data not correct")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)


from PyQt5.QtWidgets import QApplication

if __name__=="__main__":
    a = QApplication(sys.argv)
    ow = OWSRWSpectrum()
    ow.show()
    a.exec_()
    ow.saveSettings()
