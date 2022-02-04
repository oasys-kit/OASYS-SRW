import numpy, decimal
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QDialog, QVBoxLayout, QDialogButtonBox, QFileDialog

import h5py, time
from oasys.widgets.gui import FigureCanvas3D
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, ArrowStyle
try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangewidget import gui as orangegui
from oasys.widgets import gui
from oasys.util.oasys_util import get_average, get_sigma, get_fwhm, write_surface_file

from srxraylib.metrology import profiles_simulation
from silx.gui.plot.ImageView import ImageView

import matplotlib
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm

cdict_temperature = {'red': ((0.0, 0.0, 0.0),
                             (0.5, 0.0, 0.0),
                             (0.75, 1.0, 1.0),
                             (1.0, 1.0, 1.0)),
                     'green': ((0.0, 0.0, 0.0),
                               (0.25, 1.0, 1.0),
                               (0.75, 1.0, 1.0),
                               (1.0, 0.0, 0.0)),
                     'blue': ((0.0, 1.0, 1.0),
                              (0.25, 1.0, 1.0),
                              (0.5, 0.0, 0.0),
                              (1.0, 0.0, 0.0))}

        # reversed gray
cdict_reversed_gray = {'red': ((0.0, 1.0, 1.0),
                              (1.0, 0.0, 0.0)),
                       'green': ((0.0, 1.0, 1.0),
                                 (1.0, 0.0, 0.0)),
                       'blue': ((0.0, 1.0, 1.0),
                                (1.0, 0.0, 0.0))}

cmap_temperature = LinearSegmentedColormap('temperature', cdict_temperature, 256)
cmap_reversed_gray = LinearSegmentedColormap('reversed gray', cdict_reversed_gray, 256)
cmap_gray = cm.get_cmap("gray")

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
        sigma_h_field = ""
        sigma_v_field = ""
        centroid_h_field = ""
        centroid_v_field = ""
        boundary_h_field = ""
        boundary_v_field = ""
        average_field = ""

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, is_2d=True, do_average=False):
            super(SRWPlot.InfoBoxWidget, self).__init__()

            info_box_inner= gui.widgetBox(self, "Info")
            info_box_inner.setFixedHeight(458*y_scale_factor)
            info_box_inner.setFixedWidth(230*x_scale_factor)

            self.total_box   = gui.widgetBox(info_box_inner, "", orientation="vertical", height=25)
            self.total_2_box = gui.widgetBox(info_box_inner, "", orientation="vertical", height=25)

            self.total   = gui.lineEdit(self.total_box, self, "total_field", "\u03a6 [ph/s/0.1%BW]", tooltip="Total", labelWidth=115, valueType=str, orientation="horizontal")
            self.total_2 = gui.lineEdit(self.total_2_box, self, "total_field", "\u03a6 [ph/s]", tooltip="Total", labelWidth=115, valueType=str, orientation="horizontal")

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

            label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

            self.label_s_h = QLabel("\u03c3 ")
            self.label_s_h.setFixedWidth(115)
            palette =  QPalette(self.label_s_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_s_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_s_h)
            self.sigma_h = gui.lineEdit(label_box_1, self, "sigma_h_field", "", tooltip="Sigma", labelWidth=115, valueType=str, orientation="horizontal")

            if is_2d:
                label_box_2 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.label_s_v = QLabel("\u03c3 ")
                self.label_s_v.setFixedWidth(115)
                palette =  QPalette(self.label_s_v.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_s_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_s_v)
                self.sigma_v = gui.lineEdit(label_box_2, self, "sigma_v_field", "", tooltip="Sigma", labelWidth=115, valueType=str, orientation="horizontal")

            label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

            self.label_c_h = QLabel("centroid ")
            self.label_c_h.setFixedWidth(115)
            palette =  QPalette(self.label_c_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_c_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_c_h)
            self.centroid_h = gui.lineEdit(label_box_1, self, "centroid_h_field", "", tooltip="Centroid", labelWidth=115, valueType=str, orientation="horizontal")

            if is_2d:
                label_box_2 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.label_c_v = QLabel("centroid ")
                self.label_c_v.setFixedWidth(115)
                palette =  QPalette(self.label_c_v.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_c_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_c_v)
                self.centroid_v = gui.lineEdit(label_box_2, self, "centroid_v_field", "", tooltip="Sigma", labelWidth=115, valueType=str, orientation="horizontal")

            if do_average:
                label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.average = gui.lineEdit(label_box_1, self, "average_field", "Average", tooltip="Average", labelWidth=115, valueType=str, orientation="horizontal")

            label_box_1 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="vertical")

            self.label_b_h = QLabel("Range ")
            self.label_b_h.setFixedWidth(115)
            palette =  QPalette(self.label_b_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_b_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_b_h)
            self.boundary_h = gui.lineEdit(label_box_1, self, "boundary_h_field", "", tooltip="Range", labelWidth=115, valueType=str)

            if is_2d:
                label_box_2 = gui.widgetBox(info_box_inner, "", addSpace=False, orientation="vertical")

                self.label_b_v = QLabel("Range ")
                self.label_b_v.setFixedWidth(115)
                palette =  QPalette(self.label_b_v.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_b_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_b_v)
                self.boundary_v = gui.lineEdit(label_box_2, self, "boundary_v_field", "", tooltip="Range", labelWidth=115, valueType=str)

            self.total.setReadOnly(True)
            font = QFont(self.total.font())
            font.setBold(True)
            self.total.setFont(font)
            palette = QPalette(self.total.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total.setPalette(palette)

            self.total_2.setReadOnly(True)
            font = QFont(self.total_2.font())
            font.setBold(True)
            self.total_2.setFont(font)
            palette = QPalette(self.total_2.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_2.setPalette(palette)

            self.total_2_box.setVisible(False)

            self.fwhm_h.setReadOnly(True)
            font = QFont(self.fwhm_h.font())
            font.setBold(True)
            self.fwhm_h.setFont(font)
            palette = QPalette(self.fwhm_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.fwhm_h.setPalette(palette)

            self.sigma_h.setReadOnly(True)
            font = QFont(self.sigma_h.font())
            font.setBold(True)
            self.sigma_h.setFont(font)
            palette = QPalette(self.sigma_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.sigma_h.setPalette(palette)

            self.centroid_h.setReadOnly(True)
            font = QFont(self.centroid_h.font())
            font.setBold(True)
            self.centroid_h.setFont(font)
            palette = QPalette(self.centroid_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.centroid_h.setPalette(palette)

            self.boundary_h.setReadOnly(True)
            font = QFont(self.boundary_h.font())
            font.setBold(True)
            self.boundary_h.setFont(font)
            palette = QPalette(self.boundary_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.boundary_h.setPalette(palette)

            if is_2d:
                self.fwhm_v.setReadOnly(True)
                font = QFont(self.fwhm_v.font())
                font.setBold(True)
                self.fwhm_v.setFont(font)
                palette = QPalette(self.fwhm_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.fwhm_v.setPalette(palette)

                self.sigma_v.setReadOnly(True)
                font = QFont(self.sigma_v.font())
                font.setBold(True)
                self.sigma_v.setFont(font)
                palette = QPalette(self.sigma_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.sigma_v.setPalette(palette)

                self.centroid_v.setReadOnly(True)
                font = QFont(self.centroid_v.font())
                font.setBold(True)
                self.centroid_v.setFont(font)
                palette = QPalette(self.centroid_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.centroid_v.setPalette(palette)

                self.boundary_v.setReadOnly(True)
                font = QFont(self.boundary_v.font())
                font.setBold(True)
                self.boundary_v.setFont(font)
                palette = QPalette(self.boundary_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.boundary_v.setPalette(palette)

            if do_average:
                self.average.setReadOnly(True)
                font = QFont(self.average.font())
                font.setBold(True)
                self.average.setFont(font)
                palette = QPalette(self.average.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.average.setPalette(palette)

        def set_multi_energy(self, multi_energy):
            self.total_2_box.setVisible(multi_energy==True)
            self.total_box.setVisible(multi_energy==False)

        def clear(self):
            self.total.setText("0.0")
            self.total_2.setText("0.0")
            self.fwhm_h.setText("0.0000")
            if hasattr(self, "fwhm_v"):  self.fwhm_v.setText("0.0000")
            self.sigma_h.setText("0.0000")
            if hasattr(self, "sigma_v"):  self.sigma_v.setText("0.0000")
            self.sigma_h.setText("n.a.")
            if hasattr(self, "sigma_v"):  self.sigma_v.setText("n.a.")
            self.centroid_h.setText("0.0000")
            if hasattr(self, "centroid_v"):  self.centroid_v.setText("0.0000")
            self.boundary_h.setText("")
            if hasattr(self, "boundary_v"):  self.centroid_v.setText("")
            if hasattr(self, "average"): self.average.setText("0.0000")

    class Detailed1DWidget(QWidget):

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, do_average=False):
            super(SRWPlot.Detailed1DWidget, self).__init__()

            self.plot_canvas = gui.plotWindow(roi=False, control=False, position=True, logScale=True)
            self.plot_canvas.setDefaultPlotLines(True)
            self.plot_canvas.setActiveCurveColor(color='blue')
            self.plot_canvas.setMinimumWidth(590*x_scale_factor)
            self.plot_canvas.setMaximumWidth(590*x_scale_factor)
            self.do_average = do_average

            self.info_box = SRWPlot.InfoBoxWidget(x_scale_factor, y_scale_factor, is_2d=False, do_average=do_average)

            layout = QGridLayout()

            layout.addWidget(self.info_box,    0, 1, 1, 1)
            layout.addWidget(self.plot_canvas, 0, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

        def plot_1D(self, ticket, col, title, xtitle, ytitle, xum="", xrange=None, use_default_factor=True):

            if use_default_factor:
                factor = SRWPlot.get_factor(col)
            else:
                factor = 1.0

            if isinstance(ticket['histogram'].shape, list):
                histogram = ticket['histogram'][0]
            else:
                histogram = ticket['histogram']

            bins = ticket['bins']

            if not xrange is None:
                good = numpy.where((bins >= xrange[0]) & (bins <= xrange[1]))

                bins = bins[good]
                histogram = histogram[good]

            ticket['total'] = numpy.sum(histogram)
            ticket['fwhm'], ticket['fwhm_quote'], ticket['fwhm_coordinates'] = get_fwhm(histogram, bins)
            ticket['sigma'] = get_sigma(histogram, bins)
            if self.do_average: ticket['average'] = ticket['total']/len(histogram)

            bins *= factor

            self.plot_canvas.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
            if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
            if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
            if not title is None: self.plot_canvas.setGraphTitle(title)

            if ticket['fwhm'] == None: ticket['fwhm'] = 0.0

            n_patches = len(self.plot_canvas._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._backend.ax.patches.remove(self.plot_canvas._backend.ax.patches[n_patches-1])

            if not ticket['fwhm'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor, x_fwhm_f*factor
                y_fwhm             = ticket['fwhm_quote']

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
            self.info_box.total_2.setText("{:.2e}".format(decimal.Decimal(ticket['total'])))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm']*factor))
            self.info_box.label_h.setText("FWHM " + xum)
            self.info_box.sigma_h.setText("{:5.4f}".format(ticket['sigma']*factor))
            self.info_box.label_s_h.setText("\u03c3 " + xum)
            self.info_box.centroid_h.setText("{:5.4f}".format(ticket['centroid']*factor))
            self.info_box.label_c_h.setText("centroid " + xum)
            self.info_box.boundary_h.setText("{:5.4f}, {:5.4f}".format(min(bins), max(bins)))
            self.info_box.label_b_h.setText("Range " + xum)
            if self.do_average: self.info_box.average.setText("{:5.4f}".format(ticket['average']))

        def clear(self):
            self.plot_canvas.clear()
            self.info_box.clear()

    class Detailed2DWidget(QWidget):
        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, do_average=False):
            super(SRWPlot.Detailed2DWidget, self).__init__()

            self.x_scale_factor = x_scale_factor
            self.y_scale_factor = y_scale_factor

            self.plot_canvas = gui.imageWiew(parent=self)

            self.plot_canvas.setMinimumWidth(590 * x_scale_factor)
            self.plot_canvas.setMaximumWidth(590 * y_scale_factor)

            self.info_box = SRWPlot.InfoBoxWidget(x_scale_factor, y_scale_factor, is_2d=True, do_average=do_average)
            self.do_average = do_average

            layout = QGridLayout()

            layout.addWidget(   self.info_box, 0, 1, 1, 1)
            layout.addWidget(self.plot_canvas, 0, 0, 1, 1)

            layout.setColumnMinimumWidth(0, 600*x_scale_factor)
            layout.setColumnMinimumWidth(1, 230*x_scale_factor)

            self.setLayout(layout)

        def plot_2D(self, ticket, var_x, var_y, title, xtitle, ytitle, xum="", yum="", plotting_range=None, use_default_factor=True, apply_alpha_channel=False, alpha_ticket=None, is_multi_energy=False):

            matplotlib.rcParams['axes.formatter.useoffset']='False'

            self.plot_canvas.setColormap({"name":QSettings().value("output/srw-default-colormap", "gray", str),
                                          "normalization":"linear",
                                          "autoscale":True,
                                          "vmin":0,
                                          "vmax":0,
                                          "colors":256})

            if use_default_factor:
                factor1=SRWPlot.get_factor(var_x)
                factor2=SRWPlot.get_factor(var_y)
            else:
                factor1 = 1.0
                factor2 = 1.0

            if plotting_range == None:
                xx = ticket['bin_h']
                yy = ticket['bin_v']

                nbins_h = ticket['nbins_h']
                nbins_v = ticket['nbins_v']

                histogram = ticket['histogram']
            else:
                range_x  = numpy.where(numpy.logical_and(ticket['bin_h']>=plotting_range[0], ticket['bin_h']<=plotting_range[1]))
                range_y  = numpy.where(numpy.logical_and(ticket['bin_v']>=plotting_range[2], ticket['bin_v']<=plotting_range[3]))

                xx = ticket['bin_h'][range_x]
                yy = ticket['bin_v'][range_y]

                nbins_h = len(xx)
                nbins_v = len(yy)

                histogram = numpy.zeros((nbins_h, nbins_v))
                for row, i in zip(ticket['histogram'][range_x], range(nbins_h)): histogram[i, :] = row[range_y]

            if len(xx) == 0 or len(yy) == 0: raise Exception("Nothing to plot in the given range")

            xmin, xmax = xx.min(), xx.max()
            ymin, ymax = yy.min(), yy.max()

            origin = (xmin*factor1, ymin*factor2)
            scale = (abs((xmax-xmin)/nbins_h)*factor1, abs((ymax-ymin)/nbins_v)*factor2)

            data_to_plot = histogram.T

            histogram_h = numpy.sum(data_to_plot, axis=0) # data to plot axis are inverted
            histogram_v = numpy.sum(data_to_plot, axis=1)

            ticket['total'] = numpy.sum(data_to_plot)

            ticket['fwhm_h'], ticket['fwhm_quote_h'], ticket['fwhm_coordinates_h'] = get_fwhm(histogram_h, xx)
            ticket['sigma_h'] = get_sigma(histogram_h, xx)
            ticket['centroid_h'] = get_average(histogram_h, xx)

            ticket['fwhm_v'], ticket['fwhm_quote_v'], ticket['fwhm_coordinates_v'] = get_fwhm(histogram_v, yy)
            ticket['sigma_v'] = get_sigma(histogram_v, yy)
            ticket['centroid_v'] = get_average(histogram_v, yy)
            if self.do_average: ticket['average'] = ticket['total']/(nbins_h*nbins_v)


            # PyMCA inverts axis!!!! histogram must be calculated reversed
            self.plot_canvas.setImage(data_to_plot, origin=origin, scale=scale)

            if xtitle is None: xtitle=SRWPlot.get_SRW_label(var_x)
            if ytitle is None: ytitle=SRWPlot.get_SRW_label(var_y)

            self.plot_canvas.setGraphXLabel(xtitle)
            self.plot_canvas.setGraphYLabel(ytitle)
            self.plot_canvas.setGraphTitle(title)

            self.plot_canvas._histoHPlot.setGraphYLabel('A.U.')

            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._backend.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._backend.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot.setGraphXLabel('A.U.')

            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._backend.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._backend.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            n_patches = len(self.plot_canvas._histoHPlot._backend.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoHPlot._backend.ax.patches.remove(self.plot_canvas._histoHPlot._backend.ax.patches[n_patches-1])

            if not ticket['fwhm_h'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates_h']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor1, x_fwhm_f*factor1
                y_fwhm = ticket['fwhm_quote_h']

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
                x_fwhm = ticket['fwhm_quote_v']

                self.plot_canvas._histoVPlot._backend.ax.add_patch(FancyArrowPatch([x_fwhm, y_fwhm_i],
                                                                     [x_fwhm, y_fwhm_f],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='r',
                                                                     linewidth=1.5))

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()
            self.plot_canvas.replot()

            if not (numpy.logical_and(numpy.min(data_to_plot)>= -numpy.pi, numpy.max(data_to_plot)<=numpy.pi)):
                dx = (xx[1]-xx[0]) # mm
                dy = (yy[1]-yy[0])

                total_flux = data_to_plot.sum()*dx*dy
            else:
                total_flux = numpy.nan

            self.info_box.total.setText("{:.3e}".format(decimal.Decimal(total_flux)))
            self.info_box.total_2.setText("{:.3e}".format(decimal.Decimal(total_flux)))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm_h'] * factor1))
            self.info_box.fwhm_v.setText("{:5.4f}".format(ticket['fwhm_v'] * factor2))
            self.info_box.label_h.setText("FWHM " + xum)
            self.info_box.label_v.setText("FWHM " + yum)
            self.info_box.sigma_h.setText("{:5.4f}".format(ticket['sigma_h']*factor1))
            self.info_box.sigma_v.setText("{:5.4f}".format(ticket['sigma_v']*factor2))
            self.info_box.label_s_h.setText("\u03c3 " + xum)
            self.info_box.label_s_v.setText("\u03c3 " + yum)
            self.info_box.centroid_h.setText("{:5.4f}".format(ticket['centroid_h'] * factor1))
            self.info_box.centroid_v.setText("{:5.4f}".format(ticket['centroid_v'] * factor2))
            self.info_box.label_c_h.setText("centroid " + xum)
            self.info_box.label_c_v.setText("centroid " + yum)
            self.info_box.boundary_h.setText("{:5.4f}, {:5.4f}".format(xmin*factor1, xmax*factor1))
            self.info_box.boundary_v.setText("{:5.4f}, {:5.4f}".format(ymin*factor2, ymax*factor2))
            self.info_box.label_b_h.setText("Range " + xum)
            self.info_box.label_b_v.setText("Range " + yum)
            if self.do_average: self.info_box.average.setText("{:5.4f}".format(ticket['average']))

            self.info_box.set_multi_energy(is_multi_energy)

            if apply_alpha_channel==True:
                if plotting_range == None:
                    xx = alpha_ticket['bin_h']
                    yy = alpha_ticket['bin_v']

                    alpha_channel = numpy.flipud(alpha_ticket["histogram"].T)
                    plotted_histo = numpy.flipud(ticket["histogram"].T)
                else:
                    range_x  = numpy.where(numpy.logical_and(alpha_ticket['bin_h']>=plotting_range[0], alpha_ticket['bin_h']<=plotting_range[1]))
                    range_y  = numpy.where(numpy.logical_and(alpha_ticket['bin_v']>=plotting_range[2], alpha_ticket['bin_v']<=plotting_range[3]))

                    xx = alpha_ticket['bin_h'][range_x]
                    yy = alpha_ticket['bin_v'][range_y]

                    alpha_channel = []
                    for row in alpha_ticket['histogram'][range_x]:
                        alpha_channel.append(row[range_y])

                    alpha_channel = numpy.flipud(numpy.array(alpha_channel).T)

                    plotted_histo = []
                    for row in ticket['histogram'][range_x]:
                        plotted_histo.append(row[range_y])

                    plotted_histo = numpy.flipud(numpy.array(plotted_histo).T)

                xx_t = xx*SRWPlot.get_factor(var_x)
                yy_t = yy*SRWPlot.get_factor(var_y)

                extent=[min(xx_t), max(xx_t), min(yy_t), max(yy_t)]

                alpha_channel -= numpy.min(alpha_channel)
                alpha_channel /= numpy.max(alpha_channel)

                plotted_histo -= numpy.min(plotted_histo)
                plotted_histo /= numpy.max(plotted_histo)

                colormap = QSettings().value("output/srw-default-colormap", "gray", str)

                if colormap == "gray":
                    cmap = cmap_gray
                elif colormap == "temperature":
                    cmap = cmap_temperature
                elif colormap == "reversed gray":
                    cmap = cmap_reversed_gray
                else:
                    cmap = cmap_gray

                plotted_histo = cmap(plotted_histo)
                plotted_histo[..., -1] = alpha_channel

                axis = self.plot_canvas._backend.ax

                axis.clear()
                axis.set_title(title)
                axis.set_xlabel(xum)
                axis.set_ylabel(yum)
                axis.set_xlim(min(xx_t), max(xx_t))
                axis.set_ylim(min(yy_t), max(yy_t))

                axis.imshow(plotted_histo, cmap=cmap, extent=extent)

                self.plot_canvas.setKeepDataAspectRatio(False)


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

            self.plot_canvas._histoHPlot.setGraphYLabel('A.U.')
            self.plot_canvas._histoVPlot.setGraphXLabel('A.U.')

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
        ticket['fwhm'], ticket['fwhm_quote'], ticket['fwhm_coordinates'] = get_fwhm(h, bins)
        ticket['sigma'] = get_sigma(h, bins)

        return ticket

    @classmethod
    def get_ticket_2D(cls, x_array, y_array, z_array, divide_by_pixel_area=True, is_multi_energy=False):
        ticket = {'error':0}
        ticket['nbins_h'] = len(x_array)
        ticket['nbins_v'] = len(y_array)

        xrange = [x_array.min(), x_array.max() ]
        yrange = [y_array.min(), y_array.max() ]
        pixel_area = 1.0 if not divide_by_pixel_area else (x_array[1] - x_array[0]) * (y_array[1] - y_array[0])

        hh = z_array
        hh_h = hh.sum(axis=1)
        hh_v = hh.sum(axis=0)
        xx = x_array
        yy = y_array

        ticket['xrange'] = xrange
        ticket['yrange'] = yrange
        ticket['bin_h'] = xx
        ticket['bin_v'] = yy
        ticket['histogram'] = hh
        ticket['histogram_h'] = hh_h
        ticket['histogram_v'] = hh_v
        ticket['total'] = numpy.sum(z_array) * pixel_area

        ticket['fwhm_h'], ticket['fwhm_quote_h'], ticket['fwhm_coordinates_h'] = get_fwhm(hh_h, xx)
        ticket['sigma_h'] = get_sigma(hh_h, xx)

        ticket['fwhm_v'], ticket['fwhm_quote_v'], ticket['fwhm_coordinates_v'] = get_fwhm(hh_v, yy)
        ticket['sigma_v'] = get_sigma(hh_v, yy)
        ticket['is_multi_energy'] = is_multi_energy

        return ticket

    class PlotXYHdf5File(h5py.File):
        def __init__(self, file_name, mode="w"):
            try:
                super(SRWPlot.PlotXYHdf5File, self).__init__(name=file_name, mode=mode)
            except OSError as e:
                if "already open" in str(e) and mode=="w":
                    super(SRWPlot.PlotXYHdf5File, self).__init__(name=file_name, mode="a")
                    self.close()
                    super(SRWPlot.PlotXYHdf5File, self).__init__(name=file_name, mode="w")

            if mode != "r":
                self.coordinates      = self.create_group("coordinates")
                self.plots            = self.create_group("xy_plots")
                self.additional_data  = self.create_group("additional_data")

                self.attrs["default"]          = "coordinates/X"
                self.attrs["file_name"]        = file_name
                self.attrs["file_time"]        = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                self.attrs["creator"]          = "PlotXYHdf5File.__init__"
                self.attrs["code"]             = "SRW"
                self.attrs["HDF5_Version"]     = h5py.version.hdf5_version
                self.attrs["h5py_version"]     = h5py.version.version

                self.has_coordinate = False
                self.has_plot = False

        def get_plot(self, ticket=None):
            if not ticket is None:
                ticket['histogram']   = self["/xy_plots/intensity"][()]
                ticket['histogram_h'] = self["/xy_plots/intensity_h"][()]
                ticket['histogram_v'] = self["/xy_plots/intensity_v"][()]
            else:
                return self["/xy_plots/intensity"][()], \
                       self["/xy_plots/intensity_h"][()], \
                       self["/xy_plots/intensity_v"][()]

        def get_coordinates(self, ticket=None):
            if not ticket is None:
                ticket["bin_h"] = self["coordinates/X"][()]
                ticket["bin_v"] = self["coordinates/Y"][()]
            else:
                x_array = self["coordinates/X"][()]
                y_array = self["coordinates/Y"][()]

                return x_array, y_array

        def get_additional_data(self, ticket):
            ticket["nbins_h"]             = self["/additional_data"].attrs["nbins_h"]
            ticket["nbins_v"]             = self["/additional_data"].attrs["nbins_v"]
            ticket['xrange']              = self["/additional_data"].attrs["xrange"]
            ticket['yrange']              = self["/additional_data"].attrs["yrange"]
            ticket['total']               = self["/additional_data"].attrs["total"]
            ticket['fwhm_h']              = self["/additional_data"].attrs["fwhm_h"]
            ticket['fwhm_quote_h']        = self["/additional_data"].attrs["fwhm_quote_h"]
            ticket['fwhm_coordinates_h']  = self["/additional_data"].attrs["fwhm_coordinates_h"]
            ticket['sigma_h']             = self["/additional_data"].attrs["sigma_h"]
            ticket['fwhm_v']              = self["/additional_data"].attrs["fwhm_v"]
            ticket['fwhm_quote_v']        = self["/additional_data"].attrs["fwhm_quote_v"]
            ticket['fwhm_coordinates_v']  = self["/additional_data"].attrs["fwhm_coordinates_v"]
            ticket['sigma_v']             = self["/additional_data"].attrs["sigma_v"]
            ticket['is_multi_energy']     = self["/additional_data"].attrs["is_multi_energy"]

        def write_additional_data(self, ticket):
            self.additional_data.attrs["nbins_h"]            = ticket["nbins_h"]
            self.additional_data.attrs["nbins_v"]            = ticket["nbins_v"]
            self.additional_data.attrs["xrange"]             = ticket['xrange']
            self.additional_data.attrs["yrange"]             = ticket['yrange']
            self.additional_data.attrs["total"]              = ticket['total']
            self.additional_data.attrs["fwhm_h"]             = ticket['fwhm_h']
            self.additional_data.attrs["fwhm_quote_h"]       = ticket['fwhm_quote_h']
            self.additional_data.attrs["fwhm_coordinates_h"] = ticket['fwhm_coordinates_h']
            self.additional_data.attrs["sigma_h"]            = ticket['sigma_h']
            self.additional_data.attrs["fwhm_v"]             = ticket['fwhm_v']
            self.additional_data.attrs["fwhm_quote_v"]       = ticket['fwhm_quote_v']
            self.additional_data.attrs["fwhm_coordinates_v"] = ticket['fwhm_coordinates_v']
            self.additional_data.attrs["sigma_v"]            = ticket['sigma_v']
            self.additional_data.attrs["is_multi_energy"]    = ticket['is_multi_energy']

        def write_coordinates(self, ticket):
            if not self.has_coordinate:
                self.x = self.coordinates.create_dataset("X", data=ticket["bin_h"])
                self.y = self.coordinates.create_dataset("Y", data=ticket["bin_v"])
                self.has_coordinate = True
            else:
                self.x[...] = ticket["bin_h"]
                self.y[...] = ticket["bin_v"]

        def add_plot_xy(self, ticket):
            if not self.has_plot:
                self.histogram   = self.plots.create_dataset("intensity", data=ticket['histogram'])
                self.histogram_h = self.plots.create_dataset("intensity_h", data=ticket['histogram_h'])
                self.histogram_v = self.plots.create_dataset("intensity_v", data=ticket['histogram_v'])

                self.has_plot = True
            else:
                self.histogram[...]   = ticket['histogram']
                self.histogram_h[...] = ticket['histogram_h']
                self.histogram_v[...] = ticket['histogram_v']

        def add_attribute(self, attribute_name, attribute_value, dataset_name=None):
            if not dataset_name is None:
                self[dataset_name].attrs[attribute_name] = attribute_value
            else:
                self.attrs[attribute_name] = attribute_value

        def get_attribute(self,  attribute_name, dataset_name=None):
            if not dataset_name is None:
                return self[dataset_name].attrs[attribute_name]
            else:
                return self.attrs[attribute_name]

class ShowErrorProfileDialog(QDialog):

    def __init__(self, parent=None, file_name="", dimension=2):
        QDialog.__init__(self, parent)
        self.setWindowTitle('File: Surface Error Profile')

        if dimension == 2:
            self.setFixedHeight(700)

            layout = QGridLayout(self)

            figure = Figure(figsize=(8, 7))
            figure.patch.set_facecolor('white')

            axis = figure.add_subplot(111, projection='3d')

            axis.set_xlabel("X [m]")
            axis.set_ylabel("Y [m]")
            axis.set_zlabel("Z [nm]")

            figure_canvas = FigureCanvas3D(ax=axis, fig=figure, show_legend=False)
            figure_canvas.setFixedWidth(500)
            figure_canvas.setFixedHeight(645)

            self.x_coords, self.y_coords, self.z_values = read_error_profile_file(file_name, dimension=2)

            x_to_plot, y_to_plot = numpy.meshgrid(self.x_coords, self.y_coords)

            axis.plot_surface(x_to_plot, y_to_plot, (self.z_values*1e9).T,
                              rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            sloperms = profiles_simulation.slopes(self.z_values, self.x_coords, self.y_coords, return_only_rms=1)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6) + '\n' + \
                    ' Figure error rms in X direction: %f nm' % (round(self.z_values[:, 0].std()*1e9, 6)) + '\n' + \
                    ' Figure error rms in Y direction: %f nm' % (round(self.z_values[0, :].std()*1e9, 6))

            axis.set_title(title)

            figure_canvas.draw()

            axis.mouse_init()

            widget = QWidget(parent=self)

            container = gui.widgetBox(widget, "", addSpace=False, orientation="horizontal", width=500)

            orangegui.button(container, self, "Export Surface (.dat)", callback=self.save_srw_surface)
            orangegui.button(container, self, "Export Surface (.hdf5)", callback=self.save_oasys_surface)
            orangegui.button(container, self, "Close", callback=self.accept)

            layout.addWidget(figure_canvas, 0, 0)
            layout.addWidget(widget, 1, 0)

        elif dimension==1:
            layout = QVBoxLayout(self)

            figure_canvas = gui.plotWindow(resetzoom=False,
                                           autoScale=False,
                                           logScale=False,
                                           grid=False,
                                           curveStyle=False,
                                           colormap=False,
                                           aspectRatio=False, yInverted=False,
                                           copy=False, save=False, print_=False,
                                           control=False, position=False,
                                           roi=False, mask=False, fit=False)
            figure_canvas.setDefaultPlotLines(True)
            figure_canvas.setActiveCurveColor(color='blue')
            figure_canvas.setMinimumWidth(500)
            figure_canvas.setMaximumWidth(500)

            x_coords, z_values = read_error_profile_file(file_name, dimension=1)

            figure_canvas.addCurve(x_coords, z_values*1e9, "Height Error Profile", symbol='', color='blue', replace=True) #'+', '^', ','
            figure_canvas.setGraphXLabel("X [m]")
            figure_canvas.setGraphYLabel("Height Error [nm]")
            figure_canvas.setGraphTitle("Height Error Profile")

            figure_canvas.replot()

            bbox = QDialogButtonBox(QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(figure_canvas)
            layout.addWidget(bbox)

        self.setLayout(layout)

    def save_srw_surface(self):
        try:
            file_path = QFileDialog.getSaveFileName(self, "Save Surface in SRW (dat) Format", ".", "SRW format (*.dat)")[0]

            if not file_path is None and not file_path.strip() == "":
                write_error_profile_file(self.z_values.T, numpy.round(self.x_coords, 8), numpy.round(self.y_coords, 8), file_path)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

    def save_oasys_surface(self):
        try:
            file_path = QFileDialog.getSaveFileName(self, "Save Surface in Oasys (hdf5) Format", ".", "HDF5 format (*.hdf5)")[0]

            if not file_path is None and not file_path.strip() == "":
                write_surface_file(self.z_values.T, numpy.round(self.x_coords, 8), numpy.round(self.y_coords, 8), file_path)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

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

from oasys.widgets import congruence

def read_error_profile_file(file_name, separator = '\t', dimension=2):
    if dimension == 2:
        rows = open(congruence.checkFile(file_name), "r").readlines()

        # first row: x positions

        x_pos = rows[0].split(separator)
        n_x = len(x_pos)-1
        n_y = len(rows)-1

        x_coords = numpy.zeros(n_x)
        y_coords = numpy.zeros(n_y)
        z_values = numpy.zeros((n_x, n_y))

        for i_x in range(n_x):
            x_coords[i_x] = float(x_pos[i_x+1])

        for i_y in range(n_y):
            data = rows[i_y+1].split(separator)
            y_coords[i_y] = float(data[0])

            for i_x in range(n_x):
                z_values[i_x, i_y] = float(data[i_x+1])

        return x_coords, y_coords, z_values
    else:
        data = numpy.loadtxt(congruence.checkFile(file_name), delimiter=separator )

        x_coords = data[:, 0]
        z_values = data[:, 1]

        return x_coords, z_values

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

#################################################
# Physics
#################################################

import xraylib

def get_absorption_parameters(material, energy):
    energy_in_KeV = energy / 1000

    mu    = xraylib.CS_Total_CP(material, energy_in_KeV) # energy in KeV
    rho   = get_material_density(material)
    delta = 1 - xraylib.Refractive_Index_Re(material, energy_in_KeV, rho)

    return 0.01/(mu*rho), delta

def get_material_density(material_name):
    if material_name is None: return 0.0
    if str(material_name.strip()) == "": return 0.0

    try:
        compoundData = xraylib.CompoundParser(material_name)
        n_elements = compoundData["nElements"]
        if  n_elements == 1:
            return xraylib.ElementDensity(compoundData["Elements"][0])
        else:
            density = 0.0
            mass_fractions = compoundData["massFractions"]
            elements = compoundData["Elements"]
            for i in range (n_elements): density += xraylib.ElementDensity(elements[i])*mass_fractions[i]
            return density
    except:
        return 0.0




from PyQt5.QtWidgets import QApplication

if __name__=="__main__":
    print(SRWPlot.get_SRW_label(1))
    print(SRWPlot.get_SRW_label(2))
    print(SRWPlot.get_SRW_label(3))
    print("--", SRWPlot.get_SRW_label(5), "--")

    app = QApplication([])

    widget = QWidget()

    layout = QVBoxLayout()
    layout.addWidget(ImageView())

    widget.setLayout(layout)

    widget.show()

    app.exec_()
