from srim import Ion, Layer, Target, TRIM
from timeit import default_timer as timer
import os
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import pickle
import shutil
import datetime
import time
import subprocess
import pandas as pd
from config import PICKLE_DIR, SRIM_EXECUTABLE_DIRECTORY


class Simulation:
    def __init__(self, element, mass, energy, num_events, energy_interval, scp_to_remote=False, **kwargs):
        self.element = element
        self.mass = mass
        self.energy = energy
        self.isotope = f"{self.element}{self.mass}"
        self.total_energy = self.energy
        self.id = f"{self.isotope}-{self.energy / 1e6}MeV"
        self.num_events = num_events
        self.energy_interval = energy_interval

        self.target = self.setup_target(**kwargs)
        self.ion = Ion(self.element, self.total_energy, self.mass)

        self.srim_executable_directory = SRIM_EXECUTABLE_DIRECTORY
        self.scp_to_remote = scp_to_remote
        self.remote_exyz_dir = "~/kandidatarbete/Kod/kod/DataFiles"
        self.remote_username = "jakonil"

    def setup_target(self, material="CF4", density=0.001764, phase=1, width=10000.0e06):
        layer = Layer.from_formula(material, density=density, phase=phase, width=width)
        target = Target([layer])
        return target

    def european_fix(self):
        source_path = os.path.join(self.srim_executable_directory, "SRIM Outputs/EXYZ.txt")
        with open(source_path, 'r') as file:
            contents = file.read()
            contents = contents.replace(',', '.')
        with open(source_path, 'w') as file:
            file.write(contents)


    def move_exyz_file(self):
        source_path = os.path.join(self.srim_executable_directory, "SRIM Outputs/EXYZ.txt")
        time_stamp = str(datetime.datetime.now())[:-10].replace(" ", "_").replace(":", "")
        new_file_name = f"EXYZ_{self.id}_{time_stamp}.txt"
        self.exyz_file_name = new_file_name
        destination_path = os.path.join("DataFiles", new_file_name)
        shutil.copy(source_path, destination_path)
        return destination_path

    def scp_exyz_file(self, source_path):
        remote_host = "remote11.chalmers.se"
        remote_ip = f"{self.remote_username}@{remote_host}"
        command = f"scp {source_path} {remote_ip}:{self.remote_exyz_dir}"
        result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
        )
        if result.returncode == 0:
            print("File transferred successfully!")
        else:
            print(f"An error occurred: {result.stderr}")

    def run(self):
        sim_result = SimulationResult(self.isotope, self.total_energy, self.num_events)
        trim = TRIM(
            self.target, self.ion, number_ions=self.num_events, calculation=1, exyz=self.energy_interval
        )
        result = trim.run(self.srim_executable_directory)
        # Fix european decimal separator
        self.european_fix()

        # Move exyz file to DataFiles
        source_path = self.move_exyz_file()

        # Add exyz file to sim_result
        sim_result.add_exyz_file(self.exyz_file_name)

        # Move exyz file to remote machine
        if self.scp_to_remote:
            self.scp_exyz_file(source_path)

        sim_result.add_result(result)
        return sim_result

    def __str__(self):
        return f"{self.element = }, {self.energy = }, {self.num_events = }, {self.target = }"


class SimulationResult:
    def __init__(self, isotope, total_energy, num_events):
        self.isotope = isotope
        self.total_energy = total_energy
        self.num_events = num_events
        self.id = f"{self.isotope}-{self.total_energy / 1e6}MeV"
        self.label = f"SRIM-{self.id}"
        self.pickle_path = f"{PICKLE_DIR}/{self.id}.pickle"

        self.results = []

    def add_exyz_file(self, file_name):
        self.exyz_file_name = file_name

    def add_result(self, result):
        self.results.append(result)

    @staticmethod
    def normalize_units(bragg_event, energy_factor, distance_factor):
        return {
            "x_values": bragg_event["x_values"] / distance_factor,
            "dE_values": bragg_event["dE_values"] * distance_factor / energy_factor,
        }

    def get_ioniz_data(self):
        bragg_data = []
        for result in self.results:
            ioniz = result.ioniz
            x_values = ioniz.depth
            dE_values = ioniz.recoils + ioniz.ions
            bragg_event = {"x_values": x_values, "dE_values": dE_values}
            bragg_data.append(self.normalize_units(bragg_event, 1e6, 1e8))
        return bragg_data

    def get_exyz_data(self):
        bragg_data = []
        for result in self.results:
            exyz = result.exyz
            x_values = exyz.depth[1:]
            dE_values = -np.ediff1d(exyz.energy) / np.ediff1d(exyz.depth)
            bragg_event = {"x_values": x_values, "dE_values": dE_values}
            bragg_data.append(self.normalize_units(bragg_event, 1e3, 1e8))
        return bragg_data
    
    def plot(self, ax, num_events=1, exyz=False, ioniz=True):
        data = {'ioniz': self.get_ioniz_data() if ioniz else None, 
                'exyz': self.get_exyz_data2() if exyz else None}
        for _type, events in data.items():
            if events is None:
                continue
            for event in events[:num_events]:
                ax.plot(event["x_values"], event["dE_values"], label=f"{self.label}-{_type}")
    
    def read_exyz_file(self):
        """In progress, should probably not finish this"""
        exyz_file_path = f"DataFiles/{self.exyz_file_name}"
        angstrom_to_cm_factor = 1e-8
        keV_to_MeV_factor = 1e-3
        df = pd.read_csv(
            exyz_file_path,
            sep="\s+",
            header=None,
            names=[
                "Ion Number",
                "Energy",
                "Depth",
                "Y",
                "Z",
                "Electronic Stop.",
                "Recoil Energy",
            ],
            engine="python",
            skiprows=15,
            converters={
                "Ion Number": lambda x: int(x.replace(",", ".")),
                "Energy": lambda x: float(x.replace(",", "."))*keV_to_MeV_factor,
                "Depth": lambda x: float(x.replace(",", "."))*angstrom_to_cm_factor,
                "Y": lambda x: float(x.replace(",", "."))*angstrom_to_cm_factor,
                "Z": lambda x: float(x.replace(",", "."))*angstrom_to_cm_factor,
                "Electronic Stop.": lambda x: float(x.replace(",", "."))/angstrom_to_cm_factor,
                "Recoil Energy": lambda x: float(x.replace(",", ".")),
            },
        )
        df_group = df.groupby(["Ion Number"])

        def modify_data(df: pd.DataFrame):
            df["dE"] = df["Energy"].diff()
            df["dx"] = df["Depth"].diff()
            df['dE/dx'] = -df['dE']/df['dx']
            return df
        
        def extend_data(df: pd.DataFrame):
            df_ext = pd.DataFrame()
            tail_length = 20
            dEdx_tail = pd.DataFrame(np.zeros((tail_length, 1)), columns=['dE/dx'])
            extended_dEdx = pd.concat([df['dE/dx'], dEdx_tail['dE/dx']], ignore_index=True)
            df_ext['dE/dx'] = extended_dEdx
            last_depth = df['Depth'].iloc[-1]
            depth_tail = pd.DataFrame(np.linspace(last_depth, last_depth + tail_length*df['dx'].mean(), tail_length), columns=['Depth'])
            df_ext['Depth'] = pd.concat([df['Depth'], depth_tail['Depth']], ignore_index=True)
            return df_ext
        
        ion_dfs = [extend_data(modify_data(df_group.get_group(ion))) for ion in df_group.groups]
        return ion_dfs

    def get_exyz_data2(self):
        bragg_data = []
        ion_dfs = self.read_exyz_file()
        for ion_df in ion_dfs:
            x_values = ion_df["Depth"].values[1:]
            dE_values = ion_df["dE/dx"].values[1:]
            bragg_event = {"x_values": x_values, "dE_values": dE_values}
            bragg_data.append(bragg_event)
        return bragg_data
    
def simulate(element, mass, energy, num_events, energy_interval, **kwargs):
    # kwargs can be material, density, phase and width
    sim = Simulation(element, mass, energy, num_events, energy_interval, **kwargs)
    sim_result: SimulationResult = sim.run()
    save_sim_result(sim_result)
    return sim_result


def simulate_all(isotopes: list, energies: list, num_events: int, energy_interval: int, **kwargs):
    simulation_dataset = {}
    for isotope, energy in zip(isotopes, energies):
        element, mass = isotope.split("-")
        mass = int(mass)
        energy_per_nucleon = energy / mass
        if energy_per_nucleon < 1e6 or energy_per_nucleon > 30e6:
            raise Exception(f"Non-realistic {energy = } for {isotope = }")
        sim_result: SimulationResult = simulate(
            element, mass, energy, num_events, energy_interval, **kwargs
        )
        simulation_dataset[sim_result.id] = sim_result
    return simulation_dataset


def save_sim_result(sim_result: SimulationResult):
    with open(sim_result.pickle_path, "wb") as f:
        pickle.dump(sim_result, f)


def load_sim_result(pickle_path):
    with open(pickle_path, "rb") as f:
        return pickle.load(f)


def main():
    # simulation_dataset = simulate_all(["Sr-80"], 1600e6, 1)
    # sim_result: SimulationResult = simulation_dataset["Sr80-1600.0MeV"]

    # sim_result = Simulation("Ne", 20, 300e6, 1).run()
    # save_sim_result(sim_result)
    
    sim_result = Simulation("He", 4, 5.4e6, 1, 1e5, scp_to_remote=True).run()
    save_sim_result(sim_result)

    # sr = load_sim_result(sim_result.pickle_path)
    # print(sr)


if __name__ == "__main__":
    main()
