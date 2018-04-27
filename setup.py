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
    python_requires='>=3.5',
    install_requires=[
        'bugzoo>=2.1.1',
        'rooibos>=0.1.0',
        'pyyaml',
        'requests>=2.0.0',
        'flask>=0.10',
        'Flask-API'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest'
    ],
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
