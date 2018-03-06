#!/usr/bin/env python
from glob import glob
from setuptools import setup, find_packages

setup(
    name='hulk',
    version='0.0.1',
    description='Lightweight, extensible, language-independent mutation testing.',
    long_description='TBA',
    author='Chris Timperley',
    author_email='christimperley@gmail.com',
    url='https://github.com/squaresLab/Hulk',
    license='mit',
    install_requires=[
        'pyyaml',
        'requests',
        'flask'
    ],
    tests_require=['pytest'],
    include_package_data=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        '': ['*.yml']
    },
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    entry_points = {
        'console_scripts': [ 'hulkd = hulk.server:main' ]
    },
    test_suite = 'tests'
)
