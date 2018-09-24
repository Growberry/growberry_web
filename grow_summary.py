"""
Note: when running on raspberry pi, need extra libraries
sudo apt-get update
sudo apt-get install libjpeg-dev

Required packages
"""



import argparse
import imageio
import os
from os.path import join
import tempfile
from PIL import Image
from shutil import copyfile
from math import ceil

usage = "python grow_summary.py <Target Directory> <Number of images in gif> [-s width of gif]"

parser = argparse.ArgumentParser()
parser.add_argument("target_directory")
parser.add_argument("expected_fnum", help="The expected number of images resulting.")
parser.add_argument("-s", "--size", help="the width in pixles for the output gif")

args = parser.parse_args()
target_directory = None
# check if the directory given is a directory
if os.path.isdir(args.target_directory):
    target_directory = args.target_directory
else:
    print("input directory is not a directory")

expected_fnum = int(args.expected_fnum)
_path, outname = os.path.split(target_directory)
if len(outname) == 0:
    outname = _path.strip('/')
OUT = outname + ".gif"

# start with a default size for the gif:
gif_size = 420
if args.size:
    gif_size = int(args.size)


######################  FUNCTIONS  ######################
def is_bigger(img, size_thresh):
    # takes an image, returns True if the image larger than the size thresh (in bytes).
    # used here to filter out pictures taken in the dark, they are smaller.
    file_size = os.path.getsize(img)
    print('{} : {}bytes, threshold: {}'.format(img,file_size/1000,size_thresh/1000))
    if file_size > size_thresh:
        print('{}: SELECTED'.format(img))
        return True
    else:
        return False


def avg_file_size(img_dir):
    total_size = 0
    acceptable_exts = ('.jpg', '.png', '.tiff')
    img_list = []
    for img in os.listdir(img_dir):
        print('proccessing file: {}'.format(img))
        if img.endswith(acceptable_exts) and \
                os.path.isfile(os.path.join(img_dir,img)): #check it is an image file, not a directory

            total_size += int(os.path.getsize(join(img_dir, img)))
            img_list.append(os.path.join(img_dir,img))
    avg_size = total_size/len(img_list)
    return avg_size, img_list


def super_giffer(pic_list, out_loc, frame_dur=0.25, gif_width=None):
    """
    This function will take a list of pictures, resize them, and make a gif from them.
    pic_list = list of the pictures - strings of the FULL PATH.
    gif_name = what you want the gif to be named (will get written to the pic_dir
    frame_dur = frame duration in seconds (0.25 default)
    gif_width = the number of pixles you want the final gif's width to be (420 default)
    """

    # make sure the name ends with .gif
    if not out_loc.endswith(".gif"):
        print("out location must end in'.gif'")


    images = []
    files_not_included = []

    # clean and resize the images.  Write resized images into a temp folder (to be removed after)
    acceptable_exts = ('.jpg', '.png', '.tiff')
    with tempfile.TemporaryDirectory() as tmpdirname:
        for f in pic_list:
            print('processing file:{}'.format(f))
            f_path, f_name = os.path.split(f) # get the name of the files, and the path to them.
            if os.path.isfile(f) and f.endswith(acceptable_exts): # There are some stupid hidden files in folders sometimes, these mess with the automati
                if not gif_width:  # check for size change.  If no size entered, just copy the image to the tmp folder
                    copyfile(f, join(tmpdirname, f_name))
                else:
                    i = Image.open(f)
                    gif_height = int((float(gif_width) / i.size[0]) * i.size[1])
                    i_resized = i.resize((gif_width, gif_height))
                    i_resized.save(join(tmpdirname,f_name))
            else:  # if the file is not a file, or doesn't have a valid extension:
                files_not_included.append(f)


        files_to_gif = os.listdir(tmpdirname) # turn the directory into a list of image names

        print('{} images to be giffed: {}'.format(len(files_to_gif), sorted(files_to_gif, key=lambda x: int(x.split('.')[0]))))
        print('{} files of invalid format: {}'.format(len(files_not_included),files_not_included))

        for f in sorted(files_to_gif, key=lambda x: int(x.split('.')[0])):  # files are sorted to ensure correct gif order.
            img_path = join(tmpdirname, f)
            immm = imageio.imread(img_path)
            images.append(immm)  # adds the image data to the images list
        print(len(images), 'images processed.')

    # Finally: Make the gif
    imageio.mimsave(out_loc, images, duration=frame_dur)  # NEED TO HAVE AN out_loc WITH ".gif" AT THE END!!


def takespread(sequence, num):
    # stolen from SO: https://stackoverflow.com/questions/9873626/choose-m-evenly-spaced-elements-from-a-sequence-of-length-n
    length = float(len(sequence))
    for i in range(num):
        yield sequence[int(ceil(i * length / num))]


def __main__():
    # # get folder stats
    avg_img_size, image_list = avg_file_size(target_directory)

    # # select the correct number of images, evenly spaced
    imgs_to_process = []
    for i in takespread(image_list, expected_fnum):
        # check if the image is dark
        if is_bigger(i, avg_img_size):
            imgs_to_process.append(i)
    # # send those images into the gifmaking function
    super_giffer(imgs_to_process,os.path.join(target_directory, OUT),gif_width=300)



if __name__ == "__main__":
    print(type(expected_fnum),type(target_directory))
    __main__()
    if input("Do you want to scp the resuting gif to a remote location (y/n)?").upper() == "Y":
        remotehost = input('Remotehost (user@192.168.0.11):')
        remoteloc = input("Remote location (/Users/username/Desktop):")
        print('scp "{localfile}" "{remotehost}:{targetpath}"'.format(localfile=os.path.join(target_directory,OUT), remotehost=remotehost, targetpath=remoteloc))

        os.system('scp "{localfile}" "{remotehost}:{targetpath}"'.format(localfile=os.path.join(target_directory,OUT), remotehost=remotehost, targetpath=remoteloc))

