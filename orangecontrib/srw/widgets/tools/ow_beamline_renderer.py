#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2021, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2021. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# ----------------------------------------------------------------------- #

import numpy
from Shadow import OE, IdealLensOE, CompoundOE

from orangecontrib.srw.util.srw_objects import SRWData

from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource
from wofrysrw.storage_ring.light_sources.srw_gaussian_light_source import SRWGaussianLightSource
from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource
from wofrysrw.storage_ring.light_sources.srw_wiggler_light_source import SRWWigglerLightSource

from wofrysrw.beamline.optical_elements.absorbers.srw_slit import SRWSlit
from wofrysrw.beamline.optical_elements.absorbers.srw_aperture import SRWAperture
from wofrysrw.beamline.optical_elements.absorbers.srw_obstacle import SRWObstacle
from wofrysrw.beamline.optical_elements.absorbers.srw_transmission import SRWTransmission
from wofrysrw.beamline.optical_elements.absorbers.srw_filter import SRWFilter
from wofrysrw.beamline.optical_elements.ideal_elements.srw_screen import SRWScreen
from wofrysrw.beamline.optical_elements.ideal_elements.srw_ideal_lens import SRWIdealLens
from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import SRWMirror
from wofrysrw.beamline.optical_elements.gratings.srw_grating import SRWGrating
from wofrysrw.beamline.optical_elements.crystals.srw_crystal import SRWCrystal
from wofrysrw.beamline.optical_elements.other.srw_crl import SRWCRL
from wofrysrw.beamline.optical_elements.other.srw_zone_plate import SRWZonePlate

from oasys.widgets.abstract.beamline_rendering.ow_abstract_beamline_renderer import AbstractBeamlineRenderer, AspectRatioModifier, Orientations, OpticalElementsColors, initialize_arrays, get_height_shift, get_inclinations

class SRWBeamlineRenderer(AbstractBeamlineRenderer):
    name = "Beamline Renderer"
    description = "Beamline Renderer"
    icon = "icons/renderer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1000
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    inputs = [("SRWData", SRWData, "set_input")]

    srw_data = None

    def __init__(self):
        super(SRWBeamlineRenderer, self).__init__(is_using_workspace_units=False)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.srw_data = input_data
            self.render(on_receiving_input=True)

    def render_beamline(self):
        if not self.srw_data is None:
            self.figure_canvas.clear_axis()

            beamline = self.srw_data.get_srw_beamline()

            number_of_elements = beamline.get_beamline_elements_number() + (1 if self.draw_source else 0)

            centers, limits = initialize_arrays(number_of_elements=number_of_elements)

            aspect_ratio_modifier = AspectRatioModifier(element_expansion_factor=[self.element_expansion_factor,
                                                                                  self.element_expansion_factor,
                                                                                  self.element_expansion_factor],
                                                        layout_reduction_factor=[1/self.distance_compression_factor,
                                                                                 1.0,
                                                                                 1,0])
            previous_oe_distance    = 0.0
            previous_image_segment  = 0.0
            previous_image_distance = 0.0
            previous_height = self.initial_height # for better visibility
            previous_shift  = 0.0
            beam_horizontal_inclination = 0.0
            beam_vertical_inclination   = 0.0

            if self.draw_source:
                source         = beamline.get_light_source()
                magnetic_structure = source.get_magnetic_structure()
                canting = 0.0
                length  = 0.0

                if isinstance(source, SRWGaussianLightSource): source_name = "Gaussian"
                elif isinstance(source, SRWBendingMagnetLightSource): source_name = "Bending Magnet"
                elif isinstance(source, SRWUndulatorLightSource):
                    source_name = "Undulator"
                    length = magnetic_structure._period_length*magnetic_structure._number_of_periods
                    canting = magnetic_structure.longitudinal_central_position
                elif isinstance(source, SRWWigglerLightSource):
                    source_name = "Wiggler"
                    length = magnetic_structure._period_length*magnetic_structure._number_of_periods
                    canting = magnetic_structure.longitudinal_central_position
                else:  source_name = None

                previous_oe_distance = source.get_source_wavefront_parameters()._distance

                self.add_source(centers, limits, length=length, height=self.initial_height,
                                canting=canting, aspect_ration_modifier=aspect_ratio_modifier, source_name=source_name)

            oe_index = 0 if self.draw_source else -1

            for beamline_element in beamline.get_beamline_elements():
                oe_index += 1

                coordinates     = beamline_element.get_coordinates()
                optical_element = beamline_element.get_optical_element()

                source_segment = coordinates.p()
                image_segment  = coordinates.q()

                source_distance = source_segment * numpy.cos(beam_vertical_inclination) * numpy.cos(beam_horizontal_inclination)

                segment_to_oe     = previous_image_segment + source_segment
                oe_total_distance = previous_oe_distance   + previous_image_distance + source_distance

                height, shift = get_height_shift(segment_to_oe,
                                                 previous_height,
                                                 previous_shift,
                                                 beam_vertical_inclination,
                                                 beam_horizontal_inclination)

                if isinstance(optical_element, SRWScreen):
                    self.add_point(centers, limits, oe_index=oe_index,
                                   distance=oe_total_distance, height=height, shift=shift,
                                   label=None, aspect_ratio_modifier=aspect_ratio_modifier)
                elif isinstance(optical_element, SRWIdealLens):
                    self.add_point(centers, limits, oe_index=oe_index,
                                   distance=oe_total_distance, height=height, shift=shift,
                                   label="Ideal Lens", aspect_ratio_modifier=aspect_ratio_modifier)
                elif isinstance(optical_element, SRWSlit):
                    h_min, h_max, v_min, v_max = optical_element.get_boundary_shape().get_boundaries()
                    aperture = [h_max-h_min, v_max-v_min]

                    label = "Slits"
                    if isinstance(optical_element, SRWAperture): label += " (A)"
                    elif isinstance(optical_element, SRWObstacle): label += " (O)"

                    self.add_slits_filter(centers, limits, oe_index=oe_index,
                                          distance=oe_total_distance, height=height, shift=shift,
                                          aperture=aperture, label=label,
                                          aspect_ratio_modifier=aspect_ratio_modifier)
                elif isinstance(optical_element, SRWFilter):
                    self.add_slits_filter(centers, limits, oe_index=oe_index,
                                          distance=oe_total_distance, height=height, shift=shift,
                                          aperture=None, label="Filter (" + optical_element.get_material() + ")",
                                          aspect_ratio_modifier=aspect_ratio_modifier)
                elif isinstance(optical_element, SRWTransmission):
                    self.add_point(centers, limits, oe_index=oe_index,
                                   distance=oe_total_distance, height=height, shift=shift,
                                   label="Transmission Element", aspect_ratio_modifier=aspect_ratio_modifier)
                elif isinstance(optical_element, SRWCRL):
                    self.add_non_optical_element(centers, limits, oe_index=oe_index,
                                                 distance=oe_total_distance, height=height, shift=shift,
                                                 length=optical_element.number_of_lenses * 0.0025, # fictional but typical, for visibility
                                                 color=OpticalElementsColors.LENS, aspect_ration_modifier=aspect_ratio_modifier, label="CRLs")
                elif isinstance(optical_element, SRWZonePlate):
                    self.add_non_optical_element(centers, limits, oe_index=oe_index,
                                                 distance=oe_total_distance, height=height, shift=shift,
                                                 length=0.005, # fictional for visibility
                                                 color=OpticalElementsColors.LENS, aspect_ration_modifier=aspect_ratio_modifier, label="Zone Plate")
                elif (isinstance(optical_element, SRWMirror) or
                      isinstance(optical_element, SRWGrating) or
                      isinstance(optical_element, SRWCrystal)):
                    inclination = optical_element.grazing_angle
                    orientation = optical_element.orientation_of_reflection_plane # they are the same numbers

                    if (isinstance(optical_element, SRWMirror) or  isinstance(optical_element, SRWGrating)):
                        width  = optical_element.sagittal_size
                        length = optical_element.tangential_size
                    else:
                        width = 0.1 # m
                        length = 0.1 # m

                    if isinstance(optical_element, SRWMirror):
                        color = OpticalElementsColors.MIRROR
                        label = "Mirror"
                    elif isinstance(optical_element, SRWGrating):
                        color = OpticalElementsColors.GRATING
                        label = "Grating"
                    elif isinstance(optical_element, SRWCrystal):
                        color = OpticalElementsColors.CRYSTAL
                        label = "Crystal"

                    absolute_inclination, beam_horizontal_inclination, beam_vertical_inclination = get_inclinations(orientation, inclination, beam_vertical_inclination, beam_horizontal_inclination)

                    self.add_optical_element(centers, limits, oe_index=oe_index,
                                             distance=oe_total_distance, height=height, shift=shift,
                                             length=length, width=width, thickness=0.01, inclination=absolute_inclination, orientation=orientation,
                                             color=color, aspect_ration_modifier=aspect_ratio_modifier, label=label)

                image_distance = image_segment * numpy.cos(beam_vertical_inclination) * numpy.cos(beam_horizontal_inclination)  # new direction

                previous_height         = height
                previous_shift          = shift
                previous_oe_distance    = oe_total_distance
                previous_image_segment  = image_segment
                previous_image_distance = image_distance

            height, shift = get_height_shift(previous_image_segment,
                                             previous_height,
                                             previous_shift,
                                             beam_vertical_inclination,
                                             beam_horizontal_inclination)

            self.add_point(centers, limits, oe_index=number_of_elements - 1,
                           distance=previous_oe_distance + previous_image_distance,
                           height=height, shift=shift, label="End Point",
                           aspect_ratio_modifier=aspect_ratio_modifier)

            return number_of_elements, centers, limits

