
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class SRWData(object):
    def __init__(self, srw_beamline=SRWBeamline(), srw_wavefront=SRWWavefront()):
        super().__init__()

        self.__srw_beamline = srw_beamline
        self.__srw_wavefront = srw_wavefront
        self.__working_srw_beamline = srw_beamline

    def get_srw_beamline(self):
        return self.__srw_beamline

    def get_srw_wavefront(self):
        return self.__srw_wavefront

    def reset_working_srw_beamline(self):
        self.__working_srw_beamline = SRWBeamline(light_source=None)

    def get_working_srw_beamline(self):
        return self.__working_srw_beamline

    def set_working_srw_beamline(self, working_srw_beamline):
        self.__working_srw_beamline = working_srw_beamline

class SRWPreProcessorData:

       NONE = "None"

       def __init__(self,
                    error_profile_data_file=NONE,
                    error_profile_x_dim = 0.0,
                    error_profile_y_dim=0.0,
                    error_profile_x_slope=0.0,
                    error_profile_y_slope=0.0):
        super().__init__()

        self.error_profile_data_file = error_profile_data_file
        self.error_profile_x_dim = error_profile_x_dim
        self.error_profile_y_dim = error_profile_y_dim
        self.error_profile_x_slope = error_profile_x_slope
        self.error_profile_y_slope = error_profile_y_slope
