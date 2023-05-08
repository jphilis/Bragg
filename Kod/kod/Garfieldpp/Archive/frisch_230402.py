from garfield_base import GarfieldSetup
import time


SLEEP_TIME = 200
#EXYZ_FILE = "../DataFiles/EXYZ_gpp.txt"
EXYZ_FILE = "../DataFiles/EXYZ_He4-5.4MeV_2023-04-03_1113.txt"


class Chamber(GarfieldSetup):
    def __init__(self, sleep_time, file_name):
        super().__init__()

        self.sleep_time = sleep_time
        self.num_ions = 0 # 0 to load all ions
        self.num_skip_ions = 0
        self.file_name = file_name

        self.caf = self.gf.ComponentAnalyticField()
        self.sensor = self.gf.Sensor()
        self.track = self.gf.TrackTrim()


    def create_plates(self):
        """Creates plates

        # Parameters

        * vAnode - voltage of anode
        * vCathode - voltage of cathode
        """

        # Add cathode and anode and request calculation for weighting potential
        self.caf.SetMedium(self.gas)
        vAnode=100
        vCathode=-1000
        self.caf.AddPlaneY(y=5, voltage=vCathode, label='Cathode')
        self.caf.AddReadout(label='Cathode')
       
        #self.caf.AddPlaneY(y=-6, voltage=vAnode, label='Anode')
        #self.caf.AddReadout(label='Anode')

        label = 'Wire'
        for i in range(1,100):
            self.caf.AddWire(x=-5+i*0.2, y=2, diameter=0.002, voltage=1000, label=label)

        self.caf.AddReadout(label=label)
        

    #def create_wires(self, x: float, y: float, rWire: float, vFrisch: float, label: str, length: float, period: float):
    def create_wires(self, voltage=0):
        '''Create a wire plane 

        # Parameters:

        * x - position in x-direction
        * y - position in y-direction  
        * rWire - radius of wire
        * vFrisch - voltage on frisch grid
        * label - to be used later when referring to it
        * length - length of wire

        '''
        # Add wires 
        #self.caf.SetPeriodicityY(s=period)
        label = 'Wire'
        self.caf.AddWire(x=0, y=-5, diameter=0.002, voltage=voltage, label=label)
        self.caf.AddReadout(label=label)
        self.sensor.AddElectrode(self.caf, label)

    def setup_sensor(self):
        self.sensor.AddComponent(self.caf)
        #self.sensor.AddElectrode(self.caf, label="Cathode")
        #self.sensor.AddElectrode(self.caf, label="Anode")
        self.sensor.AddElectrode(self.caf, label='Wire')

    def set_signal_time_window(self):
        num_time_bins = 1000
        t_min, t_max = 0, 5
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
        #self.drift.SetMaximumStepSize(2e-3)

    def loop_over_clusters(self):
        """Cluster refer to the energy loss in a single ionizing collision of the ion
        and the electrons produced in the process.
        Each cluster correspond to one energy interval for an ion in the EXYZ file."""

        # print(len(list(self.track.GetClusters())))
        #print(list(self.track.GetClusters())[0])
        print(1111111111111111111111111111111111111111111111)
        for cluster in self.track.GetClusters():
            print(cluster.x, cluster.y, cluster.z, cluster.n, cluster.t)
            self.drift.SetElectronSignalScalingFactor(scale=cluster.n)
            #self.drift.DriftElectron(cluster.x, cluster.y, cluster.z, cluster.t)
            #self.drift.SetHoleSignalScalingFactor(cluster.n)
            #self.drift.DriftHole(cluster.x, cluster.y, cluster.z, cluster.t)
    
    def create_signal(self):
        #self.sensor.ClearSignal()
        self.track.NewTrack(x0=0, y0=0, z0=0, t0=0, dx0=1, dy0=0, dz0=0)
        self.loop_over_clusters()
        # self.sensor.ConvoluteSignals()

    def set_view_area(self,view):
        view.SetArea(xmin=-5, ymin=-5, zmin=-5, xmax=20, ymax=15, zmax=15)
        return view

    def plot_field(self):
        self.field_view = self.gf.ViewField()
        # self.field_view = self.create_canvas(view=self.field_view, name="field")
        self.field_view.SetComponent(c=self.caf)
        self.field_view = self.set_view_area(self.field_view)
        self.field_view.SetVoltageRange(vmin=-1000, vmax=100)
        self.field_view.SetNumberOfContours(n=40)

        # Plot isopotential contours
        self.field_view.Plot(option="v", drawopt="CONT1")
        # self.field_view.PlotProfile(x0=0, y0=0, z0=0, x1=15, y1=15, z1=15, option="v", normalised=False)
        
    def plot_components(self):
        self.cell_view = self.gf.ViewCell()
        self.cell_view.SetCanvas(pad=self.field_view.GetCanvas())
        self.cell_view.SetComponent(comp=self.caf)
        self.cell_view = self.set_view_area(self.cell_view)        
        self.cell_view.Plot2d()

    def plot_drift(self):
        self.drift_view = self.gf.ViewDrift()
        self.set_view_area(self.drift_view)

    def plot_signal(self):
        electrodes = ["Anode", "Cathode", "Wire"]
        #electrodes = ["Anode", "Cathode"]
        for electrode in electrodes:
            self.signal_view = self.gf.ViewSignal()
            self.create_canvas(
                view=self.signal_view,
                name=electrode,
            )
            self.signal_view.SetSensor(self.sensor)
            self.signal_view.PlotSignal(label=electrode)


    def run(self):
        #self.create_geometry(0, 0, 0, 10, 5, 5, 1, 0, 0)
        # self.plot_geometry()
        #self.sensor.AddComponent(self.caf)
        self.create_plates()
        #self.create_wires(voltage=0)
        self.setup_sensor()

        #plot_setup, plot_signal = True, False
        plot_setup, plot_signal = False, True
        if plot_setup:
            self.plot_field()
            self.plot_components()   
        elif plot_signal:
            self.read_data()
            self.set_signal_time_window()
            self.create_drift()
            self.create_signal()
            self.plot_signal()

        time.sleep(self.sleep_time)


if __name__ == '__main__':
    chamber = Chamber(SLEEP_TIME, EXYZ_FILE)
    chamber.run()
