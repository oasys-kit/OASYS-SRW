import sys, os

from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt5.QtGui import QPixmap
import orangecanvas.resources as resources
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.storage_ring.magnetic_structures.undulator import Undulator

from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource
from wofrysrw.storage_ring.magnetic_structures.srw_undulator import SRWUndulator

from orangecontrib.srw.widgets.gui.ow_srw_source import OWSRWSource

class OWSRWUndulator(OWSRWSource):

    name = "Undulator"
    description = "SRW Source: Undulator"
    icon = "icons/undulator.png"
    priority = 2

    magnetic_field_from = Setting(0)

    B_horizontal = Setting(0.0)
    B_vertical = Setting(1.5)

    K_horizontal = Setting(0.0)
    K_vertical = Setting(1.5)

    period_length = Setting(0.02)
    number_of_periods = Setting(75)
    horizontal_central_position = Setting(0.0)
    vertical_central_position = Setting(0.0)
    longitudinal_central_position = Setting(0.0)

    wf_use_harmonic = Setting(0)
    wf_harmonic_number = Setting(1)

    want_main_area=1

    initial_phase_vertical = Setting(0.0)
    initial_phase_horizontal = Setting(0.0)

    symmetry_vs_longitudinal_position_vertical = Setting(1)
    symmetry_vs_longitudinal_position_horizontal = Setting(0)

    def __init__(self):
        super().__init__()

        tabs = oasysgui.tabWidget(self.tab_source, height=175)

        left_box_2 = oasysgui.createTabPage(tabs, "ID Parameters")
        left_box_3 = oasysgui.createTabPage(tabs, "ID Magnetic Field")

        oasysgui.lineEdit(left_box_2, self, "period_length", "Period Length [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "number_of_periods", "Number of Periods", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "horizontal_central_position", "Horizontal Central Position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "vertical_central_position", "Vertical Central Position [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "longitudinal_central_position", "Longitudinal Central Position [m]", labelWidth=260, valueType=float, orientation="horizontal")


        gui.comboBox(left_box_3, self, "magnetic_field_from", label="Magnetic Field", labelWidth=350,
                     items=["From K", "From B"],
                     callback=self.set_MagneticField,
                     sendSelectedValue=False, orientation="horizontal")

        container = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="horizontal")

        horizontal_box = oasysgui.widgetBox(container, "", addSpace=False, orientation="vertical", width=215)
        vertical_box = oasysgui.widgetBox(container,  "", addSpace=False, orientation="vertical", width=155)

        gui.label(horizontal_box, self, "                     Horizontal")
        gui.label(vertical_box, self, "  Vertical")

        self.magnetic_field_box_1_h = oasysgui.widgetBox(horizontal_box, "", addSpace=False, orientation="vertical")
        self.magnetic_field_box_2_h = oasysgui.widgetBox(horizontal_box, "", addSpace=False, orientation="vertical")
        self.magnetic_field_box_1_v = oasysgui.widgetBox(vertical_box, "", addSpace=False, orientation="vertical")
        self.magnetic_field_box_2_v = oasysgui.widgetBox(vertical_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.magnetic_field_box_1_h, self, "K_horizontal", "K", labelWidth=70, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.magnetic_field_box_1_v, self, "K_vertical", " ", labelWidth=2, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.magnetic_field_box_2_h, self, "B_horizontal", "B [T]", labelWidth=70, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.magnetic_field_box_2_v, self, "B_vertical", " ", labelWidth=2, valueType=float, orientation="horizontal")

        self.set_MagneticField()

        oasysgui.lineEdit(horizontal_box, self, "initial_phase_horizontal", "\u03c6\u2080 [rad]", labelWidth=70, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(vertical_box, self, "initial_phase_vertical", " ", labelWidth=2, valueType=float, orientation="horizontal")


        gui.comboBox(horizontal_box, self, "symmetry_vs_longitudinal_position_horizontal", label="Symmetry", labelWidth=70,
                     items=["Symmetrical", "Anti-Symmetrical"],
                     sendSelectedValue=False, orientation="horizontal")

        symmetry_v_box =  oasysgui.widgetBox(vertical_box, "", addSpace=False, orientation="horizontal")
        gui.comboBox(symmetry_v_box, self, "symmetry_vs_longitudinal_position_vertical", label=" ", labelWidth=2,
                     items=["Symmetrical", "Anti-Symmetrical"],
                     sendSelectedValue=False, orientation="horizontal")
        gui.button(symmetry_v_box, self, "?", callback=self.open_help, width=12)


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

    class ShowHelpDialog(QDialog):

        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Symmetry vs Longitudinal Position')
            layout = QVBoxLayout(self)
            label = QLabel("")

            file = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.light_sources"), "misc", "symmetry.png")

            label.setPixmap(QPixmap(file))

            bbox = QDialogButtonBox(QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(label)
            layout.addWidget(bbox)


    def open_help(self):
        dialog = OWSRWUndulator.ShowHelpDialog(parent=self)
        dialog.show()

    def set_MagneticField(self):
        self.magnetic_field_box_1_h.setVisible(self.magnetic_field_from==0)
        self.magnetic_field_box_2_h.setVisible(self.magnetic_field_from==1)
        self.magnetic_field_box_1_v.setVisible(self.magnetic_field_from==0)
        self.magnetic_field_box_2_v.setVisible(self.magnetic_field_from==1)

    def set_WFUseHarmonic(self):
        self.use_harmonic_box_1.setVisible(self.wf_use_harmonic==0)
        self.use_harmonic_box_2.setVisible(self.wf_use_harmonic==1)

    def get_default_initial_z(self):
        return -0.5*self.period_length*(self.number_of_periods + 4) # initial Longitudinal Coordinate (set before the ID)

    def get_srw_source(self, electron_beam):
        symmetry_vs_longitudinal_position_horizontal = 1 if self.symmetry_vs_longitudinal_position_horizontal == 0 else -1
        symmetry_vs_longitudinal_position_vertical = 1 if self.symmetry_vs_longitudinal_position_vertical == 0 else -1

        if self.magnetic_field_from == 0:
            undulator_magnetic_structure=SRWUndulator(horizontal_central_position = 0.0,
                                                      vertical_central_position = 0.0,
                                                      longitudinal_central_position=self.longitudinal_central_position,
                                                      K_vertical=self.K_vertical,
                                                      K_horizontal=self.K_horizontal,
                                                      period_length=self.period_length,
                                                      number_of_periods=self.number_of_periods,
                                                      initial_phase_horizontal=self.initial_phase_horizontal,
                                                      initial_phase_vertical=self.initial_phase_vertical,
                                                      symmetry_vs_longitudinal_position_horizontal=symmetry_vs_longitudinal_position_horizontal,
                                                      symmetry_vs_longitudinal_position_vertical=symmetry_vs_longitudinal_position_vertical)
        else:
            undulator_magnetic_structure=SRWUndulator(horizontal_central_position = 0.0,
                                                      vertical_central_position = 0.0,
                                                      longitudinal_central_position=self.longitudinal_central_position,
                                                      period_length=self.period_length,
                                                      number_of_periods=self.number_of_periods,
                                                      initial_phase_horizontal=self.initial_phase_horizontal,
                                                      initial_phase_vertical=self.initial_phase_vertical,
                                                      symmetry_vs_longitudinal_position_horizontal=symmetry_vs_longitudinal_position_horizontal,
                                                      symmetry_vs_longitudinal_position_vertical=symmetry_vs_longitudinal_position_vertical)
            undulator_magnetic_structure.set_K_vertical_from_magnetic_field(self.B_vertical)
            undulator_magnetic_structure.set_K_horizontal_from_magnetic_field(self.B_horizontal)

        return SRWUndulatorLightSource(electron_beam=electron_beam,
                                       undulator_magnetic_structure=undulator_magnetic_structure)

    def print_specific_infos(self, srw_source):
        print("1st Harmonic Energy", srw_source.get_resonance_energy(), "\n")

    def get_automatic_sr_method(self):
        return 1

    def get_photon_energy_for_wavefront_propagation(self, srw_source):
        return self.wf_photon_energy if self.wf_use_harmonic == 1 else srw_source.get_resonance_energy()*self.wf_harmonic_number

    def get_source_length(self):
        return self.period_length*self.number_of_periods

    def checkLightSourceSpecificFields(self):
        if self.magnetic_field_from == 0:
            congruence.checkPositiveNumber(self.K_horizontal, "Horizontal K")
            congruence.checkPositiveNumber(self.K_vertical, "Vertical K")
        else:
            congruence.checkPositiveNumber(self.B_horizontal, "Horizontal B")
            congruence.checkPositiveNumber(self.B_vertical, "Vertical B")

        congruence.checkStrictlyPositiveNumber(self.period_length, "Period Length")
        congruence.checkStrictlyPositiveNumber(self.number_of_periods, "Number of Periods")

    def checkWavefrontPhotonEnergy(self):
        if self.wf_use_harmonic == 0:
            congruence.checkStrictlyPositiveNumber(self.wf_harmonic_number, "Wavefront Propagation Harmonic Number")
        else:
            congruence.checkStrictlyPositiveNumber(self.wf_photon_energy, "Wavefront Propagation Photon Energy")

    def receive_specific_syned_data(self, data):
        if isinstance(data._light_source._magnetic_structure, Undulator):
            light_source = data._light_source

            self.K_horizontal = light_source._magnetic_structure._K_horizontal
            self.K_vertical = light_source._magnetic_structure._K_vertical
            self.magnetic_field_from = 0
            self.period_length = light_source._magnetic_structure._period_length
            self.number_of_periods = light_source._magnetic_structure._number_of_periods

            self.set_MagneticField()
        else:
            raise ValueError("Syned data not correct")


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = OWSRWUndulator()
    ow.show()
    a.exec_()
    ow.saveSettings()
