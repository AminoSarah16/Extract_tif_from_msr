import specpy
import numpy
import os
from PIL import Image
import scipy.ndimage as ndimage



NAME_PART = "STED"

def main():
    root_path = r"C:\Users\Sarah\Documents\Python\Bax-analysis\IF36_selected-for-analysis-with-Jan"  # r stands for raw. So that it doesn't read the stupid windows way of filepaths with backslashes wrong.
    output_path = r"C:\Users\Sarah\Documents\Python\Extract_tif_from_msr"
    filenames = list(os.listdir(root_path))
    result_path = os.path.join(output_path, 'results')
    if not os.path.isdir(result_path):
        os.makedirs(result_path)
    for filename in filenames:  # ich erstelle eine Liste mit den Filenames in dem Ordner
        if filename.endswith(".msr"):  # wenn die Endung .msr ist, dann mach was damit, nämlich:
            print(filename)
            file_path = os.path.join(root_path, filename)
            wanted_stack_s = read_stack_from_imspector_measurement(file_path)
            make_image_from_imspector_stack(wanted_stack_s, result_path, filename)
            # break

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


def make_image_from_imspector_stack(wanted_stack_s, result_path, filename):
    """

    :param wanted_stack_s: die ausgewählten Bilder einer Messung
    :return: Numpy array davon
    """
    stack_size = len(wanted_stack_s)
    for i in range(stack_size):
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

        # Enhance contrast by compressing the histogram over the range of the grayvalues
        minimum_gray = numpy.amin(denoised_data)
        maximum_gray = numpy.amax(denoised_data)
        print("And the following greyvalue range: {} - {}".format(str(minimum_gray), str(maximum_gray)))
        factor = 255 /maximum_gray
        print(factor)
        enhanced_contrast = denoised_data * factor * 5
        thresh = 255
        super_threshold_indices = enhanced_contrast > thresh
        enhanced_contrast[super_threshold_indices] = 255
        # enhanced_contrast = numpy.round(denoised_data * 255 / (maximum_gray - minimum_gray))
        # maximum_enhanced_gray = numpy.amax(enhanced_contrast)
        # print(maximum_enhanced_gray)

        # I need to change the type of the numpy array to unsigned integer, otherwise can't be saved as tiff. unit8 = Unsigned integer (0 to 255) unit32 = Unsigned integer (0 to 4294967295)
        eight_bit_array = enhanced_contrast.astype(numpy.uint8) #brauch ich jez aber nicht mehr, weil das contrast stretching das schon gemacht hat
        output_file = os.path.join(result_path, filename[:-4] + wanted_stack.name() + '.jpg')
        img = Image.fromarray(eight_bit_array)
        img.save(output_file, format='jpeg')
#     lengths = stack.lengths()
#     pixel_sizes = (lengths[0] / data.shape[0] / 1e-6, lengths[1] / data.shape[1] / 1e-6)  # conversion m to µm
#
#     return data, pixel_sizes

if __name__ == '__main__':
    main()
