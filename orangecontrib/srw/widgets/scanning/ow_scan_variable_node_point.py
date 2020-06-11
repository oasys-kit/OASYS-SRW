#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2020, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2020. UChicago Argonne, LLC. This software was produced       #
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
# #########################################################################
import numpy
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui

from oasys.widgets.abstract.scanning.abstract_scan_variable_node_point import AbstractScanVariableLoopPoint

VARIABLES = [
    ["p", "Distance from previous Continuation Plane", "m"],
    ["q", "Distance to next Continuation Plane", "m"],
    ["angle_radial",  "Incidence Angle", "deg"],
    ["distance_from_first_focus_to_mirror_center", "1st focus to mirror center distance (p)", "m"],
    ["distance_from_mirror_center_to_second_focus", "Mirror center to 2nd focus distance (q)", "m"],
    ["radius", "Radius", "m"],
    ["tangential_radius", "Tangential Radius", "m"],
    ["sagittal_radius", "Sagittal Radius", "m"],
    ["shift_x", "Horizontal Shift", "m"],
    ["rotation_x", "Rotation Around Horizontal Axis", "deg"],
    ["shift_y", "Vertical Shift", "m"],
    ["rotation_y", "Rotation Around Vertical Axis", "deg"],
    ["angle_azimuthal", "Rotation Along Beam Axis", "deg"],
    ["height_amplification_coefficient", "Height Amplification Coefficient", ""],
    ["width", "Slit width", "m"],
    ["height", "Slit height", "m"],
    ["height", "Slit radius", "m"],
    ["thickness", "Filter Thickness", "\u03bcm"],
]

VARIABLES = numpy.array(VARIABLES)

class ScanVariableLoopPoint(AbstractScanVariableLoopPoint):

    name = "Scanning Variable Loop Point"
    description = "Tools: LoopPoint"
    icon = "icons/cycle_variable.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 0.1
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    variable_name_id = Setting(8)

    def __init__(self):
        super(ScanVariableLoopPoint, self).__init__()

    def has_variable_list(self): return True

    def create_variable_list_box(self, box):
        gui.comboBox(box, self, "variable_name_id", label="Variable Name", labelWidth=120,
                     items=VARIABLES[:, 1],
                     callback=self.set_VariableName, sendSelectedValue=False, orientation="horizontal")

    def set_VariableName(self):
        self.variable_name = VARIABLES[self.variable_name_id, 0]
        self.variable_display_name = VARIABLES[self.variable_name_id, 1]
        self.variable_um = VARIABLES[self.variable_name_id, 2]

import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ScanVariableLoopPoint()
    ow.show()
    a.exec_()
    ow.saveSettings()
