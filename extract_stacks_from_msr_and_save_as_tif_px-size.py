import specpy
import numpy
import os
from PIL import Image
import scipy.ndimage as ndimage
import configparser
from tkinter import filedialog

# work around for the fact that sometimes I duplicated the STED channels during imaging and they are saved in the measurement but ImSpector forgot the name.
# and also that ImSpector adds "stacks" when you draw a line profile

LENGTH_FACTOR = 1e+9 #from meters to nanometers
pop = '[Pop]'  ##how ImSpector names the line profile popup windows



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
            stacks = read_channels_from_imspector_measurement(file_path)
            images, stack_names = make_image_from_imspector_stack(stacks)
            for i in range(len(images)):
                image = images[i]
                stackname = stack_names[i]
                extra_factor = determine_extra_factor(i)

                denoised_data = gaussian_blur(image, sigma)
                enhanced_contrast = enhance_contrast(denoised_data, extra_factor)

                # save the original
                save_array_with_pillow(image, result_path, filename, stackname + str(i))
                # save the denoised and contrast enhanced
                save_array_with_pillow(enhanced_contrast, result_path, filename, stackname + str(i) + "contr-enh_Gauss-sigma" + str(sigma))
        except ValueError: #falls ein Stack nicht dem 2D Format entspricht, dann soll er einfach mit den anderen weitermachen
            not_handled.append(filename)
            pass

    if not not_handled:  # pythonic for if a list is empty
        print("All files were handled successfully.")
    else:
        print("These files could not be handled: " + str(not_handled))


def read_channels_from_imspector_measurement(file_path):
    """
    Lädt die Imspector Messung und findet die Kanäle (=channels) die wir über die pixel size sepzifizieren.

    """

    # File lesen
    measurement = specpy.File(file_path, specpy.File.Read)


    # lese alle stacks in eine liste
    all_channels = []
    names_of_channels = []
    channels_with_STED_pixel_size = []
    number_channels = measurement.number_of_stacks()  # returns the number of channels in the measurement (ImSpector calls them Stacks. why? no clue)
    for i in range(number_channels):
        one_channel = measurement.read(i)
        all_channels.append(one_channel)
        name_of_channel = one_channel.name()
        names_of_channels.append(name_of_channel)
        meta_data = one_channel.meta_data()  ##specpy function to access metadata
        # print(meta_data)
        pixel_size = meta_data['Pixels'][
            'PhysicalSizeX']  ##retrieves the pixelsize in meters, accessing the value in a nested dictionnary via 2 keys.
        pixel_size_in_nm = round(pixel_size * LENGTH_FACTOR)
        # print(name_of_channel, pixel_size_in_nm)
        if 10 < pixel_size_in_nm < 25:
            channels_with_STED_pixel_size.append(
                one_channel)  ##only picks out the channels where the pixel size lies between these limits

    wanted_channels = [channel for channel in channels_with_STED_pixel_size if pop not in channel.name()]  # ohne die line profile dinger
    print('The measurement contains {} channels.'.format(
        len(all_channels)))  # gibt mir aus wie viele Kanäle die Messung hat
    print('The measurement contains {} channels with STED pixel size.'.format(len(wanted_channels)))
    for channel in wanted_channels:
        print(channel.name())

    return wanted_channels


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

        # Dimensionnen von Imspector aus sind [1,1,Ny,Nx]
        size = data.shape  # The shape attribute for numpy arrays returns the dimensions of the array. If Y has n rows and m columns, then Y.shape is (n,m). So Y.shape[0] is n
        print('The numpy array of the {} channel has the following dimensions: {}'.format(wanted_stack.name(), size))

        # wir wollen aber [Nx, Ny]
            # 1) reduce to [Ny, Nx]
        data = numpy.reshape(data, size[2:])  #TODO: make sure it also works for videos or stacks

            # 2) transponieren [Nx, Ny]  ##for some reason, this is now not true anymore (5.10.20)
        # data = numpy.transpose(data)

            # 3) just to visualize the dimensions again
        size = data.shape
        print('After transposing, the numpy array of the {} channel has the following dimensions: {}'.format(wanted_stack.name(), size))

        images.append(data)
        stacknames.append(stack_name)

    return images, stacknames


def determine_extra_factor(i):  ##TODO: remove this.
    '''
    the stack we extract from the imspector measurement should only have 2 objects, and the first one is AF594 and the second one star red.
    Here we can choose whether we want to increase the contrast.
    '''
    #
    # if i == 0:
    extra_factor = 1  # applied to first channel
    # elif i == 1:
    #     extra_factor = 1  # applied to second channel
    # print(extra_factor)
    return extra_factor


def gaussian_blur(numpy_array, sigma):
    #Gaussian blur with scipy package
    denoised_data = ndimage.gaussian_filter(numpy_array, sigma=sigma)
    return denoised_data


def enhance_contrast(numpy_array, random_extra_factor):
    # Enhance contrast by stretching the histogram over the full range of the grayvalues
    minimum_gray = numpy.amin(numpy_array)
    maximum_gray = numpy.amax(numpy_array)
    mean_gray = numpy.mean(numpy_array)
    print("The channel has the following greyvalue range: {} - {}, with a mean of: {}.".format(str(minimum_gray), str(maximum_gray), str(mean_gray)))
    factor = 255/maximum_gray
    # mean_factor = 127.5 / maximum_gray
    print(factor)
    enhanced_contrast = numpy_array * factor * random_extra_factor  # depends on the position of the measurement in the stack
    thresh = 255
    super_threshold_indices = enhanced_contrast > thresh  # ich suche mir die Indices im Array, die über dem Threshold liegen
    enhanced_contrast[super_threshold_indices] = 255  # und setze die Intensitäten an diesen Stellen auf 255
    return enhanced_contrast


def save_array_with_pillow(image, result_path, filename, stackname):
    # I need to change the type of the numpy array to unsigned integer, otherwise can't be saved as tiff.
    # unit8 = Unsigned integer (0 to 255); unit32 = Unsigned integer (0 to 4294967295)
    eight_bit_array = image.astype(numpy.uint8)
    output_file = os.path.join(result_path, filename[:-4] + stackname + '.tiff')
    # print("wanted stack : {}".format(stackname)
    img = Image.fromarray(eight_bit_array)
    # print("I will save now")
    img.save(output_file, format='tiff')


if __name__ == '__main__':
    main()
