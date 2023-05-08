import ROOT
import os, sys
import math
import ctypes
# import include

# Get all for Garfieldpp:
path = os.getenv('GARFIELD_INSTALL')
print(path)
if sys.platform == 'darwin':
  ROOT.gSystem.Load(path + '/lib/libmagboltz.dylib')
  ROOT.gSystem.Load(path + '/lib/libGarfield.dylib')
else:
  ROOT.gSystem.Load(path + '/lib/libmagboltz.so')
  ROOT.gSystem.Load(path + '/lib/libGarfield.so')

gas = ROOT.Garfield.MediumMagboltz()
gas.SetComposition("cf4", 100.)
gas.SetFieldGrid(10., 500., 5, False)
gas.SetPressure(0.5 * 760.)
gas.SetTemperature(293.15)

# Generate gas table
gas.GenerateGasTable(1)
gas.WriteGasFile("CF4.gas")

mv = ROOT.Garfield.ViewMedium()
mv.SetMedium(gas)
mv.PlotElectronVelocity('e')

