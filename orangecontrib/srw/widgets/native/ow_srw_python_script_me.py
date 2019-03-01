import os, sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QFileDialog

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.srw.util.python_script import PythonConsole
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.util.srw_util import showConfirmMessage
from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource

class SRWPythonScriptME(SRWWidget):

    name = "SRW Python Script (ME)"
    description = "SRW Python Script (ME)"
    icon = "icons/python_script_me.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 2
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("SRWData", SRWData, "set_input")]

    input_srw_data=None

    sampFactNxNyForProp = Setting(1.0) #0.6 #sampling factor for adjusting nx, ny (effective if > 0)
    nMacroElec = Setting(500000) #T otal number of Macro-Electrons (Wavefronts)
    nMacroElecAvgOneProc = Setting(5) # Number of Macro-Electrons (Wavefronts) to average on each node (for MPI calculations)
    nMacroElecSavePer = Setting(20) # Saving periodicity (in terms of Macro-Electrons) for the Resulting Intensity
    srCalcMeth = Setting(1) # SR calculation method (1- undulator)
    srCalcPrec = Setting(0.01) # SR calculation rel. accuracy
    strIntPropME_OutFileName = Setting("output_srw_script_me.dat")
    _char = Setting(0)

    IMAGE_WIDTH = 890
    IMAGE_HEIGHT = 680

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box=show_automatic_box)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Refresh Script", callback=self.refresh_script)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        gen_box = oasysgui.widgetBox(self.controlArea, "SRW Native Code: ME", addSpace=False, orientation="vertical", height=530, width=self.CONTROL_AREA_WIDTH-5)

        oasysgui.lineEdit(gen_box, self, "sampFactNxNyForProp", "Sampling factor for adjusting nx, ny\n(effective if > 0)", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "nMacroElec", "Total Nr. of Electrons (Wavefronts)", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "nMacroElecAvgOneProc", "Nr. of Electrons (Wavefronts) to average on each node\n(for MPI calculations)", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "nMacroElecSavePer", "Saving periodicity (in terms of Electrons)\nfor the Resulting Intensity", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "srCalcMeth", "SR calculation method (1 - undulator)", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "srCalcPrec", "SR calculation relative accuracy", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "strIntPropME_OutFileName", "Output File Name", labelWidth=150, valueType=str, orientation="horizontal")

        gui.comboBox(gen_box, self, "_char", label="Calculation",
                     items=["Total Intensity", "Mutual Intensity"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_scr = oasysgui.createTabPage(tabs_setting, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.pythonScript = oasysgui.textArea(readOnly=False)
        self.pythonScript.setStyleSheet("background-color: white; font-family: Courier, monospace;")
        self.pythonScript.setMaximumHeight(self.IMAGE_HEIGHT - 250)

        script_box = oasysgui.widgetBox(tab_scr, "", addSpace=False, orientation="vertical", height=self.IMAGE_HEIGHT - 10, width=self.IMAGE_WIDTH - 10)
        script_box.layout().addWidget(self.pythonScript)

        console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.IMAGE_WIDTH - 10)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.IMAGE_WIDTH - 45)
        out_box.layout().addWidget(self.shadow_output)

        #############################

        button_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)

    def execute_script(self):
        if showConfirmMessage(message = "Do you confirm launching a ME propagation?",
                              informative_text="This is a very long and resource-consuming process: launching it within the OASYS environment is highly discouraged." + \
                                               "The suggested solution is to save the script into a file and to launch it in a different environment."):
            self._script = str(self.pythonScript.toPlainText())
            self.console.write("\nRunning script:\n")
            self.console.push("exec(_script)")
            self.console.new_prompt(sys.ps1)

    def save_script(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", os.getcwd(), filter='*.py')[0]

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()

                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtWidgets.QMessageBox.Ok)

    def set_input(self, srw_data):
        if not srw_data is None:
            self.input_srw_data = srw_data

            if self.is_automatic_run:
                self.refresh_script()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Input Wavefront is None", QtWidgets.QMessageBox.Ok)

    def refresh_script(self):
        if not self.input_srw_data is None:
            self.pythonScript.setText("")

            try:
                received_light_source = self.input_srw_data.get_srw_beamline().get_light_source()

                if not (isinstance(received_light_source, SRWBendingMagnetLightSource) or isinstance(received_light_source, SRWUndulatorLightSource)):
                    raise ValueError("ME Script is not available with this source")

                _char = 0 if self._char == 0 else 4

                parameters = [self.sampFactNxNyForProp,
                              self.nMacroElec,
                              self.nMacroElecAvgOneProc,
                              self.nMacroElecSavePer,
                              self.srCalcMeth,
                              self.srCalcPrec,
                              self.strIntPropME_OutFileName,
                              _char]

                self.pythonScript.setText(self.input_srw_data.get_srw_beamline().to_python_code([self.input_srw_data.get_srw_wavefront(), True, parameters]))
            except Exception as e:
                self.pythonScript.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                if self.IS_DEVELOP: raise e

