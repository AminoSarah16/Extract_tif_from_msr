import specpy
import numpy
import os
from PIL import Image
import scipy.ndimage as ndimage
import configparser

# work around for the fact that sometimes I duplicated the STED channels during imaging and they are saved in the measurement but ImSpector forgot the name.
EMPTY = " "
STED = "STED"
# falls der stack dann immer noch größer 2 ist wird der Rest einfach gepoppt und zwar:
# in der read_stack_from_imspector_measurement function in der Liste wanted_stack


def main():
    root_path = get_root_path()  # r stands for raw. So that it doesn't read the stupid windows way of filepaths with backslashes wrong.
    result_path = os.path.join(root_path, 'results_del_duplicates_Sarah')
    if not os.path.isdir(result_path):
        os.makedirs(result_path)
    # filenames = list(os.listdir(root_path))
    # for filename in filenames:  # ich erstelle eine Liste mit den Filenames in dem Ordner
    #     if filename.endswith(".msr"):  # wenn die Endung .msr ist, dann mach was damit, nämlich:
    # filename = "IF36_spl15_U2OS-DKO_pcDNA-Bax-wt_6hEx_14hAct_cytC-AF488_Tom20-AF594_Bax-SR_cl8_ringheaven.msr"
    filename = "IF36_spl21_U2OS-DKO_pcDNA-Bax-H5i_6hEx_14hAct_cytC-AF488_Tom20-AF594_Bax-SR_cl6-7_dotty-andbigdots.msr"
    print(filename)
    file_path = os.path.join(root_path, filename)
    stacks = read_stack_from_imspector_measurement(file_path)
    images = make_image_from_imspector_stack(stacks)
    for i in range(len(images)):
        image = images[i]  # ich kann nicht schreiben
        if i == 0:
            extra_factor = 2.5  # für mito contrast
        elif i == 1:
            extra_factor = 5
        elif i > 1:
            images.pop(i)
        print(extra_factor)  #TODO. decompose
        enhance_contrast(image, extra_factor)
        # TODO: save und put in loop
    # break


def get_root_path():
    """
    Retrieves the root path
    """
    config = configparser.ConfigParser()
    config.read('extract_tif_from_msr.ini')  # wenn es ein Verzeichnis höher liegen würde wäre es ("../hbujbk")
    return config['general']['root-path']


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
    all_stacks = []  #empty list
    number_stacks = measurement.number_of_stacks()  # returns the number of stacks in the measurement
    for i in range(number_stacks):
        stack = measurement.read(i)  #ein Kanal wird in Imspector als stack bezeichnet!
        all_stacks.append(stack)
    print('The measurement contains {} channels.'.format(len(all_stacks)))  # gibt mir aus wie viele Kanäle die Messung hat

    # finde alle stacks, deren name entweder das Wort STED enthält, oder welcher keine spaces (EMPTY) enthält, das kann dann nur der leere sein.
    # die CONSTANTS dafür sind oben vor der main() definiert = workaround für channel duplication.
    wanted_stack_s = [stack for stack in all_stacks if EMPTY not in stack.name() or STED in stack.name()]  # list comprehension(?)  #stack.name() ist von specpy
    print('The measurement contains {} STED channels.'.format(len(wanted_stack_s)))
    for i in range(len(wanted_stack_s)):
        if i > 1:
            wanted_stack_s.pop(i)
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

        images.append(data)

    return images


def enhance_contrast(numpy_array, random_extra_factor):
    # Enhance contrast by stretching the histogram over the full range of the grayvalues
    minimum_gray = numpy.amin(numpy_array)
    maximum_gray = numpy.amax(numpy_array)
    print("And the following greyvalue range: {} - {}".format(str(minimum_gray), str(maximum_gray)))
    factor = 255 / maximum_gray
    print(factor)
    enhanced_contrast = numpy_array * factor * random_extra_factor  # depends on the position of the measurement in the stack
    thresh = 255
    super_threshold_indices = enhanced_contrast > thresh  # ich suche mir die Indices im Array, die über dem Threshold liegen
    enhanced_contrast[super_threshold_indices] = 255  # und setze die Intensitäten an diesen Stellen auf 255
    return enhanced_contrast


# def determine_extra_factor(stack):
#     if stack[0]:
#         extra_factor = 2.5  # für mito contrast
#     elif stack[1]:
#         extra_factor = 5  # für Bax contrast  # TODO: get this function, into enhanced contrast, need to build in loop into enhanced contrast. or main?
#     return extra_factor


if __name__ == '__main__':
    main()
