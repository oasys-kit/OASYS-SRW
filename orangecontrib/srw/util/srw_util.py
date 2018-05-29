import numpy, decimal
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from matplotlib.patches import FancyArrowPatch, ArrowStyle

from oasys.widgets import gui

from silx.gui.plot.ImageView import ImageView

import matplotlib

class SRWStatisticData:
    def __init__(self, total = 0.0):
        self.total = total
        
class SRWHistoData(SRWStatisticData):
    def __init__(self, total = 0.0,
                 fwhm = 0.0,
                 x_fwhm_i = 0.0,
                 x_fwhm_f = 0.0,
                 y_fwhm = 0.0):
        super().__init__(total)
        self.fwhm = fwhm
        self.x_fwhm_i = x_fwhm_i
        self.x_fwhm_f = x_fwhm_f
        self.y_fwhm = y_fwhm

class SRWPlotData(SRWStatisticData):
    def __init__(self, total = 0.0,
                 fwhm_h = 0.0,
                 fwhm_v = 0.0):
        super().__init__(total)
        self.fwhm_h = fwhm_h
        self.fwhm_v = fwhm_v

class SRWPlot:

    _is_conversione_active = True

    #########################################################################################
    #
    # FOR TEMPORARY USE: FIX AN ERROR IN PYMCA.PLOT.IMAGEWIEW
    #
    #########################################################################################


    @classmethod
    def set_conversion_active(cls, is_active=True):
        SRWPlot._is_conversione_active = is_active


    #########################################################################################
    #
    # WIDGET FOR DETAILED PLOT
    #
    #########################################################################################

    class InfoBoxWidget(QWidget):
        total_field = ""
        fwhm_h_field = ""
        fwhm_v_field = ""

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, is_2d=True):
            super(SRWPlot.InfoBoxWidget, self).__init__()

            info_box_inner=gui.widgetBox(self, "Info")
            info_box_inner.setFixedHeight(515*y_scale_factor)
            info_box_inner.setFixedWidth(230*x_scale_factor)

            self.total = gui.lineEdit(info_box_inner, self, "total_field", "Total", tooltip="Total", labelWidth=115, valueType=str, orientation="horizontal")

            label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

            self.label_h = QLabel("FWHM ")
            self.label_h.setFixedWidth(115)
            palette =  QPalette(self.label_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_h)
            self.fwhm_h = gui.lineEdit(label_box_1, self, "fwhm_h_field", "", tooltip="FWHM", labelWidth=115, valueType=str, orientation="horizontal")

            if is_2d:
                label_box_2 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.label_v = QLabel("FWHM ")
                self.label_v.setFixedWidth(115)
                palette =  QPalette(self.label_h.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_v)
                self.fwhm_v = gui.lineEdit(label_box_2, self, "fwhm_v_field", "", tooltip="FWHM", labelWidth=115, valueType=str, orientation="horizontal")

            self.total.setReadOnly(True)
            font = QFont(self.total.font())
            font.setBold(True)
            self.total.setFont(font)
            palette = QPalette(self.total.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total.setPalette(palette)

            self.fwhm_h.setReadOnly(True)
            font = QFont(self.total.font())
            font.setBold(True)
            self.fwhm_h.setFont(font)
            palette = QPalette(self.fwhm_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.fwhm_h.setPalette(palette)

            if is_2d:
                self.fwhm_v.setReadOnly(True)
                font = QFont(self.fwhm_v.font())
                font.setBold(True)
                self.fwhm_v.setFont(font)
                palette = QPalette(self.fwhm_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.fwhm_v.setPalette(palette)

        def clear(self):
            self.total.setText("0.0")
            self.fwhm_h.setText("0.0000")
            if hasattr(self, "fwhm_v"):  self.fwhm_v.setText("0.0000")

    class Detailed1DWidget(QWidget):

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(SRWPlot.Detailed1DWidget, self).__init__()

            self.plot_canvas = gui.plotWindow(roi=False, control=False, position=True, logScale=False)
            self.plot_canvas.setDefaultPlotLines(True)
            self.plot_canvas.setActiveCurveColor(color='blue')
            self.plot_canvas.setMinimumWidth(590*x_scale_factor)
            self.plot_canvas.setMaximumWidth(590*x_scale_factor)

            self.info_box = SRWPlot.InfoBoxWidget(x_scale_factor, y_scale_factor, is_2d=False)

            layout = QGridLayout()

            layout.addWidget(   self.info_box, 0, 1, 1, 1)
            layout.addWidget(self.plot_canvas, 0, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

        def plot_1D(self, ticket, col, title, xtitle, ytitle, xum=""):

            factor=SRWPlot.get_factor(col)

            histogram = ticket['histogram']
            bins = ticket['bins']*factor

            self.plot_canvas.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
            if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
            if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
            if not title is None: self.plot_canvas.setGraphTitle(title)
            self.plot_canvas.setDrawModeEnabled(True, 'rectangle')
            self.plot_canvas.setZoomModeEnabled(True)

            if ticket['fwhm'] == None: ticket['fwhm'] = 0.0

            n_patches = len(self.plot_canvas._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._backend.ax.patches.remove(self.plot_canvas._backend.ax.patches[n_patches-1])

            if not ticket['fwhm'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor, x_fwhm_f*factor
                y_fwhm   = max(histogram)*0.5

                self.plot_canvas._backend.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                          [x_fwhm_f, y_fwhm],
                                                          arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                          color='b',
                                                          linewidth=1.5))
            if min(histogram) < 0:
                self.plot_canvas.setGraphYLimits(min(histogram), max(histogram))
            else:
                self.plot_canvas.setGraphYLimits(0, max(histogram))

            self.plot_canvas.replot()

            self.info_box.total.setText("{:.2e}".format(decimal.Decimal(ticket['total'])))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm']*factor))
            self.info_box.label_h.setText("FWHM " + xum)

        def clear(self):
            self.plot_canvas.clear()
            self.info_box.clear()

    class Detailed2DWidget(QWidget):
        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(SRWPlot.Detailed2DWidget, self).__init__()

            self.x_scale_factor = x_scale_factor
            self.y_scale_factor = y_scale_factor

            self.plot_canvas = ImageView()

            self.plot_canvas.setColormap({"name":"gray", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256})
            self.plot_canvas.setMinimumWidth(590 * x_scale_factor)
            self.plot_canvas.setMaximumWidth(590 * y_scale_factor)

            self.info_box = SRWPlot.InfoBoxWidget(x_scale_factor, y_scale_factor)

            layout = QGridLayout()

            layout.addWidget(             self.info_box, 0, 1, 2, 1)
            layout.addWidget(self.plot_canvas.toolBar(), 0, 0, 1, 1)
            layout.addWidget(          self.plot_canvas, 1, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

            self.plot_canvas.toolBar()

        def plot_2D(self, ticket, var_x, var_y, title, xtitle, ytitle, xum="", yum=""):

            matplotlib.rcParams['axes.formatter.useoffset']='False'

            factor1=SRWPlot.get_factor(var_x)
            factor2=SRWPlot.get_factor(var_y)

            xx = ticket['bin_h']
            yy = ticket['bin_v']

            nbins_h = ticket['nbins_h']
            nbins_v = ticket['nbins_v']

            xmin, xmax = xx.min(), xx.max()
            ymin, ymax = yy.min(), yy.max()

            origin = (xmin*factor1, ymin*factor2)
            scale = (abs((xmax-xmin)/nbins_h)*factor1, abs((ymax-ymin)/nbins_v)*factor2)

            # PyMCA inverts axis!!!! histogram must be calculated reversed
            data_to_plot = []
            for y_index in range(0, nbins_v):
                x_values = []
                for x_index in range(0, nbins_h):
                    x_values.append(ticket['histogram'][x_index][y_index])

                data_to_plot.append(x_values)

            self.plot_canvas.setImage(numpy.array(data_to_plot), origin=origin, scale=scale)

            if xtitle is None: xtitle=SRWPlot.get_SRW_label(var_x)
            if ytitle is None: ytitle=SRWPlot.get_SRW_label(var_y)

            self.plot_canvas.setGraphXLabel(xtitle)
            self.plot_canvas.setGraphYLabel(ytitle)
            self.plot_canvas.setGraphTitle(title)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')

            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._backend.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._backend.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            if ticket['fwhm_h'] == None: ticket['fwhm_h'] = 0.0
            if ticket['fwhm_v'] == None: ticket['fwhm_v'] = 0.0

            n_patches = len(self.plot_canvas._histoHPlot._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoHPlot._backend.ax.patches.remove(self.plot_canvas._histoHPlot._backend.ax.patches[n_patches-1])

            if not ticket['fwhm_h'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates_h']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor1, x_fwhm_f*factor1
                y_fwhm = max(ticket['histogram_h']) * 0.5

                self.plot_canvas._histoHPlot._backend.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                                     [x_fwhm_f, y_fwhm],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='b',
                                                                     linewidth=1.5))

            n_patches = len(self.plot_canvas._histoVPlot._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoVPlot._backend.ax.patches.remove(self.plot_canvas._histoVPlot._backend.ax.patches[n_patches-1])

            if not ticket['fwhm_v'] == 0.0:
                y_fwhm_i, y_fwhm_f = ticket['fwhm_coordinates_v']
                y_fwhm_i, y_fwhm_f = y_fwhm_i*factor2, y_fwhm_f*factor2
                x_fwhm = max(ticket['histogram_v']) * 0.5

                self.plot_canvas._histoVPlot._backend.ax.add_patch(FancyArrowPatch([x_fwhm, y_fwhm_i],
                                                                     [x_fwhm, y_fwhm_f],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='r',
                                                                     linewidth=1.5))

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()
            self.plot_canvas.replot()

            self.info_box.total.setText("{:.3e}".format(decimal.Decimal(ticket['total'])))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm_h'] * factor1))
            self.info_box.fwhm_v.setText("{:5.4f}".format(ticket['fwhm_v'] * factor2))
            self.info_box.label_h.setText("FWHM " + xum)
            self.info_box.label_v.setText("FWHM " + yum)

        def clear(self):
            self.plot_canvas.clear()

            self.plot_canvas._histoHPlot.clear()
            self.plot_canvas._histoVPlot.clear()

            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._backend.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._backend.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')
            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()

            self.info_box.clear()

    @classmethod
    def get_factor(cls, var):
        factor = 1.0

        if SRWPlot._is_conversione_active:
            if var == 1 or var == 2 or var == 3:
                factor = 1e3 # m to mm

        return factor

    @classmethod
    def get_SRW_label(cls, var):
        return "X" if var==1 else ("Y" if var==2 else ("Z" if var==3 else ""))

    @classmethod
    def get_ticket_1D(cls, x_array, y_array):
        ticket = {'error':0}
        ticket['nbins'] = len(x_array)

        xrange = [x_array.min(), x_array.max() ]

        bins = x_array
        h = y_array

        # output
        ticket['histogram'] = h
        ticket['bins'] = bins
        ticket['xrange'] = xrange
        ticket['total'] = numpy.sum(h)
        ticket['fwhm'] = None

        tt = numpy.where(h>=max(h)*0.5)
        if h[tt].size > 1:
            binSize = bins[1]-bins[0]
            ticket['fwhm'] = binSize*(tt[0][-1]-tt[0][0])
            ticket['fwhm_coordinates'] = (bins[tt[0][0]], bins[tt[0][-1]])

        return ticket

    @classmethod
    def get_ticket_2D(cls, x_array, y_array, z_array):
        ticket = {'error':0}
        ticket['nbins_h'] = len(x_array)
        ticket['nbins_v'] = len(y_array)

        xrange = [x_array.min(), x_array.max() ]
        yrange = [y_array.min(), y_array.max() ]

        hh = z_array
        xx = x_array
        yy = y_array

        ticket['xrange'] = xrange
        ticket['yrange'] = yrange
        ticket['bin_h'] = xx
        ticket['bin_v'] = yy
        ticket['histogram'] = hh
        ticket['histogram_h'] = hh.sum(axis=1)
        ticket['histogram_v'] = hh.sum(axis=0)
        ticket['total'] = numpy.sum(z_array)

        h = ticket['histogram_h']
        tt = numpy.where(h >= (numpy.min(h) + (numpy.max(h)-numpy.min(h))*0.5))

        if h[tt].size > 1:
            binSize = ticket['bin_h'][1]-ticket['bin_h'][0]
            ticket['fwhm_h'] = binSize*(tt[0][-1]-tt[0][0])

            ticket['fwhm_coordinates_h'] = (ticket['bin_h'][tt[0][0]],
                                            ticket['bin_h'][tt[0][-1]])
        else:
            ticket["fwhm_h"] = None

        h = ticket['histogram_v']
        tt = numpy.where(h >= numpy.min(h) + (numpy.max(h)-numpy.min(h))*0.5)

        if h[tt].size > 1:
            binSize = ticket['bin_v'][1]-ticket['bin_v'][0]
            ticket['fwhm_v'] = binSize*(tt[0][-1]-tt[0][0])
            ticket['fwhm_coordinates_v'] =(ticket['bin_v'][tt[0][0]], ticket['bin_v'][tt[0][-1]])
        else:
            ticket["fwhm_v"] = None

        return ticket

#_height_prof_data: a matrix (2D array) containing the Height Profile data in [m];
# if _ar_height_prof_x is None and _ar_height_prof_y is None: the first column in _height_prof_data is assumed to be the "longitudinal" position [m]
# and first row the "transverse" position [m], and _height_prof_data[0][0] is not used;
# otherwise the "longitudinal" and "transverse" positions on the surface are assumed to be given by _ar_height_prof_x, _ar_height_prof_y

def write_error_profile_file(zz, xx, yy, output_file, separator = '\t'):
    buffer = open(output_file, 'w')

    # first row: x positions

    first_row = "0"
    for x_pos in xx:
        first_row += separator + str(x_pos)

    first_row += "\n"

    buffer.write(first_row)

    # next rows: y pos + z
    for y_index in range(len(yy)):
        row =  str(yy[y_index])

        for x_index in range(len(xx)):
            row += separator + str(zz[y_index, x_index])

        row += "\n"

        buffer.write(row)

    buffer.close()


###############################################################
#
# MESSAGING
#
###############################################################

from PyQt5.QtWidgets import QMessageBox

def showConfirmMessage(message, informative_text, parent=None):
    msgBox = QMessageBox()
    if not parent is None: msgBox.setParent(parent)
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setText(message)
    msgBox.setInformativeText(informative_text)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)

    return msgBox.exec_() == QMessageBox.Yes

def showWarningMessage(message, parent=None):
    msgBox = QMessageBox()
    if not parent is None: msgBox.setParent(parent)
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText(message)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

def showCriticalMessage(message, parent=None):
    msgBox = QMessageBox()
    if not parent is None: msgBox.setParent(parent)
    msgBox.setIcon(QMessageBox.Critical)
    msgBox.setText(message)
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()

if __name__=="__main__":
    print(SRWPlot.get_SRW_label(1))
    print(SRWPlot.get_SRW_label(2))
    print(SRWPlot.get_SRW_label(3))
    print("--", SRWPlot.get_SRW_label(5), "--")
