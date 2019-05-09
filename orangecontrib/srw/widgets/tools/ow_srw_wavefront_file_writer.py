#TODO: this widget is valid for 1D and 2D wavefronts. Is there a better way to discriminate without duplicating widgets?

import os

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence

from orangecontrib.srw.util.srw_objects import SRWData
from wofrysrw.util.srw_hdf5 import save_wfr_2_hdf5

class OWSRWWavefrontFileWriter(widget.OWWidget):
    name = "SRW Wavefront  File Writer"
    description = "Utility: SRW Wavefront File Writer"
    icon = "icons/file_writer.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 10
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    file_name = Setting("tmp.h5")
    data_path = Setting("wfr")
    is_automatic_run= Setting(1)


    inputs = [("SRWData", SRWData, "set_input"),]

    input_data = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Write HDF5 File", self)
        self.runaction.triggered.connect(self.write_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(300)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "HDF5 File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=200)

        gui.checkBox(left_box_1, self, 'is_automatic_run', 'Automatic Execution')

        gui.separator(left_box_1, height=10)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=50)

        self.le_file_name = oasysgui.lineEdit(figure_box, self, "file_name", "File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_file_name.setFixedWidth(330)


        gui.button(figure_box, self, "...", callback=self.selectFile)

        gui.separator(left_box_1, height=10)




        self.le_data_path = oasysgui.lineEdit(left_box_1, self, "data_path", "Wavefront name (mandatory)",
                                                    labelWidth=200, valueType=str, orientation="horizontal")
        self.le_data_path.setFixedWidth(330)



        button = gui.button(self.controlArea, self, "Write File", callback=self.write_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_name, "Open HDF5 File"))

    def set_input(self, data):
        if not data is None:
            self.input_data = data

            if self.is_automatic_run:
                self.write_file()

    def write_file(self):
        self.setStatusMessage("")

        try:
            if not self.input_data is None:
                congruence.checkDir(self.file_name)

                # note that this is valid for both 1D and 2D wavefronts because both implement
                # the save_h5_file method.

                srw_wavefront = self.input_data.get_srw_wavefront()
                save_wfr_2_hdf5(self.input_data.get_srw_wavefront(),self.file_name,subgroupname=self.data_path,
                                intensity=True,phase=False,overwrite=True)

                path, file_name = os.path.split(self.file_name)

                self.setStatusMessage("File Out: " + file_name)

            else:
                QMessageBox.critical(self, "Error",
                                     "Wavefront Data not present",
                                     QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWSRWWavefrontFileWriter()
    ow.file_name = "tmp.h5"

    ow.show()
    a.exec_()
