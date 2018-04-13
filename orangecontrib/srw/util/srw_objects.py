
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class SRWData(object):

    def __init__(self, srw_beamline=SRWBeamline(), srw_wavefront=SRWWavefront()):
        super().__init__()

        self._srw_beamline = srw_beamline
        self._srw_wavefront = srw_wavefront

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
