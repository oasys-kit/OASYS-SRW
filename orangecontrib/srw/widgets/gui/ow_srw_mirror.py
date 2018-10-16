import numpy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.beamline.optical_elements.mirrors.mirror import Mirror
from syned.widget.widget_decorator import WidgetDecorator
from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import ScaleType

from orangecontrib.srw.util.srw_objects import SRWData, SRWPreProcessorData, SRWErrorProfileData, SRWReflectivityData
from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement


class OWSRWMirror(OWSRWOpticalElement):

    tangential_size                    = Setting(1.2)
    sagittal_size                      = Setting(0.01)
    horizontal_position_of_mirror_center = Setting(0.0)
    vertical_position_of_mirror_center = Setting(0.0)

    has_height_profile = Setting(0)
    height_profile_data_file           = Setting("mirror.dat")
    height_profile_data_file_dimension = Setting(0)
    height_amplification_coefficient   = Setting(1.0)

    has_reflectivity = Setting(0)

    reflectivity_value = Setting(0.95)
    reflectivity_data_file = Setting("reflectivity.dat")

    reflectivity_energies_number = Setting(100)
    reflectivity_angles_number = Setting(100)
    reflectivity_components_number = Setting(0)

    reflectivity_energy_start = Setting(100.0)
    reflectivity_energy_end = Setting(10000.0)
    reflectivity_energy_scale_type = Setting(0)

    reflectivity_angle_start = Setting(0.001)
    reflectivity_angle_end = Setting(0.005)
    reflectivity_angle_scale_type = Setting(0)

    inputs = [("SRWData", SRWData, "set_input"),
              ("PreProcessor Data #1", SRWPreProcessorData, "setPreProcessorData"),
              ("PreProcessor Data #2", SRWPreProcessorData, "setPreProcessorData"),
              WidgetDecorator.syned_input_data()[0]]

    def __init__(self):
        super().__init__(azimuth_hor_vert=True)

    def draw_specific_box(self):

        tabs_mirr = oasysgui.tabWidget(self.tab_bas)

        tab_mirr = oasysgui.createTabPage(tabs_mirr, "Mirror")
        tab_errp = oasysgui.createTabPage(tabs_mirr, "Error Profile")
        tab_refl = oasysgui.createTabPage(tabs_mirr, "Reflectivity")

        self.mirror_box = oasysgui.widgetBox(tab_mirr, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.mirror_box, self, "tangential_size", "Tangential Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "sagittal_size", "Sagittal_Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "horizontal_position_of_mirror_center", "Horizontal position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "vertical_position_of_mirror_center", "Vertical position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.mirror_box)

        self.error_box = oasysgui.widgetBox(tab_errp, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.error_box, self, "has_height_profile", label="Use Height Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_HeightProfile)

        gui.separator(self.error_box)

        self.height_profile_box_1 = oasysgui.widgetBox(self.error_box, "", addSpace=False, orientation="vertical", height=80)

        self.height_profile_box_2 = oasysgui.widgetBox(self.error_box, "", addSpace=False, orientation="vertical", height=80)

        file_box =  oasysgui.widgetBox(self.height_profile_box_2, "", addSpace=False, orientation="horizontal")

        self.le_height_profile_data_file = oasysgui.lineEdit(file_box, self, "height_profile_data_file", "Height profile data file", labelWidth=185, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectHeightProfileDataFile)

        gui.comboBox(self.height_profile_box_2, self, "height_profile_data_file_dimension", label="Dimension",
                     items=["1", "2"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.height_profile_box_2, self, "height_amplification_coefficient", "Height Amplification Coefficient", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_HeightProfile()

        self.reflectivity_box = oasysgui.widgetBox(tab_refl, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.reflectivity_box, self, "has_reflectivity", label="Use Reflectivity",
                     items=["No", "Single Value", "R vs E vs \u03b1 (vs \u03c3/\u03c0)"], labelWidth=200,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_Reflectivity)

        gui.separator(self.reflectivity_box)

        self.reflectivity_box_1 = oasysgui.widgetBox(self.reflectivity_box, "", addSpace=False, orientation="vertical", height=200)

        self.reflectivity_box_2 = oasysgui.widgetBox(self.reflectivity_box, "", addSpace=False, orientation="vertical", height=200)

        oasysgui.lineEdit(self.reflectivity_box_2, self, "reflectivity_value", "Reflectivity Value", labelWidth=260, valueType=float, orientation="horizontal")

        self.reflectivity_box_3 = oasysgui.widgetBox(self.reflectivity_box, "", addSpace=False, orientation="vertical", height=270)

        file_box =  oasysgui.widgetBox(self.reflectivity_box_3, "", addSpace=False, orientation="horizontal")

        self.le_reflectivity_data_file = oasysgui.lineEdit(file_box, self, "reflectivity_data_file", "Reflectivity data file", labelWidth=185, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectReflectivityDataFile)

        gui.separator(self.reflectivity_box_3)

        oasysgui.lineEdit(self.reflectivity_box_3, self, "reflectivity_energies_number", "Number of Energy Values", labelWidth=260, valueType=int, orientation="horizontal")

        energy_box = oasysgui.widgetBox(self.reflectivity_box_3, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(energy_box, self, "reflectivity_energy_start", "Energy Values [eV]: Initial", labelWidth=160, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(energy_box, self, "reflectivity_energy_end", "Final", labelWidth=50, valueType=float, orientation="horizontal")

        gui.comboBox(self.reflectivity_box_3, self, "reflectivity_energy_scale_type", label="Energy Scale Type",
                     items=["Linear", "Logarithmic"], labelWidth=250,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.reflectivity_box_3)

        oasysgui.lineEdit(self.reflectivity_box_3, self, "reflectivity_angles_number", "Number of Grazing Angle Values", labelWidth=260, valueType=int, orientation="horizontal")

        angle_box = oasysgui.widgetBox(self.reflectivity_box_3, "", addSpace=False, orientation="horizontal")

        oasysgui.lineEdit(angle_box, self, "reflectivity_angle_start", "Gr. Ang. Values [rad]: Initial", labelWidth=170, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(angle_box, self, "reflectivity_angle_end", "Final", labelWidth=40, valueType=float, orientation="horizontal")

        gui.comboBox(self.reflectivity_box_3, self, "reflectivity_angle_scale_type", label="Grazing Angle Scale Type",
                     items=["Linear", "Logarithmic"], labelWidth=250,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.reflectivity_box_3)

        gui.comboBox(self.reflectivity_box_3, self, "reflectivity_components_number", label="Polarization",
                     items=["Total", "\u03c3/\u03c0"], labelWidth=280,
                     sendSelectedValue=False, orientation="horizontal")


        self.set_Reflectivity()

    def selectHeightProfileDataFile(self):
        self.le_height_profile_data_file.setText(oasysgui.selectFileFromDialog(self, self.height_profile_data_file, "Height profile data file"))

    def selectReflectivityDataFile(self):
        self.le_reflectivity_data_file.setText(oasysgui.selectFileFromDialog(self, self.reflectivity_data_file, "Reflectivity data file"))

    def set_HeightProfile(self):
        self.height_profile_box_1.setVisible(self.has_height_profile==0)
        self.height_profile_box_2.setVisible(self.has_height_profile==1)

    def set_Reflectivity(self):
        self.reflectivity_box_1.setVisible(self.has_reflectivity==0)
        self.reflectivity_box_2.setVisible(self.has_reflectivity==1)
        self.reflectivity_box_3.setVisible(self.has_reflectivity==2)

    def get_optical_element(self):
        
        mirror = self.get_mirror_instance()

        mirror.tangential_size=self.tangential_size
        mirror.sagittal_size=self.sagittal_size
        mirror.grazing_angle=numpy.radians(90-self.angle_radial)
        mirror.orientation_of_reflection_plane=self.orientation_azimuthal
        mirror.invert_tangent_component = self.invert_tangent_component == 1
        mirror.height_profile_data_file=self.height_profile_data_file if self.has_height_profile else None
        mirror.height_profile_data_file_dimension=self.height_profile_data_file_dimension + 1
        mirror.height_amplification_coefficient=self.height_amplification_coefficient

        if self.has_reflectivity == 1:
            mirror.set_reflectivity(reflectivity_data=self.reflectivity_value)
        elif self.has_reflectivity == 2:
            mirror.set_reflectivity(reflectivity_data=self.read_reflectivity_data_file(),
                                    energies_number=self.reflectivity_energies_number,
                                    angles_number=self.reflectivity_angles_number,
                                    components_number=self.reflectivity_components_number + 1,
                                    energy_start=self.reflectivity_energy_start,
                                    energy_end=self.reflectivity_energy_end,
                                    energy_scale_type=ScaleType.LINEAR if self.reflectivity_energy_scale_type==0 else ScaleType.LOGARITHMIC,
                                    angle_start=self.reflectivity_angle_start,
                                    angle_end=self.reflectivity_angle_end,
                                    angle_scale_type=ScaleType.LINEAR if self.reflectivity_angle_scale_type==0 else ScaleType.LOGARITHMIC)

        return mirror



    def read_reflectivity_data_file(self):
        return numpy.loadtxt(self.reflectivity_data_file).tolist()

    def get_mirror_instance(self):
        raise NotImplementedError()

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if isinstance(optical_element, Mirror):
                boundaries = optical_element._boundary_shape.get_boundaries()

                self.tangential_size=round(abs(boundaries[3] - boundaries[2]), 6)
                self.sagittal_size=round(abs(boundaries[1] - boundaries[0]), 6)

                self.vertical_position_of_mirror_center = round(0.5*(boundaries[3] + boundaries[2]), 6)
                self.horizontal_position_of_mirror_center = round(0.5*(boundaries[1] + boundaries[0]), 6)

                self.receive_shape_specific_syned_data(optical_element)
            else:
                raise Exception("Syned Data not correct: Optical Element is not a Mirror")
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

        if self.has_reflectivity == 1:
            congruence.checkStrictlyPositiveNumber(self.reflectivity_value, "Reflectivity Value")
        elif self.has_reflectivity == 2:
            congruence.checkFile(self.reflectivity_data_file)

            congruence.checkStrictlyPositiveNumber(self.reflectivity_energies_number, "Number of Energy Values")
            congruence.checkStrictlyPositiveNumber(self.reflectivity_energy_start, "Initial Energy Value")
            congruence.checkStrictlyPositiveNumber(self.reflectivity_energy_end, "Final Energy Value")
            congruence.checkGreaterOrEqualThan(self.reflectivity_energy_end, self.reflectivity_energy_start, "Final Energy Value", "Initial Energy Value")

            congruence.checkStrictlyPositiveNumber(self.reflectivity_angles_number, "Number of Grazing Angle Values")
            congruence.checkStrictlyPositiveNumber(self.reflectivity_angle_start, "Initial Grazing Angle Value")
            congruence.checkStrictlyPositiveNumber(self.reflectivity_angle_end, "Final Grazing Angle Value")
            congruence.checkGreaterOrEqualThan(self.reflectivity_angle_end, self.reflectivity_angle_start, "Final Grazing Angle Value", "Initial Grazing Angle Value")

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
                if not data.reflectivity_data is None:    
                    if data.reflectivity_data.reflectivity_data_file != SRWReflectivityData.NONE:
                        self.has_reflectivity=2
                        self.reflectivity_data_file=data.reflectivity_data.reflectivity_data_file
                        self.reflectivity_energies_number=data.reflectivity_data.energies_number
                        self.reflectivity_angles_number=data.reflectivity_data.angles_number
                        self.reflectivity_components_number=data.reflectivity_data.components_number-1
                        self.reflectivity_energy_start=data.reflectivity_data.energy_start
                        self.reflectivity_energy_end=data.reflectivity_data.energy_end
                        self.reflectivity_energy_scale_type=0 if data.reflectivity_data.energy_scale_type==ScaleType.LINEAR else 1
                        self.reflectivity_angle_start=data.reflectivity_data.angle_start
                        self.reflectivity_angle_end=data.reflectivity_data.angle_end
                        self.reflectivity_angle_scale_type=0 if data.reflectivity_data.angle_scale_type==ScaleType.LINEAR else 1

                        self.set_Reflectivity()
                        
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)
    
