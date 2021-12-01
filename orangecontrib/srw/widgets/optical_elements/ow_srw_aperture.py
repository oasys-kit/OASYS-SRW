from wofrysrw.beamline.optical_elements.absorbers.srw_aperture import SRWAperture
from syned.beamline.optical_elements.absorbers.slit import Slit
from orangecontrib.srw.widgets.gui.ow_srw_absorber import OWSRWAbsorber

class OWSRWAperture(OWSRWAbsorber):

    name = "Aperture"
    description = "SRW: Aperture"
    icon = "icons/slit.png"
    priority = 2

    def __init__(self):
        super().__init__()

    def get_srw_object(self, boundary_shape):
        return SRWAperture(boundary_shape=boundary_shape)

    def check_syned_absorber(self, optical_element):
        return isinstance(optical_element, Slit)

    def get_syned_optical_element_name(self): return "Slit"
