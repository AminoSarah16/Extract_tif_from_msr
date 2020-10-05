import specpy
import numpy
import os
from PIL import Image
import scipy.ndimage as ndimage
import configparser
from tkinter import filedialog
from skimage import io

# work around for the fact that sometimes I duplicated the STED channels during imaging and they are saved in the measurement but ImSpector forgot the name.
EMPTY = " "
STED = "STED"
CH2 = "Ch2 {2}"  # auf der alten Waldweg software hab ich das meist als af594 Kanal gehabt
CH4 = "Ch4 {2}"
# falls der stack dann immer noch größer 2 ist wird der Rest einfach gepoppt und zwar:
# in der read_stack_from_imspector_measurement function in der Liste wanted_stack


def main():
    not_handled = []
    file_format = ".msr"
    root_path = filedialog.askdirectory()  #prompts user to choose directory. From tkinter
    result_path = os.path.join(root_path, 'extracted_tifs_from_msr')
    sigma = int(input("Please enter the desired radius for your Gaussian blur:"))
    if not os.path.isdir(result_path):
        os.makedirs(result_path)
    filenames = [filename for filename in sorted(os.listdir(root_path)) if filename.endswith(file_format)]
    if not filenames:  # pythonic for if a list is empty
        print("There are no files with this format.")
    for filename in filenames:
        try:
            print(filename)
            file_path = os.path.join(root_path, filename)
            stacks = read_stack_from_imspector_measurement(file_path)
            images, stack_names = make_image_from_imspector_stack(stacks)
            if len(images) != 2:
                print('Problem: {} ImSpector stacks, need two.'.format(len(images)))
                return  ##This is used for the same reason as break in loops. The return value doesn't matter and you
                # only want to exit the whole function. It's extremely useful in some places, even though you don't need it that often.
            for i in range(len(images)):
                image = images[i]
                stackname = stack_names[i]
                # extra_factor = determine_extra_factor(i)
                #
                # denoised_data = gaussian_blur(image, sigma)
                # enhanced_contrast = enhance_contrast(denoised_data, extra_factor)

                # save the original
                save_array_with_pillow(image, result_path, filename, stackname + str(i))
                # save the denoised and contrast enhanced
                # save_array_with_pillow(enhanced_contrast, result_path, filename, stackname + str(i) + "contr-enh_Gauss-sigma" + str(sigma))
        except ValueError: #falls ein Stack nicht dem 2D Format entspricht, dann soll er einfach mit den anderen weitermachen
            not_handled.append(filename)
            pass

    if not not_handled:  # pythonic for if a list is empty
        print("All files were handled successfully.")
    else:
        print("These files could not be handled: " + str(not_handled))


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

    # finde alle stacks, deren name entweder das Wort STED enthält, oder welcher keine spaces (EMPTY) enthält, das kann dann nur der leere (=duplizierte) sein.
    # die CONSTANTS dafür sind oben vor der main() definiert = workaround für channel duplication und bescheuerte ImSpector Benennungen..
    wanted_stack_s = [stack for stack in all_stacks if EMPTY not in stack.name() or STED in stack.name() or CH2 in stack.name() or CH4 in stack.name()]  # list comprehension(?)  #stack.name() ist von specpy
    print('The measurement contains {} STED channels.'.format(len(wanted_stack_s)))

    # if we get more than 2 stacks (one AF594 and one STAR RED) then it's most likely duplicates and we will just remove them from the list
    for i in range(len(wanted_stack_s)):
        if i > 1:
            wanted_stack_s.pop()

    return wanted_stack_s


def make_image_from_imspector_stack(wanted_stack_s):
    """

    :param wanted_stack_s: die ausgewählten Bilder einer Messung
    :return: Numpy array davon
    """
    stack_size = len(wanted_stack_s)
    images = []  # die leere Liste wo ich meine Ergebnissbilder reinspeichere
    stacknames = []
    for i in range(stack_size):
        wanted_stack = wanted_stack_s[i]  # muss ein Element aus der Liste rausfangen, damit ich es in ein numpy array umwandeln kann.
        stack_name = wanted_stack_s[i].name()
        data = wanted_stack.data()  # returns the data of the stack as a NumPy array

        # Dimensionnen von Imspector aus sind [T, Z, Y, X]
        size = data.shape  # The shape attribute for numpy arrays returns the dimensions of the array. If Y has n rows and m columns, then Y.shape is (n,m). So Y.shape[0] is n
        print('The numpy array of the {} channel has the following dimensions: {}'.format(wanted_stack.name(), size))

        # wir wollen aber [X, Y, Z]
            # 1) reduce to [Z, Y, X]
        data = numpy.reshape(data, size[1:])  #TODO: make sure it also works for videos or stacks

            # 2) transponieren [X, Y, Z]
        data = numpy.transpose(data)

            # 3) just to visualize the dimensions again
        size = data.shape
        print('After transposing, the numpy array of the {} channel has the following dimensions: {}'.format(wanted_stack.name(), size))

        images.append(data)
        stacknames.append(stack_name)

    return images, stacknames

#
# def determine_extra_factor(i):
#     '''
#     the stack we extract from the imspector measurement should only have 2 objects, and the first one is AF594 and the second one star red.
#     Here we can choose whether we want to increase the contrast.
#     '''
#     #activate thisTODO if needed: Achtung es ist grade verdreht, weil ich ein sample set bearbeitet habe, wo bax im 594er Kanal liegt
#     if i == 0:
#         extra_factor = 1  # applied to first channel
#     elif i == 1:
#         extra_factor = 1  # applied to second channel
#     print(extra_factor)
#     return extra_factor
#
#
# def gaussian_blur(numpy_array, sigma):
#     #Gaussian blur with scipy package
#     denoised_data = ndimage.gaussian_filter(numpy_array, sigma=sigma)
#     return denoised_data
#
#
# def enhance_contrast(numpy_array, random_extra_factor):
#     # Enhance contrast by stretching the histogram over the full range of the grayvalues
#     minimum_gray = numpy.amin(numpy_array)
#     maximum_gray = numpy.amax(numpy_array)
#     mean_gray = numpy.mean(numpy_array)
#     print("The channel has the following greyvalue range: {} - {}, with a mean of: {}.".format(str(minimum_gray), str(maximum_gray), str(mean_gray)))
#     factor = 255/maximum_gray
#     # mean_factor = 127.5 / maximum_gray
#     print(factor)
#     enhanced_contrast = numpy_array * factor * random_extra_factor  # depends on the position of the measurement in the stack
#     thresh = 255
#     super_threshold_indices = enhanced_contrast > thresh  # ich suche mir die Indices im Array, die über dem Threshold liegen
#     enhanced_contrast[super_threshold_indices] = 255  # und setze die Intensitäten an diesen Stellen auf 255
#     return enhanced_contrast


def save_array_with_pillow(image, result_path, filename, stackname):
    # I need to change the type of the numpy array to unsigned integer, otherwise can't be saved as tiff.
    # unit8 = Unsigned integer (0 to 255); unit32 = Unsigned integer (0 to 4294967295)
    eight_bit_array = image.astype(numpy.uint8)
    output_file = os.path.join(result_path, filename[:-4] + stackname + '.tiff')
    # print("wanted stack : {}".format(stackname)
    # img = Image.fromarray(eight_bit_array)
    # print("I will save now")
    # img.save(output_file, format='tiff', save_all=True)


    # io.imsave(output_file, eight_bit_array)

    # liste von 2D Images erzeugen
    images = [Image.fromarray(eight_bit_array[:, :, i]) for i in range(eight_bit_array.shape[2])] ## die range bezieht sich nur auf die dritte Dimension des ndarrays (daher 2, von 0,1,2)

    # speichern
    images[0].save(output_file, save_all=True, append_images=images[1:]) # speichere das nullte Image und hänge ab 1 bis zum Schluss dran.


if __name__ == '__main__':
    main()
