import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Path: kod\plot.py
# DATA_FILE_PATH = "DataFiles/data.txt"
# DATA_FILE_PATH = "DataFiles/proton_Si.txt"
DATA_FILE_PATH = "DataFiles/Ca_data.txt"

data_frame = pd.read_csv(DATA_FILE_PATH, sep="s+", header=None)
data = data_frame.values.tolist()

x = []
y = []
for row in data:
    x_num, x_pot = row[0].split(" ")[0].split(",")

    # _int = int(x_pot.split("E+")[1])
    # x.append(int(x_num) * 10 ** int(x_pot.split("E+")[1]) * 1.0e-10 / 1.0e-2)

    exp_sign = x_pot[1]
    exp_abs_value = int(str(x_pot[2:]).lstrip("0"))
    exp = eval(f"{exp_sign} {exp_abs_value}")
    normalization_factor = 1.0e-10 / 1.0e-2
    x_final = int(x_num) * normalization_factor * 10**exp
    x.append(x_final)

    col_1 = float(row[0].split("  ")[1].replace(",", "."))

    col_2 = float(row[0].split("  ")[2].replace(",", "."))

    y.append((col_1 + col_2) / 1.0e-10 * 1.0e-2 / 1.0e6)

    # y_num_1, y_pot_1 = row[0].split("  ")[1].split(",")
    # y_1 = int(y_num_1) * 10 ** int(y_pot_1.split("E+")[1])

    # y_num_2, y_pot_2 = row[0].split("  ")[2].split(",")
    # y_2 = int(y_num_2) * 10 ** int(y_pot_2.split("E+")[1])

    # y.append(y_1 + y_2)

plt.plot(x, y)
plt.show()
