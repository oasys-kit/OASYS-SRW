import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from wofrysrw.storage_ring.srw_light_source import SourceWavefrontParameters, SRWLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWSourceData
from orangecontrib.srw.widgets.gui.ow_srw_source import SRWSource


class SRWUndulator(SRWSource):

    name = "SRW Undulator"
    description = "SRW Source: Undulator"
    icon = "icons/undulator.png"
    priority = 2

    source_name = Setting("SRW Undulator")
    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.0007)
    ring_current = Setting(0.4)
    electron_beam_size_h = Setting(0.05545e-3)
    electron_beam_size_v = Setting(2.784e-6)
    emittance = Setting(0.2525e-9)
    coupling_costant = Setting(0.01)
    K_horizontal = Setting(0.0)
    K_vertical = Setting(1.5)
    period_length = Setting(0.02)
    number_of_periods = Setting(75)

    want_main_area=1

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_sou = oasysgui.createTabPage(tabs_setting, "Light Source Setting")
        tab_plots = oasysgui.createTabPage(tabs_setting, "Wavefront Setting")

        oasysgui.lineEdit(tab_sou, self, "source_name", "Light Source Name", labelWidth=260, valueType=str, orientation="horizontal")

        left_box_1 = oasysgui.widgetBox(tab_sou, "Electron Beam/Machine Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_h", "Horizontal Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_v", "Vertical Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "emittance", "Emittance [rad.m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "coupling_costant", "Coupling Costant", labelWidth=260, valueType=float, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(tab_sou, "ID Parameters", addSpace=True, orientation="vertical")

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
                                                emittance=self.emittance,
                                                coupling_costant=self.coupling_costant,
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
                                                      h_slit_gap = 0.001,
                                                      v_slit_gap = 0.001,
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
            self.send("SRWSourceData", SRWSourceData())

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtGui.QMessageBox.Ok)

            raise exception

        self.progressBarFinished()


    def checkFields(self):
        pass



if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWUndulator()
    ow.show()
    a.exec_()
    ow.saveSettings()
