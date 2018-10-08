import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from wofrysrw.beamline.optical_elements.other.srw_crl import CRLShape, PlaneOfFocusing, SRWCRL

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement

class OWSRWCRL(OWSRWOpticalElement):

    name = "CRL"
    description = "SRW: CRL"
    icon = "icons/crl.png"
    priority = 16

    plane_of_focusing = Setting(2)
    refractive_index = Setting(1e-6)
    attenuation_length = Setting(1e-3)
    shape = Setting(0)
    horizontal_aperture_size = Setting(1e-3)
    vertical_aperture_size = Setting(1e-3)
    radius_of_curvature = Setting(5e-3)
    number_of_lenses = Setting(10)
    wall_thickness = Setting(5e-5)
    horizontal_center_coordinate = Setting(0.0)
    vertical_center_coordinate = Setting(0.0)
    void_center_coordinates = Setting("")
    initial_photon_energy = Setting(0.0)
    final_photon_energy = Setting(0.0)
    horizontal_points = Setting(1001)
    vertical_points = Setting(1001)

    def __init__(self):
        super().__init__(has_orientation_angles=False)


    def draw_specific_box(self):
        self.filter_box = oasysgui.widgetBox(self.tab_bas, "CRL Setting", addSpace=False, orientation="vertical")

        gui.comboBox(self.filter_box, self, "plane_of_focusing", label="Plane of Focusing",
                     labelWidth=220, items=PlaneOfFocusing.items(), sendSelectedValue=False, orientation="horizontal")


        oasysgui.lineEdit(self.filter_box, self, "refractive_index", "Refractive Index (\u03b4)", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "attenuation_length", "Attenuation Lenght [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.filter_box, self, "shape", label="Shape",
                     labelWidth=220, items=CRLShape.items(), sendSelectedValue=False, orientation="horizontal")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(box, self, "horizontal_aperture_size", "Aperture Size H [m]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "vertical_aperture_size", "V [m]", labelWidth=90, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box, self, "radius_of_curvature", "Radius of Curvature [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "number_of_lenses", "Number of Lenses", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "wall_thickness", "Wall Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(box, self, "horizontal_center_coordinate", "Center Coord. H [m]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "vertical_center_coordinate", "V [m]", labelWidth=90, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box, self, "void_center_coordinates", "Void center coordinates [m] (x1, y1, r1, x2, y2, r2, ...)", labelWidth=350, valueType=str, orientation="vertical")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(box, self, "initial_photon_energy", "Ph. Energy Initial [eV]", labelWidth=130, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box, self, "final_photon_energy", "Final [eV]", labelWidth=90, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(self.filter_box, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(box, self, "horizontal_points", "H Points", labelWidth=130, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box, self, "vertical_points", "V Points", labelWidth=90, valueType=int, orientation="horizontal")

        gui.separator(self.filter_box)


    def get_optical_element(self):
        return SRWCRL(name=self.oe_name,
                      plane_of_focusing=self.plane_of_focusing+1,
                      refractive_index=self.refractive_index,
                      attenuation_length=self.attenuation_length,
                      shape=self.shape+1,
                      horizontal_aperture_size=self.horizontal_aperture_size,
                      vertical_aperture_size=self.vertical_aperture_size,
                      radius_of_curvature=self.radius_of_curvature,
                      number_of_lenses=self.number_of_lenses,
                      wall_thickness=self.wall_thickness,
                      horizontal_center_coordinate=self.horizontal_center_coordinate,
                      vertical_center_coordinate=self.vertical_center_coordinate,
                      void_center_coordinates=self.parse_void_center_coordinates(),
                      initial_photon_energy=self.initial_photon_energy,
                      final_photon_energy=self.final_photon_energy,
                      horizontal_points=self.horizontal_points,
                      vertical_points=self.vertical_points)

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

        congruence.checkStrictlyPositiveNumber(self.refractive_index, "Refractive Index")
        congruence.checkStrictlyPositiveNumber(self.attenuation_length, "Attenuation Length")
        congruence.checkStrictlyPositiveNumber(self.horizontal_aperture_size, "Horizontal Aperture Size")
        congruence.checkStrictlyPositiveNumber(self.vertical_aperture_size, "Vertical Aperture Size")

        congruence.checkStrictlyPositiveNumber(self.radius_of_curvature, "Radius of Curvature")
        congruence.checkStrictlyPositiveNumber(self.number_of_lenses, "Number of Lenses")
        congruence.checkStrictlyPositiveNumber(self.wall_thickness, "Wall Thickness")

        congruence.checkPositiveNumber(self.initial_photon_energy, "Initial Photon Energy")
        congruence.checkPositiveNumber(self.final_photon_energy, "Final Photon Energy")

        if self.initial_photon_energy > 0.0:
            congruence.checkGreaterOrEqualThan(self.final_photon_energy, self.initial_photon_energy, "Final Photon Energy", "Initial Photon Energy")

        congruence.checkStrictlyPositiveNumber(self.horizontal_points, "Horizontal Points")
        congruence.checkStrictlyPositiveNumber(self.vertical_points, "Vertical Points")

    def receive_specific_syned_data(self, optical_element):
        raise NotImplementedError("This element is not supported by Syned")



