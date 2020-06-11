import numpy

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from matplotlib import cm, rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.colors import colorConverter, ListedColormap

try:
    from mpl_toolkits.mplot3d import Axes3D  # mandatory to load 3D plot
except:
    pass

from oasys.widgets import gui as oasysgui

from orangecontrib.srw.util.srw_util import SRWPlot
from oasys.util.scanning_gui import HistogramData, get_sigma

class Column:
    X = 1
    Y = 2

class AbstractScanHistoWidget(QWidget):

    def __init__(self):
        super(AbstractScanHistoWidget, self).__init__()

    def plot_histo(self,
                   ticket,
                   col=Column.X,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow,
                   use_default_factor=True):
        raise NotImplementedError("this methid is abstract")


class Scan3DHistoWidget(AbstractScanHistoWidget):
    class PlotType:
        LINES = 0
        SURFACE = 1

    def __init__(self, image_height=645, image_width=860, type=PlotType.LINES):
        super(Scan3DHistoWidget, self).__init__()

        self.figure = Figure(figsize=(image_height, image_width))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')
        self.axis.set_title("")
        self.axis.clear()

        self.colorbar = None

        self.plot_canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout()

        layout.addWidget(self.plot_canvas)

        self.setLayout(layout)

        self.xx = None
        self.yy = None
        self.zz = None

        self.title = ""
        self.xlabel = ""
        self.ylabel = ""
        self.zlabel = ""

        self.__type=type
        self.__cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.5)

    def clear(self):
        self.reset_plot()
        try:
            self.plot_canvas.draw()
        except:
            pass

    def reset_plot(self):
        self.xx = None
        self.yy = None
        self.zz = None
        self.axis.set_title("")
        self.axis.clear()

    def set_labels(self, title, xlabel, ylabel, zlabel):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.zlabel = zlabel

    def restore_labels(self):
        self.axis.set_title(self.title)
        self.axis.set_xlabel(self.xlabel)
        self.axis.set_ylabel(self.ylabel)
        self.axis.set_zlabel(self.zlabel)

    def set_xrange(self, xrange):
            self.xx = xrange


    def plot_histo(self,
                   ticket,
                   col=Column.X,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow,
                   use_default_factor=True):

        if use_default_factor:
            factor=SRWPlot.get_factor(col)
        else:
            factor=1.0

        if histo_index==0 and xrange is None:
            fwhm = ticket['fwhm']
            xrange = ticket['xrange']

            centroid = xrange[0] + (xrange[1] - xrange[0])*0.5

            if not fwhm is None:
                xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        if isinstance(ticket['histogram'].shape, list):
            histogram = ticket['histogram'][0]
        else:
            histogram = ticket['histogram']

        bins = ticket['bins']

        if not xrange is None:
            good = numpy.where((bins >= xrange[0]) & (bins <= xrange[1]))

            bins = bins[good]
            histogram = histogram[good]

        bins *= factor

        if histo_index==0:
            self.set_xrange(bins)
        elif self.xx.shape != bins.shape:
            histogram = numpy.interp(self.xx, bins, histogram)
            bins = self.xx.copy()

        histogram_stats = histogram
        bins_stats = bins

        fwhm = ticket['fwhm']

        sigma = get_sigma(histogram_stats, bins_stats)
        fwhm = sigma*2.35 if fwhm is None else fwhm*factor

        peak_intensity = numpy.average(histogram_stats[numpy.where(histogram_stats>=numpy.max(histogram_stats)*0.85)])

        rcParams['axes.formatter.useoffset']='False'

        self.set_labels(title=title, xlabel=xtitle, ylabel=scan_variable_name, zlabel=ytitle)

        self.add_histo(scan_variable_value, histogram, has_colormap, colormap, histo_index)

        return HistogramData(histogram_stats, bins_stats, 0.0, xrange, fwhm, sigma, peak_intensity)

    def add_histo(self, scan_value, intensities, has_colormap, colormap, histo_index):
        if self.xx is None: raise ValueError("Initialize X range first")
        if self.xx.shape != intensities.shape: raise ValueError("Given Histogram has a different binning")

        if isinstance(scan_value, str):
            self.yy = numpy.array([1]) if self.yy is None else numpy.append(self.yy, len(self.yy)+1)
        else:
            self.yy = numpy.array([scan_value]) if self.yy is None else numpy.append(self.yy, scan_value)

        if self.zz is None:
            self.zz = numpy.array([intensities])
        else:
            self.zz = numpy.append(self.zz, intensities)

        self.axis.clear()

        self.restore_labels()

        x_to_plot, y_to_plot = numpy.meshgrid(self.xx, self.yy)
        zz_to_plot = self.zz.reshape(len(self.yy), len(self.xx))

        if self.__type==Scan3DHistoWidget.PlotType.SURFACE:
            if has_colormap:
                self.axis.plot_surface(x_to_plot, y_to_plot, zz_to_plot,
                                       rstride=1, cstride=1, cmap=colormap, linewidth=0.5, antialiased=True)
            else:
                self.axis.plot_surface(x_to_plot, y_to_plot, zz_to_plot,
                                       rstride=1, cstride=1, color=self.__cc('black'), linewidth=0.5, antialiased=True)

        elif self.__type==Scan3DHistoWidget.PlotType.LINES:

            if has_colormap:
                self.plot_lines_colormap(x_to_plot, y_to_plot, zz_to_plot, colormap, histo_index)
            else:
                self.plot_lines_black(x_to_plot, zz_to_plot)

            xmin = numpy.min(self.xx)
            xmax = numpy.max(self.xx)
            ymin = numpy.min(self.yy)
            ymax = numpy.max(self.yy)
            zmin = numpy.min(self.zz)
            zmax = numpy.max(self.zz)

            self.axis.set_xlim(xmin,xmax)
            self.axis.set_ylim(ymin,ymax)
            self.axis.set_zlim(zmin,zmax)

        self.axis.mouse_init()

        try:
            self.plot_canvas.draw()
        except:
            pass

    def add_empty_curve(self, histo_data):
        pass


    def plot_lines_black(self, X, Z):
        verts = []
        for i in range(len(self.yy)):
            verts.append(list(zip(X[i], Z[i, :])))

        self.axis.add_collection3d(LineCollection(verts, colors=[self.__cc('black')]), zs=self.yy, zdir='y')

    def plot_lines_colormap(self, X, Y, Z, colormap, histo_index):

        import matplotlib.pyplot as plt

        # Set normalization to the same values for all plots
        norm = plt.Normalize(numpy.min(self.zz), numpy.max(self.zz))

        # Check sizes to loop always over the smallest dimension
        n,m = Z.shape

        if n>m:
            X=X.T; Y=Y.T; Z=Z.T
            m,n = n,m

        transparent_colormap = colormap(numpy.arange(colormap.N))
        transparent_colormap[:,-1] = 0.5*numpy.ones(colormap.N)
        transparent_colormap = ListedColormap(transparent_colormap)

        for j in range(n):
            # reshape the X,Z into pairs
            points = numpy.array([X[j,:], Z[j,:]]).T.reshape(-1, 1, 2)
            segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
            lc = LineCollection(segments, cmap=transparent_colormap, norm=norm)

            # Set the values used for colormapping
            lc.set_array((Z[j,1:]+Z[j,:-1])/2)
            lc.set_linewidth(2) # set linewidth a little larger to see properly the colormap variation
            self.axis.add_collection3d(lc, zs=(Y[j,1:]+Y[j,:-1])/2,  zdir='y') # add line to axes

        if histo_index==0:
            self.colorbar = self.figure.colorbar(lc) # add colorbar, as the normalization is the same for all,

        self.colorbar.update_normal(lc)
        self.colorbar.draw_all()
        self.colorbar.update_bruteforce(lc)

class ScanHistoWidget(AbstractScanHistoWidget):

    def __init__(self):
        super(ScanHistoWidget, self).__init__()

        self.plot_canvas = oasysgui.plotWindow(parent=None,
                                               backend=None,
                                               resetzoom=True,
                                               autoScale=True,
                                               logScale=False,
                                               grid=True,
                                               curveStyle=True,
                                               colormap=False,
                                               aspectRatio=False,
                                               yInverted=False,
                                               copy=True,
                                               save=True,
                                               print_=True,
                                               control=True,
                                               position=True,
                                               roi=False,
                                               mask=False,
                                               fit=True)

        layout = QVBoxLayout()

        layout.addWidget(self.plot_canvas)

        self.setLayout(layout)


    def plot_histo(self,
                   ticket,
                   col=Column.X,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow,
                   use_default_factor=True):
        if use_default_factor:
            factor=SRWPlot.get_factor(col)
        else:
            factor=1.0

        if histo_index==0 and xrange is None:
            fwhm = ticket['fwhm']
            xrange = ticket['xrange']

            centroid = xrange[0] + (xrange[1] - xrange[0])*0.5

            if not fwhm is None:
                xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        if isinstance(ticket['histogram'].shape, list):
            histogram = ticket['histogram'][0]
        else:
            histogram = ticket['histogram']

        bins = ticket['bins']

        if not xrange is None:
            good = numpy.where((bins >= xrange[0]) & (bins <= xrange[1]))

            bins = bins[good]
            histogram = histogram[good]

        bins *= factor

        histogram_stats = histogram
        bins_stats = bins

        fwhm = ticket['fwhm']

        sigma = get_sigma(histogram_stats, bins_stats)
        fwhm = sigma*2.35 if fwhm is None else fwhm*factor

        peak_intensity = numpy.average(histogram_stats[numpy.where(histogram_stats>=numpy.max(histogram_stats)*0.85)])

        if histo_index==0 and show_reference:
            h_title = "Reference"
        else:
            h_title = scan_variable_name + ": " + str(scan_variable_value)

        color="#000000"

        import matplotlib
        matplotlib.rcParams['axes.formatter.useoffset']='False'

        if histo_index== 0:
            offset = int(peak_intensity*0.3)

        self.plot_canvas.addCurve(bins, histogram + offset*histo_index, h_title, symbol='', color=color, xlabel=xtitle, ylabel=ytitle, replace=False) #'+', '^', ','

        if add_labels: self.plot_canvas._backend.ax.text(xrange[0]*factor*1.05, offset*histo_index*1.05, h_title)

        if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
        if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
        if not title is None:  self.plot_canvas.setGraphTitle(title)

        for label in self.plot_canvas._backend.ax.yaxis.get_ticklabels():
            label.set_color('white')
            label.set_fontsize(1)

        self.plot_canvas.setActiveCurveColor(color="#00008B")

        self.plot_canvas.resetZoom()
        self.plot_canvas.replot()

        self.plot_canvas.setGraphXLimits(xrange[0]*factor, xrange[1]*factor)

        self.plot_canvas.setActiveCurve(h_title)

        self.plot_canvas.setDefaultPlotLines(True)
        self.plot_canvas.setDefaultPlotPoints(False)

        self.plot_canvas.getLegendsDockWidget().setFixedHeight(510)
        self.plot_canvas.getLegendsDockWidget().setVisible(True)

        self.plot_canvas.addDockWidget(Qt.RightDockWidgetArea, self.plot_canvas.getLegendsDockWidget())

        return HistogramData(histogram_stats, bins_stats, offset, xrange, fwhm, sigma, peak_intensity)

    def add_empty_curve(self, histo_data):
        self.plot_canvas.addCurve(numpy.array([histo_data.get_centroid()]),
                                  numpy.zeros(1),
                                 "Click on curve to highlight it",
                                  xlabel="",
                                  ylabel="",
                                  symbol='',
                                  color='white')

        self.plot_canvas.setActiveCurve("Click on curve to highlight it")
