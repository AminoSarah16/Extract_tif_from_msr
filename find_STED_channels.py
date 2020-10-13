import specpy
import numpy
import os

LENGTH_FACTOR = 1e+9 #from meters to nanometers
pop = '[Pop]'  ##how ImSpector names the line profile popup windows

'''
Figures out the STED channels and also the confocal channels that have been recorded with a STED resolution via the
pixelsize in the metadata of the msr file.
'''


def main():
    file_path = "C:/Users/sschwei/Desktop/test3/IF55a_spl1_U2OS_18hActD_Tom20-M507-AF488_Bax-NT-M99-AF594_Bak-M427-SR_cl1_no-green-laser.msr"
    measurement = specpy.File(file_path, specpy.File.Read)
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
        pixel_size = meta_data['Pixels']['PhysicalSizeX']  ##retrieves the pixelsize in meters
        pixel_size_in_nm = round(pixel_size * LENGTH_FACTOR)
        # print(name_of_channel, pixel_size_in_nm)
        if 10 < pixel_size_in_nm < 25:
            channels_with_STED_pixel_size.append(one_channel)  ##only picks out the channels where the pixel size lies between these limits

    actual_channels = [channel for channel in channels_with_STED_pixel_size if pop not in channel.name()]  # ohne die line profile dinger
    print('The measurement contains {} channels.'.format(len(all_channels)))  # gibt mir aus wie viele Kanäle die Messung hat
    print('The measurement contains {} channels with STED pixel size.'.format(len(actual_channels)))
    for channel in actual_channels:
        print(channel.name())


if __name__ == '__main__':
    main()