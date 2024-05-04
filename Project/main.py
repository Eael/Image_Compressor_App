import os
from PIL import Image
from glob import glob


def main():
    icons_directory = input("Input the directory where the icons are located: ") #C:/Users/teyee/Documents/PYTHON EARL/PythonAPI/images/
    save_directory = input("Input the directory where the resized icons are saved: ")
    size = input("Input the size of the icons in the form (width, height): ")
    rotate_by = int(input("How many degrees should image be rotated? "))

    size = tuple(map(int, size.split(',')))

    for file in glob('{}/ic_*'.format(icons_directory)):
        path, filename = os.path.split(file)
        filename = os.path.splitext(filename)[0]
        image = Image.open(file).convert('RGB')
        image.rotate(rotate_by)
        image.resize(size)
        image.save('{}{}.jpeg'.format(save_directory, filename))

    print('OK')


if __name__ == '__main__':
    main()
