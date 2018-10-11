from syned.beamline.optical_elements.ideal_elements.screen import Screen

from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen
from wofrysrw.propagator.wavefront2D.srw_wavefront import PolarizationComponent

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

    def run_calculation_for_plots(self, tickets, progress_bar_value):
        if not self.output_wavefront is None:
            super().run_calculation_for_plots(tickets, progress_bar_value)

            if self.view_type == 1:
                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True)

                tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

            elif self.view_type == 2:
                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

                tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

                tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

    def receive_specific_syned_data(self, optical_element):
        if not optical_element is None:
            if not isinstance(optical_element, Screen):
                raise Exception("Syned Data not correct: Optical Element is not a Screen")
        else:
            raise Exception("Syned Data not correct: Empty Optical Element")

    def getVariablesToPlot(self):
        if self.view_type == 2:
            return [[1, 2], [1, 2], [1, 2], [1, 2], [1, 2], [1, 2]]
        else:
            return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if self.view_type == 2:
            if with_um: return ["Intensity SE \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity SE \u03c3 [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE \u03c0 [rad]",
                                "Phase SE \u03c3 [rad]",
                                "Intensity ME \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity ME \u03c3 [ph/s/.1%bw/mm\u00b2]"]
            else: return ["Intensity SE \u03c0",
                          "Intensity SE \u03c3",
                          "Phase SE \u03c0",
                          "Phase SE \u03c3",
                          "Intensity ME \u03c0 (Convolution)",
                          "Intensity ME \u03c3 (Convolution)"]
        else:
            if with_um: return ["Intensity SE [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE [rad]",
                                "Intensity ME [ph/s/.1%bw/mm\u00b2]"]
            else: return ["Intensity SE",
                          "Phase SE",
                          "Intensity ME (Convolution)"]

    def getXTitles(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]

    def getYTitles(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]

    def getXUM(self):
        if self.view_type == 2:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]
        else:
            return ["X [\u03bcm]", "X [\u03bcm]", "X [\u03bcm]"]

    def getYUM(self):
        if self.view_type == 2:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]
        else:
            return ["Y [\u03bcm]", "Y [\u03bcm]", "Y [\u03bcm]"]


