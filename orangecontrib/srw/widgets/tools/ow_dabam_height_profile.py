import os, sys
from PyQt5.QtWidgets import QApplication

import orangecanvas.resources as resources

from oasys.widgets.error_profile.ow_abstract_dabam_height_profile import OWAbstractDabamHeightProfile

from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWErrorProfileData
import orangecontrib.srw.util.srw_util as SU

class OWdabam_height_profile(OWAbstractDabamHeightProfile):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 2
    category = ""
    keywords = ["dabam_height_profile"]

    outputs = [OWAbstractDabamHeightProfile.get_dabam_output(),
               {"name": "PreProcessor_Data",
                "type": SRWPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "dabam_height_profile_usage.png")

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
    w = OWdabam_height_profile()
    w.si_to_user_units = 100
    w.show()
    app.exec()
    w.saveSettings()
