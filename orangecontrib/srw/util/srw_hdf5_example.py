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

__authors__ = ["R Celestre, M Sanchez del Rio"]
__license__ = "MIT"
__date__ = "27/05/2018"

"""

Example of dumping and loading SRW wavefronts to hdf5 files

"""


import numpy
from srwlib import *

from srw_hdf5 import save_wfr_2_hdf5, load_hdf5_2_wfr, load_hdf5_2_dictionary


import scipy.constants as codata

try:
    import matplotlib.pylab as plt
    # plt.switch_backend("Qt5Agg")
    from srxraylib.plot.gol import plot_image
except:
    raise Exception("Failed to import graphics tools.")


#
# main code
#

def plot_wfr(wfr,kind='intensity',show=True,xtitle="X",ytitle="Y",title="",aspect='auto'):

	if kind == 'intensity':
		ar1 = array('f', [0]*wfr.mesh.nx*wfr.mesh.ny) # "flat" 2D array to take intensity data
		srwl.CalcIntFromElecField(ar1, wfr, 6, 0, 3, wfr.mesh.eStart, 0, 0)
	elif kind == 'phase':
		ar1 = array('d', [0]*wfr.mesh.nx*wfr.mesh.ny) # "flat" array to take 2D phase data (note it should be 'd')
		srwl.CalcIntFromElecField(ar1, wfr, 0, 4, 3, wfr.mesh.eStart, 0, 0)
	else:
		raise Exception("Unknown kind of calculation: %s"%(kind))

	arxx = numpy.array(ar1)
	arxx = arxx.reshape((wfr.mesh.ny,wfr.mesh.nx)).T
	x = numpy.linspace(1e6*wfr.mesh.xStart, 1e6*wfr.mesh.xFin, wfr.mesh.nx)
	y = numpy.linspace(1e6*wfr.mesh.yStart, 1e6*wfr.mesh.yFin, wfr.mesh.ny)

	plot_image(arxx, x, y, xtitle="%s (%d pixels)"%(xtitle,x.size), ytitle="%s (%d pixels)"%(ytitle,y.size), title=title, aspect=aspect,show=show)

	return ar1,x,y

def calculate_undulator_source(Source="EBS",pMltLr=28.3,do_plots=True):
    #############################################################################
    # Photon source
    #********************************Undulator parameters
    numPer = 77			# Number of ID Periods
    undPer = 0.0183		# Period Length [m]
    phB = 0	        	# Initial Phase of the Horizontal field component
    sB = 1		        # Symmetry of the Horizontal field component vs Longitudinal position
    xcID = 0 			# Transverse Coordinates of Undulator Center [m]
    ycID = 0
    zcID = 0
    n = 1
    beamE = 17
    #********************************Storage ring parameters

    # Wavelength = 1E-10*12.39841975/beamE
    Wavelength = codata.h*codata.c/codata.e/(1e3*beamE)


    # these first order moments CONTAIN the initial condition of the electron (X,X',Y,Y') (energy comes later)
    eBeam = SRWLPartBeam()
    eBeam.Iavg = 0.2             # average Current [A]
    eBeam.partStatMom1.x = 0.
    eBeam.partStatMom1.y = 0.
    eBeam.partStatMom1.z = -0.5*undPer*(numPer + 4) # initial Longitudinal Coordinate (set before the ID)
    eBeam.partStatMom1.xp = 0.   					# initial Relative Transverse Velocities
    eBeam.partStatMom1.yp = 0.

    electron_rest_energy_in_GeV = codata.electron_mass*codata.c**2/codata.e*1e-9
    KtoBfactor = codata.e/(2*pi*codata.electron_mass*codata.c)

    #
    # obviously these emittances value (with exception of the electron_energy) are not used for
    # the single electron calculation
    #
    if (Source.lower() == 'ebs'):
        # e- beam paramters (RMS) EBS
        sigEperE = 9.3E-4 			# relative RMS energy spread
        sigX  = 30.3E-06			# horizontal RMS size of e-beam [m]
        sigXp = 4.4E-06				# horizontal RMS angular divergence [rad]
        sigY  = 3.6E-06				# vertical RMS size of e-beam [m]
        sigYp = 1.46E-06			# vertical RMS angular divergence [rad]
        electron_energy_in_GeV = 6.00
    else:
        # e- beam paramters (RMS) ESRF @ low beta
        sigEperE = 1.1E-3 			# relative RMS energy spread
        sigX     = 48.6E-06			# horizontal RMS size of e-beam [m]
        sigXp    = 106.9E-06			# horizontal RMS angular divergence [rad]
        sigY     = 3.5E-06				# vertical RMS size of e-beam [m]
        sigYp    = 1.26E-06			# vertical RMS angular divergence [rad]
        electron_energy_in_GeV = 6.04

    eBeam.partStatMom1.gamma = electron_energy_in_GeV/electron_rest_energy_in_GeV # Relative Energy
    K = sqrt(2)*sqrt(((Wavelength*2*n*eBeam.partStatMom1.gamma**2)/undPer)-1)
    print("K: ",K)
    B = K/(undPer*KtoBfactor)	# Peak Horizontal field [T] (undulator)


    # 2nd order stat. moments
    eBeam.arStatMom2[0] = sigX*sigX			 # <(x-<x>)^2>
    eBeam.arStatMom2[1] = 0					 # <(x-<x>)(x'-<x'>)>
    eBeam.arStatMom2[2] = sigXp*sigXp		 # <(x'-<x'>)^2>
    eBeam.arStatMom2[3] = sigY*sigY		     # <(y-<y>)^2>
    eBeam.arStatMom2[4] = 0					 # <(y-<y>)(y'-<y'>)>
    eBeam.arStatMom2[5] = sigYp*sigYp		 # <(y'-<y'>)^2>
    eBeam.arStatMom2[10] = sigEperE*sigEperE # <(E-<E>)^2>/<E>^2

    # Electron trajectory
    eTraj = 0

    # Precision parameters
    arPrecSR = [0]*7
    arPrecSR[0] = 1		# SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
    arPrecSR[1] = 0.01	# relative precision
    arPrecSR[2] = 0		# longitudinal position to start integration (effective if < zEndInteg)
    arPrecSR[3] = 0		# longitudinal position to finish integration (effective if > zStartInteg)
    arPrecSR[4] = 20000	# Number of points for trajectory calculation
    arPrecSR[5] = 1		# Use "terminating terms"  or not (1 or 0 respectively)
    arPrecSR[6] = 0		# sampling factor for adjusting nx, ny (effective if > 0)	# -1 @Petra


    und = SRWLMagFldU([SRWLMagFldH(n, 'v', B, phB, sB, 1)], undPer, numPer)

    magFldCnt = SRWLMagFldC([und], array('d', [xcID]), array('d', [ycID]), array('d', [zcID]))

    #********************************Wavefronts
    # Monochromatic wavefront
    wfr = SRWLWfr()
    wfr.allocate(1, 512, 256)  # Photon Energy, Horizontal and Vertical Positions
    wfr.mesh.zStart = pMltLr
    wfr.mesh.eStart = beamE*1E3
    wfr.mesh.eFin = wfr.mesh.eStart
    wfr.mesh.xStart = -2.5*1E-3
    wfr.mesh.xFin = - wfr.mesh.xStart
    wfr.mesh.yStart = -1*1E-3
    wfr.mesh.yFin = - wfr.mesh.yStart
    wfr.partBeam = eBeam

    print('source calculation starts ... ')
    srwl.CalcElecFieldSR(wfr, eTraj, magFldCnt, arPrecSR)

    #
    # plot source
    #
    if do_plots:
        plot_wfr(wfr,kind='intensity',title='Source Intensity at ' + str(wfr.mesh.eStart) + ' eV',
                 xtitle='Horizontal Position [\u03bcm]',
                 ytitle='Vertical Position [\u03bcm]',aspect=None,show=True)


    print('\nsource calculation finished\n')
    return wfr

def propagate_beamline(wfr,do_plots=True):

    print("beamline calculations starts...")

    pMltLr = 28.3
    pSlt   = 40


    Drft1  = SRWLOptD((pSlt-pMltLr))

    W_MltLr = 13*1E-3
    L_MltLr = 120*1E-3
    grzAngl = 31.42*1E-3
    oeAptrMltLr = SRWLOptA('r','a',L_MltLr*numpy.sin(grzAngl),W_MltLr)

    fMltLrh = 1/((1/pMltLr)+(1/(pSlt-pMltLr)))
    fMltLrv =1E23
    oeMltLr = SRWLOptL(_Fx=fMltLrh, _Fy=fMltLrv)


    #============= Wavefront Propagation Parameters =======================#
    #                [ 0] [1] [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9] [10] [11]
    ppAptrMltLr		=[ 0,  0, 1.,   0,   0,  1.,  4.,  1.,  4.,   0,   0,   0]
    ppMltLr			=[ 0,  0, 1.,   0,   0,  1.,  1.,  1.,  1.,   0,   0,   0]
    ppDrft1 		=[ 0,  0, 1.,   2,   0,  1.,  1.,  1.,  1.,   0,   0,   0]


    optBL = SRWLOptC(
                    [oeAptrMltLr,   oeMltLr,   Drft1],
                    [ppAptrMltLr,   ppMltLr, ppDrft1]
                     )

    srwl.PropagElecField(wfr, optBL)

    if do_plots:
        plot_wfr(wfr,kind='intensity',title='Focal Intensity at ' + str(wfr.mesh.eStart) + ' eV',
                 xtitle='Horizontal Position [\u03bcm]',
                 ytitle='Vertical Position [\u03bcm]',show=True)

    print('\nbeamline calculation finished\n')
    return wfr

if __name__ == "__main__":

    do_calculate = True
    do_load = True
    do_compare = True

    show_plots = False

    if do_calculate:
        wfr = calculate_undulator_source(do_plots=show_plots)

        save_wfr_2_hdf5(wfr,"tmp2.h5",intensity=True,phase=True,overwrite=True)

        wfr_end = propagate_beamline(wfr,do_plots=show_plots)

        save_wfr_2_hdf5(wfr_end,"tmp2.h5",intensity=True,phase=False,overwrite=False,subgroupname="wfr_end")

    if do_load:
        wfr_loaded = load_hdf5_2_wfr("tmp2.h5","wfr")

        save_wfr_2_hdf5(wfr_loaded,"tmp2bis.h5",intensity=True,phase=False,overwrite=True)

        wfr_end2 = propagate_beamline(wfr_loaded,do_plots=False)

        save_wfr_2_hdf5(wfr_end2,"tmp2bis.h5",intensity=True,phase=True,overwrite=False,subgroupname="wfr_end")



    if do_compare:
        wf1_source = load_hdf5_2_dictionary("tmp2.h5","wfr")
        wf2_source = load_hdf5_2_dictionary("tmp2bis.h5","wfr")
        print("comparing wavefront at source")
        for key in wf1_source.keys():
            print("   checking field: ",key)
            numpy.testing.assert_almost_equal(wf1_source[key],wf2_source[key])

        wf1_end = load_hdf5_2_dictionary("tmp2.h5","wfr_end")
        wf2_end = load_hdf5_2_dictionary("tmp2bis.h5","wfr_end")
        print("comparing wavefront propagated")
        for key in wf1_source.keys():
            print("   checking field: ",key)
            numpy.testing.assert_almost_equal(1e-6*wf1_end[key],1e-6*wf2_end[key],1)
