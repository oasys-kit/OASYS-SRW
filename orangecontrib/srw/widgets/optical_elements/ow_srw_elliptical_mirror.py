import numpy

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.beamline.shape import Ellipsoid

from wofrysrw.beamline.optical_elements.mirrors.srw_elliptical_mirror import SRWEllipticalMirror

from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWEllipticalMirror(OWSRWMirror):

    name = "Elliptical Mirror"
    description = "SRW: Elliptical Mirror"
    icon = "icons/ellipsoid_mirror.png"
    priority = 5

    distance_from_first_focus_to_mirror_center  = Setting(1.0)
    distance_from_mirror_center_to_second_focus = Setting(1.0)

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWEllipticalMirror(distance_from_first_focus_to_mirror_center=self.distance_from_first_focus_to_mirror_center,
                                   distance_from_mirror_center_to_second_focus=self.distance_from_mirror_center_to_second_focus)

    def draw_specific_box(self):
        super().draw_specific_box()

        oasysgui.lineEdit(self.mirror_box, self, "distance_from_first_focus_to_mirror_center", "1st focus to mirror center distance (p) [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "distance_from_mirror_center_to_second_focus", "Mirror center to 2nd focus distance (q) [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element._surface_shape, Ellipsoid):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Elliptical")

        p, q = optical_element._surface_shape.get_p_q(numpy.radians(90-self.angle_radial))

        self.distance_from_first_focus_to_mirror_center = numpy.round(p, 6)
        self.distance_from_mirror_center_to_second_focus = numpy.round(q, 6)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.distance_from_first_focus_to_mirror_center,  "Distance from first focus to mirror center (p)")
        congruence.checkStrictlyPositiveNumber(self.distance_from_mirror_center_to_second_focus, "Distance from mirror center to second focus (q)")
