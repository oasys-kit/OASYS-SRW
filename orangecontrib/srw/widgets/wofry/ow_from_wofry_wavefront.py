from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.srw.util.srw_objects import SRWData

from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class OWFromWofryWavefront2d(widget.OWWidget):
    name = "From Wofry Wavefront 2D"
    id = "fromWofryWavefront2D"
    description = "from Wofry Wavefront 2D"
    icon = "icons/from_wofry_wavefront_2d.png"
    priority = 1
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("GenericWavefront2D", GenericWavefront2D, "set_input")]

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRWData",
                "id":"SRWData"}]

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        main_box = oasysgui.widgetBox(self.controlArea, "Wofry to SRW Wavefront Converter", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=50)

        gui.label(main_box, self, "--------------- from Wofry GenericWavefront2D to SRW SRWWfr ---------------")

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            try:
                self.send("SRWData", SRWData(srw_wavefront=SRWWavefront.fromGenericWavefront(input_data)))
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                #raise exception