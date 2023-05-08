import ROOT
import os, sys

class GarfieldSetup:
    def __init__(self):
        self.path = '/chalmers/groups/subprog/devuan.compile/garfield/ins'
        # self.path = os.getenv("GARFIELD_INSTALL") # Doesn't work in jupyter notebook

        # self.initiate_garfield() # Todo: comment out to make old files work
        self.gf = ROOT.Garfield
        self.import_gas()

        self.window_width = 600
        self.window_height = 600



    def initiate_garfield(self):
        if sys.platform == "darwin":
            ROOT.gSystem.Load(self.path + "/lib/libmagboltz.dylib")
            ROOT.gSystem.Load(self.path + "/lib/libGarfield.dylib")
        else:
            ROOT.gSystem.Load(self.path + "/lib/libmagboltz.so")
            ROOT.gSystem.Load(self.path + "/lib/libGarfield.so")
            # x = ROOT.gSystem.Load(self.path + "/lib/libmagboltz.so")
            # y = ROOT.gSystem.Load(self.path + "/lib/libGarfield.so")

    def create_canvas(self, view, name, title="Window"):
        canvas = ROOT.TCanvas(name, title, self.window_width, self.window_height)
        view.SetCanvas(canvas)
        return view

    def import_gas(self):
        self.gas = self.gf.MediumMagboltz()
        #self.gas.LoadGasFile("ar_93_co2_7_3bar.gas")
        self.gas.LoadGasFile("CF4.gas")
        self.gas.LoadIonMobility(
            self.path + "/share/Garfield/Data/IonMobility_CF4+_CF4.txt"
        )
