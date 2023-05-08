import matplotlib.pyplot as plt
from read_geant4 import Geant4Result, FILE_NAME
from simulation import simulate, simulate_all, load_sim_result, SimulationResult
from config import PICKLE_DIR, DATA_DIR


def plot_all(simulation_dataset):
    fig, ax = plt.subplots()
    legend = []
    for id, sim_result in simulation_dataset.items():
        bragg_events = sim_result.get_exyz_data()
        for bragg_event in bragg_events:
            plt.plot(bragg_event["x_values"], bragg_event["dE_values"])
            # print(sim_result.isotope)
            legend.append(
                f"{sim_result.isotope}-{sim_result.total_energy / 1e6:.0f}MeV"
            )
    ax.legend(legend)
    plt.show()


def plot_srim_vs_geant4(ax, *args, **kwargs):
    # fig, ax = plt.subplots()
    for result in args:
        result.plot(ax)
    ax.legend()
    ax.set_xlabel("Depth [cm]")
    ax.set_ylabel("dE/dx [MeV/cm]")
    ax.set_title(f"SRIM vs Geant4")
    # plt.show()


def main():
    # srim_result = simulate("Ne", 300e6, 20, 1)
    srim_result: SimulationResult = load_sim_result(f"{PICKLE_DIR}/Ne20-300.0MeV.pickle")

    geant4_result = Geant4Result.from_file_name(FILE_NAME, DATA_DIR)

    plot_srim_vs_geant4(srim_result, geant4_result)



if __name__ == "__main__":
    main()
