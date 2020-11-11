import sys

from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from wofrysrw.storage_ring.light_sources.srw_3d_light_source import SRW3DLightSource
from wofrysrw.storage_ring.magnetic_structures.srw_3d_magnetic_structure import SRW3DMagneticStructure

from orangecontrib.srw.widgets.gui.ow_srw_source import OWSRWSource

class OWSRW3DLightSource(OWSRWSource):

    name = "3D Light Source"
    description = "SRW Source: 3D Light Source"
    icon = "icons/3d.png"
    priority = 100

    file_name = Setting("")
    comment_character = Setting("#")
    interpolation_method = Setting(0)

    want_main_area=1

    def __init__(self):
        super().__init__()

        left_box_2 = oasysgui.widgetBox(self.tab_source, "3D file Parameters", addSpace=True, orientation="vertical", height=175)

        file_box =  oasysgui.widgetBox(left_box_2, "", addSpace=False, orientation="horizontal")

        self.le_file_name = oasysgui.lineEdit(file_box, self, "file_name", "3D data file", labelWidth=95, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.select3DDataFile)

        oasysgui.lineEdit(left_box_2, self, "comment_character", "Comment Character", labelWidth=320, valueType=str, orientation="horizontal")

        gui.comboBox(left_box_2, self, "interpolation_method", label="Interpolation Method",
                     items=["bi-linear", "bi-quadratic", "bi-cubic"], labelWidth=260,
                     sendSelectedValue=False, orientation="horizontal")


        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def select3DDataFile(self):
        self.le_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_name, "3D data file"))

    # TODO: these methods maker sense only after reading the file, must be fixed

    def get_automatic_sr_method(self):
        return 2

    def get_default_initial_z(self):
        try:
            return SRW3DMagneticStructure.get_default_initial_z(self.file_name, self.comment_character)
        except:
            return 0.0

    def get_source_length(self):
        try:
            return SRW3DMagneticStructure.get_source_length(self.file_name, self.comment_character)
        except:
            return 0.0

    def get_srw_source(self, electron_beam):
        return SRW3DLightSource(electron_beam=electron_beam,
                                magnet_magnetic_structure=SRW3DMagneticStructure(self.file_name, self.comment_character, self.interpolation_method+1))

    def print_specific_infos(self, srw_source):
        pass

    def checkLightSourceSpecificFields(self):
        congruence.checkFile(self.file_name)
        congruence.checkEmptyString(self.comment_character, "Comment character")

    def receive_specific_syned_data(self, data):
        raise ValueError("Syned data not available for this kind of source")


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRW3DMagneticStructure()
    ow.show()
    a.exec_()
    ow.saveSettings()
