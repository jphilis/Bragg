from srim import Ion, Layer, Target, TRIM
from timeit import default_timer as timer
import os

# SRIM_EXECUTABLE_DIRECTORY = "C:/Users/Johan/Documents/kandidatarbete/SRIM-2013"
SRIM_EXECUTABLE_DIRECTORY = "../../SRIM-2013"
OUTPUT_DIRECTORY = "DataFilesTest"

ion = Ion("Ca", energy=800e6)

# Construct a layer of Carbontetraflouride with a density of 0.00125 g/cm^3
layer = Layer.from_formula("CF4", density=0.00125, phase=1, width=10000.0e06)

# Construct a target of a single layer of Nickel
target = Target([layer])

# Initialize a TRIM calculation with given target and ion for 25 ions, quick calculation
trim = TRIM(target, ion, number_ions=1, calculation=1)

# Specify the directory of SRIM.exe
# For windows users the path will include C://...


def time_runs(srim_executable_directory, trim, executions=1):
    start = timer()
    for _ in range(executions):
        result = trim.run(srim_executable_directory)
    end = timer()
    print(f"Time for {executions} executions: {end - start}s")
    print(f"Time per execution: {(end - start) / executions}s")
    print(f"Number of executions per second: {executions / (end - start)}")
    print(f"Number of executions per day: {executions / (end - start) * 60 * 60 * 24}")
    return result


def copy_srim_output_files(output_directory, srim_executable_directory):
    os.makedirs(output_directory, exist_ok=True)
    TRIM.copy_output_files(srim_executable_directory, output_directory)


def analyze_result(result):
    return result.ioniz


def main():
    result = time_runs(SRIM_EXECUTABLE_DIRECTORY, trim, executions=1)
    copy_srim_output_files(OUTPUT_DIRECTORY, SRIM_EXECUTABLE_DIRECTORY)
    ioniz_result = analyze_result(result)
    print(ioniz_result)


if __name__ == "__main__":
    main()
