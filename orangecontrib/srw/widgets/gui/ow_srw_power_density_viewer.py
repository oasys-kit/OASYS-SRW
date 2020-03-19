import numpy

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.widgets.gui.ow_srw_wavefront_viewer import SRWWavefrontViewer

from silx.gui.plot import Plot2D

class SRWPowerDensityViewer(SRWWavefrontViewer):

    def __init__(self, show_general_option_box=True, show_automatic_box=True, show_view_box=True):
        super().__init__(show_general_option_box=show_general_option_box, show_automatic_box=show_automatic_box, show_view_box=show_view_box)

    def plot_2D(self, ticket, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum="", ignore_range=False, apply_alpha_channel=False, alpha_ticket=None, do_unwrap=False):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = Plot2D()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

            self.plot_canvas[plot_canvas_index].resetZoom()
            self.plot_canvas[plot_canvas_index].setXAxisAutoScale(True)
            self.plot_canvas[plot_canvas_index].setYAxisAutoScale(True)
            self.plot_canvas[plot_canvas_index].setGraphGrid(False)
            self.plot_canvas[plot_canvas_index].setKeepDataAspectRatio(False)
            self.plot_canvas[plot_canvas_index].yAxisInvertedAction.setVisible(False)

            self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
            self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)
            self.plot_canvas[plot_canvas_index].getMaskAction().setVisible(False)
            self.plot_canvas[plot_canvas_index].getRoiAction().setVisible(False)
            self.plot_canvas[plot_canvas_index].getColormapAction().setVisible(True)

        if self.use_range == 1 and not ignore_range:
            plotting_range = [self.range_x_min/1000, self.range_x_max/1000, self.range_y_min/1000, self.range_y_max/1000]
        else:
            plotting_range = None

        factor1=SRWPlot.get_factor(var_x)
        factor2=SRWPlot.get_factor(var_y)

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

            histogram = []
            for row in ticket['histogram'][range_x]:
                histogram.append(row[range_y])

            nbins_h = len(xx)
            nbins_v = len(yy)

        if len(xx) == 0 or len(yy) == 0:
            raise Exception("Nothing to plot in the given range")

        xmin, xmax = xx.min(), xx.max()
        ymin, ymax = yy.min(), yy.max()

        origin = (xmin*factor1, ymin*factor2)
        scale = (abs((xmax-xmin)/nbins_h)*factor1, abs((ymax-ymin)/nbins_v)*factor2)

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        # PyMCA inverts axis!!!! histogram must be calculated reversed
        self.plot_canvas[plot_canvas_index].addImage(ticket['histogram'].T,
                                  legend="Power Density",
                                  scale=scale,
                                  origin=origin,
                                  colormap=colormap,
                                  replace=True)

        self.plot_canvas[plot_canvas_index].setActiveImage("Power Density")

        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
