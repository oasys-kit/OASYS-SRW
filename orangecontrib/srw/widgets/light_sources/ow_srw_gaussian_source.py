__author__ = 'labx'

import sys
from numpy import nan

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream
from oasys.util.oasys_util import TriggerIn, TriggerOut

from syned.widget.widget_decorator import WidgetDecorator

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontParameters, WavefrontPrecisionParameters
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.storage_ring.light_sources.srw_gaussian_light_source import SRWGaussianLightSource, Polarization

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer


class OWSRWGaussianSource(SRWWavefrontViewer, WidgetDecorator):

    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]
    name = "Gaussian Source"
    description = "SRW Source: Gaussian Source"
    icon = "icons/gaussian_source.png"
    priority = 10

    inputs = WidgetDecorator.syned_input_data()
    inputs.append(("Trigger", TriggerOut, "sendNewWavefront"))

    outputs = [{"name":"SRWData",
                "type":SRWData,
                "doc":"SRW Source Data",
                "id":"data"}]

    want_main_area=1

    source_name = None

    beam_center_at_waist_x = Setting(0.0)
    beam_center_at_waist_y = Setting(0.0)
    beam_center_at_waist_z = Setting(0.0)
    average_angle_at_waist_x = Setting(0.0)
    average_angle_at_waist_y = Setting(0.0)
    energy_per_pulse = Setting(0.001)
    repetition_rate = Setting(1)
    polarization = Setting(0)
    horizontal_sigma_at_waist = Setting(1e-6)
    vertical_sigma_at_waist = Setting(1e-6)
    pulse_duration = Setting(10e-15)
    transverse_gauss_hermite_mode_order_x = Setting(0)
    transverse_gauss_hermite_mode_order_y = Setting(0)

    wf_photon_energy = Setting(8000.0)
    wf_h_slit_gap = Setting(0.001)
    wf_v_slit_gap =Setting( 0.001)
    wf_h_slit_points=Setting(100)
    wf_v_slit_points=Setting(100)
    wf_distance = Setting(10.0)

    wf_sampling_factor_for_adjusting_nx_ny = Setting(0.0)

    TABS_AREA_HEIGHT = 618
    CONTROL_AREA_WIDTH = 405

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run SRW", self)
        self.runaction.triggered.connect(self.runSRWSource)
        self.addAction(self.runaction)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run SRW Source", callback=self.runSRWSource)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_source = oasysgui.createTabPage(self.tabs_setting, "Light Source Setting")

        left_box_1 = oasysgui.widgetBox(self.tab_source, "Gaussian Source Parameters", addSpace=True, orientation="vertical", height=380)

        oasysgui.lineEdit(left_box_1, self, "beam_center_at_waist_x", "Beam center at waist x [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "beam_center_at_waist_y", "Beam center at waist y [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "beam_center_at_waist_z", "Beam center at waist z [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "average_angle_at_waist_x", "Average angle at waist x [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "average_angle_at_waist_y", "Average angle at waist y [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "energy_per_pulse", "Energy per pulse [J]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "repetition_rate", "Repetition rate [Hz]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_1, self, "polarization", label="Polarization",
                     items=Polarization.tuple(), labelWidth=150,
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(left_box_1, self, "horizontal_sigma_at_waist", "\u03c3x at waist [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "vertical_sigma_at_waist", "\u03c3y at waist [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "pulse_duration", "Pulse duration [s]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "transverse_gauss_hermite_mode_order_x", "Transverse Gauss-Hermite mode order x", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "transverse_gauss_hermite_mode_order_y", "Transverse Gauss-Hermite mode order y", labelWidth=260, valueType=int, orientation="horizontal")

        self.tab_plots = oasysgui.createTabPage(self.tabs_setting, "Wavefront Setting")

        self.tabs_plots_setting = oasysgui.tabWidget(self.tab_plots)
        
        # PROPAGATION -------------------------------------------
        
        tab_wav = oasysgui.createTabPage(self.tabs_plots_setting, "Propagation")

        wav_box = oasysgui.widgetBox(tab_wav, "Wavefront Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(wav_box, self, "wf_photon_energy", "Photon Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_h_slit_gap", "H Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_v_slit_gap", "V Slit Gap [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_h_slit_points", "H Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_v_slit_points", "V Slit Points", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(wav_box, self, "wf_distance", "Propagation Distance [m]", labelWidth=260, valueType=float, orientation="horizontal")

        pre_box = oasysgui.widgetBox(tab_wav, "Precision Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(pre_box, self, "wf_sampling_factor_for_adjusting_nx_ny", "Sampling factor for adjusting nx/ny\n(effective if > 0)", labelWidth=260, valueType=int, orientation="horizontal")

        gui.rubber(self.controlArea)


    def runSRWSource(self):
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            srw_source = self.get_srw_source()
            srw_source.name = self.source_name if not self.source_name is None else self.windowTitle(),

            self.progressBarSet(10)

            self.setStatusMessage("Running SRW")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.progressBarSet(20)

            self.setStatusMessage("")

            beamline = SRWBeamline(light_source=srw_source)
            wavefront = self.calculate_wavefront_propagation(srw_source)

            tickets = []

            if self.is_do_plots():
                self.setStatusMessage("Plotting Results")

                self.run_calculation_intensity(wavefront, tickets)

                self.plot_results(tickets)

            self.setStatusMessage("")

            self.send("SRWData", SRWData(srw_beamline=beamline, srw_wavefront=wavefront))

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    def sendNewWavefront(self, trigger):
        if trigger and trigger.new_object == True:
            self.runSRWSource()

    def get_srw_source(self):
        return SRWGaussianLightSource(beam_center_at_waist_x=self.beam_center_at_waist_x,
                                      beam_center_at_waist_y=self.beam_center_at_waist_y,
                                      beam_center_at_waist_z=self.beam_center_at_waist_z,
                                      average_angle_at_waist_x=self.average_angle_at_waist_x,
                                      average_angle_at_waist_y=self.average_angle_at_waist_y,
                                      photon_energy=self.wf_photon_energy,
                                      energy_per_pulse=self.energy_per_pulse,
                                      repetition_rate=self.repetition_rate,
                                      polarization=self.polarization + 1,
                                      horizontal_sigma_at_waist=self.horizontal_sigma_at_waist,
                                      vertical_sigma_at_waist=self.vertical_sigma_at_waist,
                                      pulse_duration=self.pulse_duration,
                                      transverse_gauss_hermite_mode_order_x=self.transverse_gauss_hermite_mode_order_x,
                                      transverse_gauss_hermite_mode_order_y=self.transverse_gauss_hermite_mode_order_y)

    def checkFields(self):
        congruence.checkPositiveNumber(self.energy_per_pulse, "Energy per pulse")
        congruence.checkPositiveNumber(self.horizontal_sigma_at_waist, "\u03c3x at waist")
        congruence.checkPositiveNumber(self.vertical_sigma_at_waist, "\u03c3y at waist")
        congruence.checkPositiveNumber(self.pulse_duration, "Pulse duration")
        congruence.checkPositiveNumber(self.transverse_gauss_hermite_mode_order_x, "Transverse Gauss-Hermite mode order x")
        congruence.checkPositiveNumber(self.transverse_gauss_hermite_mode_order_y, "Transverse Gauss-Hermite mode order y")

        # WAVEFRONT

        congruence.checkStrictlyPositiveNumber(self.wf_photon_energy, "Wavefront Propagation Photon Energy")
        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_gap, "Wavefront Propagation H Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_gap, "Wavefront Propagation V Slit Gap")
        congruence.checkStrictlyPositiveNumber(self.wf_h_slit_points, "Wavefront Propagation H Slit Points")
        congruence.checkStrictlyPositiveNumber(self.wf_v_slit_points, "Wavefront Propagation V Slit Points")
        congruence.checkPositiveNumber(self.wf_distance, "Wavefront Propagation Distance")
        congruence.checkPositiveNumber(self.wf_sampling_factor_for_adjusting_nx_ny, "Wavefront Propagation Sampling Factor for adjusting nx/ny")


    def run_calculation_intensity(self, srw_wavefront, tickets, progress_bar_value=30):

        e, h, v, i = srw_wavefront.get_intensity(multi_electron=False)

        tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value)

        e, h, v, i = srw_wavefront.get_phase()

        tickets.append(SRWPlot.get_ticket_2D(h*1000, v*1000, i[int(e.size/2)]))

        self.progressBarSet(progress_bar_value + 20)

    def calculate_wavefront_propagation(self, srw_source):
        wf_parameters = WavefrontParameters(photon_energy_min = self.wf_photon_energy,
                                            photon_energy_max = self.wf_photon_energy,
                                            photon_energy_points=1,
                                            h_slit_gap = self.wf_h_slit_gap,
                                            v_slit_gap = self.wf_v_slit_gap,
                                            h_slit_points=self.wf_h_slit_points,
                                            v_slit_points=self.wf_v_slit_points,
                                            distance = self.wf_distance,
                                            wavefront_precision_parameters=WavefrontPrecisionParameters(sampling_factor_for_adjusting_nx_ny=self.wf_sampling_factor_for_adjusting_nx_ny))

        return srw_source.get_SRW_Wavefront(source_wavefront_parameters=wf_parameters)

    def receive_syned_data(self, data):
        if not data is None: QMessageBox.critical(self, "Error", "Syned data not supported for Gaussian Light Source", QMessageBox.Ok)

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2]]

    def getWeightedPlots(self):
        return [False, True]

    def getWeightTickets(self):
        return [nan, 0]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity [ph/s/.1%bw/mm\u00b2]",
                            "Phase [rad]"]
        else: return ["Intensity", "Phase"]

    def getXTitles(self):
        return ["X [\u03bcm]", "X [\u03bcm]"]

    def getYTitles(self):
        return ["Y [\u03bcm]", "Y [\u03bcm]"]

    def getXUM(self):
        return ["X [\u03bcm]", "X [\u03bcm]"]

    def getYUM(self):
        return ["Y [\u03bcm]", "Y [\u03bcm]"]
