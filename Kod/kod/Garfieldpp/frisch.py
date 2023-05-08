import time
import sys

import matplotlib.pyplot as plt
import ROOT

from garfield_base import GarfieldSetup
from func_lib import load_root_libraries, load_garfield

# EXYZ_FILE = "../DataFiles/EXYZ_gpp.txt"
EXYZ_FILE = "../DataFiles/EXYZ_He4-5.4MeV_2023-04-03_1113.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Li6-10.0MeV_2023-04-04_1352.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_C12-100.0MeV_2023-04-04_1335.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Be8-20.0MeV_2023-04-04_1357.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Ca40-800.0MeV_2023-04-04_1253.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Ca40-800.0MeV_2023-04-04_1253 copy.txt"


class Chamber(GarfieldSetup):
    def __init__(
        self,
        file_name,
        label="Signals",
        plotSignal=False,
        plotSetup=False,
        plotDrift=False,
        use_frisch=True,
        row_step=1,
        num_time_bins=2000,
        t_min=0,
        t_max=3000,
        field_strength = 100,
        distance_between_plates=10,
        num_wires=200,
        grid2anode_ratio=0.95,
        wire_diameter=0.002,
        chamber_half_size=25,
    ):
        super().__init__()

        self.label = label
        self.file_name = file_name
        self.num_ions = 1  # 0 to load all ions
        self.num_skip_ions = 0
        self.row_step = row_step
        self.num_time_bins = num_time_bins
        self.t_min, self.t_max = t_min, t_max


        self.caf = self.gf.ComponentAnalyticField()
        self.sensor = self.gf.Sensor()
        self.track = self.gf.TrackTrim()

        self.electrodes = []
        self.total_half_size = 100
        self.chamber_half_size = chamber_half_size
        self.plot_margin = 1.1
        # self.voltage_difference = voltage_difference
        self.distance_between_plates = distance_between_plates
        # self.voltage_per_cm = self.voltage_difference / self.distance_between_plates
        self.field_strength = field_strength

        self.use_frisch = use_frisch
        self.num_wires = num_wires
        self.grid2anode_ratio = grid2anode_ratio
        self.wire_diameter = wire_diameter

        self.debug_mode = False # If True the program will stopa after plotting setup
        self.plotSetup = plotSetup
        self.plotSignal = plotSignal # Plots the ROOT signal
        self.plotDrift = plotDrift

    def setup_caf(self):
        self.caf.SetMedium(self.gas)
        grid_to_anode_distance = self.distance_between_plates/2*(1-self.grid2anode_ratio)
        grid_to_cathode_distance = self.distance_between_plates-grid_to_anode_distance
        anode_voltage = grid_to_anode_distance * self.field_strength
        cathode_voltage = - grid_to_cathode_distance*self.field_strength
        # absolute_voltage = self.voltage_per_cm * self.distance_between_plates / 2
        # absolute_voltage = self.voltage_difference / 2

        print(f"{grid_to_anode_distance= } || {grid_to_cathode_distance= }")
        print(f"{anode_voltage= } || {cathode_voltage= }")

        self.caf.AddPlaneY(
            y=-self.distance_between_plates / 2,
            voltage=cathode_voltage,
            label="Cathode",
        )
        self.caf.AddReadout(label="Cathode")
        self.electrodes.append("Cathode")

        self.caf.AddPlaneY(
            y=self.distance_between_plates / 2,
            voltage=anode_voltage,
            label="Anode",
        )
        self.caf.AddReadout(label="Anode")
        self.electrodes.append("Anode")

        if self.use_frisch:
            for i in range(self.num_wires):
                y = self.distance_between_plates / 2 * self.grid2anode_ratio
                self.caf.AddWire(
                    x=2 * self.chamber_half_size / self.num_wires * (i + 0.5)
                    - self.chamber_half_size,
                    y=y,
                    # diameter=0.002,
                    diameter=self.wire_diameter,
                    voltage= 0, #y * self.voltage_per_cm,
                    label="Frisch grid",
                    length=100,
                )
            self.caf.AddReadout(label="Frisch grid")
            self.electrodes.append("Frisch grid")

    def setup_sensor(self):
        self.sensor.AddComponent(self.caf)
        self.set_area(self.sensor, self.total_half_size)
        for electrode in self.electrodes:
            self.sensor.AddElectrode(self.caf, label=electrode)

    def set_signal_time_window(self):
        self.t_step = (self.t_max - self.t_min) / self.num_time_bins
        self.sensor.SetTimeWindow(self.t_min, self.t_step, self.num_time_bins)

    def read_data(self):
        """Read the data file from SRIM"""

        # Import ions.
        file = self.track.ReadFile(
            file=self.file_name,
            nIons=self.num_ions,
            nSkip=self.num_skip_ions,
        )
        if not file:
            raise Exception("Failed to read EXYZ file.")

        # Connect the track to a sensor.
        self.track.SetSensor(self.sensor)

    def create_drift(self):
        self.drift = self.gf.DriftLineRKF()
        self.drift.SetSensor(self.sensor)
        # self.drift.SetMaximumStepSize(10.0e-4)

    def loop_through_clusters(self):
        """Cluster refer to the energy loss in a single ionizing collision of the ion
        and the electrons produced in the process.
        Each cluster correspond to one energy interval for an ion in the EXYZ file."""

        # for cluster in self.track.GetClusters():
        #     self.drift.SetElectronSignalScalingFactor(scale=cluster.n)
        #     self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)
        #     # self.drift.SetHoleSignalScalingFactor(cluster.n)
        #     # self.drift.DriftHole(cluster.x, cluster.y, cluster.z, cluster.t)
        clusters = self.track.GetClusters()
        for i in range(0, len(clusters), self.row_step):
            cluster = clusters[i]
            self.drift.SetElectronSignalScalingFactor(scale=cluster.n)
            self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)

    def create_signal(self):
        # self.sensor.ClearSignal()
        self.track.NewTrack(
            x0=-self.chamber_half_size * 0.95, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0
            # x0=0, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0
        )
        # self.track.NewTrack(x0=0, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0)
        self.loop_through_clusters()

    def set_area(self, obj, size):
        obj.SetArea(
            xmin=-size,
            zmin=-size,
            ymin=-size,
            xmax=size,
            ymax=size,
            zmax=size,
        )
        return obj

    def plot_setup(self):
        self.field_view = self.gf.ViewField()
        self.field_view = self.create_canvas(view=self.field_view, name="setup")
        self.field_view.SetComponent(c=self.caf)
        self.field_view.SetNumberOfContours(n=40)
        self.set_area(self.field_view, self.chamber_half_size * self.plot_margin)
        self.field_view.PlotContour()
        # self.field_view.Plot(option="v", drawopt="CONT1")

        self.cell_view = self.gf.ViewCell()
        self.cell_view.SetCanvas(pad=self.field_view.GetCanvas())
        self.cell_view.SetComponent(comp=self.caf)
        self.set_area(self.cell_view, self.chamber_half_size * self.plot_margin)
        self.cell_view.Plot2d()

    def enable_drift_plot(self):
        self.drift_view = self.gf.ViewDrift()
        self.drift_view = self.create_canvas(view=self.drift_view, name="drift")
        self.drift.EnablePlotting(self.drift_view)
        self.track.EnablePlotting(self.drift_view)
        self.set_area(self.drift_view, self.chamber_half_size * self.plot_margin)

        self.cell_view = self.gf.ViewCell()
        self.cell_view.SetComponent(comp=self.caf)
        self.cell_view.SetCanvas(pad=self.drift_view.GetCanvas())
        self.set_area(self.cell_view, self.chamber_half_size * self.plot_margin)

    def get_signals(self):
        self.times = [self.t_min + i * self.t_step for i in range(self.num_time_bins)]
        self.signals = {
            electrode: [
                self.sensor.GetSignal(label=electrode, bin=i)
                for i in range(self.num_time_bins)
            ]
            for electrode in self.electrodes
        }
        return {"times": self.times, "signals": self.signals}
    
    def plot_signals(self, ax, t_min_plot=None, t_max_plot=None):
        self.get_signals()
        # add titel and axis labels
        ax.set_title(self.label)
        ax.set_ylabel("i [fC/ns]")
        ax.set_ylabel("t [ns]")

        if t_min_plot is None:
            t_min_plot = self.t_min
        if t_max_plot is None:
            t_max_plot = self.t_max

        i_start = int(t_min_plot // self.t_step)
        i_end = int(t_max_plot // self.t_step)
        times2plot = self.times[i_start:i_end]
        for electrode in self.electrodes:
            # ax.plot(self.times, self.signals[electrode], label=electrode)
            ax.plot(times2plot, self.signals[electrode][i_start:i_end], label=electrode)
        ax.legend(prop = {'size': 8})

    def plot_signal_root(self):
        for electrode in self.electrodes:
            self.signal_view = self.gf.ViewSignal()
            self.create_canvas(
                view=self.signal_view,
                name=electrode,
                title=electrode,
            )
            self.signal_view.SetSensor(self.sensor)
            self.signal_view.PlotSignal(label=electrode)
            time.sleep(1)

    def run(self):
        self.setup_caf()
        self.setup_sensor()

        if self.plotSetup:
            self.plot_setup()
            if self.debug_mode:
                input("Press Enter to continue...")

        self.read_data()
        self.set_signal_time_window()

        self.create_drift()
        if self.plotDrift:
            self.enable_drift_plot()

        for i in range(self.num_ions):
            self.create_signal()

            if self.plotDrift:
                self.cell_view.Plot2d()
                self.drift_view.Plot(twod=True, axis=False)
                # ROOT.gPad.Update() # TODO: why is this needed?
            if self.plotSignal:
                fig, ax = plt.subplots()
                self.plot_signals(ax)
                plt.show()
                # self.plot_signal_root()

        # input("Press Enter to continue...")


if __name__ == "__main__":
    load_garfield()

    # EXYZ_FILE = "../DataFiles/EXYZ_He4-5.4MeV_2023-04-03_1113.txt"
    EXYZ_FILE = "../DataFiles/EXYZ_Sr80-1200.0MeV_2023-04-27_1454.txt"

    # chamber = Chamber(EXYZ_FILE, use_frisch=False, plotSetup=True, plotDrift=True, plotSignal=True, row_step=1)
    # EXYZ_FILE = "../DataFiles/EXYZ_He4-5.4MeV_2023-04-26_1144.txt"
    chamber = Chamber(EXYZ_FILE, use_frisch=False, plotSetup=True, plotDrift=True, plotSignal=True)

    # chamber = Chamber(EXYZ_FILE, use_frisch=False, plotSetup=True, plotDrift=True, plotSignal=True, row_step=10)
    chamber.run()
