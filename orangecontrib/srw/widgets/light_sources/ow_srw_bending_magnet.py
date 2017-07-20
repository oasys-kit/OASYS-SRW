import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from syned.widget.widget_decorator import WidgetDecorator

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters
from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.widgets.gui.ow_srw_source import SRWSource

from syned.storage_ring.magnetic_structures.bending_magnet import BendingMagnet

class SRWBendingMagnet(SRWSource, WidgetDecorator):

    name = "SRW Bending Magnet"
    description = "SRW Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 1

    inputs = WidgetDecorator.syned_input_data()

    magnetic_radius = Setting(5.56)
    magnetic_field = Setting(1.2)
    length = Setting(0.8)

    want_main_area=1

    def __init__(self):
        super().__init__()

        left_box_2 = oasysgui.widgetBox(self.tab_source, "ID Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_2, self, "magnetic_radius", "Magnetic Radius [m]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculateMagneticField)
        oasysgui.lineEdit(left_box_2, self, "magnetic_field", "Magnetic Field [T]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculateMagneticRadius)
        oasysgui.lineEdit(left_box_2, self, "length", "Length [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def get_srw_source(self):
        return SRWBendingMagnetLightSource(name=self.source_name,
                                           electron_energy_in_GeV=self.electron_energy_in_GeV,
                                           electron_energy_spread=self.electron_energy_spread,
                                           ring_current=self.ring_current,
                                           electron_beam_size_h=self.electron_beam_size_h,
                                           electron_beam_size_v=self.electron_beam_size_v,
                                           electron_beam_divergence_h=self.electron_beam_divergence_h,
                                           electron_beam_divergence_v=self.electron_beam_divergence_v,
                                           magnetic_radius=self.magnetic_radius,
                                           magnetic_field=self.magnetic_field,
                                           length=self.length)

    def print_specific_infos(self, srw_source):
        pass

    def get_automatic_sr_method(self):
        return 2

    def get_source_length(self):
        return self.length

    def run_calculation_flux(self, srw_source, tickets, progress_bar_value=50):
        wf_parameters = WavefrontParameters(photon_energy_min = self.spe_photon_energy_min,
                                                  photon_energy_max = self.spe_photon_energy_max,
                                                  photon_energy_points=self.spe_photon_energy_points,
                                                  h_slit_gap = self.spe_h_slit_gap,
                                                  v_slit_gap = self.spe_v_slit_gap,
                                                  h_slit_points=10,
                                                  v_slit_points=10,
                                                  distance = self.spe_distance,
                                                  wavefront_precision_parameters=WavefrontPrecisionParameters(sr_method=0 if self.spe_sr_method == 0 else self.get_automatic_sr_method(),
                                                                                                              relative_precision=self.spe_relative_precision,
                                                                                                              start_integration_longitudinal_position=self.spe_start_integration_longitudinal_position,
                                                                                                              end_integration_longitudinal_position=self.spe_end_integration_longitudinal_position,
                                                                                                              number_of_points_for_trajectory_calculation=self.spe_number_of_points_for_trajectory_calculation,
                                                                                                              use_terminating_terms=self.spe_use_terminating_terms,
                                                                                                              sampling_factor_for_adjusting_nx_ny=self.spe_sampling_factor_for_adjusting_nx_ny))
        srw_wavefront = srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

        e, i = srw_source.srw_wavefront()

        tickets.append(SRWPlot.get_ticket_1D(e, i))

        self.progressBarSet(progress_bar_value)

    def checkLightSourceSpecificFields(self):
        congruence.checkStrictlyPositiveNumber(self.magnetic_radius, "Magnetic Radius")
        congruence.checkStrictlyPositiveNumber(self.magnetic_field, "Magnetic Field")
        congruence.checkStrictlyPositiveNumber(self.length, "Length")

    def receive_syned_data(self, data):
        if not data is None:
            if not data._light_source is None and isinstance(data._light_source._magnetic_structure, BendingMagnet):
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

                self.magnetic_field = light_source._magnetic_structure._magnetic_field
                self.magnetic_radius = light_source._magnetic_structure._radius
                self.length = light_source._magnetic_structure._length
            else:
                raise ValueError("Syned data not correct")

    def calculateMagneticField(self):
        if self.magnetic_radius > 0:
           self.magnetic_field=BendingMagnet.calculate_magnetic_field(self.magnetic_radius, self.electron_energy_in_GeV)

    def calculateMagneticRadius(self):
        if self.magnetic_field > 0:
           self.magnetic_radius=BendingMagnet.calculate_magnetic_radius(self.magnetic_field, self.electron_energy_in_GeV)


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWBendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
