from wofrysrw.beamline.optical_elements.absorbers.srw_obstacle import SRWObstacle

from orangecontrib.srw.widgets.gui.ow_srw_slits import OWSRWSlits

class OWSRWObstacle(OWSRWSlits):

    name = "Obstacle"
    description = "SRW: Obstacle"
    icon = "icons/beam_stopper.png"
    priority = 3

    def __init__(self):
        super().__init__()

    def get_srw_object(self, boundary_shape):
        return SRWObstacle(boundary_shape=boundary_shape)