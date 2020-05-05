from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerOut
from oasys.util.oasys_objects import OasysThicknessErrorsData

from syned.beamline.optical_elements.absorbers.filter import Filter
from syned.widget.widget_decorator import WidgetDecorator

from wofrysrw.beamline.optical_elements.absorbers.srw_filter import SRWFilter

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement


class OWSRWFilter(OWSRWOpticalElement):

    name = "Filter"
    description = "SRW: Filter"
    icon = "icons/filter.png"
    priority = 3.1

    inputs = [("SRWData", SRWData, "set_input"),
              ("Trigger", TriggerOut, "propagate_new_wavefront"),
              ("Thickness Error Data", OasysThicknessErrorsData, "setThicknessErrorProfile"),
              WidgetDecorator.syned_input_data()[0]]

    horizontal_shift = Setting(0.0)
    vertical_shift = Setting(0.0)

    width = Setting(0.001)
    height = Setting(0.001)

    horizontal_number_of_points = Setting(100)
    vertical_number_of_points = Setting(100)

    material = Setting("Be")
    thickness = Setting(500)
    has_thickness_error = Setting(0)
    thickness_error_profile = Setting("")

    def __init__(self):
        super().__init__(has_orientation_angles=False)

    def draw_specific_box(self):
        shape_box = oasysgui.widgetBox(self.tab_bas, "Shape", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(shape_box, self, "horizontal_shift", "Horizontal Shift [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(shape_box, self, "vertical_shift", "Vertical Shift [m]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(shape_box, self, "width", "Width [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(shape_box, self, "height", "Height [m]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(shape_box, self, "horizontal_number_of_points", "Horizontal Nr. Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(shape_box, self, "vertical_number_of_points", "Vertical Nr, Points", labelWidth=260, valueType=int, orientation="horizontal")

        material_box = oasysgui.widgetBox(self.tab_bas, "Material", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(material_box, self, "material", "Chemical Formula", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "thickness", "Thickness [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(material_box, self, "has_thickness_error", label="Use Thickness Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_ThicknessError)

        gui.separator(material_box)

        self.error_box_1 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="vertical", height=30)
        self.error_box_2 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="vertical", height=30)

        file_box =  oasysgui.widgetBox(self.error_box_2, "", addSpace=False, orientation="horizontal")

        self.le_thickness_error_profile = oasysgui.lineEdit(file_box, self, "thickness_error_profile", "Thickness error data file", labelWidth=155, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectThicknessErrorProfile)

        self.set_ThicknessError()

    def set_ThicknessError(self):
        self.error_box_1.setVisible(self.has_thickness_error == 0)
        self.error_box_2.setVisible(self.has_thickness_error == 1)

    def selectThicknessErrorProfile(self):
        self.le_thickness_error_profile.setText(oasysgui.selectFileFromDialog(self, self.thickness_error_profile, "Thickness error data file", file_extension_filter="*.h5"))

    def get_optical_element(self):
        return SRWFilter(name=self.name,
                         material=self.material,
                         thickness=self.thickness*1e-6,
                         x_range=[self.horizontal_shift - self.width/2, self.horizontal_shift + self.width/2],
                         y_range=[self.vertical_shift - self.height/2, self.vertical_shift + self.height/2],
                         n_points_x=self.horizontal_number_of_points,
                         n_points_y=self.vertical_number_of_points,
                         energy=self.input_srw_data.get_srw_wavefront().get_photon_energy(),
                         thickness_error_profile=None if self.has_thickness_error==0 else self.thickness_error_profile)

    def check_data(self):
        super().check_data()

        congruence.checkNumber(self.horizontal_shift, "Horizontal Shift")
        congruence.checkNumber(self.vertical_shift, "Vertical Shift")

        congruence.checkStrictlyPositiveNumber(self.width, "Width")
        congruence.checkStrictlyPositiveNumber(self.height, "Height")

        congruence.checkStrictlyPositiveNumber(self.horizontal_number_of_points, "Horizontal Nr. Points")
        congruence.checkStrictlyPositiveNumber(self.vertical_number_of_points, "Vertical Nr. Points")

        congruence.checkEmptyString(self.material, "Chemical Formula")
        congruence.checkStrictlyPositiveNumber(self.thickness, "Thickness")

        if self.has_thickness_error == 1: congruence.checkFile(self.thickness_error_profile)

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if isinstance(optical_element, Filter):
                self.material = optical_element.get_material()
                self.thickness = optical_element.get_thickness()*1e6
            else:
                raise Exception("Syned Data not correct: Optical Element is not a Filter")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")

    def setThicknessErrorProfile(self, thickness_errors_data):
        try:
            thickness_error_profile_data_files = thickness_errors_data.thickness_error_profile_data_files

            if not thickness_error_profile_data_files is None:
                self.has_thickness_error = 1
                self.thickness_error_profile = thickness_error_profile_data_files[0]
                self.set_ThicknessError()
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception
