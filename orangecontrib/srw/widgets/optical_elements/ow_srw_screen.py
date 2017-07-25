from syned.beamline.optical_elements.ideal_elements.screen import Screen

from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement

class OWSRWScreen(OWSRWOpticalElement):

    name = "Screen"
    description = "SRW: Screen"
    icon = "icons/screen.png"
    priority = 20

    def __init__(self):
        super().__init__(has_orientation_angles=False)

        self.tabs_prop_setting.removeTab(0)

    def draw_specific_box(self):
        pass

    def get_optical_element(self):
        return SRWScreen(name=self.oe_name)

    def check_data(self):
        super().check_data()

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if not isinstance(optical_element, Screen):
                raise Exception("Syned Data not correct: Optical Element is not a Screen")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")



