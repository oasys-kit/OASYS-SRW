
from wofrysrw.beamline.srw_beamline import SRWBeamline
from wofrysrw.storage_ring.srw_light_source import SRWLightSource
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront


class SRWData(object):
    def __init__(self, srw_wavefront=SRWWavefront()):
        self._srw_wavefront = srw_wavefront

class SRWSourceData(SRWData):

    def __init__(self, srw_light_source=SRWLightSource(), srw_wavefront=SRWWavefront()):
        super().__init__(srw_wavefront)

        self._srw_light_source = srw_light_source


class SRWOEData(SRWData):
    def __init__(self, srw_beamline=SRWBeamline(), srw_wavefront=SRWWavefront()):
        super().__init__(srw_wavefront)

        self._srw_beamline = srw_beamline
