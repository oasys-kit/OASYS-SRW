import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.beamline.optical_elements.mirrors.mirror import Mirror

from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import SRWMirror, Orientation


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

    def __init__(self):
        super().__init__(azimuth_hor_vert=True)

    def draw_specific_box(self):
        self.mirror_box = oasysgui.widgetBox(self.tab_bas, "Mirror Setting", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.mirror_box, self, "tangential_size", "Tangential Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "sagittal_size", "Sagittal_Size [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "horizontal_position_of_mirror_center", "Horizontal position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "vertical_position_of_mirror_center", "Vertical position of mirror center [m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(self.mirror_box, self, "has_height_profile", label="Use Height Error Profile",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_HeightProfile)

        self.height_profile_box_1 = oasysgui.widgetBox(self.mirror_box, "", addSpace=False, orientation="vertical", height=100)

        self.height_profile_box_2 = oasysgui.widgetBox(self.mirror_box, "", addSpace=False, orientation="vertical", height=100)

        file_box =  oasysgui.widgetBox(self.height_profile_box_2, "", addSpace=False, orientation="horizontal")

        self.le_height_profile_data_file = oasysgui.lineEdit(file_box, self, "height_profile_data_file", "Height profile data file", labelWidth=185, valueType=str, orientation="horizontal")
        gui.button(file_box, self, "...", callback=self.selectHeightProfileDataFile)

        gui.comboBox(self.height_profile_box_2, self, "height_profile_data_file_dimension", label="Dimension",
                     items=["1", "2"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.height_profile_box_2, self, "height_amplification_coefficient", "Height Amplification Coefficient", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_HeightProfile()

    def selectHeightProfileDataFile(self):
        self.le_height_profile_data_file.setText(oasysgui.selectFileFromDialog(self, self.height_profile_data_file, "Height profile data file"))

    def set_HeightProfile(self):
        self.height_profile_box_1.setVisible(self.has_height_profile==0)
        self.height_profile_box_2.setVisible(self.has_height_profile==1)

    def get_optical_element(self):
        
        mirror = self.get_mirror_instance()
        
        mirror.name=self.oe_name
        mirror.tangential_size=self.tangential_size
        mirror.sagittal_size=self.sagittal_size
        mirror.grazing_angle=numpy.radians(90-self.angle_radial)
        mirror.orientation_of_reflection_plane=self.orientation_azimuthal
        mirror.height_profile_data_file=self.height_profile_data_file if self.has_height_profile else None
        mirror.height_profile_data_file_dimension=self.height_profile_data_file_dimension + 1
        mirror.height_amplification_coefficient=self.height_amplification_coefficient
        
        return mirror
        
    def get_mirror_instance(self):
        return SRWMirror()

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




