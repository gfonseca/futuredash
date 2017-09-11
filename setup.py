#!/usr/bin/env python2
from setuptools import setup
import os

icons = ["./icons/" + i for i in os.listdir("./icons/")]

setup(name='futuredash',
      version='0.1',
      description='a simple status bar with python and zen',
      author='Georgio Barbosa',
      author_email='georgio.barbosa@gmail.com',
      license='Apache v2.0',
      packages=['futuredash'],
      scripts=['futuredash/futuredash'],
      data_files = [
        ("/etc/futuredash/icons/", icons)
      ],
      zip_safe=False)
