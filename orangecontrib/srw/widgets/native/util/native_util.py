import numpy
from scipy.interpolate import RectBivariateSpline

from srxraylib.util.data_structures import ScaledMatrix, ScaledArray


def calculate_degree_of_coherence_vs_sum_and_difference_from_file(filename_in, mode="Igor"):

    coor, coor_conj, mutual_intensity  = load_mutual_intensity_file(filename_in)

    if mode == "Igor":
        sum, difference, degree_of_coherence = calculate_degree_of_coherence_vs_sum_and_difference_igor_macro(coor, coor_conj, mutual_intensity)
    else:
        sum, difference, degree_of_coherence = calculate_degree_of_coherence_vs_sum_and_difference(coor, coor_conj, mutual_intensity)

    return sum, difference, degree_of_coherence


#-----------------------------------------------------------
#FROM OLEG'S IGOR MACRO ------------------------------------
#-----------------------------------------------------------
def calculate_degree_of_coherence_vs_sum_and_difference_igor_macro(coor, coor_conj, mutual_intensity, rel_thresh=1e-4):

    nmInMutInt = ScaledMatrix(x_coord=coor, y_coord=coor_conj, z_values=mutual_intensity, interpolator=True)

    xStart = nmInMutInt.offset_x()
    xNp = nmInMutInt.size_x()
    xStep = nmInMutInt.delta_x()
    xEnd = xStart + (xNp - 1)*xStep

    yStart = nmInMutInt.offset_y()
    yNp =  nmInMutInt.size_y()
    yStep = nmInMutInt.delta_y()
    yEnd = yStart + (yNp - 1)*yStep

    xNpNew = 2*xNp - 1
    yNpNew = 2*yNp - 1

    print("Creating Matrix wInMutCohRes")

    wInMutCohRes = ScaledMatrix(x_coord=numpy.zeros(xNpNew),
                                y_coord=numpy.zeros(yNpNew),
                                z_values=numpy.zeros((xNpNew, yNpNew)),
                                interpolator=False)

    xHalfNp = round(xNp*0.5)
    yHalfNp = round(yNp*0.5)

    wInMutCohRes.set_scale_from_steps(axis=0, initial_scale_value=(xStart - xHalfNp*xStep), scale_step=xStep)
    wInMutCohRes.set_scale_from_steps(axis=1, initial_scale_value=(yStart - yHalfNp*yStep), scale_step=yStep)

    dimx, dimy = wInMutCohRes.shape()
    for inx in range(0, dimx):
        for iny in range(0,dimy):
            x = wInMutCohRes.get_x_value(inx)
            y = wInMutCohRes.get_y_value(iny)

            wInMutCohRes.set_z_value(inx, iny,
                                     nmInMutInt.interpolate_value(x, y)*
                                     srwUtiNonZeroIntervB(x,
                                                          xStart,
                                                          xEnd)*
                                     srwUtiNonZeroIntervB(y,
                                                          yStart,
                                                          yEnd))

    wInMutCohRes.compute_interpolator()

    print("Done")

    print("Creating Matrix wMutCohNonRot")

    wMutCohNonRot = ScaledMatrix(x_coord=nmInMutInt.get_x_values(),
                                 y_coord=nmInMutInt.get_y_values(),
                                 z_values=numpy.zeros(nmInMutInt.shape()),
                                 interpolator=False)

    abs_thresh = rel_thresh*abs(nmInMutInt.interpolate_value(0, 0))

    dimx, dimy = wMutCohNonRot.shape()
    for inx in range(0, dimx):
        for iny in range(0, dimy):
            x = wMutCohNonRot.get_x_value(inx)
            y = wMutCohNonRot.get_y_value(iny)

            wMutCohNonRot.set_z_value(inx, iny,
                                      numpy.abs(wInMutCohRes.interpolate_value(x, y))/
                                      (numpy.sqrt(abs(wInMutCohRes.interpolate_value(x, x)*wInMutCohRes.interpolate_value(y, y))) + abs_thresh))


    wMutCohNonRot.compute_interpolator()

    print("Done")
    print("Creating Matrix nmResDegCoh")

    nmResDegCoh = ScaledMatrix(x_coord=nmInMutInt.get_x_values(),
                               y_coord=nmInMutInt.get_y_values(),
                               z_values=numpy.zeros(nmInMutInt.shape()),
                               interpolator=False)

    xmin = wMutCohNonRot.offset_x()
    nx = wMutCohNonRot.size_x()
    xstep = wMutCohNonRot.delta_x()
    xmax = xmin + (nx - 1)*xstep

    ymin = wMutCohNonRot.offset_y()
    ny = wMutCohNonRot.size_y()
    ystep = wMutCohNonRot.delta_y()
    ymax = ymin + (ny - 1)*ystep


    dimx, dimy = nmResDegCoh.shape()
    for inx in range(0, dimx):
        for iny in range(0, dimy):
            x = nmResDegCoh.get_x_value(inx)
            y = nmResDegCoh.get_y_value(iny)

            nmResDegCoh.set_z_value(inx, iny, srwUtiInterp2DBilin((x+y),
                                                                  (x-y),
                                                                  wMutCohNonRot,
                                                                  xmin,
                                                                  xmax,
                                                                  xstep,
                                                                  ymin,
                                                                  ymax,
                                                                  ystep))

    return nmResDegCoh.get_x_values(), nmResDegCoh.get_y_values(), nmResDegCoh.get_z_values()

def calculate_degree_of_coherence_vs_sum_and_difference(coor, coor_conj, mutual_intensity, set_extrapolated_to_zero=True):
    """
    Calculates the modulus of the complex degree of coherence versus coordinates x1+x2 and x1-x2
        (or y1+y2 and y1-y2)

    :param coor: the x1 or y1 coordinate
    :param coor_conj: the x2 or y2 coordinate
    :param mutual_intensity: the mutual intensity vs (x1,x2) [or y2,y3]
    :param filename: Name of output hdf5 filename (optional, default=None, no output file)
    :return: x1,x2,DOC
    """

    interpolator0 = RectBivariateSpline(coor, coor_conj, mutual_intensity, bbox=[None, None, None, None], kx=3, ky=3, s=0)

    X = numpy.outer(coor,numpy.ones_like(coor_conj))
    Y = numpy.outer(numpy.ones_like(coor),coor_conj)

    nmResDegCoh_z = numpy.abs(interpolator0( X+Y,X-Y, grid=False)) /\
                numpy.sqrt(numpy.abs(interpolator0( X+Y,X+Y, grid=False))) /\
                numpy.sqrt(numpy.abs(interpolator0( X-Y,X-Y, grid=False)))

    if set_extrapolated_to_zero:
        nx,ny = nmResDegCoh_z.shape

        idx = numpy.outer(numpy.arange(nx),numpy.ones((ny)))
        idy = numpy.outer(numpy.ones((nx)),numpy.arange(ny))

        mask = numpy.ones_like(idx)

        bad = numpy.where(idy < 1.*(idx-nx/2)*ny/nx)
        mask[ bad ] = 0

        bad = numpy.where(idy > ny - 1.*(idx-nx/2)*ny/nx)
        mask[ bad ] = 0

        bad = numpy.where(idy < 0.5*ny - 1.*idx*ny/nx)
        mask[ bad ] = 0

        bad = numpy.where(idy > 0.5*ny + 1.*idx*ny/nx)
        mask[ bad ] = 0

        nmResDegCoh_z *= mask


    return coor, coor_conj, nmResDegCoh_z

def load_intensity_file(filename):
    data, dump, allrange, arLabels, arUnits = file_load(filename)

    dim_x = allrange[5]
    dim_y = allrange[8]
    np_array = data.reshape((dim_y, dim_x))
    np_array = np_array.transpose()
    x_coordinates = numpy.linspace(allrange[3], allrange[4], dim_x)
    y_coordinates = numpy.linspace(allrange[6], allrange[7], dim_y)

    return x_coordinates, y_coordinates, np_array


def load_mutual_intensity_file(filename):
    data, dump, allrange, arLabels, arUnits = file_load(filename)

    dim_x = allrange[5]
    dim_y = allrange[8]

    dim = 1
    if dim_x > 1: dim = dim_x
    elif dim_y > 1: dim = dim_y

    np_array = data.reshape((dim, dim))
    np_array = np_array.transpose()

    if dim_x > 1:
        coordinates = numpy.linspace(allrange[3], allrange[4], dim_x)
        conj_coordinates = numpy.linspace(allrange[3], allrange[4], dim_x)
    elif dim_y > 1:
        coordinates = numpy.linspace(allrange[6], allrange[7], dim_y)
        conj_coordinates = numpy.linspace(allrange[6], allrange[7], dim_y)
    else:
        coordinates = None
        conj_coordinates = None

    return coordinates, conj_coordinates, np_array

# copied from SRW's uti_plot_com and slightly  modified (no _enum)
def file_load(_fname, _read_labels=1):
    import numpy as np
    nLinesHead = 11
    hlp = []

    with open(_fname,'r') as f:
        for i in range(nLinesHead):
            hlp.append(f.readline())

    ne, nx, ny = [int(hlp[i].replace('#','').split()[0]) for i in [3,6,9]]
    ns = 1
    testStr = hlp[nLinesHead - 1]
    if testStr[0] == '#':
        ns = int(testStr.replace('#','').split()[0])

    e0,e1,x0,x1,y0,y1 = [float(hlp[i].replace('#','').split()[0]) for i in [1,2,4,5,7,8]]

    data = numpy.squeeze(numpy.loadtxt(_fname, dtype=numpy.float64)) #get data from file (C-aligned flat)

    allrange = e0, e1, ne, x0, x1, nx, y0, y1, ny

    arLabels = ['Photon Energy', 'Horizontal Position', 'Vertical Position', 'Intensity']
    arUnits = ['eV', 'm', 'm', 'ph/s/.1%bw/mm\u00b2']

    if _read_labels:

        arTokens = hlp[0].split(' [')
        arLabels[3] = arTokens[0].replace('#','')
        arUnits[3] = '';
        if len(arTokens) > 1:
            arUnits[3] = arTokens[1].split('] ')[0]

        for i in range(3):
            arTokens = hlp[i*3 + 1].split()
            nTokens = len(arTokens)
            nTokensLabel = nTokens - 3
            nTokensLabel_mi_1 = nTokensLabel - 1
            strLabel = ''
            for j in range(nTokensLabel):
                strLabel += arTokens[j + 2]
                if j < nTokensLabel_mi_1: strLabel += ' '
            arLabels[i] = strLabel
            arUnits[i] = arTokens[nTokens - 1].replace('[','').replace(']','')

    return data, None, allrange, arLabels, arUnits


def srwUtiNonZeroIntervB(p, pmin, pmax):
    if((p < pmin) or (p > pmax)):
        return 0.
    else:
        return 1.

def srwUtiInterp2DBilin(x, y, matrix, xmin, xmax, xstep, ymin, ymax, ystep):

    if((x < xmin) or (x > xmax) or (y < ymin) or (y > ymax)):
        return 0

    x0 = xmin + numpy.trunc((x - xmin)/xstep)*xstep
    if(x0 >= xmax): x0 = xmax - xstep

    x1 = x0 + xstep

    y0 = ymin + numpy.trunc((y - ymin)/ystep)*ystep
    if(y0 >= ymax): y0 = ymax - ystep

    y1 = y0 + ystep

    t = (x - x0)/xstep
    u = (y - y0)/ystep

    return (1 - t)*(1 - u)*(matrix.interpolate_value(x0, y0)) + \
           t*(1 - u)*(matrix.interpolate_value(x1, y0)) + \
           t*u*(matrix.interpolate_value(x1, y1)) + \
           (1 - t)*u*(matrix.interpolate_value(x0, y1))
