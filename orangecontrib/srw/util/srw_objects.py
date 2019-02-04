
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class SRWData(object):
    def __init__(self, srw_beamline=SRWBeamline(), srw_wavefront=SRWWavefront()):
        super().__init__()

        self.__srw_beamline = srw_beamline
        self.__srw_wavefront = srw_wavefront

    def get_srw_beamline(self):
        return self.__srw_beamline

    def get_srw_wavefront(self):
        return self.__srw_wavefront

    def reset_working_srw_beamline(self):
        if hasattr(self, "__working_srw_beamline"): self.__working_srw_beamline = SRWBeamline(light_source=None)

    def get_working_srw_beamline(self):
        if hasattr(self, "__working_srw_beamline"): return self.__working_srw_beamline
        else: return self.__srw_beamline.duplicate()

    def set_working_srw_beamline(self, working_srw_beamline):
        self.__working_srw_beamline = working_srw_beamline

class SRWErrorProfileData:
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

from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import ScaleType

class SRWReflectivityData:
    NONE = "None"

    def __init__(self,
                 reflectivity_data_file=NONE,
                 energies_number=1,
                 angles_number=1,
                 components_number=1,
                 energy_start=0.0,
                 energy_end=0.0,
                 energy_scale_type=ScaleType.LINEAR,
                 angle_start=0.0,
                 angle_end=0.0,
                 angle_scale_type=ScaleType.LINEAR):

        self.reflectivity_data_file = reflectivity_data_file
        self.energies_number   = energies_number
        self.angles_number     = angles_number
        self.components_number = components_number
        self.energy_start      = energy_start
        self.energy_end        = energy_end
        self.energy_scale_type = energy_scale_type
        self.angle_start       = angle_start
        self.angle_end         = angle_end
        self.angle_scale_type  = angle_scale_type

class SRWPreProcessorData:

       def __init__(self,
                    error_profile_data=None,
                    reflectivity_data = None):
        super().__init__()

        self.error_profile_data = error_profile_data
        self.reflectivity_data = reflectivity_data
