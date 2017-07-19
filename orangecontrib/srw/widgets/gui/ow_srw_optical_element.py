import numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.beamline_element import BeamlineElement

from wofry.propagator.propagator import PropagationManager, PropagationElements, PropagationParameters
from wofrysrw.propagator.propagators2D.srw_fresnel import FresnelSRW

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer


def initialize_propagator_2D():
    propagator = PropagationManager.Instance()

    propagator.add_propagator(FresnelSRW())

try:
    initialize_propagator_2D()
except:
    pass

class OWSRWOpticalElement(SRWWavefrontViewer, WidgetDecorator):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    keywords = ["data", "file", "load", "read"]
    category = "SRW Optical Elements"


    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRW Optical Element Data",
                "id":"data"}]

    inputs = [("SRWData", SRWData, "set_input"),
              WidgetDecorator.syned_input_data()[0]]

    oe_name         = Setting("")
    p               = Setting(0.0)
    q               = Setting(0.0)
    angle_radial    = Setting(0.0)
    angle_azimuthal = Setting(0.0)

    shape = Setting(0)
    surface_shape = Setting(0)

    input_wavefront = None
    wavefront_to_plot = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Propagate Wavefront", self)
        self.runaction.triggered.connect(self.propagate_wavefront)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Propagate Wavefront", callback=self.propagate_wavefront)
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

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-10)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "O.E. Setting")
        self.tab_pro = oasysgui.createTabPage(self.tabs_setting, "Propagation Setting")

        oasysgui.lineEdit(self.tab_bas, self, "oe_name", "O.E. Name", labelWidth=260, valueType=str, orientation="horizontal")

        self.coordinates_box = oasysgui.widgetBox(self.tab_bas, "Coordinates", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.coordinates_box, self, "p", "Distance from previous Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.coordinates_box, self, "q", "Distance to next Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.coordinates_box, self, "angle_radial", "Incident Angle (to normal) [deg]", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.coordinates_box, self, "angle_azimuthal", "Rotation along Beam Axis [deg]", labelWidth=280, valueType=float, orientation="horizontal")

        self.draw_specific_box()

    def draw_specific_box(self):
        raise NotImplementedError()

    def check_data(self):
        congruence.checkPositiveNumber(self.p, "Distance from previous Continuation Plane")
        congruence.checkPositiveNumber(self.q, "Distance to next Continuation Plane")
        congruence.checkPositiveAngle(self.angle_radial, "Incident Angle (to normal)")
        congruence.checkPositiveAngle(self.angle_azimuthal, "Rotation along Beam Axis")

    def propagate_wavefront(self):
        try:
            self.progressBarInit()

            if self.input_wavefront is None: raise Exception("No Input Wavefront")

            self.check_data()

            # propagation to o.e.

            propagation_elements = PropagationElements()

            beamline_element = BeamlineElement(optical_element=self.get_optical_element(),
                                               coordinates=ElementCoordinates(p=self.p,
                                                                              q=self.q,
                                                                              angle_radial=numpy.radians(self.angle_radial),
                                                                              angle_azimuthal=numpy.radians(self.angle_azimuthal)))

            propagation_elements.add_beamline_element(beamline_element)

            propagation_parameters = PropagationParameters(wavefront=self.input_wavefront.duplicate(),
                                                           propagation_elements = propagation_elements)

            self.set_additional_parameters(propagation_parameters)

            propagator = PropagationManager.Instance()

            output_wavefront = propagator.do_propagation(propagation_parameters=propagation_parameters,
                                                         handler_name=FresnelSRW.HANDLER_NAME)


            self.wavefront_to_plot = output_wavefront

            self.initializeTabs()
            self.do_plot_results()
            self.progressBarFinished()

            self.send("GenericWavefront2D", output_wavefront)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

            raise e

    def set_additional_parameters(self, propagation_parameters):
        raise NotImplementedError()

    def get_optical_element(self):
        raise NotImplementedError()

    def set_input(self, wavefront):
        if not wavefront is None:
            self.input_wavefront = wavefront

            if self.is_automatic_execution:
                self.propagate_wavefront()

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = ["Wavefront 2D"]
        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def do_plot_results(self, progressBarValue=80):
        if not self.wavefront_to_plot is None:

            self.progressBarSet(progressBarValue)

            titles = ["Wavefront 2D Intensity"]

            self.plot_data2D(data2D=self.wavefront_to_plot.get_intensity(),
                             dataX=self.wavefront_to_plot.get_coordinate_x(),
                             dataY=self.wavefront_to_plot.get_coordinate_y(),
                             progressBarValue=progressBarValue,
                             tabs_canvas_index=0,
                             plot_canvas_index=0,
                             title=titles[0],
                             xtitle="Horizontal Coordinate",
                             ytitle="Vertical Coordinate")


            self.progressBarFinished()

    def receive_syned_data(self, data):
        if not data is None:
            beamline_element = data.get_beamline_element_at(-1)

            if not beamline_element is None:
                self.oe_name = beamline_element._optical_element._name
                self.p = beamline_element._coordinates._p
                self.q = beamline_element._coordinates._q
                self.angle_azimuthal = beamline_element._coordinates._angle_azimuthal
                self.angle_radial = beamline_element._coordinates._angle_radial

                self.receive_specific_syned_data(beamline_element._optical_element)
            else:
                raise Exception("Syned Data not correct: Empty Beamline Element")

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError()

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass




