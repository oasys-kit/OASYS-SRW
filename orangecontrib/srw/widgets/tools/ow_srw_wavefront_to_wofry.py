from orangewidget import gui

from oasys.widgets import widget

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.srw.util.srw_objects import SRWData

class OWToWofryWavefront2d(widget.OWWidget):
    name = "To Wofry Wavefront 2D"
    id = "toWofryWavefront2D"
    description = "To Wofry Wavefront 2D"
    icon = "icons/to_wofry_wavefront_2d.png"
    priority = 21
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("SRWData", SRWData, "set_input")]

    outputs = [{"name":"GenericWavefront2D",
                "type":GenericWavefront2D,
                "doc":"GenericWavefront2D",
                "id":"GenericWavefront2D"}]

    CONTROL_AREA_WIDTH = 605

    srw_data = None

    want_main_area = 0

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setFixedHeight(self.geometry().height())
        self.setFixedWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        label = gui.label(self.controlArea, self, "From SRW Wavefront To Wofry Wavefront")
        font = QFont(label.font())
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(14)
        label.setFont(font)
        palette = QPalette(label.palette()) # make a copy of the palette
        palette.setColor(QPalette.Foreground, QColor('Dark Blue'))
        label.setPalette(palette) # assign new palette

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_wavefront, height=45)


    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.srw_data = input_data

            self.convert_wavefront()

    def convert_wavefront(self):
        try:
            if not self.srw_data is None:
                self.send("GenericWavefront2D", self.srw_data.get_srw_wavefront().toGenericWavefront())
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception
