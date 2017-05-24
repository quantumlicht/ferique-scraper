import os
import zipfile
import re
FORCE_INCLUDE_LIST = ['uritemplate', 'pyasn']
IGNORE_LIST = ['egg', 'README', 'tests', 'certifi', 'easy_install', 'wincertstore']
IGNORE_DIR = ['pip', 'setuptools', '__pycache__', 'egg', 'wheel']
ROOT_DIR = './site-packages'

#TODO Package credential folder and add .gitkeep
REQUIRED_DEPS = ['lambda_function.py', 'google_writer.py', 'transform.py', 'scraper.py']


def match_in_list(to_match, possible_match_list):
    return any([re.search(r'{}'.format(element), to_match) for element in possible_match_list])

first_level = True
with open('version.txt', 'r') as version:
    major, minor = version.read().split('.')

    with zipfile.ZipFile("./builds/pack_{}_{}.zip".format(int(major), int(minor)), "w", zipfile.ZIP_DEFLATED) as zf:

        # ZIP Main files
        for dep in REQUIRED_DEPS:
            print('adding dep {}'.format(dep))
            zf.write(os.path.join('./', dep))

        # Change dir so that we don't zip the folder itself
        os.chdir(ROOT_DIR)
        for dirname, subdirs, files in os.walk('./'):
            # Do not walk the top dirs we want to ignore
            # We only do it for first dir.
            # Some of the ignored dirs could show recursively, yet we would not want to remove them
            for directory in list(subdirs):
                if directory in IGNORE_DIR and first_level:
                    print('removing dir {}'.format(directory))
                    subdirs.remove(directory)
            first_level = False

            if not match_in_list(dirname, IGNORE_LIST):
                zf.write(dirname)
                for filename in files:
                    if not match_in_list(filename, IGNORE_LIST) or match_in_list(filename, FORCE_INCLUDE_LIST):
                        zf.write(os.path.join(dirname, filename))
                    else:
                        print('excluding file {}'.format(os.path.join(dirname, filename)))
            else:
                print('excluding dir {}'.format(dirname))

