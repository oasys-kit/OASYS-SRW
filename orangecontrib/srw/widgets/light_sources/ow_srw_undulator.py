import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.insertion_device as synedid

from wofrysrw.storage_ring.srw_light_source import SourceWavefrontParameters, SRWLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_source import SRWSource


class SRWUndulator(SRWSource, WidgetDecorator):

    name = "SRW Undulator"
    description = "SRW Source: Undulator"
    icon = "icons/undulator.png"
    priority = 2


    K_horizontal = Setting(0.0)
    K_vertical = Setting(1.5)
    period_length = Setting(0.02)
    number_of_periods = Setting(75)

    inputs = [WidgetDecorator.syned_input_data()]

    want_main_area=1

    def __init__(self):
        super().__init__()

        tab_plots = oasysgui.createTabPage(self.tabs_setting, "Wavefront Setting")

        left_box_2 = oasysgui.widgetBox(self.tab_source, "ID Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_2, self, "K_horizontal", "Horizontal K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "K_vertical", "Vertical K", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "period_length", "Period Length [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "number_of_periods", "Number of Periods", labelWidth=260, valueType=float, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def runSRWSource(self):
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            undulator = SRWUndulatorLightSource(name=self.source_name,
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

            self.progressBarSet(10)

            self.setStatusMessage("Running SRW")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            print(undulator.get_electron_beam().get_electron_beam_geometrical_properties().to_info())

            resonance_energy = undulator.get_resonance_energy()

            print("1st Harmonic Energy", resonance_energy)

            properties = undulator.get_photon_source_properties(harmonic=1)

            print(properties.to_info())

            self.progressBarSet(20)

            tickets = []

            wf_parameters = SourceWavefrontParameters(photon_energy_min = resonance_energy*1,
                                                      photon_energy_max = resonance_energy*1,
                                                      photon_energy_points=1,
                                                      h_slit_gap = 0.01,
                                                      v_slit_gap = 0.01,
                                                      h_slit_points=100,
                                                      v_slit_points=100,
                                                      distance = 10.0)

            e, h, v, i = undulator.get_flux_per_unit_surface(source_wavefront_parameters=wf_parameters)


            tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))


            self.progressBarSet(30)

            wf_parameters = SourceWavefrontParameters(photon_energy_min = resonance_energy*1,
                                                      photon_energy_max = resonance_energy*1,
                                                      photon_energy_points=1,
                                                      h_slit_gap = 0.001,
                                                      v_slit_gap = 0.001,
                                                      h_slit_points=100,
                                                      v_slit_points=100,
                                                      distance = 10.0)

            h, v, p = undulator.get_power_density(source_wavefront_parameters=wf_parameters)

            print(SRWLightSource.get_total_power_from_power_density(h, v, p))

            tickets.append(SRWPlot.get_ticket_2D(h, v, p))

            self.progressBarSet(40)

            wf_parameters = SourceWavefrontParameters(photon_energy_min = 1,
                                                      photon_energy_max = 12001,
                                                      photon_energy_points=12000,
                                                      h_slit_gap = 0.001,
                                                      v_slit_gap = 0.001,
                                                      h_slit_points=1,
                                                      v_slit_points=1,
                                                      distance = 10.0)

            e, i = undulator.get_undulator_flux(source_wavefront_parameters=wf_parameters)

            tickets.append(SRWPlot.get_ticket_1D(e, i))

            self.setStatusMessage("Plotting Results")

            self.progressBarSet(50)

            self.plot_results(tickets)

            self.setStatusMessage("")

            #TODO: COMPLETE!
            self.send("SRWData", SRWData())

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtGui.QMessageBox.Ok)

            raise exception

        self.progressBarFinished()


    def checkFields(self):
        pass


    def receive_syned_data(self, data):
        
        if isinstance(data, synedb.Beamline):
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
        else:
            raise ValueError("Syned data not correct")


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWUndulator()
    ow.show()
    a.exec_()
    ow.saveSettings()
