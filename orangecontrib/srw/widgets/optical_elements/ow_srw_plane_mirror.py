from syned.beamline.shape import Plane

from wofrysrw.beamline.optical_elements.mirrors.srw_plane_mirror import SRWPlaneMirror

from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWPlaneMirror(OWSRWMirror):

    name = "Plane Mirror"
    description = "SRW: Plane Mirror"
    icon = "icons/plane_mirror.png"
    priority = 4

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWPlaneMirror()

    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element._surface_shape, Plane):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Plane")

