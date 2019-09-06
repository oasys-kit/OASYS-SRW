from numpy import nan

from syned.beamline.optical_elements.ideal_elements.screen import Screen

from wofry.propagator.propagator import PropagationManager

from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen
from wofrysrw.propagator.propagators2D.srw_propagation_mode import SRWPropagationMode
from wofrysrw.propagator.propagators2D.srw_fresnel_native import SRW_APPLICATION
from wofrysrw.propagator.wavefront2D.srw_wavefront import PolarizationComponent

from orangewidget.settings import Setting
from orangewidget import gui

from orangecontrib.srw.widgets.gui.ow_srw_optical_element import OWSRWOpticalElement
from orangecontrib.srw.util.srw_util import SRWPlot

class OWSRWScreen(OWSRWOpticalElement):

    name = "Screen"
    description = "SRW: Screen"
    icon = "icons/screen.png"
    priority = 20

    is_final_screen = Setting(0)

    def __init__(self):
        super().__init__(has_orientation_angles=False, has_oe_wavefront_propagation_parameters_tab=False, has_displacement_tab=False)

        self.cb_is_final_screen = gui.comboBox(self.tab_bas, self, "is_final_screen", label="Compute Wavefront Propagation", items=["No", "Yes"],
                                               labelWidth=300, sendSelectedValue=False, orientation="horizontal", callback=self.set_is_final_screen)

        self.set_is_final_screen()

    def set_is_final_screen(self):
        propagation_mode = PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION)

        self.cb_is_final_screen.setEnabled(propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE)
        self.view_type = 0 if propagation_mode == SRWPropagationMode.WHOLE_BEAMLINE and self.is_final_screen == 0 else self.view_type

        self.set_PlotQuality()

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
