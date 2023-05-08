import ROOT
import os, sys
import math
import ctypes
import time
#from initiate import initiate_garfield
#from graphics import create_view_window
from garfield_base import GarfieldSetup

FILE_NAME = "../DataFiles/EXYZ_gpp.txt"
#FILE_NAME = "EXYZ_Ca40_800MeV.txt"
PLOT_TIME = 1


class Chamber(GarfieldSetup):
    #def __init__(self, path, file_name, plot_time, gf):
    def __init__(self, file_name, plot_time):
        super().__init__()
        #self.path = path
        self.file_name = file_name
        self.plot_time = plot_time
        #self.gf = gf

        self.plotDrift = False
        self.plotSignal = True
        self.silicon_half_thickness = 100.0e-4
        # self.silicon_half_thickness = 200.e-4
        self.num_ions = 1  # set to 0 to load all ions
        self.num_skip_ions = 0

        self.window_height = 600
        self.window_width = 600

        self.gas = None
        self.cmp_constant = None
        self.sensor = None
        self.track = None
        self.drift = None
        self.signal_view = None
        self.field_view = None

        self.drift_view = None
        self.cell_view = None

    def set_cmp_fields(self):
        self.cmp_constant = self.gf.ComponentConstant()

        # ex, ey, ez components of the (uniform) electric field
        self.cmp_constant.SetElectricField(ex=0.0, ey=5000.0, ez=0.0)

        d = self.silicon_half_thickness
        x_min, x_max, y_min, y_max, z_min, z_max = -d, 0.0, -d, d, d, d
        self.cmp_constant.SetArea(x_min, x_max, y_min, y_max, z_min, z_max)
        self.cmp_constant.SetMedium(self.gf.MediumSilicon())

        self.cmp_constant.SetWeightingField(wx=0, wy=1.0 / d, wz=0.0, label="readout")
        self.cmp_constant.SetWeightingPotential(x=0, y=0, z=0, v=1.0)

    def create_sensor(self):
        """A sensor is a composite of components, combining fields from different
        components to completely describe a detector."""

        self.sensor = self.gf.Sensor()
        # include the component when calculating the electric and magnetic field
        self.sensor.AddComponent(self.cmp_constant)
        # Request the weighting field label to be used for computing the signal
        self.sensor.AddElectrode(self.cmp_constant, label="readout")

    def set_signal_time_window(self):
        num_time_bins = 1000
        t_min, t_max = 0, 10
        t_step = (t_max - t_min) / num_time_bins
        self.sensor.SetTimeWindow(t_min, t_step, num_time_bins)

    # Used in create_track
    def load_exyz_file(self):
        if not self.track.ReadFile(self.file_name, self.num_ions, self.num_skip_ions):
            raise Exception("Failed to read EXYZ file.")

    def create_track(self):
        """Simulate ionization patterns produces by the ion
        traversing the detector."""
        self.track = self.gf.TrackTrim()
        self.load_exyz_file()
        self.track.SetSensor(self.sensor)

    def create_drift(self):
        # RKF integration.
        self.drift = self.gf.DriftLineRKF()
        self.drift.SetSensor(self.sensor)
        self.drift.SetMaximumStepSize(10.0e-4)

    def create_drift_view(self):
        self.drift_view = self.gf.ViewDrift()

    # not necessary
    def enable_plotting(self):
        pass
        # self.drift.EnablePlotting(self.drift_view)
        #self.track.EnablePlotting(self.drift_view)

    def loop_over_clusters(self):
        """Cluster refer to the energy loss in a single ionizing collision of the ion
        and the electrons produced in the process.
        Each cluster correspond to one energy interval for an ion in the EXYZ file."""

        # print(len(list(self.track.GetClusters())))
        for cluster in self.track.GetClusters():
            self.drift.SetElectronSignalScalingFactor(cluster.n)
            self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)
            self.drift.SetHoleSignalScalingFactor(cluster.n)
            self.drift.DriftHole(cluster.x, cluster.y, cluster.z, cluster.t)

    def set_drift_view_area(self):
        self.drift_view.SetArea(-2.0e-4, 0.0, 2.0e-4, 100.0e-4)

    def create_signal_view(self):
        self.signal_view = self.gf.ViewSignal()
        self.create_canvas(
            view=self.signal_view,
            name="signal",
        )
        self.signal_view.SetSensor(self.sensor)

    def create_field_view(self):
        self.field_view = self.gf.ViewField()
        self.create_canvas(
            view=self.signal_view,
            name="signal",
        )
        self.field_view.SetComponent(self.cmp_constant)
        self.field_view.SetSensor(self.sensor)

    # Not used
    def plot_drift_view(self):
        self.drift_view.GetCanvas().Clear()
        self.cell_view.Plot2d()
        self.drift_view.Plot(True, False)
        ROOT.gPad.Update()

    def plot_signal_view(self):
        "letters t, e, i represent three different graphs"
        self.signal_view.PlotSignal(label="readout", optTotal="tei")
        # print(self.signal_view.PlotSignal.__doc__)

    def plot_field_view(self):
        # self.field_view.PlotProfile(
        #     x0=0, y0=0, z0=0,
        #     x1=0, y1=0, z1=10,
        #     option="e", normalised=False
        # )
        # self.field_view.PlotContourWeightingField(
        #     label="readout", option="e"
        # )
        self.field_view.PlotWeightingField(label="readout", option="e", drawopt="")
        
    def setup(self):
        self.set_cmp_fields()
        self.create_sensor()
        self.set_signal_time_window()
        self.create_track()
        self.create_drift()
        #self.create_drift_view()
        self.enable_plotting()

    def plot_all_ions(self):
        for i in range(self.num_ions):
            self.sensor.ClearSignal()
            self.track.NewTrack(x0=0, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0)
            self.loop_over_clusters()
            #self.set_drift_view_area() # move to setup?
            self.sensor.ConvoluteSignals()

            self.create_signal_view()
            self.plot_signal_view()

            time.sleep(self.plot_time)

    def run(self):
        self.setup()
        self.plot_all_ions()


def main():
    #path, gf = initiate_garfield()
    #chamber = Chamber(path, FILE_NAME, PLOT_TIME, gf)
    chamber = Chamber(FILE_NAME, PLOT_TIME)
    chamber.run()


if __name__ == "__main__":
    main()
