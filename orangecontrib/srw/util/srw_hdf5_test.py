# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2018 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/

__authors__ = ["M Sanchez del Rio"]
__license__ = "MIT"
__date__ = "27/05/2018"

"""

test write/read SRW wavefront to hdf5 files

test based on Example 4 of the SRW distribution (undulator + lens)

"""

import unittest
import numpy
from srwlib import *

from srw_hdf5 import save_wfr_2_hdf5, load_hdf5_2_wfr, load_hdf5_2_dictionary
import os


class SRWhdf5Test(unittest.TestCase):

    def create_source(self):

        #############################################################################
        # SRWLIB Example#4: Calculating synchrotron (undulator) radiation electric field (from one electron)
        # and simulating wavefront propagation through a simple optical system
        # v 0.06
        #############################################################################

        print('SRWLIB Python Example # 4:')
        print('Calculating synchrotron (undulator) radiation electric field (from one electron) and performing simulation of wavefront propagation through a simple optical system')

        #***********Undulator
        numPer = 40.5 #Number of ID Periods (without counting for terminations; semi-integer => symmetric vs long. pos.; to allow harmonics to be symmetric or anti-symmetric?)
        undPer = 0.049 #Period Length [m]
        Bx = 0.57/3. #Peak Horizontal field [T]
        By = 0.57 #Peak Vertical field [T]
        phBx = 0 #Initial Phase of the Horizontal field component
        phBy = 0 #Initial Phase of the Vertical field component
        sBx = -1 #Symmetry of the Horizontal field component vs Longitudinal position
        sBy = 1 #Symmetry of the Vertical field component vs Longitudinal position
        xcID = 0 #Transverse Coordinates of Undulator Center [m]
        ycID = 0
        zcID = 0 #Longitudinal Coordinate of Undulator Center [m]

        und = SRWLMagFldU([SRWLMagFldH(1, 'v', By, phBy, sBy, 1), SRWLMagFldH(1, 'h', Bx, phBx, sBx, 1)], undPer, numPer) #Ellipsoidal Undulator
        magFldCnt = SRWLMagFldC([und], array('d', [xcID]), array('d', [ycID]), array('d', [zcID])) #Container of all Field Elements

        #***********Electron Beam
        elecBeam = SRWLPartBeam()
        elecBeam.Iavg = 0.5 #Average Current [A]
        elecBeam.partStatMom1.x = 0. #Initial Transverse Coordinates (initial Longitudinal Coordinate will be defined later on) [m]
        elecBeam.partStatMom1.y = 0.
        elecBeam.partStatMom1.z = -0.5*undPer*(numPer + 4) #Initial Longitudinal Coordinate (set before the ID)
        elecBeam.partStatMom1.xp = 0 #Initial Relative Transverse Velocities
        elecBeam.partStatMom1.yp = 0
        elecBeam.partStatMom1.gamma = 3./0.51099890221e-03 #Relative Energy

        #***********Precision Parameters for SR calculation
        meth = 1 #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
        relPrec = 0.01 #relative precision
        zStartInteg = 0 #longitudinal position to start integration (effective if < zEndInteg)
        zEndInteg = 0 #longitudinal position to finish integration (effective if > zStartInteg)
        npTraj = 20000 #Number of points for trajectory calculation
        useTermin = 1 #Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
        sampFactNxNyForProp = 1 #sampling factor for adjusting nx, ny (effective if > 0)
        arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

        #***********Initial Wavefront
        wfr = SRWLWfr()
        wfr.allocate(1, 100, 100) #Numbers of points vs Photon Energy, Horizontal and Vertical Positions (may be modified by the library!)
        wfr.mesh.zStart = 20. #Longitudinal Position [m] at which SR has to be calculated
        wfr.mesh.eStart = 1095. #1090. #Initial Photon Energy [eV]
        wfr.mesh.eFin = 1095. #1090. #Final Photon Energy [eV]
        wfr.mesh.xStart = -0.001 #Initial Horizontal Position [m]
        wfr.mesh.xFin = 0.001 #Final Horizontal Position [m]
        wfr.mesh.yStart = -0.001 #Initial Vertical Position [m]
        wfr.mesh.yFin = 0.001 #Final Vertical Position [m]
        wfr.partBeam = elecBeam


        #**********************Calculation (SRWLIB function calls) and post-processing
        print('   Performing Initial Electric Field calculation ... ', end='')
        srwl.CalcElecFieldSR(wfr, 0, magFldCnt, arPrecPar)
        print('done')

        return wfr


    def propagate_beamline(self,wfr):

        #############################################################################
        # SRWLIB Example#4: Calculating synchrotron (undulator) radiation electric field (from one electron)
        # and simulating wavefront propagation through a simple optical system
        # v 0.06
        #############################################################################


        #***********Optical Elements and Propagation Parameters
        fx = wfr.mesh.zStart/2 #Lens focal lengths
        fy = wfr.mesh.zStart/2
        optLens = SRWLOptL(fx, fy) #Lens
        optDrift = SRWLOptD(wfr.mesh.zStart) #Drift space

        propagParLens = [1, 1, 1., 0, 0, 1., 1.5, 1., 1.5, 0, 0, 0]
        propagParDrift = [1, 1, 1., 0, 0, 1., 1., 1., 1., 0, 0, 0]
        #Wavefront Propagation Parameters:
        #[0]: Auto-Resize (1) or not (0) Before propagation
        #[1]: Auto-Resize (1) or not (0) After propagation
        #[2]: Relative Precision for propagation with Auto-Resizing (1. is nominal)
        #[3]: Allow (1) or not (0) for semi-analytical treatment of the quadratic (leading) phase terms at the propagation
        #[4]: Do any Resizing on Fourier side, using FFT, (1) or not (0)
        #[5]: Horizontal Range modification factor at Resizing (1. means no modification)
        #[6]: Horizontal Resolution modification factor at Resizing
        #[7]: Vertical Range modification factor at Resizing
        #[8]: Vertical Resolution modification factor at Resizing
        #[9]: Type of wavefront Shift before Resizing (not yet implemented)
        #[10]: New Horizontal wavefront Center position after Shift (not yet implemented)
        #[11]: New Vertical wavefront Center position after Shift (not yet implemented)
        optBL = SRWLOptC([optLens, optDrift], [propagParLens, propagParDrift]) #"Beamline" - Container of Optical Elements (together with the corresponding wavefront propagation instructions)


        print('   Simulating Electric Field Wavefront Propagation ... ', end='')
        srwl.PropagElecField(wfr, optBL)
        print('done')

        return wfr

    def test_source(self):

        print("\n#\n# SRW hdf5 test write/load source\n#\n")

        wfr = self.create_source()

        save_wfr_2_hdf5(wfr,"tmp1.h5",intensity=True,phase=True,overwrite=True)

        wfr_loaded = load_hdf5_2_wfr("tmp1.h5","wfr")

        save_wfr_2_hdf5(wfr_loaded,"tmp2.h5",intensity=True,phase=True,overwrite=True)


        wf1 = load_hdf5_2_dictionary("tmp1.h5","wfr")
        wf2 = load_hdf5_2_dictionary("tmp2.h5","wfr")
        print("comparing wavefront at source")
        for key in wf1.keys():
            print("   checking field: ",key)
            numpy.testing.assert_almost_equal(wf1[key],wf2[key])

        os.remove("tmp1.h5")
        os.remove("tmp2.h5")


    def test_propagation(self):

        # calculate:
        wfr = self.create_source()

        save_wfr_2_hdf5(wfr,"tmp3.h5",intensity=True,phase=True,overwrite=True)

        wfr_end = self.propagate_beamline(wfr)

        save_wfr_2_hdf5(wfr_end,"tmp3.h5",intensity=True,phase=False,overwrite=False,subgroupname="wfr_end")

        # load:
        wfr_loaded = load_hdf5_2_wfr("tmp3.h5","wfr")

        save_wfr_2_hdf5(wfr_loaded,"tmp3bis.h5",intensity=True,phase=False,overwrite=True)

        wfr_end2 = self.propagate_beamline(wfr_loaded)

        save_wfr_2_hdf5(wfr_end2,"tmp3bis.h5",intensity=True,phase=True,overwrite=False,subgroupname="wfr_end")

        wf1_source = load_hdf5_2_dictionary("tmp3.h5","wfr")
        wf2_source = load_hdf5_2_dictionary("tmp3bis.h5","wfr")
        print("comparing wavefront at source")
        for key in wf1_source.keys():
            print("   checking field: ",key)
            numpy.testing.assert_almost_equal(wf1_source[key],wf2_source[key])

        wf1_end = load_hdf5_2_dictionary("tmp3.h5","wfr_end")
        wf2_end = load_hdf5_2_dictionary("tmp3bis.h5","wfr_end")
        print("comparing wavefront propagated")
        for key in wf1_source.keys():
            print("   checking field: ",key)
            numpy.testing.assert_almost_equal(1e-6*wf1_end[key],1e-6*wf2_end[key],1)

        os.remove("tmp3.h5")
        os.remove("tmp3bis.h5")