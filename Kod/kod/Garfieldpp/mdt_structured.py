import ROOT
import os, sys
import math
import ctypes
import time
from garfield_base import GarfieldSetup


FILE_NAME = 'mdt_elx_delta.txt'
PLOT_TIME = 1

class Chamber(GarfieldSetup):
    def __init__(self, plot_time, file_name):
        super().__init__()
        self.file_name = file_name
        self.plot_time = plot_time

        self.plotDrift = True
        self.plotSignal = True
        # Wire radius [cm]
        self.r_wire = 25.0e-4
        # Outer radius of the tube [cm]
        self.r_tube = 0.71
        # Voltages
        self.v_wire = 2730.0
        self.v_tube = 0.0
        self.window_width = 400
        self.window_height = 400
        self.num_tracks = 10

        self.gas = None
        self.cmp_field = None
        self.sensor = None
        self.track = None
        self.drift = None
        self.drift_view = None
        self.cell_view = None
        self.signal_view = None

    def create_gas(self):
        self.gas = self.gf.MediumMagboltz()
        #self.gas.LoadGasFile("ar_93_co2_7_3bar.gas")
        self.gas.LoadGasFile("CF4.gas")
        self.gas.LoadIonMobility(
            self.path + "/share/Garfield/Data/IonMobility_CF4+_CF4.txt"
        )

    def create_cmp_analytic_field(self):
        self.cmp_field = self.gf.ComponentAnalyticField()
        self.cmp_field.SetMedium(self.gas)

        self.cmp_field.AddWire(x=-0.4, y=0, diameter=2 * self.r_wire, voltage=self.v_wire, label="s")
        self.cmp_field.AddWire(x=0.4, y=0, diameter=2 * self.r_wire, voltage=self.v_wire, label="s")
        # Add the tube.
        self.cmp_field.AddTube(radius=self.r_tube, voltage=self.v_tube, nEdges=0, label="t")
        # Request calculation of the weighting field.
        self.cmp_field.AddReadout("s")

    def create_sensor(self):
        self.sensor = self.gf.Sensor()
        self.sensor.AddComponent(self.cmp_field)
        self.sensor.AddElectrode(self.cmp_field, "s")

    def set_signal_time_window(self):
        tstep = 0.5
        tmin = -0.5 * tstep
        nbins = 1000
        self.sensor.SetTimeWindow(tmin, tstep, nbins)

    def load_data(self):
        with open(self.file_name, "r") as infile:
            times = ROOT.std.vector("double")()
            values = ROOT.std.vector("double")()
            for line in infile:
                line = line.strip()
                line = line.split()
                times.push_back(1.0e3 * float(line[0]))
                values.push_back(float(line[1]))
            self.sensor.SetTransferFunction(times, values)

    def create_track(self):
        self.track = self.gf.TrackHeed()
        self.track.SetParticle("muon")
        self.track.SetEnergy(170.0e9)
        self.track.SetSensor(self.sensor)

    def create_drift(self):
        # RKF integration.
        self.drift = self.gf.DriftLineRKF()
        self.drift.SetSensor(self.sensor)
        # Todo: change this and see if it changes randomness
        # self.drift.SetGainFluctuationsPolya(0.0, 20000.0)
        #self.drift.SetGainFluctuationsPolya(0.0, 10.0)


    def create_drift_view(self):
        self.drift_view = self.gf.ViewDrift()
        self.drift_view = self.create_canvas(self.drift_view, 'cD')

    def create_cell_view(self):
        self.cell_view = self.gf.ViewCell()

    def enable_drift_plot(self):
        self.drift.EnablePlotting(self.drift_view)
        self.track.EnablePlotting(self.drift_view)
        self.cell_view.SetComponent(self.cmp_field)
        self.cell_view.SetCanvas(self.drift_view.GetCanvas())

    def create_signal_view(self):
        self.signal_view = self.gf.ViewSignal()
        self.signal_view = self.create_canvas(self.signal_view, 'cS')
        self.signal_view.SetSensor(self.sensor)

    def plot_drift(self):
        self.drift_view.GetCanvas().Clear()
        self.cell_view.Plot2d()
        self.drift_view.Plot(True, False)
        ROOT.gPad.Update()

    def loop_through_clusters(self):
        for cluster in self.track.GetClusters():
            for electron in cluster.electrons:
                self.drift.DriftElectron(electron.x, electron.y, electron.z, electron.t)
            if self.plotDrift:
                self.plot_drift()

    def plot(self):
        # r_track = 0.3
        r_track = 0.3
        x0 = r_track
        y0 = - math.sqrt(self.r_tube ** 2 - r_track ** 2)

        for i in range(self.num_tracks):
            self.sensor.ClearSignal()
            self.track.NewTrack(x0=x0, y0=y0, z0=0, t0=0, dx0=0, dy0=1, dz0=0)
            self.loop_through_clusters()
            self.sensor.ConvoluteSignals()

            nt = ctypes.c_int(0)
            if not self.sensor.ComputeThresholdCrossings(-2.0, "s", nt):
                continue
            if self.plotSignal:
               self.signal_view.PlotSignal("s")

            time.sleep(self.plot_time)

    def run(self):
        self.create_gas()
        self.create_cmp_analytic_field()
        self.create_sensor()
        self.set_signal_time_window()
        self.load_data()
        self.create_track()
        self.create_drift()
        self.create_drift_view()
        self.create_cell_view()
        self.enable_drift_plot()
        self.create_signal_view()

        self.plot()


def main():
    chamber = Chamber(PLOT_TIME, FILE_NAME)
    chamber.run()

if __name__ == "__main__":
    main()
