__author__ = 'labx'

import os, sys

from PyQt4.QtGui import QPalette, QColor, QFont, QMessageBox
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

class SRWSource(SRWWavefrontViewer):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRW Source Data",
                "id":"data"}]

    want_main_area=1

    source_name = Setting("SRW Source")

    electron_energy_in_GeV = Setting(2.0)
    electron_energy_spread = Setting(0.0007)
    ring_current = Setting(0.4)
    electron_beam_size_h = Setting(0.05545e-3)
    electron_beam_size_v = Setting(2.784e-6)
    electron_beam_divergence_h = Setting(0.2525e-9)
    electron_beam_divergence_v = Setting(0.01)

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run SRW", self)
        self.runaction.triggered.connect(self.runSRWSource)
        self.addAction(self.runaction)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run SRW Source", callback=self.runSRWSource)
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

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_source = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        oasysgui.lineEdit(self.tab_source, self, "source_name", "Light Source Name", labelWidth=260, valueType=str, orientation="horizontal")

        left_box_1 = oasysgui.widgetBox(self.tab_source, "Electron Beam/Machine Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "electron_energy_in_GeV", "Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_energy_spread", "Energy Spread", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "ring_current", "Ring Current [A]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_h", "Horizontal Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_size_v", "Vertical Beam Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_divergence_h", "Horizontal Beam Divergence [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "electron_beam_divergence_v", "Vertical Beam Divergence", labelWidth=260, valueType=float, orientation="horizontal")
