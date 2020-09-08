from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangecontrib.srw.util.srw_objects import SRWData

from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource
from wofrysrw.storage_ring.light_sources.srw_gaussian_light_source import SRWGaussianLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource
from wofrysrw.storage_ring.light_sources.srw_wiggler_light_source import SRWWigglerLightSource

class OWSRWInfo(widget.OWWidget):
    name = "Info"
    id = "OWSRWInfo"
    description = "Info"
    icon = "icons/info.png"
    priority = 35
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("SRWData", SRWData, "set_input")]

    CONTROL_AREA_WIDTH = 600
    CONTROL_AREA_HEIGHT = 650

    srw_data = None

    want_main_area = 0

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, self.CONTROL_AREA_HEIGHT+10))))

        self.setFixedHeight(self.geometry().height())
        self.setFixedWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.text_area = oasysgui.textArea(height=self.CONTROL_AREA_HEIGHT-10, width=self.CONTROL_AREA_WIDTH-5, readOnly=True)
        self.text_area.setText("")
        self.text_area.setStyleSheet("background-color: white; font-family: Courier, monospace;")

        self.controlArea.layout().addWidget(self.text_area)


    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.srw_data = input_data

            self.build_info()



    def build_info(self):
        try:
            self.text_area.clear()

            from wofrysrw.beamline.srw_beamline import SRWBeamline

            beamline = self.srw_data.get_srw_beamline()

            source = beamline.get_light_source()
            beamline_elements = beamline.get_beamline_elements()
            source_wavefront_parameters = source.get_source_wavefront_parameters()

            final_screen_to_source = source_wavefront_parameters._distance

            if isinstance(source, SRWBendingMagnetLightSource):
                txt = '  ******** BENDING MAGNET SOURCE ********\n\n'
            elif isinstance(source, SRWGaussianLightSource):
                txt = '  ********    GAUSSIAN SOURCE    ********\n\n'
            elif isinstance(source, SRWUndulatorLightSource):
                txt = '  ********    UNDULATOR SOURCE   ********\n\n'
            elif isinstance(source, SRWWigglerLightSource):
                txt = '  ********    WIGGLER SOURCE     ********\n\n'
            else:
                txt = '  ********   UNDEFINED SOURCE    ********\n\n'

            txt += "  Photon Energy: %10.4f eV\n"%(source_wavefront_parameters._photon_energy_min)

            txt += "  Acceptance Slit aperture (h x v): %8.6f x %8.6f m\n"%(source_wavefront_parameters._h_slit_gap, source_wavefront_parameters._v_slit_gap)
            txt += "  Acceptance Slit points   (h x v): %4d x %4d\n"%(source_wavefront_parameters._h_slit_points, source_wavefront_parameters._v_slit_points)
            txt += "  Acceptance Slit distance: %7.4f m\n\n"%(final_screen_to_source)

            txt += '  ********  SUMMARY OF DISTANCES ********\n'
            txt += '   ** DISTANCES FOR ALL O.E. [m] **           \n\n'
            txt += "%4s %20s %8s %8s %8s %8s \n"%('OE#','TYPE','p [m]','q [m]','src-oe','src-screen')
            txt += '----------------------------------------------------------------------\n'

            txt_2 = '\n\n  ********  ELLIPTICAL ELEMENTS  ********\n'
            txt_2 += "%4s %8s %8s %8s %1s\n"%('OE#', 'p(ell)','q(ell)','p+q(ell)', 'M')
            txt_2 += '----------------------------------------------------------------------\n'

            oe = 0
            for beamline_element in beamline_elements:
                oe += 1
                coordinates = beamline_element.get_coordinates()
                optical_element = beamline_element.get_optical_element()

                p = coordinates.p()
                q = coordinates.q()

                final_screen_to_source = final_screen_to_source + p + q
                oe_to_source           = final_screen_to_source - q

                oetype = optical_element.__class__.__name__[3:]

                txt += "%4d %20s %8.4f %8.4f %8.4f %8.4f \n"%(oe, oetype, p, q, oe_to_source, final_screen_to_source)

                if "Elliptical" in oetype:
                    p, q = optical_element.get_p_q()
                    txt_2 += '%4d %8.4f %8.4f %8.4f %8.4f\n'%(oe, p, q, p+q, p/q)

            txt += txt_2

            self.text_area.setText(txt)

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception
