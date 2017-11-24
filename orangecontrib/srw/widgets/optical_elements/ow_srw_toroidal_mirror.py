import numpy

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.beamline.shape import Toroidal

from wofrysrw.beamline.optical_elements.mirrors.srw_toroidal_mirror import SRWToroidalMirror

from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWToroidallMirror(OWSRWMirror):

    name = "Toroidal Mirror"
    description = "SRW: Toroidal Mirror"
    icon = "icons/toroidal_mirror.png"
    priority = 5

    tangential_radius  = Setting(1.0)
    sagittal_radius = Setting(1.0)

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWToroidalMirror(tangential_radius=self.tangential_radius,
                                   sagittal_radius=self.sagittal_radius)

    def draw_specific_box(self):
        super().draw_specific_box()

        oasysgui.lineEdit(self.mirror_box, self, "tangential_radius", "Tangential Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "sagittal_radius", "Sagittal Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element._surface_shape, Toroidal):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Toroidal")

        self.tangential_radius = numpy.round(optical_element._surface_shape._maj_radius, 6)
        self.sagittal_radius = numpy.round(optical_element._surface_shape._min_radius, 6)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.tangential_radius,  "Tangential Radius")
        congruence.checkStrictlyPositiveNumber(self.sagittal_radius, "Sagittal Radius")
