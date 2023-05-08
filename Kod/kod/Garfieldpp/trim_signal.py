import ROOT
import os, sys
import math
import ctypes
import time


FILE_NAME = "EXYZ_example.txt"
PLOT_TIME = 20

def initiate_garfield():
    path = os.getenv("GARFIELD_INSTALL")
    print("PATH:", path)
    if sys.platform == "darwin":
        ROOT.gSystem.Load(path + "/lib/libmagboltz.dylib")
        ROOT.gSystem.Load(path + "/lib/libGarfield.dylib")
    else:
        ROOT.gSystem.Load(path + "/lib/libmagboltz.so")
        ROOT.gSystem.Load(path + "/lib/libGarfield.so")
    return path, ROOT.Garfield

class Chamber:
    def __init__(self, path, file_name, plot_time, gf):
        self.path = path
        self.file_name = file_name
        self.plot_time = plot_time
        self.gf = gf

        self.plotDrift = True
        self.plotSignal = True
        # Wire radius [cm]
        self.r_wire = 25.0e-4
        # Outer radius of the tube [cm]
        self.r_tube = 0.71
        # Voltages
        self.v_wire = 2730.0
        self.v_tube = 0.0
        # [cm]
        self.silicon_half_thickness = 100.e-4
        # self.silicon_half_thickness = 200.e-4
        self.num_ions = 1

        self.gas = None
        self.cmp_constant = None
        self.sensor = None
        self.track = None
        self.drift = None
        self.drift_view = None
        self.cell_view = None
        self.signal_view = None

    def set_cmp_fields(self):
        self.cmp_constant = self.gf.ComponentConstant()
        self.cmp_constant.SetElectricField(0., 5000., 0.)

        d = self.silicon_half_thickness
        self.cmp_constant.SetArea(-d, 0., -d, d, d, d)
        self.cmp_constant.SetMedium(self.gf.MediumSilicon())
        self.cmp_constant.SetWeightingField(0, 1. / d, 0., "readout")
        self.cmp_constant.SetWeightingPotential(0, 0, 0, 1.)
        print(self.cmp_constant.SetMedium.__doc__)

    def create_sensor(self):
        self.sensor = self.gf.Sensor()
        self.sensor.AddComponent(self.cmp_constant)
        self.sensor.AddElectrode(self.cmp_constant, "readout")

    def set_signal_time_window(self):
        num_time_bins = 1000
        t_min, t_max = 0, 10
        t_step = (t_max - t_min) / num_time_bins
        self.sensor.SetTimeWindow(t_min, t_step, num_time_bins)

    # Used in create_track
    def load_exyz_file(self):
        if not self.track.ReadFile(self.file_name, self.num_ions):
            raise Exception("Failed to read EXYZ file.")

    def create_track(self):
        self.track = self.gf.TrackTrim()
        self.load_exyz_file()
        self.track.SetSensor(self.sensor)

    def create_drift(self):
        # RKF integration.
        self.drift = self.gf.DriftLineRKF()
        self.drift.SetSensor(self.sensor)
        self.drift.SetMaximumStepSize(10.e-4)

    def create_drift_view(self):
        self.drift_view = self.gf.ViewDrift()
        # Todo: figure out what this does
        cD = ROOT.TCanvas('cD', '', 600, 600)
        self.drift_view.SetCanvas(cD)

    def enable_plotting(self):
        self.drift.EnablePlotting(self.drift_view)
        self.track.EnablePlotting(self.drift_view)
        # self.cell_view.SetComponent(self.cmp_field)
        # self.cell_view.SetCanvas(self.drift_view.GetCanvas())

    def create_ion_track(self):
        self.track.NewTrack(0., 0., 0., 0., 0., 1., 0.)

    def loop_over_clusters(self):
        for cluster in self.track.GetClusters():
            self.drift.SetElectronSignalScalingFactor(cluster.n)
            self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)
            self.drift.SetHoleSignalScalingFactor(cluster.n)
            self.drift.DriftHole(cluster.x, cluster.y, cluster.z, cluster.t)

    def set_drift_view_area(self):
        self.drift_view.SetArea(-2.e-4, 0., 2.e-4, 100.e-4)

    def create_signal_view(self):
        self.signal_view = self.gf.ViewSignal()
        # Todo: figure out what this does
        cS = ROOT.TCanvas('cS', '', 600, 600)
        self.signal_view.SetCanvas(cS)

        self.signal_view.SetSensor(self.sensor)

    # Not used
    def plot_drift(self):
        self.drift_view.GetCanvas().Clear()
        self.cell_view.Plot2d()
        self.drift_view.Plot(True, False)
        ROOT.gPad.Update()

    def plot_signal_view(self):
        self.signal_view.PlotSignal("readout", "tei")
        time.sleep(self.plot_time)

    def run(self):
        self.set_cmp_fields()
        self.create_sensor()
        self.set_signal_time_window()
        self.create_track()
        self.create_drift()
        self.create_drift_view()
        self.enable_plotting()
        self.create_ion_track()
        self.loop_over_clusters()
        self.set_drift_view_area()
        self.create_signal_view()
        self.plot_signal_view()


def main():
    path, gf = initiate_garfield()
    chamber = Chamber(path, FILE_NAME, PLOT_TIME, gf)
    chamber.run()

if __name__ == "__main__":
    main()
