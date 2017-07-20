from wofrysrw.beamline.optical_elements.absorbers.srw_aperture import SRWAperture

from orangecontrib.srw.widgets.gui.ow_srw_slits import OWSRWSlits

class OWSRWAperture(OWSRWSlits):

    name = "Aperture"
    description = "SRW: Aperture"
    icon = "icons/slit.png"
    priority = 2

    def __init__(self):
        super().__init__()

    def get_srw_object(self, boundary_shape):
        return SRWAperture(boundary_shape=boundary_shape)