
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class SRWData(object):

    def __init__(self, srw_beamline=SRWBeamline(), srw_wavefront=SRWWavefront()):
        super().__init__()

        self._srw_beamline = srw_beamline
        self._srw_wavefront = srw_wavefront
