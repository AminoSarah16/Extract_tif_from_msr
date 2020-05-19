# Extract_tif_from_msr.py
Takes an folder full of imspector measurements (.msr) and extracts the images that contain NAME_PART.
creates an image out of this numpy array
does some contrast stretching (optional - can also comment that out)
then saves as jpg with pillow library.
