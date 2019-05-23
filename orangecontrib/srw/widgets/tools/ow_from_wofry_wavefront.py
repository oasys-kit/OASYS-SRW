from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import widget

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.srw.util.srw_objects import SRWData

from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront, WavefrontPropagationParameters

from oasys_srw.srwlib import *

class OWFromWofryWavefront2d(widget.OWWidget):
    name = "From Wofry Wavefront 2D"
    id = "fromWofryWavefront2D"
    description = "from Wofry Wavefront 2D"
    icon = "icons/from_wofry_wavefront_2d.png"
    priority = 20
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("GenericWavefront2D", GenericWavefront2D, "set_input")]

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRWData",
                "id":"SRWData"}]

    CONTROL_AREA_WIDTH = 405

    want_main_area = 0

    Rx = Setting(10.0)
    dRx = Setting(0.001)

    Ry = Setting(10.0)
    dRy = Setting(0.001)

    wavefront = None

    def __init__(self):
        super().__init__()


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setFixedHeight(200)
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        box = oasysgui.widgetBox(self.controlArea, "SRW Wavefront Setting", addSpace=False, orientation="horizontal", height=100)

        box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=60)
        box_2 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=60)

        oasysgui.lineEdit(box_1, self, "Rx", "Rx",labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "dRx", "dRx",labelWidth=50, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(box_2, self, "Ry", "Ry",labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "dRy", "dRy",labelWidth=50, valueType=float, orientation="horizontal")

        gui.button(self.controlArea, self, "Convert", callback=self.convert_wavefront, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wavefront = input_data

            self.convert_wavefront()

    def convert_wavefront(self):
        if not self.wavefront is None:
            try:
                srw_wavefront     = SRWWavefront.fromGenericWavefront(self.wavefront)
                srw_wavefront.Rx  = self.Rx
                srw_wavefront.dRx = self.dRx
                srw_wavefront.Ry  = self.Ry
                srw_wavefront.dRy = self.dRy

                self.send("SRWData", SRWData(srw_wavefront=srw_wavefront))
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception
