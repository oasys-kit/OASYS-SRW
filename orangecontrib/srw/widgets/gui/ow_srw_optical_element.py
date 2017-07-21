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
from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontPropagationParameters

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

from orangecontrib.srw.util.srw_util import SRWPlot

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

    drift_auto_resize_before_propagation                         = Setting(0)
    drift_auto_resize_after_propagation                          = Setting(0)
    drift_relative_precision_for_propagation_with_autoresizing   = Setting(1.0)
    drift_allow_semianalytical_treatment_of_quadratic_phase_term = Setting(0)
    drift_do_any_resizing_on_fourier_side_using_fft              = Setting(0)
    drift_horizontal_range_modification_factor_at_resizing       = Setting(1.0)
    drift_horizontal_resolution_modification_factor_at_resizing  = Setting(1.0)
    drift_vertical_range_modification_factor_at_resizing         = Setting(1.0)
    drift_vertical_resolution_modification_factor_at_resizing    = Setting(1.0)
    drift_type_of_wavefront_shift_before_resizing                = Setting(0)
    drift_new_horizontal_wavefront_center_position_after_shift   = Setting(0)
    drift_new_vertical_wavefront_center_position_after_shift     = Setting(0)

    oe_auto_resize_before_propagation                         = Setting(0)
    oe_auto_resize_after_propagation                          = Setting(0)
    oe_relative_precision_for_propagation_with_autoresizing   = Setting(1.0)
    oe_allow_semianalytical_treatment_of_quadratic_phase_term = Setting(0)
    oe_do_any_resizing_on_fourier_side_using_fft              = Setting(0)
    oe_horizontal_range_modification_factor_at_resizing       = Setting(2.0)
    oe_horizontal_resolution_modification_factor_at_resizing  = Setting(5.0)
    oe_vertical_range_modification_factor_at_resizing         = Setting(6.0)
    oe_vertical_resolution_modification_factor_at_resizing    = Setting(3.0)
    oe_type_of_wavefront_shift_before_resizing                = Setting(0)
    oe_new_horizontal_wavefront_center_position_after_shift   = Setting(0)
    oe_new_vertical_wavefront_center_position_after_shift     = Setting(0)

    input_srw_data = None
    wavefront_to_plot = None

    has_orientation_angles=True

    TABS_AREA_HEIGHT = 555
    CONTROL_AREA_WIDTH = 405

    def __init__(self, has_orientation_angles=True):
        super().__init__()

        self.has_orientation_angles=has_orientation_angles

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

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "O.E. Setting")
        self.tab_pro = oasysgui.createTabPage(self.tabs_setting, "Wavefront Propagation Setting")

        oasysgui.lineEdit(self.tab_bas, self, "oe_name", "O.E. Name", labelWidth=260, valueType=str, orientation="horizontal")

        self.coordinates_box = oasysgui.widgetBox(self.tab_bas, "Coordinates", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.coordinates_box, self, "p", "Distance from previous Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.coordinates_box, self, "q", "Distance to next Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal")

        if self.has_orientation_angles:
            oasysgui.lineEdit(self.coordinates_box, self, "angle_radial", "Incident Angle (to normal) [deg]", labelWidth=280, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.coordinates_box, self, "angle_azimuthal", "Rotation along Beam Axis [deg]", labelWidth=280, valueType=float, orientation="horizontal")

        self.draw_specific_box()

        self.tabs_prop_setting = oasysgui.tabWidget(self.tab_pro)
        self.tabs_prop_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-10)

        self.tab_oe = oasysgui.createTabPage(self.tabs_prop_setting, "Optical Element")
        self.tab_drift = oasysgui.createTabPage(self.tabs_prop_setting, "Drift Space")

        # DRIFT SPACE
        
        gui.comboBox(self.tab_drift, self, "drift_auto_resize_before_propagation", label="Auto Resize Before Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_drift, self, "drift_auto_resize_after_propagation", label="Auto Resize After Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift, self, "drift_relative_precision_for_propagation_with_autoresizing", "Relative precision for propagation with\nautoresizing (1.0 is nominal)", labelWidth=280, valueType=float, orientation="horizontal")

        gui.comboBox(self.tab_drift, self, "drift_allow_semianalytical_treatment_of_quadratic_phase_term", label="Allow semianalytical treatment of quadratic\nphase term",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_drift, self, "drift_do_any_resizing_on_fourier_side_using_fft", label="Do any resizing on fourier side using fft",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift, self, "drift_horizontal_range_modification_factor_at_resizing", "Horizontal range modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_horizontal_resolution_modification_factor_at_resizing", "Horizontal resolution modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_vertical_range_modification_factor_at_resizing", "Vertical range modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_vertical_resolution_modification_factor_at_resizing", "Vertical resolution modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        
        # not yet used by SRW
        #oasysgui.lineEdit(self.tab_drift, self, "drift_type_of_wavefront_shift_before_resizing", "Type of wavefront shift before resizing", labelWidth=280, valueType=int, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift, self, "drift_new_horizontal_wavefront_center_position_after_shift", "New horizontal wavefront center position [m]", labelWidth=280, valueType=float, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift, self, "drift_new_vertical_wavefront_center_position_after_shift", "New vertical wavefront center position [m]", labelWidth=280, valueType=float, orientation="horizontal")


        # DRIFT SPACE
        
        gui.comboBox(self.tab_oe, self, "oe_auto_resize_before_propagation", label="Auto Resize Before Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_oe, self, "oe_auto_resize_after_propagation", label="Auto Resize After Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_oe, self, "oe_relative_precision_for_propagation_with_autoresizing", "Relative precision for propagation with\nautoresizing (1.0 is nominal)", labelWidth=280, valueType=float, orientation="horizontal")

        gui.comboBox(self.tab_oe, self, "oe_allow_semianalytical_treatment_of_quadratic_phase_term", label="Allow semianalytical treatment of quadratic\nphase term",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_oe, self, "oe_do_any_resizing_on_fourier_side_using_fft", label="Do any resizing on fourier side using fft",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_oe, self, "oe_horizontal_range_modification_factor_at_resizing", "Horizontal range modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_oe, self, "oe_horizontal_resolution_modification_factor_at_resizing", "Horizontal resolution modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_oe, self, "oe_vertical_range_modification_factor_at_resizing", "Vertical range modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_oe, self, "oe_vertical_resolution_modification_factor_at_resizing", "Vertical resolution modification factor\nat resizing (1.0 means no modification)", labelWidth=280, valueType=float, orientation="horizontal")
        
        # not yet used by SRW
        #oasysgui.lineEdit(self.tab_oe, self, "oe_type_of_wavefront_shift_before_resizing", "Type of wavefront shift before resizing", labelWidth=280, valueType=int, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_oe, self, "oe_new_horizontal_wavefront_center_position_after_shift", "New horizontal wavefront center position [m]", labelWidth=280, valueType=float, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_oe, self, "oe_new_vertical_wavefront_center_position_after_shift", "New vertical wavefront center position [m]", labelWidth=280, valueType=float, orientation="horizontal")


    def draw_specific_box(self):
        raise NotImplementedError()

    def check_data(self):
        congruence.checkPositiveNumber(self.p, "Distance from previous Continuation Plane")
        congruence.checkPositiveNumber(self.q, "Distance to next Continuation Plane")
        if self.has_orientation_angles:
            congruence.checkPositiveAngle(self.angle_radial, "Incident Angle (to normal)")
            congruence.checkPositiveAngle(self.angle_azimuthal, "Rotation along Beam Axis")
        else:
            self.angle_radial = 0.0
            self.angle_azimuthal = 0.0

    def propagate_wavefront(self):
        try:
            self.progressBarInit()

            if self.input_srw_data is None: raise Exception("No Input Data")

            self.check_data()

            # propagation to o.e.

            propagation_elements = PropagationElements()

            beamline_element = BeamlineElement(optical_element=self.get_optical_element(),
                                               coordinates=ElementCoordinates(p=self.p,
                                                                              q=self.q,
                                                                              angle_radial=numpy.radians(self.angle_radial),
                                                                              angle_azimuthal=numpy.radians(self.angle_azimuthal)))

            propagation_elements.add_beamline_element(beamline_element)

            propagation_parameters = PropagationParameters(wavefront=self.input_srw_data._srw_wavefront.duplicate(),
                                                           propagation_elements = propagation_elements)

            self.set_additional_parameters(propagation_parameters)

            propagator = PropagationManager.Instance()

            output_wavefront = propagator.do_propagation(propagation_parameters=propagation_parameters,
                                                         handler_name=FresnelSRW.HANDLER_NAME)

            self.wavefront_to_plot = output_wavefront

            self.initializeTabs()

            tickets = []

            self.run_calculations(tickets=tickets, progress_bar_value=50)

            self.plot_results(tickets, 80)

            self.progressBarFinished()

            output_beamline = self.input_srw_data._srw_beamline.duplicate()
            output_beamline.append_beamline_element(beamline_element)

            self.send("SRWData", SRWData(srw_beamline=output_beamline,
                                         srw_wavefront=output_wavefront))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

            raise e

    def set_additional_parameters(self, propagation_parameters):
        propagation_parameters.set_additional_parameters("srw_drift_wavefront_propagation_parameters",
                                                         WavefrontPropagationParameters(
                                                             auto_resize_before_propagation                         = self.drift_auto_resize_before_propagation,
                                                             auto_resize_after_propagation                          = self.drift_auto_resize_after_propagation,
                                                             relative_precision_for_propagation_with_autoresizing   = self.drift_relative_precision_for_propagation_with_autoresizing,
                                                             allow_semianalytical_treatment_of_quadratic_phase_term = self.drift_allow_semianalytical_treatment_of_quadratic_phase_term,
                                                             do_any_resizing_on_fourier_side_using_fft              = self.drift_do_any_resizing_on_fourier_side_using_fft,
                                                             horizontal_range_modification_factor_at_resizing       = self.drift_horizontal_range_modification_factor_at_resizing,
                                                             horizontal_resolution_modification_factor_at_resizing  = self.drift_horizontal_resolution_modification_factor_at_resizing ,
                                                             vertical_range_modification_factor_at_resizing         = self.drift_vertical_range_modification_factor_at_resizing,
                                                             vertical_resolution_modification_factor_at_resizing    = self.drift_vertical_resolution_modification_factor_at_resizing ,
                                                             type_of_wavefront_shift_before_resizing                = self.drift_type_of_wavefront_shift_before_resizing,
                                                             new_horizontal_wavefront_center_position_after_shift   = self.drift_new_horizontal_wavefront_center_position_after_shift,
                                                             new_vertical_wavefront_center_position_after_shift     = self.drift_new_vertical_wavefront_center_position_after_shift
                                                         ))

        propagation_parameters.set_additional_parameters("srw_oe_wavefront_propagation_parameters",
                                                         WavefrontPropagationParameters(
                                                             auto_resize_before_propagation                         = self.oe_auto_resize_before_propagation,
                                                             auto_resize_after_propagation                          = self.oe_auto_resize_after_propagation,
                                                             relative_precision_for_propagation_with_autoresizing   = self.oe_relative_precision_for_propagation_with_autoresizing,
                                                             allow_semianalytical_treatment_of_quadratic_phase_term = self.oe_allow_semianalytical_treatment_of_quadratic_phase_term,
                                                             do_any_resizing_on_fourier_side_using_fft              = self.oe_do_any_resizing_on_fourier_side_using_fft,
                                                             horizontal_range_modification_factor_at_resizing       = self.oe_horizontal_range_modification_factor_at_resizing,
                                                             horizontal_resolution_modification_factor_at_resizing  = self.oe_horizontal_resolution_modification_factor_at_resizing ,
                                                             vertical_range_modification_factor_at_resizing         = self.oe_vertical_range_modification_factor_at_resizing,
                                                             vertical_resolution_modification_factor_at_resizing    = self.oe_vertical_resolution_modification_factor_at_resizing ,
                                                             type_of_wavefront_shift_before_resizing                = self.oe_type_of_wavefront_shift_before_resizing,
                                                             new_horizontal_wavefront_center_position_after_shift   = self.oe_new_horizontal_wavefront_center_position_after_shift,
                                                             new_vertical_wavefront_center_position_after_shift     = self.oe_new_vertical_wavefront_center_position_after_shift
                                                         ))

    def get_optical_element(self):
        raise NotImplementedError()

    def set_input(self, srw_data):
        if not srw_data is None:
            self.input_srw_data = srw_data

            if self.is_automatic_run:
                self.propagate_wavefront()

    def run_calculations(self, tickets, progress_bar_value):
        e, h, v, i = self.wavefront_to_plot.get_intensity(multi_electron=False)

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value)

        e, h, v, i = self.wavefront_to_plot.get_phase()

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value + 5)

        e, h, v, i = self.wavefront_to_plot.get_intensity(multi_electron=True)

        tickets.append(SRWPlot.get_ticket_2D(h, v, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value + 5)

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

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity SE [ph/s/.1%bw/mm^2]", "Phase SE [rad]", "Intensity ME [ph/s/.1%bw/mm^2]"]
        else: return ["Intensity SE", "Phase SE", "Intensity ME"]

    def getXTitles(self):
        return ["X [mm]", "X [mm]", "X [mm]"]

    def getYTitles(self):
        return ["Y [mm]", "Y [mm]", "Y [mm]"]

    def getXUM(self):
        return ["X [mm]", "X [mm]", "X [mm]"]

    def getYUM(self):
        return ["Y [mm]", "Y [mm]", "Y [mm]"]
