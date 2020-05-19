# Extract_tif_from_msr.py
Takes an folder full of imspector measurements (.msr) and extracts the images that contain NAME_PART.
creates an image out of this numpy array
does some contrast stretching (optional - can also comment that out)
then saves as jpg with pillow library.

#so muss die .ini Datei aussehen, und sie muss exakt im gleichen Ordner liegen wie das Skript
[general]

; put the root path for the analysis here
root-path=C:\Users\Sarah\Documents\Python\Bax-analysis\IF36_selected-for-analysis-with-Jan
