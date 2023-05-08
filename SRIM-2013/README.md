## Install SRIM-2013 on windows
1. Go to srim.org
2. Click Download SRIM-2013
3. Scroll down and choose SRIM-2013 (not SRIM-2013 Professional)
4. You will get a file SRIM-2013-Std.e
5. Rename it to SRIM-2013-Std.exe
6. Move it to a new directory /kandidatarbete/SRIM-2013
7. Double click SRIM-2013-Std.exe and choose "Extract All"
8. You will get a bunch of files in your directory.
9. Go into SRIM-setup and right click the (right-click).bat file, run it as administrator
10. Click enter til you installed all things (there will be some errors). 
11. When you see a window with an "installera" button, click it and then end the window.
12. Click enter again in the command window til done.
13. Now run SRIM.exe, TRIM might not work but that is fine.

## Install pysrim
1. poetry add pysrim or pip install pysrim (you don't have to if the repository is up to date.
2. ```py import srim ```
3. If the import doesn't work, follow to fix some bugs.

### Fix some bugs in pysrim
1. Go to the path of the error message when importing pysrim. Something like ..........\site-packages\srim\core
2. Open elementdb.py and do the following changes on line 10:
  ```py
  # return yaml.load(open(dbpath, "r")) - original
  return yaml.full_load(open(dbpath, "r"))
  ```
3. Go back to ..........\site-packages\srim
4. Open output.py and do the following changes on line 71:
  ```py
  # return int(float(match.group(1))) - original
  return int(float(match.group(1).replace(b',', b'.')))
  ```
  This fixes an issue with a comma sign in the IONIZ.txt header.
5. Also, in output.py, do the following changes on line 87:
  ```py
  # data = np.genfromtxt(BytesIO(output[match.end():]), max_rows=100) #-- original
  data = np.genfromtxt(BytesIO(output[match.end():].replace(b',', b'.')), max_rows=100)
  ```
6. Now the program should work.
