import os, numpy
from numpy import nan

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox, QDialog, QLabel, QSizePolicy

import orangecanvas.resources as resources

from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import TriggerIn, TriggerOut

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.beamline_element import BeamlineElement

from wofry.propagator.propagator import PropagationManager, PropagationElements, PropagationParameters
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront, PolarizationComponent, WavefrontPropagationParameters, WavefrontPropagationOptionalParameters
from wofrysrw.propagator.propagators2D.srw_propagation_mode import SRWPropagationMode
from wofrysrw.propagator.propagators2D.srw_fresnel_native import FresnelSRWNative, SRW_APPLICATION
from wofrysrw.propagator.propagators2D.srw_fresnel_wofry import FresnelSRWWofry
from wofrysrw.beamline.optical_elements.srw_optical_element import SRWOpticalElementDisplacement

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer
from wofrysrw.beamline.optical_elements.srw_optical_element import Orientation

from orangecontrib.srw.util.srw_util import SRWPlot


class OWSRWOpticalElement(SRWWavefrontViewer, WidgetDecorator):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    keywords = ["data", "file", "load", "read"]
    category = "SRW Optical Elements"

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRW Optical Element Data",
                "id":"data"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    inputs = [("SRWData", SRWData, "set_input"),
              ("Trigger", TriggerOut, "propagate_new_wavefront"),
              WidgetDecorator.syned_input_data()[0]]

    oe_name         = None
    p               = Setting(0.0)
    q               = Setting(0.0)
    angle_radial    = Setting(0.0)
    angle_azimuthal = Setting(0.0)
    orientation_azimuthal = Setting(0)
    invert_tangent_component = Setting(0)

    shape = Setting(0)
    surface_shape = Setting(0)

    drift_before_auto_resize_before_propagation                         = Setting(0)
    drift_before_auto_resize_after_propagation                          = Setting(0)
    drift_before_relative_precision_for_propagation_with_autoresizing   = Setting(1.0)
    drift_before_allow_semianalytical_treatment_of_quadratic_phase_term = Setting(1)
    drift_before_do_any_resizing_on_fourier_side_using_fft              = Setting(0)
    drift_before_horizontal_range_modification_factor_at_resizing       = Setting(1.0)
    drift_before_horizontal_resolution_modification_factor_at_resizing  = Setting(1.0)
    drift_before_vertical_range_modification_factor_at_resizing         = Setting(1.0)
    drift_before_vertical_resolution_modification_factor_at_resizing    = Setting(1.0)
    drift_before_type_of_wavefront_shift_before_resizing                = Setting(0)
    drift_before_new_horizontal_wavefront_center_position_after_shift   = Setting(0)
    drift_before_new_vertical_wavefront_center_position_after_shift     = Setting(0)

    drift_before_orientation_of_the_output_optical_axis_vector_x = Setting(0.0)
    drift_before_orientation_of_the_output_optical_axis_vector_y = Setting(0.0)
    drift_before_orientation_of_the_output_optical_axis_vector_z = Setting(0.0)
    drift_before_orientation_of_the_horizontal_base_vector_x     = Setting(0.0)
    drift_before_orientation_of_the_horizontal_base_vector_y     = Setting(0.0)

    drift_auto_resize_before_propagation                         = Setting(0)
    drift_auto_resize_after_propagation                          = Setting(0)
    drift_relative_precision_for_propagation_with_autoresizing   = Setting(1.0)
    drift_allow_semianalytical_treatment_of_quadratic_phase_term = Setting(1)
    drift_do_any_resizing_on_fourier_side_using_fft              = Setting(0)
    drift_horizontal_range_modification_factor_at_resizing       = Setting(1.0)
    drift_horizontal_resolution_modification_factor_at_resizing  = Setting(1.0)
    drift_vertical_range_modification_factor_at_resizing         = Setting(1.0)
    drift_vertical_resolution_modification_factor_at_resizing    = Setting(1.0)
    drift_type_of_wavefront_shift_before_resizing                = Setting(0)
    drift_new_horizontal_wavefront_center_position_after_shift   = Setting(0)
    drift_new_vertical_wavefront_center_position_after_shift     = Setting(0)

    drift_after_orientation_of_the_output_optical_axis_vector_x = Setting(0.0)
    drift_after_orientation_of_the_output_optical_axis_vector_y = Setting(0.0)
    drift_after_orientation_of_the_output_optical_axis_vector_z = Setting(0.0)
    drift_after_orientation_of_the_horizontal_base_vector_x     = Setting(0.0)
    drift_after_orientation_of_the_horizontal_base_vector_y     = Setting(0.0)

    oe_auto_resize_before_propagation                         = Setting(0)
    oe_auto_resize_after_propagation                          = Setting(0)
    oe_relative_precision_for_propagation_with_autoresizing   = Setting(1.0)
    oe_allow_semianalytical_treatment_of_quadratic_phase_term = Setting(0)
    oe_do_any_resizing_on_fourier_side_using_fft              = Setting(0)
    oe_horizontal_range_modification_factor_at_resizing       = Setting(1.0)
    oe_horizontal_resolution_modification_factor_at_resizing  = Setting(1.0)
    oe_vertical_range_modification_factor_at_resizing         = Setting(1.0)
    oe_vertical_resolution_modification_factor_at_resizing    = Setting(1.0)
    oe_type_of_wavefront_shift_before_resizing                = Setting(0)
    oe_new_horizontal_wavefront_center_position_after_shift   = Setting(0)
    oe_new_vertical_wavefront_center_position_after_shift     = Setting(0)

    oe_orientation_of_the_output_optical_axis_vector_x = Setting(0.0)
    oe_orientation_of_the_output_optical_axis_vector_y = Setting(0.0)
    oe_orientation_of_the_output_optical_axis_vector_z = Setting(0.0)
    oe_orientation_of_the_horizontal_base_vector_x     = Setting(0.0)
    oe_orientation_of_the_horizontal_base_vector_y     = Setting(0.0)

    has_displacement = Setting(0)
    shift_x = Setting(0.0)
    shift_y = Setting(0.0)
    rotation_x = Setting(0.0)
    rotation_y = Setting(0.0)

    input_srw_data = None

    has_orientation_angles=True
    has_oe_wavefront_propagation_parameters_tab = True
    azimuth_hor_vert=False
    has_p = True
    has_q = True
    check_positive_distances = True
    has_displacement_tab=True

    TABS_AREA_HEIGHT = 555
    CONTROL_AREA_WIDTH = 405

    def __init__(self, has_orientation_angles=True, azimuth_hor_vert=False, has_p=True, has_q=True, check_positive_distances=True, has_oe_wavefront_propagation_parameters_tab=True, has_displacement_tab=True):
        super().__init__()

        self.has_orientation_angles=has_orientation_angles
        self.azimuth_hor_vert=azimuth_hor_vert
        self.has_p = has_p
        self.has_q = has_q
        self.check_positive_distances = check_positive_distances
        self.has_oe_wavefront_propagation_parameters_tab = has_oe_wavefront_propagation_parameters_tab
        self.has_displacement_tab=has_displacement_tab


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

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "Optical Element")
        self.tab_pro = oasysgui.createTabPage(self.tabs_setting, "Wavefront Propagation")
        if self.has_displacement_tab: self.tab_dis = oasysgui.createTabPage(self.tabs_setting, "Displacement")

        self.coordinates_box = oasysgui.widgetBox(self.tab_bas, "Coordinates", addSpace=True, orientation="vertical")

        if self.has_p:
            oasysgui.lineEdit(self.coordinates_box, self, "p", "Distance from previous Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal",
                              callback=self.set_p)
        if self.has_q:
            oasysgui.lineEdit(self.coordinates_box, self, "q", "Distance to next Continuation Plane [m]", labelWidth=280, valueType=float, orientation="horizontal",
                              callback=self.set_q)

        if self.has_orientation_angles:
            self.le_angle_radial = oasysgui.lineEdit(self.coordinates_box, self, "angle_radial", "Incident Angle (to normal) [deg]", labelWidth=280, valueType=float, orientation="horizontal")

            if self.azimuth_hor_vert:
                gui.comboBox(self.coordinates_box, self, "orientation_azimuthal", label="Orientation of central normal vector",
                             items=["Up", "Down", "Left", "Right"], labelWidth=300,
                             sendSelectedValue=False, orientation="horizontal")
                gui.comboBox(self.coordinates_box, self, "invert_tangent_component", label="Invert Tangent Component",
                             items=["No", "Yes"], labelWidth=300,
                             sendSelectedValue=False, orientation="horizontal")
            else:
                oasysgui.lineEdit(self.coordinates_box, self, "angle_azimuthal", "Rotation along Beam Axis [deg]", labelWidth=280, valueType=float, orientation="horizontal")

        self.draw_specific_box()

        self.tabs_prop_setting = oasysgui.tabWidget(self.tab_pro)
        self.tabs_prop_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-10)

        self.tab_drift_before = oasysgui.createTabPage(self.tabs_prop_setting, "Drift Space Before")
        if self.has_oe_wavefront_propagation_parameters_tab: self.tab_oe = oasysgui.createTabPage(self.tabs_prop_setting, "Optical Element")
        self.tab_drift = oasysgui.createTabPage(self.tabs_prop_setting, "Drift Space After")

        self.set_p()
        self.set_q()

        # DRIFT SPACE

        gui.comboBox(self.tab_drift_before, self, "drift_before_auto_resize_before_propagation", label="Auto Resize Before Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_drift_before, self, "drift_before_auto_resize_after_propagation", label="Auto Resize After Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_relative_precision_for_propagation_with_autoresizing", "Relative precision for propagation with\nautoresizing (1.0 is nominal)", labelWidth=300, valueType=float, orientation="horizontal")

        propagator_box = oasysgui.widgetBox(self.tab_drift_before, "", addSpace=False, orientation="horizontal")

        gui.comboBox(propagator_box, self, "drift_before_allow_semianalytical_treatment_of_quadratic_phase_term", label="Propagator",
                     items=["Standard", "Quadratic Term", "Quadratic Term Special", "From Waist", "To Waist"], labelWidth=200,
                     sendSelectedValue=False, orientation="horizontal")

        gui.button(propagator_box, self, "?", width=20, callback=self.show_propagator_info)

        gui.comboBox(self.tab_drift_before, self, "drift_before_do_any_resizing_on_fourier_side_using_fft", label="Do any resizing on fourier side using fft",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_horizontal_range_modification_factor_at_resizing", "H range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_horizontal_resolution_modification_factor_at_resizing", "H resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_vertical_range_modification_factor_at_resizing", "V range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_vertical_resolution_modification_factor_at_resizing", "V resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")

        # not yet used by SRW
        #oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_type_of_wavefront_shift_before_resizing", "Type of wavefront shift before resizing", labelWidth=300, valueType=int, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_new_horizontal_wavefront_center_position_after_shift", "New horizontal wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift_before, self, "drift_before_new_vertical_wavefront_center_position_after_shift", "New vertical wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")

        drift_before_optional_box = oasysgui.widgetBox(self.tab_drift_before, "Optional", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(drift_before_optional_box, self, "drift_before_orientation_of_the_output_optical_axis_vector_x", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_before_optional_box, self, "drift_before_orientation_of_the_output_optical_axis_vector_y", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_before_optional_box, self, "drift_before_orientation_of_the_output_optical_axis_vector_z", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Z", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_before_optional_box, self, "drift_before_orientation_of_the_horizontal_base_vector_x"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_before_optional_box, self, "drift_before_orientation_of_the_horizontal_base_vector_y"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")

        # OE
        if self.has_oe_wavefront_propagation_parameters_tab:
            gui.comboBox(self.tab_oe, self, "oe_auto_resize_before_propagation", label="Auto Resize Before Propagation",
                         items=["No", "Yes"], labelWidth=300,
                         sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.tab_oe, self, "oe_auto_resize_after_propagation", label="Auto Resize After Propagation",
                         items=["No", "Yes"], labelWidth=300,
                         sendSelectedValue=False, orientation="horizontal")

            oasysgui.lineEdit(self.tab_oe, self, "oe_relative_precision_for_propagation_with_autoresizing", "Relative precision for propagation with\nautoresizing (1.0 is nominal)", labelWidth=300, valueType=float, orientation="horizontal")

            propagator_box = oasysgui.widgetBox(self.tab_oe, "", addSpace=False, orientation="horizontal")

            gui.comboBox(propagator_box, self, "oe_allow_semianalytical_treatment_of_quadratic_phase_term", label="Propagator",
                         items=["Standard", "Quadratic Term", "Quadratic Term Special", "From Waist", "To Waist"], labelWidth=200,
                         sendSelectedValue=False, orientation="horizontal")

            gui.button(propagator_box, self, "?", width=20, callback=self.show_propagator_info)

            gui.comboBox(self.tab_oe, self, "oe_do_any_resizing_on_fourier_side_using_fft", label="Do any resizing on fourier side using fft",
                         items=["No", "Yes"], labelWidth=300,
                         sendSelectedValue=False, orientation="horizontal")

            oasysgui.lineEdit(self.tab_oe, self, "oe_horizontal_range_modification_factor_at_resizing", "H range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.tab_oe, self, "oe_horizontal_resolution_modification_factor_at_resizing", "H resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.tab_oe, self, "oe_vertical_range_modification_factor_at_resizing", "V range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(self.tab_oe, self, "oe_vertical_resolution_modification_factor_at_resizing", "V resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")

            # not yet used by SRW
            #oasysgui.lineEdit(self.tab_oe, self, "oe_type_of_wavefront_shift_before_resizing", "Type of wavefront shift before resizing", labelWidth=300, valueType=int, orientation="horizontal")
            #oasysgui.lineEdit(self.tab_oe, self, "oe_new_horizontal_wavefront_center_position_after_shift", "New horizontal wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")
            #oasysgui.lineEdit(self.tab_oe, self, "oe_new_vertical_wavefront_center_position_after_shift", "New vertical wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")

            oe_optional_box = oasysgui.widgetBox(self.tab_oe, "Optional", addSpace=False, orientation="vertical")

            oasysgui.lineEdit(oe_optional_box, self, "oe_orientation_of_the_output_optical_axis_vector_x", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(oe_optional_box, self, "oe_orientation_of_the_output_optical_axis_vector_y", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(oe_optional_box, self, "oe_orientation_of_the_output_optical_axis_vector_z", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Z", labelWidth=290, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(oe_optional_box, self, "oe_orientation_of_the_horizontal_base_vector_x"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(oe_optional_box, self, "oe_orientation_of_the_horizontal_base_vector_y"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")

        # DRIFT SPACE

        gui.comboBox(self.tab_drift, self, "drift_auto_resize_before_propagation", label="Auto Resize Before Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.tab_drift, self, "drift_auto_resize_after_propagation", label="Auto Resize After Propagation",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift, self, "drift_relative_precision_for_propagation_with_autoresizing", "Relative precision for propagation with\nautoresizing (1.0 is nominal)", labelWidth=300, valueType=float, orientation="horizontal")

        propagator_box = oasysgui.widgetBox(self.tab_drift, "", addSpace=False, orientation="horizontal")

        gui.comboBox(propagator_box, self, "drift_allow_semianalytical_treatment_of_quadratic_phase_term", label="Propagator",
                     items=["Standard", "Quadratic Term", "Quadratic Term Special", "From Waist", "To Waist"], labelWidth=200,
                     sendSelectedValue=False, orientation="horizontal")

        gui.button(propagator_box, self, "?", width=20, callback=self.show_propagator_info)

        gui.comboBox(self.tab_drift, self, "drift_do_any_resizing_on_fourier_side_using_fft", label="Do any resizing on fourier side using fft",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.tab_drift, self, "drift_horizontal_range_modification_factor_at_resizing", "H range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_horizontal_resolution_modification_factor_at_resizing", "H resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_vertical_range_modification_factor_at_resizing", "V range modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.tab_drift, self, "drift_vertical_resolution_modification_factor_at_resizing", "V resolution modification factor at resizing", labelWidth=300, valueType=float, orientation="horizontal")

        # not yet used by SRW
        #oasysgui.lineEdit(self.tab_drift, self, "drift_type_of_wavefront_shift_before_resizing", "Type of wavefront shift before resizing", labelWidth=300, valueType=int, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift, self, "drift_new_horizontal_wavefront_center_position_after_shift", "New horizontal wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")
        #oasysgui.lineEdit(self.tab_drift, self, "drift_new_vertical_wavefront_center_position_after_shift", "New vertical wavefront center position [m]", labelWidth=300, valueType=float, orientation="horizontal")

        drift_optional_box = oasysgui.widgetBox(self.tab_drift, "Optional", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(drift_optional_box, self, "drift_after_orientation_of_the_output_optical_axis_vector_x", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_optional_box, self, "drift_after_orientation_of_the_output_optical_axis_vector_y", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_optional_box, self, "drift_after_orientation_of_the_output_optical_axis_vector_z", "Orientation of the Output Optical Axis vector\nin the Incident Beam Frame: Z", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_optional_box, self, "drift_after_orientation_of_the_horizontal_base_vector_x"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: X", labelWidth=290, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(drift_optional_box, self, "drift_after_orientation_of_the_horizontal_base_vector_y"    , "Orientation of the Horizontal Base vector of the\nOutput Frame in the Incident Beam Frame: Y", labelWidth=290, valueType=float, orientation="horizontal")

        #DISPLACEMENTS

        if self.has_displacement_tab:

            gui.comboBox(self.tab_dis, self, "has_displacement", label="Has Displacement",
                         items=["No", "Yes"], labelWidth=280,
                         sendSelectedValue=False, orientation="horizontal", callback=self.set_displacement)

            gui.separator(self.tab_dis)

            self.displacement_box = oasysgui.widgetBox(self.tab_dis, "", addSpace=False, orientation="vertical", height=250)
            self.displacement_box_empty = oasysgui.widgetBox(self.tab_dis, "", addSpace=False, orientation="vertical", height=250)

            shift_box = oasysgui.widgetBox(self.displacement_box, "Shift", addSpace=False, orientation="vertical")

            oasysgui.lineEdit(shift_box, self, "shift_x", "Horizontal [m]", labelWidth=280, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(shift_box, self, "shift_y", "Vertical [m]", labelWidth=280, valueType=float, orientation="horizontal")

            rotation_box = oasysgui.widgetBox(self.displacement_box, "Rotation", addSpace=False, orientation="vertical")

            oasysgui.lineEdit(rotation_box, self, "rotation_y", "Around Horizontal Axis [CCW, deg]", labelWidth=280, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(rotation_box, self, "rotation_x", "Around Vertical Axis [CCW, deg]", labelWidth=280, valueType=float, orientation="horizontal")

            self.set_displacement()

    def set_p(self):
        if self.p == 0.0:
            self.tab_drift_before.setEnabled(False)
        else:
            self.tab_drift_before.setEnabled(True)

    def set_q(self):
        if self.q  == 0.0:
            self.tab_drift.setEnabled(False)
        else:
            self.tab_drift.setEnabled(True)

    def set_displacement(self):
        self.displacement_box.setVisible(self.has_displacement==1)
        self.displacement_box_empty.setVisible(self.has_displacement==0)

    class PropagatorInfoDialog(QDialog):

        usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "propagator_info.png")

        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Propagator Info')

            self.setMinimumHeight(180)
            self.setMinimumWidth(340)

            usage_box = oasysgui.widgetBox(self, "", addSpace=True, orientation="vertical")

            label = QLabel("")
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setPixmap(QPixmap(self.usage_path))

            usage_box.layout().addWidget(label)

            bbox = QDialogButtonBox(QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)

            usage_box.layout().addWidget(bbox)


    def show_propagator_info(self):
        try:
            dialog = OWSRWOpticalElement.PropagatorInfoDialog(parent=self)
            dialog.show()
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def draw_specific_box(self):
        raise NotImplementedError()

    def check_data(self):
        if self.check_positive_distances:
            if self.has_p: congruence.checkPositiveNumber(self.p, "Distance from previous Continuation Plane")
            if self.has_q: congruence.checkPositiveNumber(self.q, "Distance to next Continuation Plane")
        else:
            if self.has_p: congruence.checkNumber(self.p, "Distance from previous Continuation Plane")
            if self.has_q: congruence.checkNumber(self.q, "Distance to next Continuation Plane")

        if self.has_orientation_angles:
            congruence.checkPositiveAngle(self.angle_radial, "Incident Angle (to normal)")

            if self.azimuth_hor_vert:
                if self.orientation_azimuthal == Orientation.UP:
                    self.angle_azimuthal = 0.0
                elif self.orientation_azimuthal == Orientation.DOWN:
                    self.angle_azimuthal = 180.0
                elif self.orientation_azimuthal == Orientation.LEFT:
                    self.angle_azimuthal = 90.0
                elif self.orientation_azimuthal == Orientation.RIGHT:
                    self.angle_azimuthal = 270.0
            else:
                congruence.checkPositiveAngle(self.angle_azimuthal, "Rotation along Beam Axis")
        else:
            self.angle_radial = 0.0
            self.angle_azimuthal = 0.0

        if self.has_displacement:
            congruence.checkAngle(self.rotation_x, "Rotation Around Horizontal Axis")
            congruence.checkAngle(self.rotation_y, "Rotation Around Vertical Axis")

    def propagate_new_wavefront(self, trigger):
        try:
            if trigger and trigger.new_object == True:
                if trigger.has_additional_parameter("variable_name"):
                    if self.input_srw_data is None: raise Exception("No Input Data")

                    variable_name = trigger.get_additional_parameter("variable_name").strip()
                    variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                    variable_value = trigger.get_additional_parameter("variable_value")
                    variable_um = trigger.get_additional_parameter("variable_um")

                    if "," in variable_name:
                        variable_names = variable_name.split(",")

                        for variable_name in variable_names:
                            setattr(self, variable_name.strip(), variable_value)
                    else:
                        setattr(self, variable_name, variable_value)

                    self.input_srw_data.get_srw_wavefront().setScanningData(SRWWavefront.ScanningData(variable_name, variable_value, variable_display_name, variable_um))
                    self.propagate_wavefront()

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def propagate_wavefront(self):
        try:
            self.progressBarInit()

            if self.input_srw_data is None: raise Exception("No Input Data")

            self.check_data()

            # propagation to o.e.

            propagator = PropagationManager.Instance()
            propagation_mode = propagator.get_propagation_mode(SRW_APPLICATION)

            handler_name = FresnelSRWNative.HANDLER_NAME if propagation_mode == SRWPropagationMode.STEP_BY_STEP  or \
                                                            propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE else \
                           FresnelSRWWofry.HANDLER_NAME

            input_wavefront = self.input_srw_data.get_srw_wavefront()
            srw_beamline = self.input_srw_data.get_srw_beamline().duplicate()
            working_srw_beamline = self.input_srw_data.get_working_srw_beamline().duplicate()

            optical_element = self.get_optical_element()
            optical_element.name = self.oe_name if not self.oe_name is None else self.windowTitle()

            if self.has_displacement==1:
                optical_element.displacement = SRWOpticalElementDisplacement(shift_x=self.shift_x,
                                                                             shift_y=self.shift_y,
                                                                             rotation_x=numpy.radians(-self.rotation_x),
                                                                             rotation_y=numpy.radians(-self.rotation_y))

            beamline_element = BeamlineElement(optical_element=optical_element,
                                               coordinates=ElementCoordinates(p=self.p,
                                                                              q=self.q,
                                                                              angle_radial=numpy.radians(self.angle_radial),
                                                                              angle_azimuthal=numpy.radians(self.angle_azimuthal)))

            srw_beamline.append_beamline_element(beamline_element)
            working_srw_beamline.append_beamline_element(beamline_element)

            self.progressBarSet(20)

            if propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE:
                self.set_additional_parameters(beamline_element, None, srw_beamline)
                self.set_additional_parameters(beamline_element, None, working_srw_beamline)

                if hasattr(self, "is_final_screen") and self.is_final_screen == 1:
                    propagation_parameters = PropagationParameters(wavefront=input_wavefront.duplicate(),
                                                                   propagation_elements = None)

                    propagation_parameters.set_additional_parameters("working_beamline", working_srw_beamline)

                    self.setStatusMessage("Begin Propagation")

                    output_wavefront = propagator.do_propagation(propagation_parameters=propagation_parameters,
                                                                 handler_name=handler_name)
                    self.setStatusMessage("Propagation Completed")

                    output_srw_data = SRWData(srw_beamline=srw_beamline,
                                              srw_wavefront=output_wavefront)
                    output_srw_data.reset_working_srw_beamline()
                else:
                    output_wavefront = None

                    output_srw_data = SRWData(srw_beamline=srw_beamline,
                                              srw_wavefront=input_wavefront)
            else:
                propagation_elements = PropagationElements()
                propagation_elements.add_beamline_element(beamline_element)

                propagation_parameters = PropagationParameters(wavefront=input_wavefront.duplicate(),
                                                               propagation_elements = propagation_elements)

                self.set_additional_parameters(beamline_element, propagation_parameters, srw_beamline)

                self.setStatusMessage("Begin Propagation")

                output_wavefront = propagator.do_propagation(propagation_parameters=propagation_parameters,
                                                             handler_name=handler_name)

                self.setStatusMessage("Propagation Completed")

                output_srw_data = SRWData(srw_beamline=srw_beamline,
                                          srw_wavefront=output_wavefront)

            self.progressBarSet(50)

            if not output_wavefront is None:
                output_wavefront.setScanningData(self.input_srw_data.get_srw_wavefront().scanned_variable_data)

                self.output_wavefront = output_wavefront
                self.initializeTabs()

                tickets = []

                self.run_calculation_for_plots(tickets=tickets, progress_bar_value=50)

                self.plot_results(tickets, 80)

            self.progressBarFinished()
            self.setStatusMessage("")

            self.send("SRWData", output_srw_data)

            self.send("Trigger", TriggerIn(new_object=True))

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

            if self.IS_DEVELOP: raise e

    def set_additional_parameters(self, beamline_element, propagation_parameters=None, beamline=None):
        from wofrysrw.beamline.srw_beamline import Where

        srw_drift_before_wavefront_propagation_parameters = None
        srw_drift_before_wavefront_propagation_optional_parameters = None

        # DRIFT BEFORE
        if beamline_element.get_coordinates().p() != 0:
            srw_drift_before_wavefront_propagation_parameters = WavefrontPropagationParameters(
                                                                 auto_resize_before_propagation                         = self.drift_before_auto_resize_before_propagation,
                                                                 auto_resize_after_propagation                          = self.drift_before_auto_resize_after_propagation,
                                                                 relative_precision_for_propagation_with_autoresizing   = self.drift_before_relative_precision_for_propagation_with_autoresizing,
                                                                 allow_semianalytical_treatment_of_quadratic_phase_term = self.drift_before_allow_semianalytical_treatment_of_quadratic_phase_term,
                                                                 do_any_resizing_on_fourier_side_using_fft              = self.drift_before_do_any_resizing_on_fourier_side_using_fft,
                                                                 horizontal_range_modification_factor_at_resizing       = self.drift_before_horizontal_range_modification_factor_at_resizing,
                                                                 horizontal_resolution_modification_factor_at_resizing  = self.drift_before_horizontal_resolution_modification_factor_at_resizing ,
                                                                 vertical_range_modification_factor_at_resizing         = self.drift_before_vertical_range_modification_factor_at_resizing,
                                                                 vertical_resolution_modification_factor_at_resizing    = self.drift_before_vertical_resolution_modification_factor_at_resizing ,
                                                                 type_of_wavefront_shift_before_resizing                = self.drift_before_type_of_wavefront_shift_before_resizing,
                                                                 new_horizontal_wavefront_center_position_after_shift   = self.drift_before_new_horizontal_wavefront_center_position_after_shift,
                                                                 new_vertical_wavefront_center_position_after_shift     = self.drift_before_new_vertical_wavefront_center_position_after_shift
                                                             )

            if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_drift_before_wavefront_propagation_parameters", srw_drift_before_wavefront_propagation_parameters)

            if self.has_drift_before_wavefront_propagation_optional_parameters():
                srw_drift_before_wavefront_propagation_optional_parameters = WavefrontPropagationOptionalParameters(
                                                                     orientation_of_the_output_optical_axis_vector_x = self.drift_before_orientation_of_the_output_optical_axis_vector_x,
                                                                     orientation_of_the_output_optical_axis_vector_y = self.drift_before_orientation_of_the_output_optical_axis_vector_y,
                                                                     orientation_of_the_output_optical_axis_vector_z = self.drift_before_orientation_of_the_output_optical_axis_vector_z,
                                                                     orientation_of_the_horizontal_base_vector_x     = self.drift_before_orientation_of_the_horizontal_base_vector_x,
                                                                     orientation_of_the_horizontal_base_vector_y     = self.drift_before_orientation_of_the_horizontal_base_vector_y
                                                                 )

                if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_drift_before_wavefront_propagation_optional_parameters", srw_drift_before_wavefront_propagation_optional_parameters)

        if not beamline is None: beamline.append_wavefront_propagation_parameters(srw_drift_before_wavefront_propagation_parameters, srw_drift_before_wavefront_propagation_optional_parameters, Where.DRIFT_BEFORE)

        # OE
        srw_oe_wavefront_propagation_parameters = None
        srw_oe_wavefront_propagation_optional_parameters = None

        if self.has_oe_wavefront_propagation_parameters_tab:
            srw_oe_wavefront_propagation_parameters = WavefrontPropagationParameters(
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
                                                             )


            if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_oe_wavefront_propagation_parameters", srw_oe_wavefront_propagation_parameters)

            if self.has_oe_wavefront_propagation_optional_parameters():
                srw_oe_wavefront_propagation_optional_parameters = WavefrontPropagationOptionalParameters(
                                                                     orientation_of_the_output_optical_axis_vector_x = self.oe_orientation_of_the_output_optical_axis_vector_x,
                                                                     orientation_of_the_output_optical_axis_vector_y = self.oe_orientation_of_the_output_optical_axis_vector_y,
                                                                     orientation_of_the_output_optical_axis_vector_z = self.oe_orientation_of_the_output_optical_axis_vector_z,
                                                                     orientation_of_the_horizontal_base_vector_x     = self.oe_orientation_of_the_horizontal_base_vector_x,
                                                                     orientation_of_the_horizontal_base_vector_y     = self.oe_orientation_of_the_horizontal_base_vector_y
                                                                 )

                if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_oe_wavefront_propagation_optional_parameters", srw_oe_wavefront_propagation_optional_parameters)

        if not beamline is None: beamline.append_wavefront_propagation_parameters(srw_oe_wavefront_propagation_parameters, srw_oe_wavefront_propagation_optional_parameters, Where.OE)

        # DRIFT AFTER
        srw_drift_after_wavefront_propagation_parameters = None
        srw_drift_after_wavefront_propagation_optional_parameters = None

        if beamline_element.get_coordinates().q():
            srw_drift_after_wavefront_propagation_parameters = WavefrontPropagationParameters(
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
                                                             )


            if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_drift_after_wavefront_propagation_parameters", srw_drift_after_wavefront_propagation_parameters)

            if self.has_drift_after_wavefront_propagation_optional_parameters():
                srw_drift_after_wavefront_propagation_optional_parameters = WavefrontPropagationOptionalParameters(
                                                                     orientation_of_the_output_optical_axis_vector_x = self.drift_after_orientation_of_the_output_optical_axis_vector_x,
                                                                     orientation_of_the_output_optical_axis_vector_y = self.drift_after_orientation_of_the_output_optical_axis_vector_y,
                                                                     orientation_of_the_output_optical_axis_vector_z = self.drift_after_orientation_of_the_output_optical_axis_vector_z,
                                                                     orientation_of_the_horizontal_base_vector_x     = self.drift_after_orientation_of_the_horizontal_base_vector_x,
                                                                     orientation_of_the_horizontal_base_vector_y     = self.drift_after_orientation_of_the_horizontal_base_vector_y
                                                                 )

                if not propagation_parameters is None: propagation_parameters.set_additional_parameters("srw_drift_after_wavefront_propagation_optional_parameters", srw_drift_after_wavefront_propagation_optional_parameters)

        if not beamline is None: beamline.append_wavefront_propagation_parameters(srw_drift_after_wavefront_propagation_parameters, srw_drift_after_wavefront_propagation_optional_parameters, Where.DRIFT_AFTER)

    def has_drift_before_wavefront_propagation_optional_parameters(self):
        return self.drift_before_orientation_of_the_output_optical_axis_vector_x != 0.0 or \
               self.drift_before_orientation_of_the_output_optical_axis_vector_y != 0.0 or \
               self.drift_before_orientation_of_the_output_optical_axis_vector_z != 0.0 or \
               self.drift_before_orientation_of_the_horizontal_base_vector_x     != 0.0 or \
               self.drift_before_orientation_of_the_horizontal_base_vector_y     != 0.0

    def has_oe_wavefront_propagation_optional_parameters(self):
        return self.oe_orientation_of_the_output_optical_axis_vector_x != 0.0 or \
               self.oe_orientation_of_the_output_optical_axis_vector_y != 0.0 or \
               self.oe_orientation_of_the_output_optical_axis_vector_z != 0.0 or \
               self.oe_orientation_of_the_horizontal_base_vector_x     != 0.0 or \
               self.oe_orientation_of_the_horizontal_base_vector_y     != 0.0

    def has_drift_after_wavefront_propagation_optional_parameters(self):
        return self.drift_after_orientation_of_the_output_optical_axis_vector_x != 0.0 or \
               self.drift_after_orientation_of_the_output_optical_axis_vector_y != 0.0 or \
               self.drift_after_orientation_of_the_output_optical_axis_vector_z != 0.0 or \
               self.drift_after_orientation_of_the_horizontal_base_vector_x     != 0.0 or \
               self.drift_after_orientation_of_the_horizontal_base_vector_y     != 0.0

    def get_optical_element(self):
        raise NotImplementedError()

    def set_input(self, srw_data):
        if not srw_data is None:
            self.input_srw_data = srw_data

            if self.is_automatic_run:
                self.propagate_wavefront()

    def run_calculation_for_plots(self, tickets, progress_bar_value):
        if self.view_type==2:
            e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

            self.progressBarSet(progress_bar_value)

            e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

            e, h, v, p = self.output_wavefront.get_phase(polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, p[int(e.size/2)]))

            self.progressBarSet(progress_bar_value + 10)

            e, h, v, p = self.output_wavefront.get_phase(polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, p[int(e.size/2)]))
        elif self.view_type==1:
            e, h, v, i = self.output_wavefront.get_intensity(multi_electron=False)

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

            self.progressBarSet(progress_bar_value)

            e, h, v, p = self.output_wavefront.get_phase()

            tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, p[int(e.size/2)]))

            self.progressBarSet(progress_bar_value + 10)

    def receive_syned_data(self, data):
        if not data is None:
            try:
                beamline_element = data.get_beamline_element_at(-1)

                if not beamline_element is None:
                    self.oe_name = beamline_element._optical_element._name
                    self.p = beamline_element._coordinates._p
                    self.q = beamline_element._coordinates._q

                    if self.has_orientation_angles:
                        self.angle_azimuthal = numpy.degrees(beamline_element._coordinates._angle_azimuthal)
                        self.angle_radial = numpy.degrees(beamline_element._coordinates._angle_radial)

                    if self.azimuth_hor_vert:
                        if self.angle_azimuthal == 0.0:
                            self.orientation_azimuthal = Orientation.UP
                        elif self.angle_azimuthal == 180.0:
                            self.orientation_azimuthal = Orientation.DOWN
                        elif self.angle_azimuthal == 90.0:
                            self.orientation_azimuthal = Orientation.LEFT
                        elif self.angle_azimuthal == 270.0:
                            self.orientation_azimuthal == Orientation.RIGHT
                        else:
                            raise Exception("Syned Data not correct: Orientation of central normal vector not recognized")
                    else:
                        self.angle_azimuthal = 0.0
                        self.angle_radial    = 0.0

                    self.receive_specific_syned_data(beamline_element._optical_element)
                else:
                    raise Exception("Syned Data not correct: Empty Beamline Element")
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError()

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def getVariablesToPlot(self):
        if self.view_type == 2:
            return [[1, 2], [1, 2], [1, 2], [1, 2]]
        else:
            return [[1, 2], [1, 2]]

    def getWeightedPlots(self):
        if self.view_type == 2:
            return [False, False, True, True]
        else:
            return [False, True]

    def getWeightTickets(self):
        if self.view_type == 2:
            return [nan, nan, 0, 1]
        else:
            return [nan, 0]


    def getTitles(self, with_um=False):
        if self.view_type == 2:
            if with_um: return ["Intensity SE \u03c3 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity SE \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE \u03c3 [rad]",
                                "Phase SE \u03c0 [rad]"]
            else: return ["Intensity SE \u03c3",
                          "Intensity SE \u03c0",
                          "Phase SE \u03c3",
                          "Phase SE \u03c0"]
        else:
            if with_um: return ["Intensity SE [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE [rad]"]
            else: return ["Intensity SE",
                          "Phase SE"]

    def getXTitles(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]"]

    def getYTitles(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]"]

    def getXUM(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]"]

    def getYUM(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]"]
