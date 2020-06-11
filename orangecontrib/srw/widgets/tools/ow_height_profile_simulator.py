import os, sys

from PyQt5.QtWidgets import QApplication

import orangecanvas.resources as resources

from oasys.widgets.abstract.error_profile.abstract_height_profile_simulator import OWAbstractHeightErrorProfileSimulator

from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWErrorProfileData
import orangecontrib.srw.util.srw_util as SU

class OWheight_profile_simulator(OWAbstractHeightErrorProfileSimulator):
    name = "Height Profile Simulator"
    id = "height_profile_simulator"
    description = "Calculation of mirror surface height profile"
    icon = "icons/simulator.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 1
    category = ""
    keywords = ["height_profile_simulator"]

    outputs = [{"name": "PreProcessor_Data",
                "type": SRWPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "height_error_profile_usage.png")

    def __init__(self):
        super().__init__()

    def get_usage_path(self):
        return self.usage_path

    def write_error_profile_file(self):
        SU.write_error_profile_file(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.send("PreProcessor_Data", SRWPreProcessorData(error_profile_data=SRWErrorProfileData(error_profile_data_file=self.heigth_profile_file_name,
                                                                                                  error_profile_x_dim=dimension_x,
                                                                                                  error_profile_y_dim=dimension_y)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWheight_profile_simulator()
    w.show()
    app.exec()
    w.saveSettings()
