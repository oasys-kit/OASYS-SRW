import sys

from oasys.widgets import widget

from orangewidget import  gui
from oasys.widgets import gui as oasysgui

from PyQt5 import QtGui

from orangecontrib.srw.util.srw_objects import SRWTriggerOut

class Pin(widget.OWWidget):

    name = "Pin"
    description = "Tools: Pin"
    icon = "icons/pin.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", SRWTriggerOut, "passTrigger")]

    outputs = [{"name":"Trigger",
                "type":SRWTriggerOut,
                "doc":"Trigger",
                "id":"Trigger"}]

    want_main_area = 0
    want_control_area = 1

    def __init__(self):

         self.setFixedWidth(300)
         self.setFixedHeight(100)

         gui.separator(self.controlArea, height=20)
         gui.label(self.controlArea, self, "         SIMPLE PASSAGE POINT", orientation="horizontal")
         gui.rubber(self.controlArea)

    def passTrigger(self, trigger):
            self.send("Trigger", trigger)

if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = Pin()
    ow.show()
    a.exec_()
    ow.saveSettings()