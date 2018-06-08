from syned.beamline.shape import Plane

from wofrysrw.beamline.optical_elements.gratings.srw_plain_grating import SRWPlaneGrating

from orangecontrib.srw.widgets.gui.ow_srw_grating import OWSRWGrating

class OWSRWPlaneGrating(OWSRWGrating):

    name = "Plane Grating"
    description = "SRW: Plane Grating"
    icon = "icons/plane_grating.png"
    priority = 8

    def __init__(self):
        super().__init__()

    def get_grating_instance(self):
        return SRWPlaneGrating()

    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element._surface_shape, Plane):
            raise Exception("Syned Data not correct: Grating Surface Shape is not Plane")

