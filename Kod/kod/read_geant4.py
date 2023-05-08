from dataclasses import dataclass, field
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from config import DATA_DIR

# DATA_DIR  = "DataFiles\\Geant4"
# FILE_NAME = "Ca40_800MeV_100_events_CF4_500mbar_train.txt"
FILE_NAME = "Ne20_300MeV_100_events_CF4_500mbar_train.txt"

@dataclass
class Geant4Result:
    isotope: str
    total_energy: float
    num_events: int
    id: str
    results: pd.DataFrame
    label: str

    def __post_init__(self):
        pass

    @classmethod
    def from_file_name(cls, file_name, directory):
        # isotope, total_energy, num_events, id, results = "", 10.0, 100, "id", []
        isotope, total_energy, num_events, id = cls.get_attributes_from_file_name(file_name)
        results = cls.read_data_file(file_name, directory)
        label = f"Geant4-{id}"
        return cls(isotope, total_energy, num_events, id, results, label)

    @staticmethod
    def get_attributes_from_file_name(file_name):
        isotope, total_energy, num_events = file_name.rstrip('.txt').split("_")[:3]
        total_energy = float(total_energy.rstrip('MeV')) * 1e6
        id = f"{isotope}-{total_energy / 1e6}MeV"
        return isotope, total_energy, num_events, id

    @staticmethod
    def read_data_file(file_name, directory):
        results = pd.read_csv(os.path.join(directory, file_name), sep="\s+", header=None).transpose()
        num_points = results.shape[0]
        chamber_length = 50
        # depth = pd.DataFrame(np.linspace(0, chamber_length, num_points))
        # results["depth"] = depth
        results["depth"] = np.linspace(0, chamber_length, num_points)
        return results

    def get_bragg_data(self):
        bragg_data = []
        x_values = self.results["depth"].values
        for result in self.results.transpose().values[:-1]:
            dE_values = result
            bragg_event = {"x_values": x_values, "dE_values": dE_values}
            bragg_data.append(bragg_event)
        return bragg_data
    
    def get_average_bragg_data(self):
        data = self.results.values
        depth = data[:, -1]
        dE_values = data[:, :-1]
        return depth, dE_values.mean(axis=1)
    
    def plot_average(self, ax):
        depth, dE_values = self.get_average_bragg_data()
        ax.plot(depth, dE_values, label=self.label)
        
    def plot(self, ax, num_events=1):
        bragg_data = self.get_bragg_data()
        for bragg_event in bragg_data[:num_events]:
            ax.plot(bragg_event["x_values"], bragg_event["dE_values"], label=self.label)

def main():
    gr = Geant4Result.from_file_name(FILE_NAME, DATA_DIR)
    data = gr.results.values
    depth = data[:, -1]
    dE = data[:, :-1]
    
    # Plot mean of dE
    fig, ax = plt.subplots()
    ax.plot(depth, dE.mean(axis=1))
    ax.set_xlabel("Depth [cm]")
    ax.set_ylabel("dE/dx [MeV/cm]")
    ax.set_title(f"Geant4")
    plt.show()

if __name__ == "__main__":
    main()
