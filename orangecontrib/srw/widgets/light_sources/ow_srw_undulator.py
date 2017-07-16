import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.widget.widget_decorator import WidgetDecorator

import syned.storage_ring.magnetic_structures.insertion_device as synedid

from wofrysrw.storage_ring.srw_light_source import SourceWavefrontParameters, WavefrontPrecisionParameters
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import FluxPrecisionParameters, SRWUndulatorLightSource

from orangecontrib.srw.widgets.gui.ow_srw_source import SRWSource
from orangecontrib.srw.util.srw_util import SRWPlot

class SRWUndulator(SRWSource, WidgetDecorator):

    name = "SRW Undulator"
    description = "SRW Source: Undulator"
    icon = "icons/undulator.png"
    priority = 2


    K_horizontal = Setting(0.0)
    K_vertical = Setting(1.5)
    period_length = Setting(0.02)
    number_of_periods = Setting(75)

    inputs = WidgetDecorator.syned_input_data()

    wf_use_harmonic = Setting(0)
    wf_harmonic_number = Setting(1)

    want_main_area=1

    def __init__(self):
        super().__init__()

        left_box_2 = oasysgui.widgetBox(self.tab_source, "ID Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_2, self, "K_horizontal", "Horizontal K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "K_vertical", "Vertical K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "period_length", "Period Length [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "number_of_periods", "Number of Periods", labelWidth=260, valueType=float, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def build_wf_photon_energy_box(self, box):

        gui.comboBox(box, self, "wf_use_harmonic", label="Energy Setting",
                                            items=["Harmonic", "Other"], labelWidth=260,
                                            callback=self.set_WFUseHarmonic, sendSelectedValue=False, orientation="horizontal")

        self.use_harmonic_box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=30)
        oasysgui.lineEdit(self.use_harmonic_box_1, self, "wf_harmonic_number", "Harmonic #", labelWidth=260, valueType=int, orientation="horizontal")

        self.use_harmonic_box_2 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=30)
        oasysgui.lineEdit(self.use_harmonic_box_2, self, "wf_photon_energy", "Photon Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_WFUseHarmonic()

    def set_WFUseHarmonic(self):
        self.use_harmonic_box_1.setVisible(self.wf_use_harmonic==0)
        self.use_harmonic_box_2.setVisible(self.wf_use_harmonic==1)

    def get_srw_source(self):
        return SRWUndulatorLightSource(name=self.source_name,
                                       electron_energy_in_GeV=self.electron_energy_in_GeV,
                                       electron_energy_spread=self.electron_energy_spread,
                                       ring_current=self.ring_current,
                                       electron_beam_size_h=self.electron_beam_size_h,
                                       electron_beam_size_v=self.electron_beam_size_v,
                                       electron_beam_divergence_h=self.electron_beam_divergence_h,
                                       electron_beam_divergence_v=self.electron_beam_divergence_v,
                                       K_horizontal=self.K_horizontal,
                                       K_vertical=self.K_vertical,
                                       period_length=self.period_length,
                                       number_of_periods=int(self.number_of_periods))

    def print_specific_infos(self, srw_source):
        print("1st Harmonic Energy", srw_source.get_resonance_energy())
        print(srw_source.get_photon_source_properties(harmonic=1).to_info())

    def get_automatic_sr_method(self):
        return 1

    def get_photon_energy_for_wavefront_propagation(self, srw_source):
        return self.wf_photon_energy if self.wf_use_harmonic == 1 else srw_source.get_resonance_energy()*self.wf_harmonic_number

    def get_source_length(self, srw_source):
        return srw_source.get_length()

    def checkSpecificFields(self):
        pass

    def run_calculation_flux(self, srw_source, tickets, progress_bar_value=50):
        wf_parameters = SourceWavefrontParameters(photon_energy_min = self.spe_photon_energy_min,
                                                  photon_energy_max = self.spe_photon_energy_max,
                                                  photon_energy_points=self.spe_photon_energy_points,
                                                  h_slit_gap = self.spe_h_slit_gap,
                                                  v_slit_gap = self.spe_v_slit_gap,
                                                  h_slit_points=1,
                                                  v_slit_points=1,
                                                  distance = self.spe_distance,
                                                  wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.spe_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                              relative_precision=self.spe_relative_precision,
                                                                                                              start_integration_longitudinal_position=self.spe_start_integration_longitudinal_position,
                                                                                                              end_integration_longitudinal_position=self.spe_end_integration_longitudinal_position,
                                                                                                              number_of_points_for_trajectory_calculation=self.spe_number_of_points_for_trajectory_calculation,
                                                                                                              use_terminating_terms=self.spe_use_terminating_terms,
                                                                                                              sampling_factor_for_adjusting_nx_ny=self.spe_sampling_factor_for_adjusting_nx_ny))

        e, i = srw_source.get_flux(source_wavefront_parameters=wf_parameters,
                                   flux_precision_parameters=FluxPrecisionParameters(initial_UR_harmonic=self.spe_initial_UR_harmonic,
                                                                                     final_UR_harmonic=self.spe_final_UR_harmonic,
                                                                                     longitudinal_integration_precision_parameter=self.spe_longitudinal_integration_precision_parameter,
                                                                                     azimuthal_integration_precision_parameter=self.spe_azimuthal_integration_precision_parameter))

        tickets.append(SRWPlot.get_ticket_1D(e, i))

        self.progressBarSet(progress_bar_value)


    def receive_syned_data(self, data):
        if not data is None:
            if not data._light_source is None and isinstance(data._light_source._magnetic_structure, synedid.InsertionDevice):
                light_source = data._light_source

                self.source_name = light_source._name
                self.electron_energy_in_GeV = light_source._electron_beam._energy_in_GeV
                self.electron_energy_spread = light_source._electron_beam._energy_spread
                self.ring_current = light_source._electron_beam._current

                x, xp, y, yp = light_source._electron_beam.get_sigmas_all()

                self.electron_beam_size_h = x
                self.electron_beam_size_v = y
                self.electron_beam_divergence_h = xp
                self.electron_beam_divergence_v = yp

                self.K_horizontal = light_source._magnetic_structure._K_horizontal
                self.K_vertical = light_source._magnetic_structure._K_vertical
                self.period_length = light_source._magnetic_structure._period_length
                self.number_of_periods = light_source._magnetic_structure._number_of_periods
            else:
                raise ValueError("Syned data not correct")


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWUndulator()
    ow.show()
    a.exec_()
    ow.saveSettings()
