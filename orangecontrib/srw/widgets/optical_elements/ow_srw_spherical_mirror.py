import numpy

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.beamline.shape import Sphere

from wofrysrw.beamline.optical_elements.mirrors.srw_spherical_mirror import SRWSphericalMirror

from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWSphericallMirror(OWSRWMirror):

    name = "Spherical Mirror"
    description = "SRW: Spherical Mirror"
    icon = "icons/spherical_mirror.png"
    priority = 6

    radius  = Setting(1.0)

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWSphericalMirror(radius=self.radius)

    def draw_specific_box(self):
        super().draw_specific_box()

        oasysgui.lineEdit(self.mirror_box, self, "radius", "Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element.get_surface_shape(), Sphere):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Spherical")

        self.radius = numpy.round(optical_element.get_surface_shape().get_radius(), 6)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.radius,  "Tangential Radius")
