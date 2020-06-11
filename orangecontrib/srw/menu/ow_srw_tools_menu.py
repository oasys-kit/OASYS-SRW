__author__ = 'labx'

from orangecanvas.scheme.link import SchemeLink
from oasys.menus.menu import OMenu

from wofry.propagator.propagator import PropagationManager
from wofrysrw.propagator.propagators2D.srw_fresnel_native import SRW_APPLICATION
from wofrysrw.propagator.propagators2D.srw_propagation_mode import SRWPropagationMode

from orangecontrib.srw.util.srw_util import showWarningMessage, showCriticalMessage
from orangecontrib.srw.widgets.optical_elements.ow_srw_screen import OWSRWScreen
from orangecontrib.srw.widgets.native.ow_srw_intensity_plotter import OWSRWIntensityPlotter
from orangecontrib.srw.widgets.native.ow_srw_me_degcoh_plotter import OWSRWDegCohPlotter
from srw.widgets.basic_loops.ow_srw_accumulation_point import OWSRWAccumulationPoint
from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

class SRWToolsMenu(OMenu):

    def __init__(self):
        super().__init__(name="SRW")

        self.openContainer()
        self.addContainer("Propagation Mode")
        self.addSubMenu("Element by Element (Wofry)")
        self.addSubMenu("Element by Element (SRW Native)")
        self.addSubMenu("Whole beamline at Final Screen (SRW Native)")
        self.addSeparator()
        self.addSubMenu("Disable Wavefront Propagation on all the Final Screens")
        self.closeContainer()
        self.openContainer()
        self.addContainer("Plotting")
        self.addSubMenu("Select Plots \'No\' on all Source and O.E. widgets")
        self.addSubMenu("Select Plots \'Yes\' on all Source and O.E. widgets")
        self.closeContainer()

    def executeAction_1(self, action):
        try:
            propagation_mode =  PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION)

            try:
                PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, SRWPropagationMode.STEP_BY_STEP_WOFRY)

                self.set_srw_live_propagation_mode()

                showWarningMessage("Propagation Mode: Element by Element (Wofry)")
            except Exception as exception:
                showCriticalMessage(exception.args[0])

                try:
                    PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, propagation_mode)
                    self.set_srw_live_propagation_mode()
                except:
                    pass
        except:
            pass

    def executeAction_2(self, action):
        try:
            propagation_mode =  PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION)

            try:
                PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, SRWPropagationMode.STEP_BY_STEP)

                self.set_srw_live_propagation_mode()

                showWarningMessage("Propagation Mode: Element by Element (SRW Native)")
            except Exception as exception:
                showCriticalMessage(exception.args[0])

                try:
                    PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, propagation_mode)
                    self.set_srw_live_propagation_mode()
                except:
                    pass
        except:
            pass

    def executeAction_3(self, action):
        try:
            propagation_mode =  PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION)

            try:
                PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, SRWPropagationMode.WHOLE_BEAMLINE)

                self.set_srw_live_propagation_mode()

                showWarningMessage("Propagation Mode: Whole beamline at Final Screen (SRW Native)")
            except Exception as exception:
                showCriticalMessage(exception.args[0])

                try:
                    PropagationManager.Instance().set_propagation_mode(SRW_APPLICATION, propagation_mode)
                    self.set_srw_live_propagation_mode()
                except:
                    pass
        except:
            pass



    def executeAction_4(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, OWSRWScreen):
                    if hasattr(widget, "is_final_screen") and hasattr(widget, "set_is_final_screen"):
                        if (PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) != SRWPropagationMode.WHOLE_BEAMLINE):
                            raise Exception("Action possibile only while Propagation Mode: Whole beamline at Final Screen (SRW Native)")

                        if hasattr(widget, "show_view_box") and getattr(widget, "show_view_box"):
                            widget.is_final_screen = 0
                            widget.set_is_final_screen()
        except Exception as exception:
            showCriticalMessage(exception.args[0])

    def executeAction_5(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, SRWWidget) and not (isinstance(widget, OWSRWIntensityPlotter) or
                                                          isinstance(widget, OWSRWDegCohPlotter) or
                                                          isinstance(widget, OWSRWAccumulationPoint)):
                    if hasattr(widget, "view_type") and hasattr(widget, "set_PlotQuality"):
                        if (PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == SRWPropagationMode.WHOLE_BEAMLINE):
                            raise Exception("Action not possibile while Propagation Mode: Whole beamline at Final Screen (SRW Native)")

                        if hasattr(widget, "show_view_box") and getattr(widget, "show_view_box"):
                            widget.view_type = 0
                            widget.set_PlotQuality()

        except Exception as exception:
            showCriticalMessage(exception.args[0])

    def executeAction_6(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, SRWWidget) and not (isinstance(widget, OWSRWIntensityPlotter) or
                                                          isinstance(widget, OWSRWDegCohPlotter) or
                                                          isinstance(widget, OWSRWAccumulationPoint)):
                    if hasattr(widget, "view_type") and hasattr(widget, "set_PlotQuality"):
                        if (PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == SRWPropagationMode.WHOLE_BEAMLINE):
                            raise Exception("Action not possibile while Propagation Mode: Whole beamline at Final Screen (SRW Native)")

                    if hasattr(widget, "show_view_box") and getattr(widget, "show_view_box"):
                        widget.view_type = 1
                        widget.set_PlotQuality()

        except Exception as exception:
            showCriticalMessage(exception.args[0])

    #################################################################

    def set_srw_live_propagation_mode(self):
        for node in self.canvas_main_window.current_document().scheme().nodes:
            widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

            if hasattr(widget, "set_srw_live_propagation_mode"):
                widget.set_srw_live_propagation_mode()

                if (PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == SRWPropagationMode.WHOLE_BEAMLINE):
                    if not (isinstance(widget, OWSRWScreen) or
                            isinstance(widget, OWSRWIntensityPlotter) or
                            isinstance(widget, OWSRWDegCohPlotter) or
                            isinstance(widget, OWSRWAccumulationPoint)) \
                            or getattr(widget, "is_final_screen") == False:
                        if hasattr(widget, "view_type") and hasattr(widget, "set_PlotQuality"):
                            if hasattr(widget, "show_view_box") and getattr(widget, "show_view_box"):
                                widget.view_type = 0
                                widget.set_PlotQuality()

                if isinstance(widget, OWSRWScreen): widget.set_is_final_screen()


    #################################################################
    #
    # SCHEME MANAGEMENT
    #
    #################################################################

    def getWidgetFromNode(self, node):
        return self.canvas_main_window.current_document().scheme().widget_for_node(node)

    def createLinks(self, nodes):
        previous_node = None
        for node in nodes:
            if not (isinstance(node, str)) and not previous_node is None and not (isinstance(previous_node, str)):
                link = SchemeLink(source_node=previous_node, source_channel="Beam", sink_node=node, sink_channel="Input Beam")
                self.canvas_main_window.current_document().addLink(link=link)
            previous_node = node

    def getWidgetDesc(self, widget_name):
        return self.canvas_main_window.widget_registry.widget(widget_name)

    def createNewNode(self, widget_desc):
        return self.canvas_main_window.current_document().createNewNode(widget_desc)

    def createNewNodeAndWidget(self, widget_desc):
        messages = []

        try:
            node = self.createNewNode(widget_desc)
            widget = self.getWidgetFromNode(node)

            # here you can put values on the attrubutes

        except Exception as exception:
            messages.append(exception.args[0])

        return widget, node, messages
