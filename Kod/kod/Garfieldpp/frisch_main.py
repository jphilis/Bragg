from garfield_base import GarfieldSetup
import ROOT

SLEEP_TIME = 200
#EXYZ_FILE = "../DataFiles/EXYZ_gpp.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_He4-5.4MeV_2023-04-03_1113.txt"
EXYZ_FILE = "../DataFiles/EXYZ_Ca40-800.0MeV_2023-04-04_1253.txt"
#EXYZ_FILE = "../DataFiles/EXYZ_C12-100.0MeV_2023-04-04_1335 copy.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Li6-10.0MeV_2023-04-04_1352.txt"
# EXYZ_FILE = "../DataFiles/EXYZ_Be8-20.0MeV_2023-04-04_1357.txt"


class Chamber(GarfieldSetup):
    def __init__(self, sleep_time, file_name):
        super().__init__()

        self.sleep_time = sleep_time
        self.num_ions = 1 # 0 to load all ions
        self.num_skip_ions = 0
        self.file_name = file_name

        self.caf = self.gf.ComponentAnalyticField()
        self.sensor = self.gf.Sensor()
        self.track = self.gf.TrackTrim()

        self.electrodes = []

        self.plotSetup = True
        self.plotSignal = True
        self.plotDrift = True


    def create_electrodes(self, vAnode: float, vCathode: float):
        """Creates plates

        # Parameters

        * vAnode - voltage of anode
        * vCathode - voltage of cathode
        """

        # Add cathode and anode and request calculation for weighting potential
        self.caf.SetMedium(self.gas)
        
        self.caf.AddPlaneY(y=10, voltage=vCathode, label='Cathode')
        self.caf.AddReadout(label='Cathode')
        self.electrodes.append("Cathode")
    
        self.caf.AddPlaneY(y=-10, voltage=vAnode, label='Anode')
        self.caf.AddReadout(label='Anode')
        self.electrodes.append("Anode")

        # Add Wires and request calc
        for i in range(1,200):
            self.caf.AddWire(x=-10+i*0.2, y=-8, diameter=0.002, voltage=0, label='Grid')
        self.caf.AddReadout(label='Grid')
        self.electrodes.append('Grid')

        # Add all the electrodes 
        self.sensor.AddComponent(self.caf)
        for electrode in self.electrodes:
            self.sensor.AddElectrode(self.caf, label=electrode)

    def set_signal_time_window(self):
        num_time_bins = 1000
        t_min, t_max = 0, 10
        t_step = (t_max - t_min) / num_time_bins
        self.sensor.SetTimeWindow(t_min, t_step, num_time_bins)
        
    def read_data(self):
        '''Read the data file from SRIM
        '''
        
        # Import ions.
        file = self.track.ReadFile(
            file=self.file_name, 
            nIons=self.num_ions, 
            nSkip= self.num_skip_ions
        )
        if not file:
            raise Exception("Failed to read EXYZ file.")
        
        # Connect the track to a sensor.
        self.track.SetSensor(self.sensor)
        
    def create_drift(self):
        self.drift = self.gf.DriftLineRKF()
        self.drift.SetSensor(self.sensor)
        size=100
        self.sensor.SetArea(xmin=-size, ymin=-size, zmin=-size, xmax=size, ymax=size, zmax=size)
        #self.drift.SetMaximumStepSize(10.0e-4)

    def loop_through_clusters(self):
        """Cluster refer to the energy loss in a single ionizing collision of the ion
        and the electrons produced in the process.
        Each cluster correspond to one energy interval for an ion in the EXYZ file."""

        for cluster in self.track.GetClusters():
            self.drift.SetElectronSignalScalingFactor(scale=cluster.n)
            self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)
    
    def create_signal(self):
        #self.sensor.ClearSignal()
        self.track.NewTrack(x0=-9, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0)
        self.loop_through_clusters()

    def set_view_area(self, view):
        size = 100
        view.SetArea(xmin=-size, ymin=-size, zmin=-size, xmax=size, ymax=size, zmax=size)
        return view

    def plot_setup(self):
        self.field_view = self.gf.ViewField()
        self.field_view = self.create_canvas(view=self.field_view, name="setup")
        self.field_view.SetComponent(c=self.caf)
        self.field_view.SetNumberOfContours(n=40)
        self.field_view.Plot(option="v", drawopt="CONT1")

        self.cell_view = self.gf.ViewCell()
        self.cell_view.SetCanvas(pad=self.field_view.GetCanvas())
        self.cell_view.SetComponent(comp=self.caf)
        size=100
        self.cell_view.SetArea(xmin=-size, ymin=-size, zmin=-size, xmax=size, ymax=size, zmax=size)
        self.cell_view.Plot2d()


    def enable_drift_plot(self):
        self.drift_view = self.gf.ViewDrift()
        self.drift_view = self.create_canvas(view=self.drift_view, name="drift")
        self.drift.EnablePlotting(self.drift_view)
        self.track.EnablePlotting(self.drift_view)

        self.cell_view = self.gf.ViewCell()
        self.cell_view.SetComponent(comp=self.caf)
        self.cell_view.SetCanvas(pad=self.drift_view.GetCanvas())

    def plot_signal(self):
        for electrode in self.electrodes:
            self.signal_view = self.gf.ViewSignal()
            self.create_canvas(
                view=self.signal_view,
                name=electrode,
            )
            self.signal_view.SetSensor(self.sensor)
            self.signal_view.PlotSignal(label=electrode)

    def run(self):

        self.create_electrodes(vAnode=100, vCathode=-1000)
        if self.plotSetup:
            self.plot_setup()
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
                ROOT.gPad.Update()
            if self.plotSignal:
                self.plot_signal()
            
        input("Press Enter to continue...")

if __name__ == '__main__':
    chamber = Chamber(SLEEP_TIME, EXYZ_FILE)
    chamber.run()
