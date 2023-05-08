import ROOT
import ctypes
import sys
import matplotlib.pyplot as plt
import numpy as np

def load_root_libraries():
    root_path = root_path = "/chalmers/sw/unsup64/root-6.26.10/lib"
    ctypes.cdll.LoadLibrary(f"{root_path}/libCore.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libThread.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libtbb.so.2")
    ctypes.cdll.LoadLibrary(f"{root_path}/libImt.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libRIO.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libNet.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libTree.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libMathCore.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libMatrix.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libHist.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libGeom.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libXMLIO.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libGdml.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libGraf.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libGpad.so")
    ctypes.cdll.LoadLibrary(f"{root_path}/libGraf3d.so")
    # this one can't be found and might be necessary for root plots
    # ctypes.cdll.LoadLibrary(f'{root_path}/libcppyy_backend3_7.so')


def load_garfield():
    garfield_path = "/chalmers/groups/subprog/devuan.compile/garfield/ins/lib"
    if sys.platform == "darwin":
        ROOT.gSystem.Load(f"{garfield_path}/libmagboltz.dylib")
        ROOT.gSystem.Load(f"{garfield_path}/libGarfield.dylib")
    else:
        ROOT.gSystem.Load(f"{garfield_path}/libmagboltz.so")
        ROOT.gSystem.Load(f"{garfield_path}/libGarfield.so")

def get_subplot_rows_cols(num_plots, max_cols):
    if num_plots == 1:
        return 1, 1
    elif num_plots <= max_cols:
        return 1, num_plots
    else:
        num_cols = min(max_cols, int(np.ceil(np.sqrt(num_plots))))
        num_rows = int(np.ceil(num_plots / num_cols))
        return num_rows, num_cols

def plot_chambers(*args, width=5, height=4, max_cols=2, t_min_plot=None, t_max_plot=None):
    """args is a list of chamber objects"""
    num_plots = len(args)
    num_rows, num_cols = get_subplot_rows_cols(num_plots, max_cols)
    fig, axs = plt.subplots(
        num_rows, num_cols, figsize=(width * num_cols, height * num_rows)
    )
    for i, chamber in enumerate(args):
        ax = axs.flat[i] if num_plots > 1 else axs
        chamber.run()
        chamber.plot_signals(ax, t_min_plot=t_min_plot, t_max_plot=t_max_plot)
    fig.tight_layout()
    plt.show()
