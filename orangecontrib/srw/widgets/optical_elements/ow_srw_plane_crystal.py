from syned.beamline.shape import Plane

from orangecontrib.srw.widgets.gui.ow_srw_crystal import OWSRWCrystal

class OWSRWPlaneCrystal(OWSRWCrystal):

    name = "Plane Crystal"
    description = "SRW: Plane Crystal"
    icon = "icons/plane_crystal.png"
    priority = 7

    def __init__(self):
        super().__init__()

    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element._surface_shape, Plane):
            raise Exception("Syned Data not correct: Crystal Surface Shape is not Plane")

