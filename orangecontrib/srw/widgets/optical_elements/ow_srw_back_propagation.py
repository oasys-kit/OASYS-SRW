from numpy import nan
from syned.beamline.optical_elements.ideal_elements.screen import Screen

from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen
from wofrysrw.propagator.wavefront2D.srw_wavefront import PolarizationComponent

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement, SRWWavefrontViewer

class OWSRWBackPropagation(OWSRWOpticalElement):

    name = "Back Propagation"
    description = "SRW: Back Propagation"
    icon = "icons/backpropagation.png"
    priority = 30

    def __init__(self):
        super().__init__(has_orientation_angles=False,
                         has_q=False,
                         has_oe_wavefront_propagation_parameters_tab=False,
                         has_displacement_tab=False,
                         check_positive_distances=False)

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

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

            elif self.view_type == 2:
                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_HORIZONTAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

                e, h, v, i = self.output_wavefront.get_intensity(multi_electron=True, polarization_component_to_be_extracted=PolarizationComponent.LINEAR_VERTICAL)

                SRWWavefrontViewer.add_2D_wavefront_plot(e, h, v, i, tickets)

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

    def getWeightedPlots(self):
        if self.view_type == 2:
            return [False, False, True, True, False, False]
        else:
            return [False, True, False]

    def getWeightTickets(self):
        if self.view_type == 2:
            return [nan, nan, 0, 1, nan, nan]
        else:
            return [nan, 0, nan]

    def getTitles(self, with_um=False):
        if self.view_type == 2:
            if with_um: return ["Intensity SE \u03c3 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity SE \u03c0 [ph/s/.1%bw/mm\u00b2]",
                                "Phase SE \u03c3 [rad]",
                                "Phase SE \u03c0 [rad]",
                                "Intensity ME \u03c3 [ph/s/.1%bw/mm\u00b2]",
                                "Intensity ME \u03c0 [ph/s/.1%bw/mm\u00b2]"]
            else: return ["Intensity SE \u03c3",
                          "Intensity SE \u03c0",
                          "Phase SE \u03c3",
                          "Phase SE \u03c0",
                          "Intensity ME \u03c3 (Convolution)",
                          "Intensity ME \u03c0 (Convolution)"]
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


