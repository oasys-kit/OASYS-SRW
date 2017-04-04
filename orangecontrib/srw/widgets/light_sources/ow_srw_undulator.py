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
                                                      h_slit_points=51,
                                                      v_slit_points=51,
                                                      distance = 10.0)

            e, h, v, i = undulator.get_flux_per_unit_surface(source_wavefront_parameters=wf_parameters)


            tickets.append(SRWPlot.get_ticket_2D(h, v, i))


            wf_parameters = SourceWavefrontParameters(h_slit_gap = 0.001,
                                                      v_slit_gap = 0.001,
                                                      h_slit_points=51,
                                                      v_slit_points=51,
                                                      distance = 10.0)

            h, v, p = undulator.get_power_density(source_wavefront_parameters=wf_parameters)

            print(SRWLightSource.get_total_power_from_power_density(h, v, p))

            tickets.append(SRWPlot.get_ticket_2D(h, v, p))


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

            self.progressBarSet(80)
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

    def sendNewBeam(self, trigger):
        if trigger and trigger.new_beam == True:
            self.runShadowSource()

    def setupUI(self):
        self.set_OptimizeSource()
        self.calculateMagneticField()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.e_min = congruence.checkPositiveNumber(self.e_min, "Minimum energy")
        self.e_max = congruence.checkPositiveNumber(self.e_max, "Maximum energy")
        congruence.checkLessThan(self.e_min, self.e_max,  "Minimum energy",  "Maximum energy")

        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Sigma x")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Sigma z")
        self.emittance_x = congruence.checkPositiveNumber(self.emittance_x, "Emittance x")
        self.emittance_z = congruence.checkPositiveNumber(self.emittance_z, "Emittance z")
        self.distance_from_waist_x = congruence.checkPositiveNumber(self.distance_from_waist_x, "Distance from waist x")
        self.distance_from_waist_z = congruence.checkPositiveNumber(self.distance_from_waist_z, "Distance from waist z")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.magnetic_radius = congruence.checkPositiveNumber(self.magnetic_radius, "Magnetic radius")
        self.horizontal_half_divergence_from = congruence.checkPositiveNumber(self.horizontal_half_divergence_from,
                                                                             "Horizontal half-divergence from [+]")
        self.horizontal_half_divergence_to = congruence.checkPositiveNumber(self.horizontal_half_divergence_to,
                                                                           "Horizontal half-divergence to [-]")
        self.max_vertical_half_divergence_from = congruence.checkPositiveNumber(self.max_vertical_half_divergence_from,
                                                                               "Max vertical half-divergence from [+]")
        self.max_vertical_half_divergence_to = congruence.checkPositiveNumber(self.max_vertical_half_divergence_to,
                                                                             "Max vertical half-divergence to [-]")
        if self.optimize_source > 0:
            self.max_number_of_rejected_rays = congruence.checkPositiveNumber(self.max_number_of_rejected_rays,
                                                                             "Max number of rejected rays")
            congruence.checkFile(self.optimize_file_name)

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT = self.number_of_rays
        shadow_src.src.ISTAR1 = self.seed
        shadow_src.src.PH1 = self.e_min
        shadow_src.src.PH2 = self.e_max
        shadow_src.src.F_OPD = 1
        shadow_src.src.F_SR_TYPE = self.sample_distribution_combo
        shadow_src.src.F_POL = 1 + self.generate_polarization_combo
        shadow_src.src.SIGMAX = self.sigma_x
        shadow_src.src.SIGMAZ = self.sigma_z
        shadow_src.src.EPSI_X = self.emittance_x
        shadow_src.src.EPSI_Z = self.emittance_z
        shadow_src.src.BENER = self.energy
        shadow_src.src.EPSI_DX = self.distance_from_waist_x
        shadow_src.src.EPSI_DZ = self.distance_from_waist_z
        shadow_src.src.R_MAGNET = self.magnetic_radius
        shadow_src.src.R_ALADDIN = self.magnetic_radius * 100
        shadow_src.src.HDIV1 = self.horizontal_half_divergence_from
        shadow_src.src.HDIV2 = self.horizontal_half_divergence_to
        shadow_src.src.VDIV1 = self.max_vertical_half_divergence_from
        shadow_src.src.VDIV2 = self.max_vertical_half_divergence_to
        shadow_src.src.FDISTR = 4 + 2 * self.calculation_mode_combo
        shadow_src.src.F_BOUND_SOUR = self.optimize_source
        if self.optimize_source > 0:
            shadow_src.src.FILE_BOUND = bytes(congruence.checkFileName(self.optimize_file_name), 'utf-8')
        shadow_src.src.NTOTALPOINT = self.max_number_of_rejected_rays

    def deserialize(self, shadow_file):
        if not shadow_file is None:
            try:
                self.number_of_rays=int(shadow_file.getProperty("NPOINT"))
                self.seed=int(shadow_file.getProperty("ISTAR1"))
                self.e_min=float(shadow_file.getProperty("PH1"))
                self.e_max=float(shadow_file.getProperty("PH2"))
                self.sample_distribution_combo=int(shadow_file.getProperty("F_SR_TYPE"))
                self.generate_polarization_combo=int(shadow_file.getProperty("F_POL"))-1

                self.sigma_x=float(shadow_file.getProperty("SIGMAX"))
                self.sigma_z=float(shadow_file.getProperty("SIGMAZ"))
                self.emittance_x=float(shadow_file.getProperty("EPSI_X"))
                self.emittance_z=float(shadow_file.getProperty("EPSI_Z"))
                self.energy=float(shadow_file.getProperty("BENER"))
                self.distance_from_waist_x=float(shadow_file.getProperty("EPSI_DX"))
                self.distance_from_waist_z=float(shadow_file.getProperty("EPSI_DZ"))

                self.magnetic_radius=float(shadow_file.getProperty("R_MAGNET"))
                self.horizontal_half_divergence_from=float(shadow_file.getProperty("HDIV1"))
                self.horizontal_half_divergence_to=float(shadow_file.getProperty("HDIV2"))
                self.max_vertical_half_divergence_from=float(shadow_file.getProperty("VDIV1"))
                self.max_vertical_half_divergence_to=float(shadow_file.getProperty("VDIV2"))
                self.calculation_mode_combo = (int(shadow_file.getProperty("FDISTR"))-4)/2

                self.optimize_source = int(shadow_file.getProperty("F_BOUND_SOUR"))
                self.optimize_file_name = str(shadow_file.getProperty("FILE_BOUND"))

                if not shadow_file.getProperty("NTOTALPOINT") is None:
                    self.max_number_of_rejected_rays = int(shadow_file.getProperty("NTOTALPOINT"))
                else:
                    self.max_number_of_rejected_rays = 10000000
            except Exception as exception:
                raise BlockingIOError("Bending magnet source failed to load, bad file format: " + exception.args[0])

            self.setupUI()


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = BendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
