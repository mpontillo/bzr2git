import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "bzr2git",
    version = "0.0.1",
    author = "Mike Pontillo",
    author_email = "pontillo@gmail.com",
    description = "Quick and dirty migration tool from bzr to git.",
    license = "BSD",
    keywords = "bzr git migrate migration",
    url = "https://github.com/mpontillo/bzr2git/",
    packages=['bzr2git'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        "console_scripts": [
            "bzr2git = bzr2git.main:main",
        ],
    },

)

