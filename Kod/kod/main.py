from argparse import ArgumentParser
from pprint import pprint

from simulation import simulate_all
from func_lib import plot_all


def get_arguments():
    parser = ArgumentParser(description="add description")

    parser.add_argument(
        "-i",
        "--isotopes",
        type=str,
        nargs="+",
        help="isotope to test",
        default=["Ca-40"],
    )
    parser.add_argument(
        "-E",
        "--energies",
        type=float,
        nargs="+",
        help="initial energies",
        default=[800e6],
    )
    parser.add_argument(
        "-N",
        "--num_events",
        type=int,
        help="number of events per isotope",
        default=1,
    )
    parser.add_argument(
        "-x",
        "--energy_interval",
        type=float,
        help="interval between energt measurements",
        default=1e4,
    )
    parser.add_argument(
        "-m",
        "--material",
        type=str,
        help="material in bragg chamber",
        default="CF4",
    )
    parser.add_argument(
        "-d",
        "--density",
        type=float,
        help="density of material",
        default=0.001764,
    )
    parser.add_argument(
        "-p",
        "--phase",
        type=int,
        help="phase of material",
        default=1,
    )

    return parser.parse_args()


def check_args(args):
    if len(args.isotopes) != len(args.energies):
        raise Exception("Number of isotopes must match number of energies")


def main():
    args = get_arguments()
    check_args(args)

    simulation_dataset = simulate_all(
        args.isotopes,
        args.energies,
        args.num_events,
        args.energy_interval,
        material=args.material,
        density=args.density,
        phase=args.phase,
    )

    pprint(simulation_dataset)


if __name__ == "__main__":
    main()
