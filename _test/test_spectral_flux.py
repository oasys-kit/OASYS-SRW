from srwlib import *
from uti_plot import *
import numpy

if not srwl_uti_proc_is_master(): exit()

####################################################
# LIGHT SOURCE

part_beam = SRWLPartBeam()
part_beam.Iavg               = 0.32
part_beam.partStatMom1.x     = 0.0
part_beam.partStatMom1.y     = 0.0
part_beam.partStatMom1.z     = -2.2
part_beam.partStatMom1.xp    = 0.0
part_beam.partStatMom1.yp    = 0.0
part_beam.partStatMom1.gamma = 3913.9023956982596
part_beam.arStatMom2[0]      = 6.395841000000001e-08
part_beam.arStatMom2[1]      = 0.0
part_beam.arStatMom2[2]      = 8.300161e-10
part_beam.arStatMom2[3]      = 3.4003359999999997e-10
part_beam.arStatMom2[4]      = 0.0
part_beam.arStatMom2[5]      = 2.7405225e-11
part_beam.arStatMom2[10]     = 4.9e-07

magnetic_fields = []
magnetic_fields.append(SRWLMagFldH(1, 'v', 0.20562712276984735, 0, 1, 1))
magnetic_structure = SRWLMagFldU(magnetic_fields,0.1,40.0)
magnetic_field_container = SRWLMagFldC([magnetic_structure], array('d', [0]), array('d', [0]), array('d', [0]))

mesh = SRWLRadMesh(_eStart=100,
                   _eFin  =1200,
                   _ne    =1100,
                   _xStart=0.0,
                   _xFin  =0.0,
                   _nx    =1,
                   _yStart=0,
                   _yFin  =0,
                   _ny    =1,
                   _zStart=11.517)

wfr = SRWLWfr()
wfr.allocate(mesh.ne, mesh.nx, mesh.ny)
wfr.mesh = mesh
wfr.partBeam = part_beam

initial_mesh = deepcopy(wfr.mesh)
srwl.CalcElecFieldSR(wfr, 0, magnetic_field_container, [1,0.01,0.0,0.0,100000,1,0.0])

print('done')
print('   Extracting Intensity from calculated Electric Field ... ', end='')
arI1 = array('f', [0]*wfr.mesh.ne)
srwl.CalcIntFromElecField(arI1, wfr, 6, 0, 0, wfr.mesh.eStart, wfr.mesh.xStart, wfr.mesh.yStart)
print('done')

#save ascii file with intensity
#srwl_uti_save_intens_ascii(arI, mesh0, <file_path>)
uti_plot1d(arI1, [wfr.mesh.eStart, wfr.mesh.eFin, wfr.mesh.ne], ['Photon Energy [eV]', 'Intensity [ph/s/.1%bw/mm^2]', 'On-Axis Spectrum'])

uti_plot_show()

