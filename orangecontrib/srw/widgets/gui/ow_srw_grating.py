import numpy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerOut

from syned.beamline.optical_elements.gratings.grating import Grating
from syned.widget.widget_decorator import WidgetDecorator

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement
from orangecontrib.srw.util.srw_util import ShowErrorProfileDialog
from orangecontrib.srw.util.srw_objects import SRWData, SRWPreProcessorData, SRWErrorProfileData

class OWSRWGrating(OWSRWOpticalElement):

    tangential_size                    = Setting(1.2)
    sagittal_size                      = Setting(0.01)
    horizontal_position_of_mirror_center = Setting(0.0)
    vertical_position_of_mirror_center = Setting(0.0)

    add_acceptance_slit = Setting(0)

    has_height_profile = Setting(0)
    height_profile_data_file           = Setting("mirror.dat")
    height_profile_data_file_dimension = Setting(0)
    height_amplification_coefficient   = Setting(1.0)

    diffraction_order                  = Setting(1)
    grooving_density_0                 = Setting(800.0) # groove density [lines/mm] (coefficient a0 in the polynomial groove density: a0 + a1*y + a2*y^2 + a3*y^3 + a4*y^4)
    grooving_density_1                 = Setting(0.0) # groove density polynomial coefficient a1 [lines/mm\u00b2]
    grooving_density_2                 = Setting(0.0) # groove density polynomial coefficient a2 [lines/mm\u00b3]
    grooving_density_3                 = Setting(0.0) # groove density polynomial coefficient a3 [lines/mm\u2074]
    grooving_density_4                 = Setting(0.0)  # groove density polynomial coefficient a4 [lines/mm\u2075]
    grooving_angle                     = Setting(0.0)  # angle between the groove direction and the sagittal direction of the substrate

    inputs = [("SRWData", SRWData, "set_input"),
              ("Trigger", TriggerOut, "propagate_new_wavefront"),
              ("PreProcessor Data", SRWPreProcessorData, "setPreProcessorData"),
              WidgetDecorator.syned_input_data()[0]]

    def __init__(self):
        super().__init__(azimuth_hor_vert=True)

    def draw_specific_box(self):

        tabs_grat = oasysgui.tabWidget(self.tab_bas)

        tab_grat = oasysgui.createTabPage(tabs_grat, "Grating")
        tab_errp = oasysgui.createTabPage(tabs_grat, "Error Profile")

        self.grating_setting = oasysgui.tabWidget(tab_grat)
        
        substrate_tab = oasysgui.createTabPage(self.grating_setting, "Substrate Mirror Setting")
        grooving_tab = oasysgui.createTabPage(self.grating_setting, "Grooving Setting")

        self.substrate_box = oasysgui.widgetBox(substrate_tab, "", addSpace=False, orientation="vertical")
        self.grooving_box = oasysgui.widgetBox(grooving_tab, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.substrate_box, self, "tangential_size", "Tangential Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.substrate_box, self, "sagittal_size", "Sagittal_Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.substrate_box, self, "horizontal_position_of_mirror_center", "Horizontal position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.substrate_box, self, "vertical_position_of_mirror_center", "Vertical position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.substrate_box, self, "add_acceptance_slit", label="Add Acceptance Slit",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.grooving_box, self, "diffraction_order", "Diffraction order", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.grooving_box, self, "grooving_angle", "Angle between groove direction and\nsagittal direction of the substrate [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.grooving_box, self, "grooving_density_0", "Groove density [lines/mm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.grooving_box, self, "grooving_density_1", "Groove den. poly. coeff. a1 [lines/mm\u00b2]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.grooving_box, self, "grooving_density_2", "Groove den. poly. coeff. a2 [lines/mm\u00b3]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.grooving_box, self, "grooving_density_3", "Groove den. poly. coeff. a3 [lines/mm\u2074]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.grooving_box, self, "grooving_density_4", "Groove den. poly. coeff. a4 [lines/mm\u2075]", labelWidth=260, valueType=float, orientation="horizontal")


        self.error_box = oasysgui.widgetBox(tab_errp, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.error_box, self, "has_height_profile", label="Use Height Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_HeightProfile)

        gui.separator(self.error_box)

        self.height_profile_box_1 = oasysgui.widgetBox(self.error_box, "", addSpace=False, orientation="vertical", height=110)
        self.height_profile_box_2 = oasysgui.widgetBox(self.error_box, "", addSpace=False, orientation="vertical", height=110)

        file_box =  oasysgui.widgetBox(self.height_profile_box_2, "", addSpace=False, orientation="horizontal")

        self.le_height_profile_data_file = oasysgui.lineEdit(file_box, self, "height_profile_data_file", "Height profile data file", labelWidth=155, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectHeightProfileDataFile)

        file_box_2 =  oasysgui.widgetBox(self.height_profile_box_2, "", addSpace=False, orientation="horizontal")

        gui.comboBox(file_box_2, self, "height_profile_data_file_dimension", label="Dimension",
                     items=["1", "2"], labelWidth=280,
                     sendSelectedValue=False, orientation="horizontal")

        gui.button(file_box_2, self, "View", callback=self.view_height_profile)

        oasysgui.lineEdit(self.height_profile_box_2, self, "height_amplification_coefficient", "Height Amplification Coefficient", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_HeightProfile()

    def selectHeightProfileDataFile(self):
        self.le_height_profile_data_file.setText(oasysgui.selectFileFromDialog(self, self.height_profile_data_file, "Height profile data file"))

    def set_HeightProfile(self):
        self.height_profile_box_1.setVisible(self.has_height_profile==0)
        self.height_profile_box_2.setVisible(self.has_height_profile==1)

    def get_optical_element(self):
        grating = self.get_grating_instance()

        grating.tangential_size=self.tangential_size
        grating.sagittal_size=self.sagittal_size
        grating.grazing_angle=numpy.radians(90-self.angle_radial)
        grating.orientation_of_reflection_plane=self.orientation_azimuthal
        grating.invert_tangent_component = self.invert_tangent_component == 1
        grating.add_acceptance_slit=self.add_acceptance_slit == 1
        grating.height_profile_data_file=self.height_profile_data_file if self.has_height_profile else None
        grating.height_profile_data_file_dimension=self.height_profile_data_file_dimension + 1
        grating.height_amplification_coefficient=self.height_amplification_coefficient
        grating.diffraction_order=self.diffraction_order
        grating.grooving_density_0=self.grooving_density_0
        grating.grooving_density_1=self.grooving_density_1
        grating.grooving_density_2=self.grooving_density_2
        grating.grooving_density_3=self.grooving_density_3
        grating.grooving_density_4=self.grooving_density_4
        grating.grooving_angle=numpy.radians(self.grooving_angle)

        return grating

    def set_additional_parameters(self, beamline_element, propagation_parameters, beamline):
        grating = beamline.get_beamline_element_at(-1).get_optical_element()

        orientation_of_the_output_optical_axis_vector_x, \
        orientation_of_the_output_optical_axis_vector_y, \
        orientation_of_the_output_optical_axis_vector_z, \
        orientation_of_the_horizontal_base_vector_x    , \
        orientation_of_the_horizontal_base_vector_y     = grating.get_output_orientation_vectors(self.input_srw_data.get_srw_wavefront().get_photon_energy())

        self.oe_orientation_of_the_output_optical_axis_vector_x = round(orientation_of_the_output_optical_axis_vector_x, 8)
        self.oe_orientation_of_the_output_optical_axis_vector_y = round(orientation_of_the_output_optical_axis_vector_y, 8)
        self.oe_orientation_of_the_output_optical_axis_vector_z = round(orientation_of_the_output_optical_axis_vector_z, 8)
        self.oe_orientation_of_the_horizontal_base_vector_x     = round(orientation_of_the_horizontal_base_vector_x, 8)
        self.oe_orientation_of_the_horizontal_base_vector_y     = round(orientation_of_the_horizontal_base_vector_y, 8)

        super(OWSRWGrating, self).set_additional_parameters(beamline_element, propagation_parameters, beamline)

    def get_grating_instance(self):
        raise NotImplementedError()

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if isinstance(optical_element, Grating):
                boundaries = optical_element._boundary_shape.get_boundaries()

                self.tangential_size=round(abs(boundaries[3] - boundaries[2]), 6)
                self.sagittal_size=round(abs(boundaries[1] - boundaries[0]), 6)

                self.vertical_position_of_mirror_center = round(0.5*(boundaries[3] + boundaries[2]), 6)
                self.horizontal_position_of_mirror_center = round(0.5*(boundaries[1] + boundaries[0]), 6)
                
                self.grooving_density_0=optical_element._ruling*1e-3
                
                self.receive_shape_specific_syned_data(optical_element)
            else:
                raise Exception("Syned Data not correct: Optical Element is not a Grating")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")

    def receive_shape_specific_syned_data(self, optical_element):
        raise NotImplementedError


    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.tangential_size, "Tangential Size")
        congruence.checkStrictlyPositiveNumber(self.sagittal_size, "Sagittal Size")

        if self.has_height_profile:
            congruence.checkFile(self.height_profile_data_file)

        congruence.checkPositiveNumber(self.diffraction_order, "Diffraction Order")
        congruence.checkStrictlyPositiveNumber(self.grooving_density_0, "Groove density")

    def setPreProcessorData(self, data):
        if data is not None:
            try:
                if not data.error_profile_data is None:
                    if data.error_profile_data.error_profile_data_file != SRWErrorProfileData.NONE:
                        self.height_profile_data_file = data.error_profile_data.error_profile_data_file
                        self.height_profile_data_file_dimension = 1
                        self.has_height_profile = 1
        
                        self.set_HeightProfile()
        
                        changed = False
        
                        if self.sagittal_size > data.error_profile_data.error_profile_x_dim or \
                           self.tangential_size > data.error_profile_data.error_profile_y_dim:
                            changed = True
        
                        if changed:
                            if QMessageBox.information(self, "Confirm Modification",
                                                          "Dimensions of this O.E. must be changed in order to ensure congruence with the error profile surface, accept?",
                                                          QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                                if self.sagittal_size > data.error_profile_data.error_profile_x_dim:
                                    self.sagittal_size = data.error_profile_data.error_profile_x_dim
                                if self.tangential_size > data.error_profile_data.error_profile_y_dim:
                                    self.tangential_size = data.error_profile_data.error_profile_y_dim
        
                                QMessageBox.information(self, "QMessageBox.information()",
                                                              "Dimensions of this O.E. were changed",
                                                              QMessageBox.Ok)
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def view_height_profile(self):
        pass
        try:
            dialog = ShowErrorProfileDialog(parent=self,
                                            file_name=self.height_profile_data_file,
                                            dimension=self.height_profile_data_file_dimension+1)
            dialog.show()
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

