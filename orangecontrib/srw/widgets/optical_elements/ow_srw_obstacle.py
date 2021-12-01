from wofrysrw.beamline.optical_elements.absorbers.srw_obstacle import SRWObstacle
from syned.beamline.optical_elements.absorbers.beam_stopper import BeamStopper

from orangecontrib.srw.widgets.gui.ow_srw_absorber import OWSRWAbsorber

class OWSRWObstacle(OWSRWAbsorber):

    name = "Obstacle"
    description = "SRW: Obstacle"
    icon = "icons/beam_stopper.png"
    priority = 3

    def __init__(self):
        super().__init__()

    def get_srw_object(self, boundary_shape):
        return SRWObstacle(boundary_shape=boundary_shape)

    def check_syned_absorber(self, optical_element):
        return isinstance(optical_element, BeamStopper)

    def get_syned_optical_element_name(self): return "Beam Stopper"
