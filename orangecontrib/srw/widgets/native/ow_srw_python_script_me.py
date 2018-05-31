import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QFileDialog
from orangewidget import gui
from oasys.widgets import gui as oasysgui, widget
from oasys.util.oasys_util import EmittingStream

from orangecontrib.srw.util.python_script import PythonConsole
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.util.srw_util import showConfirmMessage

class SRWPythonScriptME(widget.OWWidget):

    name = "SRW Python Script (ME)"
    description = "SRW Python Script (ME)"
    icon = "icons/python_script_me.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("SRWData", SRWData, "set_input")]

    WIDGET_WIDTH = 950
    WIDGET_HEIGHT = 650

    want_main_area=1
    want_control_area = 0

    input_beam=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height()*0.95, self.WIDGET_HEIGHT))))


        gen_box = gui.widgetBox(self.mainArea, "SRW Native Code", addSpace=False, orientation="horizontal")

        tabs_setting = oasysgui.tabWidget(gen_box)
        tabs_setting.setFixedHeight(self.WIDGET_HEIGHT-60)
        tabs_setting.setFixedWidth(self.WIDGET_WIDTH-60)

        tab_scr = oasysgui.createTabPage(tabs_setting, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.pythonScript = oasysgui.textArea(readOnly=False)
        self.pythonScript.setStyleSheet("background-color: white; font-family: Courier, monospace;")
        self.pythonScript.setMaximumHeight(self.WIDGET_HEIGHT - 300)

        script_box = oasysgui.widgetBox(tab_scr, "", addSpace=False, orientation="vertical", height=self.WIDGET_HEIGHT - 80, width=self.WIDGET_WIDTH - 80)
        script_box.layout().addWidget(self.pythonScript)

        console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.WIDGET_WIDTH - 80)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.WIDGET_HEIGHT - 80)
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
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", ".", "*.py")[0]

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()

                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtWidgets.QMessageBox.Ok)


    def set_input(self, srw_data=SRWData()):
        if not srw_data is None:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.input_srw_data = srw_data

            self.pythonScript.setText("")

            try:
                sampFactNxNyForProp = 1.0 #0.6 #sampling factor for adjusting nx, ny (effective if > 0)
                nMacroElec = 500000 #T otal number of Macro-Electrons (Wavefronts)
                nMacroElecAvgOneProc = 5 # Number of Macro-Electrons (Wavefronts) to average on each node (for MPI calculations)
                nMacroElecSavePer = 20 # Saving periodicity (in terms of Macro-Electrons) for the Resulting Intensity
                srCalcMeth = 1 # SR calculation method (1- undulator)
                srCalcPrec = 0.01 # SR calculation rel. accuracy
                strIntPropME_OutFileName = "output_srw_script_me.dat"
                _char = 4

                parameters = [sampFactNxNyForProp, nMacroElec, nMacroElecAvgOneProc, nMacroElecSavePer, srCalcMeth, srCalcPrec, strIntPropME_OutFileName, _char]

                self.pythonScript.setText(self.input_srw_data.get_srw_beamline().to_python_code([srw_data.get_srw_wavefront(), True, parameters]))
            except Exception as e:
                self.pythonScript.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                raise e
        else:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       "Data not displayable: No good rays or bad content",
                                       QtWidgets.QMessageBox.Ok)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
