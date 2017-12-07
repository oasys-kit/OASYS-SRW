from syned.beamline.optical_elements.ideal_elements.screen import Screen

from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement

from orangecontrib.srw.util.srw_util import SRWPlot

class OWSRWBackPropagation(OWSRWOpticalElement):

    name = "Back Propagation"
    description = "SRW: Back Propagation"
    icon = "icons/backpropagation.png"
    priority = 30

    def __init__(self):
        super().__init__(has_orientation_angles=False, has_q=False, check_positive_distances=False)

        self.tabs_prop_setting.removeTab(2)
        self.tabs_prop_setting.removeTab(1)

    def draw_specific_box(self):
        pass

    def get_optical_element(self):
        return SRWScreen(name=self.oe_name)

    def check_data(self):
        super().check_data()

    def run_calculations(self, tickets, progress_bar_value):
        super().run_calculations(tickets, progress_bar_value)

        e, h, v, i = self.wavefront_to_plot.get_intensity(multi_electron=True)

        tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if not isinstance(optical_element, Screen):
                raise Exception("Syned Data not correct: Optical Element is not a Screen")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity SE [ph/s/.1%bw/mm^2]",
                            "Phase SE [rad]",
                            "Intensity ME [ph/s/.1%bw/mm^2]"]
        else: return ["Intensity SE", "Phase SE", "Intensity ME (Convolution)"]

    def getXTitles(self):
        return ["X [um]", "X [um]", "X [um]"]

    def getYTitles(self):
        return ["Y [um]", "Y [um]", "Y [um]"]

    def getXUM(self):
        return ["X [um]", "X [um]", "X [um]"]

    def getYUM(self):
        return ["Y [um]", "Y [um]", "Y [um]"]

