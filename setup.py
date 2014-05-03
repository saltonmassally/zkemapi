# -*- coding: utf-8 -*-
import distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup

tests_require = ['pytest']

setup(
    name = "zkemapi",
    version = "0.0.1",
    packages = ['zkemapi'],
    include_package_data=True,
    package_data = {
        '': ['distribute_setup.py'],
        },

    # metadata 
    author = "John Montero",
    author_email = "johnmc [at] molicom [dot] com.pe",
    description = "Control de Asistencia del Personal",
    long_description = "",
   classifiers=[
        'Development Status :: 1 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
      ],

    license = "MIT",
    keywords = "daemon asistencia personal",
    url = "",   

)

