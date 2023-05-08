import ROOT
import os, sys
import math
import ctypes

def initiate_garfield():
  global GF, gas, caf, cv, cc, sensor, tr, drift
  # Get all for Garfieldpp:
  path = os.getenv('GARFIELD_INSTALL')
  # print(path)
  if sys.platform == 'darwin':
    ROOT.gSystem.Load(path + '/lib/libmagboltz.dylib')
    ROOT.gSystem.Load(path + '/lib/libGarfield.dylib')
  else:
    ROOT.gSystem.Load(path + '/lib/libmagboltz.so')
    ROOT.gSystem.Load(path + '/lib/libGarfield.so')

  GF = ROOT.Garfield

  # Get gas file:
  gas = GF.MediumMagboltz()
  gas.LoadGasFile('cf4.gas')
  gas.LoadIonMobility(path + '/share/Garfield/Data/IonMobility_CF4+_CF4.txt')

  # Fler Funktionklasser som behövs
  caf = GF.ComponentAnalyticField()
  cv = GF.ComponentVoxel()
  cc = GF.ComponentConstant()
  sensor = GF.Sensor()
  tr = GF.TrackTrim()
  drift = GF.DriftLineRKF()

def create_geometry(cx: float, cy: float, cz: float, lx: float, ly: float, lz: float, dx: float, dy: float, dz: float):
  """Creates gemoetry for the enviroment.
  
  # Parameters:
  
  * cx - center x coordinate of box (equivalent for y,z)
  * lx - half length of box in x direction (equivalent for y,z)
  * dx - direction/orientation of box (1 or 0)
  """

  # Skapa miljön bestående av gasen och ett rätblock:
  geo_simple = GF.GeometrySimple()
  geo_simple.SetMedium(gas)
  box = GF.SolidBox(cx, cy, cz, lx, ly, lz, dx, dy, dz)
  geo_simple.AddSolid(box, gas)

  # Skapa och printa miljön
  view = GF.ViewGeometry()
  view.SetGeometry(geo_simple)
  #view.Plot()
  #input("input num")

def create_plates(vAnode: float, vCathode: float):
  """Creates plates

  # Parameters

  * vAnode - voltage of anode
  * vCathode - voltage of cathode
  """
 

  # Add cathode and anode and request calculation for weighting potential
  caf.AddPlaneX(10, vCathode, 'Cathode')
  caf.AddReadout('Cathode')
  caf.AddPlaneX(0, vAnode, 'Anode')
  caf.AddReadout('Anode')
  sensor.AddComponent(caf)
  #sensor.AddElectrode(cc, "readout")
  

def create_wires(x: float, y: float, rWire: float, vFrisch: float, label: str, length: float, period: float):
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
  caf.SetPeriodicityY(period)
  caf.AddWire(x, y, 2 * rWire, vFrisch, label, length)
  caf.AddReadout(label)

def read_data(filename: str):
  '''Read the data file from SRIM
  '''
  
  # Import ions.
  if not tr.ReadFile(filename, 1): #number of ions = 1
      raise Exception("Failed to read EXYZ file.")
  
  # Connect the track to a sensor.
  tr.SetSensor(sensor)

def transfer_function(nTimeBins: float, tmin: float, tmax: float):
  '''Translate charge to voltage sig  § §-++-+-nals 
  
  TODO fix signals so they are not reset med mera

  '''

  # Make a sensor.
  sensor.AddComponent(caf)

  # för att beräkna drift lines
  drift.SetSensor(sensor)

  sensor.AddElectrode(caf, 'Cathode')
  sensor.AddElectrode(caf, 'Anode')
  sensor.AddElectrode(caf, 'Frisch')

  # Set the signal time window.
  tstep = (tmax - tmin) / nTimeBins
  sensor.SetTimeWindow(tmin, tstep, nTimeBins)

  # Set the delta reponse function.
  infile = open('mdt_elx_delta.txt', 'r')
  times = ROOT.std.vector('double')()
  values = ROOT.std.vector('double')()
  for line in infile:
    line = line.strip()
    line = line.split()
    times.push_back(1.e3 * float(line[0]))
    values.push_back(float(line[1]))
  infile.close()
  sensor.SetTransferFunction(times, values)
  #sensor.ConvoluteSignals()

def plot():
  '''Plot signals and drift lines

  TODO work in progress
  
  '''
  driftView = ROOT.Garfield.ViewDrift()
  cD = ROOT.TCanvas('cD', '', 600, 600)
  driftView.SetCanvas(cD)
  cellView = ROOT.Garfield.ViewCell()
  plotDrift = True
  if plotDrift:
    drift.EnablePlotting(driftView)
    tr.EnablePlotting(driftView)
    cellView.SetComponent(caf)
    cellView.SetCanvas(driftView.GetCanvas())

  signalView = GF.ViewSignal()
  cS = ROOT.TCanvas('cS', '', 600, 600)
  signalView.SetCanvas(cS)
  signalView.SetSensor(sensor)
  plotSignal = True

  rTrack = 0.3
  rTube = 5
  x0 = rTrack
  y0 = -math.sqrt(rTube * rTube - rTrack * rTrack)

  nTracks = 1
  for j in range(nTracks):
    sensor.ClearSignal()
    tr.NewTrack(x0, y0, 0, 0, 0, 1, 0)
    for cluster in tr.GetClusters():
      for electron in cluster.electrons:
        drift.DriftElectron(electron.x, electron.y, electron.z, electron.t)
      if plotDrift:
        driftView.GetCanvas().Clear()
        cellView.Plot2d()
        driftView.Plot(True, False)
        ROOT.gPad.Update()
    sensor.ConvoluteSignals()
    nt = ctypes.c_int(0)
    if sensor.ComputeThresholdCrossings(-2., 's', nt) == False:
      continue
    if plotSignal:
      signalView.PlotSignal('s')

def main():
  initiate_garfield() 
  create_geometry(5, 0, 0, 5, 5, 10, 0, 0, 1)
  create_plates(100, -1000)
  create_wires(1, 0, 2.e-3, 0, 'Frisch', 20, 0.2)
  read_data('../DataFiles/EXYZ.txt')
  #transfer_function(1000, 0, 10)
  #plot()
  input("input num")

if __name__ == "__main__":
  main()