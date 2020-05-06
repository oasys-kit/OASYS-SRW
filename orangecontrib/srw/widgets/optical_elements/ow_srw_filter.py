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
from orangecontrib.srw.util.srw_util import get_absorption_parameters
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

    material_data = Setting(0)
    material = Setting("Be")
    refractive_index = Setting(1e-6)
    attenuation_length = Setting(1e-3)
    thickness = Setting(500)
    has_thickness_error = Setting(0)
    thickness_error_profile = Setting("")
    scaling_factor = Setting(1.0)

    def __init__(self):
        super().__init__(has_orientation_angles=False)

    def draw_specific_box(self):
        material_box = oasysgui.widgetBox(self.tab_bas, "Material", addSpace=True, orientation="vertical")

        gui.comboBox(material_box, self, "material_data", label="Material Properties from", labelWidth=180,
                             items=["Chemical Formula", "Absorption Parameters"],
                             callback=self.set_MaterialData,
                             sendSelectedValue=False, orientation="horizontal")

        self.filter_box_1 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="vertical", height=30, width=self.CONTROL_AREA_WIDTH-40)
        self.filter_box_2 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="horizontal", height=30, width=self.CONTROL_AREA_WIDTH-40)

        oasysgui.lineEdit(self.filter_box_1, self, "material", "Chemical Formula", labelWidth=260, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(self.filter_box_2, self, "refractive_index", "Refr. Index (\u03b4)", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box_2, self, "attenuation_length", "Att. Lenght [m]", valueType=float, orientation="horizontal")

        self.set_MaterialData()

        oasysgui.lineEdit(material_box, self, "thickness", "Thickness [\u03bcm]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(material_box, self, "has_thickness_error", label="Use Thickness Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_ThicknessError)

        gui.separator(material_box)

        self.error_box_1 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="vertical", height=60)
        self.error_box_2 = oasysgui.widgetBox(material_box, "", addSpace=False, orientation="vertical", height=60)

        file_box =  oasysgui.widgetBox(self.error_box_2, "", addSpace=False, orientation="horizontal")

        self.le_thickness_error_profile = oasysgui.lineEdit(file_box, self, "thickness_error_profile", "Error data file", labelWidth=100, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectThicknessErrorProfile)

        oasysgui.lineEdit(self.error_box_2, self, "scaling_factor", "Error Scaling Factor", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_ThicknessError()

    def set_MaterialData(self):
        self.filter_box_1.setVisible(self.material_data==0)
        self.filter_box_2.setVisible(self.material_data==1)

    def set_ThicknessError(self):
        self.error_box_1.setVisible(self.has_thickness_error == 0)
        self.error_box_2.setVisible(self.has_thickness_error == 1)

    def selectThicknessErrorProfile(self):
        self.le_thickness_error_profile.setText(oasysgui.selectFileFromDialog(self, self.thickness_error_profile, "Thickness error data file", file_extension_filter="*.h5"))

    def get_optical_element(self):
        wavefront = self.input_srw_data.get_srw_wavefront()
        energy    = wavefront.get_photon_energy()
        mesh      = wavefront.mesh

        if self.material_data==0:
            material                  = self.material
            attenuation_length, delta = get_absorption_parameters(self.material, energy)
        else:
            material           = None
            delta              = self.refractive_index
            attenuation_length = self.attenuation_length

        return SRWFilter(name=self.name,
                         material=material,
                         thickness=self.thickness*1e-6,
                         attenuation_length=attenuation_length,
                         delta=delta,
                         x_range=[mesh.xStart, mesh.xFin],
                         y_range=[mesh.yStart, mesh.yFin],
                         n_points_x=mesh.nx,
                         n_points_y=mesh.ny,
                         energy=energy,
                         thickness_error_profile_file=None if self.has_thickness_error == 0 else self.thickness_error_profile,
                         scaling_factor=self.scaling_factor)

    def check_data(self):
        super().check_data()

        congruence.checkEmptyString(self.material, "Material")
        congruence.checkStrictlyPositiveNumber(self.thickness, "Thickness")

        if self.has_thickness_error == 1:
            congruence.checkFile(self.thickness_error_profile)
            congruence.checkStrictlyPositiveNumber(self.scaling_factor, "Scaling Factor")

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
            QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception
