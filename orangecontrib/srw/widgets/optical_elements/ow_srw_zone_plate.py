import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from wofrysrw.beamline.optical_elements.other.srw_zone_plate import SRWZonePlate

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement

class OWSRWZonePlate(OWSRWOpticalElement):

    name = "Zone Plate"
    description = "SRW: Zone Plate"
    icon = "icons/zone_plate.png"
    priority = 15

    total_number_of_zones=Setting(100)
    outer_zone_radius=Setting(0.1e-03)
    thickness=Setting(10e-06)
    delta_main_material=Setting(1e-06)
    delta_complementary_material=Setting(0.0)
    attenuation_length_main_material=Setting(0.1)
    attenuation_length_complementary_material=Setting(1e-06)
    x = Setting(0.0)
    y = Setting(0.0)

    def __init__(self):
        super().__init__(has_orientation_angles=False)


    def draw_specific_box(self):
        self.filter_box = oasysgui.widgetBox(self.tab_bas, "Zone Plate Setting", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.filter_box, self, "total_number_of_zones", "Total Number of Zones", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "outer_zone_radius", "Outer Zone Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "thickness", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.filter_box)
        
        oasysgui.lineEdit(self.filter_box, self, "x", "Horizontal coordinate of center [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "y", "Vertical coordinate of center [m]", labelWidth=260, valueType=float, orientation="horizontal")
        
        gui.separator(self.filter_box)

        material_box = oasysgui.widgetBox(self.filter_box, "Materials", addSpace=True, orientation="vertical")
        
        gui.label(material_box, self, "\"Main\":")
        oasysgui.lineEdit(material_box, self, "delta_main_material", "Refractive index decrement", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "attenuation_length_main_material", "Attenuation length [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(material_box)
        gui.label(material_box, self, "\"Complementary\":")
        oasysgui.lineEdit(material_box, self, "delta_complementary_material", "Refractive index decrement", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(material_box, self, "attenuation_length_complementary_material", "Attenuation length [m]", labelWidth=260, valueType=float, orientation="horizontal")

    def get_optical_element(self):
        return SRWZonePlate(name=self.oe_name,
                            total_number_of_zones=self.total_number_of_zones,
                            outer_zone_radius=self.outer_zone_radius,
                            thickness=self.thickness,
                            delta_main_material=self.delta_main_material,
                            delta_complementary_material=self.delta_complementary_material,
                            attenuation_length_main_material=self.attenuation_length_main_material,
                            attenuation_length_complementary_material=self.attenuation_length_complementary_material,
                            x=self.x,
                            y=self.y)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.total_number_of_zones, "Total Number of Zones")
        congruence.checkStrictlyPositiveNumber(self.outer_zone_radius, "Outer Zone Radius")
        congruence.checkStrictlyPositiveNumber(self.thickness, "Thickness")
        congruence.checkPositiveNumber(self.delta_main_material, "Main Material: Refractive index decrement")
        congruence.checkPositiveNumber(self.delta_complementary_material, "Complementary Material: Refractive index decrement")
        congruence.checkPositiveNumber(self.attenuation_length_main_material, "Main Material: Attenuation length")
        congruence.checkPositiveNumber(self.attenuation_length_complementary_material, "Complementary Material: Attenuation length")

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError("This element is not supported by Syned")



