import shutil
import pandas as pd


DATA_FILE_PATH = "DataFiles/Ca_data.txt"


def move_file(source_path, destination_path):
    shutil.move(source_path, destination_path)

def remove_header(data_file_path):
    pass


def main():
    source_path = "C:/Users/jakob/OneDrive/Chalmers/3/Kandidatarbete/SRIM-2013/IONIZ.txt"
    destination_path = "C:/Users/jakob/OneDrive/Chalmers/3/Kandidatarbete/Kod/kod/DataFiles/IONIZ_moved.txt"
    # move_file(source_path, destination_path)

if __name__ == "__main__":
    main()