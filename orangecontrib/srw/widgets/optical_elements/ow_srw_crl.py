import os

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerOut
import oasys.util.oasys_util as OU
from oasys.util.oasys_objects import OasysThicknessErrorsData

from syned.widget.widget_decorator import WidgetDecorator

from wofrysrw.beamline.optical_elements.other.srw_crl import CRLShape, PlaneOfFocusing, SRWCRL

from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement
from orangecontrib.srw.util.srw_util import get_absorption_parameters

class OWSRWCRL(OWSRWOpticalElement):

    name = "CRL"
    description = "SRW: CRL"
    icon = "icons/crl.png"
    priority = 16

    plane_of_focusing = Setting(2)
    material_data = Setting(0)
    material = Setting("Be")
    refractive_index = Setting(1e-6)
    attenuation_length = Setting(1e-3)
    shape = Setting(0)
    diameter = Setting(400)
    radius_of_curvature = Setting(50)
    number_of_lenses = Setting(10)
    wall_thickness = Setting(30)
    horizontal_center_coordinate = Setting(0.0)
    vertical_center_coordinate = Setting(0.0)
    void_center_coordinates = Setting("")
    horizontal_points = Setting(1001)
    vertical_points = Setting(1001)

    has_thickness_error = Setting(0)
    crl_error_profiles = Setting([])
    crl_scaling_factor = Setting(1.0)

    inputs = [("SRWData", SRWData, "set_input"),
              ("Thickness Errors Data", OasysThicknessErrorsData, "setThicknessErrorProfiles"),
              ("Trigger", TriggerOut, "propagate_new_wavefront"),
              WidgetDecorator.syned_input_data()[0]]

    def __init__(self):
        super().__init__(has_orientation_angles=False)

    def draw_specific_box(self):
        tabs_crl = gui.tabWidget(self.tab_bas)
        tab_bas = oasysgui.createTabPage(tabs_crl, "CRL")

        self.filter_box = oasysgui.widgetBox(tab_bas, "CRL Setting", addSpace=False, orientation="vertical")

        gui.comboBox(self.filter_box, self, "plane_of_focusing", label="Plane of Focusing",
                     labelWidth=220, items=PlaneOfFocusing.items(), sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(self.filter_box, self, "material_data", label="Material Properties from", labelWidth=180,
                             items=["Chemical Formula", "Absorption Parameters"],
                             callback=self.set_MaterialData,
                             sendSelectedValue=False, orientation="horizontal")

        self.filter_box_1 = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="vertical", height=30, width=self.CONTROL_AREA_WIDTH-40)
        self.filter_box_2 = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal", height=30, width=self.CONTROL_AREA_WIDTH-40)

        oasysgui.lineEdit(self.filter_box_1, self, "material", "Chemical Formula", labelWidth=260, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box_2, self, "refractive_index", "Refr. Index (\u03b4)", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box_2, self, "attenuation_length", "Att. Lenght [m]", valueType=float, orientation="horizontal")

        self.set_MaterialData()

        gui.comboBox(self.filter_box, self, "shape", label="Shape",
                     labelWidth=220, items=CRLShape.items(), sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box, self, "diameter", "Diameter [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "radius_of_curvature", "Radius of Curvature [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "horizontal_points", "H Points", labelWidth=130, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box, self, "vertical_points", "V Points", labelWidth=90, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box, self, "number_of_lenses", "Number of Lenses", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "wall_thickness", "Wall Thickness [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "horizontal_center_coordinate", "Center Coord. H [m]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "vertical_center_coordinate", "V [m]", labelWidth=90, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box, self, "void_center_coordinates", "Void center coordinates [m] (x1, y1, r1, x2, y2, r2, ...)", labelWidth=350, valueType=str, orientation="vertical")

        gui.separator(self.filter_box)

        tab_thick = oasysgui.createTabPage(tabs_crl, "Thickness Error")

        gui.comboBox(tab_thick, self, "has_thickness_error", label="Use Thickness Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_ThicknessError)

        gui.separator(tab_thick)

        self.thickness_error_box_1 = oasysgui.widgetBox(tab_thick, "Thickness Error Files", addSpace=False, orientation="vertical", height=340, width=self.CONTROL_AREA_WIDTH - 30)
        self.thickness_error_box_2 = oasysgui.widgetBox(tab_thick, "", addSpace=False, orientation="vertical", height=340, width=self.CONTROL_AREA_WIDTH - 30)

        self.files_area = oasysgui.textArea(height=265)
        self.thickness_error_box_1.layout().addWidget(self.files_area)

        self.refresh_files_text_area()

        oasysgui.lineEdit(self.thickness_error_box_1, self, "crl_scaling_factor", "Thickness Error Scaling Factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_ThicknessError()

    def refresh_files_text_area(self):
        text = ""
        for file in self.crl_error_profiles: text += file + "\n"
        self.files_area.setText(text)

    def setThicknessErrorProfiles(self, thickness_errors_data):
        try:
            thickness_error_profile_data_files = thickness_errors_data.thickness_error_profile_data_files
            if not thickness_error_profile_data_files is None:
                self.crl_error_profiles = thickness_error_profile_data_files
                self.refresh_files_text_area()
                self.has_thickness_error = 1
                self.set_ThicknessError()
        except Exception as exception:
            QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)
            if self.IS_DEVELOP: raise exception

    def set_ThicknessError(self):
        self.thickness_error_box_2.setVisible(self.has_thickness_error == 0)
        self.thickness_error_box_1.setVisible(self.has_thickness_error == 1)

    def set_MaterialData(self):
        self.filter_box_1.setVisible(self.material_data==0)
        self.filter_box_2.setVisible(self.material_data==1)

    def get_optical_element(self):
        wavefront = self.input_srw_data.get_srw_wavefront()
        energy    = wavefront.get_photon_energy()

        if self.material_data == 0:
            attenuation_length, delta = get_absorption_parameters(self.material, energy)

            print("Refractive Index (\u03b4) :" + str(delta) + "\n" + \
                  "Attenuation Length [m]    :" + str(attenuation_length))
        else:
            delta              = self.refractive_index
            attenuation_length = self.attenuation_length

        return SRWCRL(name=self.oe_name,
                      plane_of_focusing=self.plane_of_focusing+1,
                      delta=delta,
                      attenuation_length=attenuation_length,
                      shape=self.shape+1,
                      horizontal_aperture_size=self.diameter*1e-6,
                      vertical_aperture_size=self.diameter*1e-6,
                      radius_of_curvature=self.radius_of_curvature*1e-6,
                      number_of_lenses=self.number_of_lenses,
                      wall_thickness=self.wall_thickness*1e-6,
                      horizontal_center_coordinate=self.horizontal_center_coordinate,
                      vertical_center_coordinate=self.vertical_center_coordinate,
                      void_center_coordinates=self.parse_void_center_coordinates(),
                      initial_photon_energy=energy,
                      final_photon_energy=energy,
                      horizontal_points=self.horizontal_points,
                      vertical_points=self.vertical_points,
                      thickness_error_profile_files=None if self.has_thickness_error==0 else self.crl_error_profiles,
                      scaling_factor=self.crl_scaling_factor)

    def parse_void_center_coordinates(self):
        if self.void_center_coordinates.strip() == "":
            return None

        else:
            void_center_coordinates = []
            tokens = self.void_center_coordinates.strip().split(",")

            for token in tokens:
                void_center_coordinates.append(float(token))

            return void_center_coordinates

    def check_data(self):
        super().check_data()

        if self.material_data==0:
            self.material = congruence.checkEmptyString(self.material, "Chemical Formula")
        else:
            congruence.checkStrictlyPositiveNumber(self.refractive_index, "Refractive Index")
            congruence.checkStrictlyPositiveNumber(self.attenuation_length, "Attenuation Length")

        congruence.checkStrictlyPositiveNumber(self.diameter, "Diameter")
        congruence.checkStrictlyPositiveNumber(self.radius_of_curvature, "Radius of Curvature")
        congruence.checkStrictlyPositiveNumber(self.number_of_lenses, "Number of Lenses")
        congruence.checkStrictlyPositiveNumber(self.wall_thickness, "Wall Thickness")

        congruence.checkStrictlyPositiveNumber(self.horizontal_points, "Horizontal Points")
        congruence.checkStrictlyPositiveNumber(self.vertical_points, "Vertical Points")

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError("This element is not supported by Syned")
