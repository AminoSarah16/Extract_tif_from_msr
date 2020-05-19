import specpy
import numpy
import os
from PIL import Image
import scipy.ndimage as ndimage
import configparser

#TODO: open the previous images automatically and cut the last two measurements - specpy..?

NAME_PART = "STED"

def main():
    root_path = get_root_path()  # r stands for raw. So that it doesn't read the stupid windows way of filepaths with backslashes wrong.
    # output_path = r"C:\Users\Sarah\Documents\Python\Extract_tif_from_msr"
    result_path = os.path.join(root_path, 'results_Sarah')
    if not os.path.isdir(result_path):
        os.makedirs(result_path)
    filenames = list(os.listdir(root_path))
    for filename in filenames:  # ich erstelle eine Liste mit den Filenames in dem Ordner
        if filename.endswith(".msr"):  # wenn die Endung .msr ist, dann mach was damit, nämlich:
            print(filename)
            file_path = os.path.join(root_path, filename)
            wanted_stack_s = read_stack_from_imspector_measurement(file_path)
            images = make_image_from_imspector_stack(wanted_stack_s)
            save_array_with_pillow(images, result_path, filename, wanted_stack_s)
            print("main-end")
            break


def read_stack_from_imspector_measurement(file_path):
    """
    Lädt die Imspector Messung und findet die Kanäle (=stacks) die wir mit namepart sepzifizieren.

    :param file_path: Pfad der Imspector Messung.
    :param name_part: Teil des Stacknamens
    :return: Alles Kanäla (=Stacks), die so heißen
    """

    # File lesen
    measurement = specpy.File(file_path, specpy.File.Read)


    # lese alle stacks in eine liste
    stacks = []  #empty list
    number_stacks = measurement.number_of_stacks()  # returns the number of stacks in the measurement
    for i in range(number_stacks):
        stack = measurement.read(i)  #ein Kanal wird in Imspector als stack bezeichnet!
        stacks.append(stack)
    print('The measurement contains {} channels.'.format(len(stacks)))  # gibt mir aus wie viele Kanäle die Messung hat

    # finde alle stacks, deren name name_part enthält
    wanted_stack_s = [stack for stack in stacks if NAME_PART in stack.name()]  # list comprehension(?)  #stack.name() ist von specpy
    print('The measurement contains {} {} channels.'.format(len(wanted_stack_s), NAME_PART))

    return wanted_stack_s


def make_image_from_imspector_stack(wanted_stack_s):
    """

    :param wanted_stack_s: die ausgewählten Bilder einer Messung
    :return: Numpy array davon
    """
    stack_size = len(wanted_stack_s)
    images = []  # die leere Liste wo ich meine Ergebnissbilder reinspeichere
    for i in range(stack_size):  # TODO: diese for loop in die main und ab data= erst hier lassen
        wanted_stack = wanted_stack_s[i]  # muss ein Element aus der Liste rausfangen, damit ich es in ein numpy array umwandeln kann.
        data = wanted_stack.data()  # returns the data of the stack as a NumPy array

        # Dimensionnen von Imspector aus sind [1,1,Ny,Nx]
        size = data.shape  # The shape attribute for numpy arrays returns the dimensions of the array. If Y has n rows and m columns, then Y.shape is (n,m). So Y.shape[0] is n
        # print('The numpy array of the current {} channel has the following dimensions: {}'.format(NAME_PART, size))

        # wir wollen aber [Nx, Ny]
            # 1) reduce to [Ny, Nx]
        data = numpy.reshape(data, size[2:])

            # 2) transponieren [Nx, Ny]
        data = numpy.transpose(data)

            # 3) just to visualize the dimensions again
        size = data.shape
        print('The numpy array of the {} channel has the following dimensions: {}'.format(wanted_stack.name(), size))

        #Gaussian blur with scipy package
        denoised_data = ndimage.gaussian_filter(data, sigma=2)

        if "594" in wanted_stack.name():
            extra_factor = 2.5  # für mito contrast
        elif "STAR RED" in wanted_stack.name():
            extra_factor = 5  # für Bax contrast  # TODO: get out of this function, into enhanced contrast, need to build in loop into enhanced contrast. or main?
        enhanced_contrast = enhance_contrast(denoised_data, extra_factor)

        images.append(enhanced_contrast)

    return images


def enhance_contrast(numpy_array, random_extra_factor):
    # Enhance contrast by stretching the histogram over the full range of the grayvalues
    minimum_gray = numpy.amin(numpy_array)
    maximum_gray = numpy.amax(numpy_array)
    print("And the following greyvalue range: {} - {}".format(str(minimum_gray), str(maximum_gray)))
    factor = 255 / maximum_gray
    print(factor)
    enhanced_contrast = numpy_array * factor * random_extra_factor  # TODO: set a different factor for Bax and mito channels
    thresh = 255
    super_threshold_indices = enhanced_contrast > thresh  # ich suche mir die Indices im Array, die über dem Threshold liegen
    enhanced_contrast[super_threshold_indices] = 255  # und setze die Intensitäten an diesen Stellen auf 255
    return enhanced_contrast


def save_array_with_pillow(images, result_path, filename, wanted_stack_s):
    # I need to change the type of the numpy array to unsigned integer, otherwise can't be saved as tiff.
    # unit8 = Unsigned integer (0 to 255); unit32 = Unsigned integer (0 to 4294967295)
    for i in range(len(images)):
        image = images[i]  # ich kann nicht schreiben for image in images, weil ich den counter i brauche für später
        eight_bit_array = image.astype(numpy.uint8)
        output_file = os.path.join(result_path, filename[:-4] + wanted_stack_s[i].name() + '.jpg')  # nämlich für den stackname hier
        # print("wanted stack : {}".format(wanted_stack_s[i].name()))
        img = Image.fromarray(eight_bit_array)
        img.save(output_file, format='jpeg')


def get_root_path():
    """
    Retrieves the root path
    """
    config = configparser.ConfigParser()
    config.read('extract_tif_from_msr.ini')  # wenn es ein Verzeichnis höher liegen würde wäre es ("../hbujbk")
    return config['general']['root-path']

if __name__ == '__main__':
    main()
