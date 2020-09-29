Python 3.6, 64-bit!
von specpy immer die wheel Datei von der ImSpector Version in "C:\Imspector\Versions\16.1\python" kopieren, mit der die dateien generiert wurden
dann dieses specpy über die cmd line local installieren mit pip: pip install "path_to_wheel_file" (in den Scripts folder von Python 3.6)


# Extract_tif_from_msr.py
Takes an folder full of imspector measurements (.msr) and extracts the images that contain NAME_PART.
creates an image out of this numpy array
does some contrast stretching (optional - can also comment that out)
then saves as jpg with pillow library.

#so muss die .ini Datei aussehen, und sie muss exakt im gleichen Ordner liegen wie das Skript
[general]

; put the root path for the analysis here
root-path=C:\Users\Sarah\Documents\Python\Bax-analysis\IF36_selected-for-analysis-with-Jan
