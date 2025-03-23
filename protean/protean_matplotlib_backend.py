import matplotlib

from matplotlib.backends.backend_svg import FigureCanvasSVG,_BackendSVG

from matplotlib.backend_bases import _Backend

figures_to_show = []

class FigureCanvasNTPY(FigureCanvasSVG):
  def __init__(self, figure, *args, **kwargs):
    FigureCanvasSVG.__init__(self, figure, *args, **kwargs)
    global figures_to_show 
    figures_to_show.append(self)


@_Backend.export
class _BackendProtean(_Backend):
  backend_version = matplotlib.__version__
  FigureCanvas = FigureCanvasProtean

def flush_figures():
  global figures_to_show 
  new_figures = figures_to_show.copy()
  figures_to_show = []
  return new_figures

