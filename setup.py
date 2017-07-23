#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = (
    'celery>=4.0.0',
    'redis==2.10.5'
)

dependency_links = [
    '-e git+https://github.com/duncan-r/SHIP.git@tuflow_refactor#egg=ship',
    '-e git+https://github.com/JamesRamm/fmdb.git#egg=fmdb'
]

setup_requirements = [
    # TODO(JamesRamm): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='qflow',
    version='0.1.0',
    description="Execution of Tuflow models using the Celery distributed task queue",
    long_description=readme + '\n\n' + history,
    author="James Ramm",
    author_email='jamessramm@gmail.com',
    url='https://github.com/JamesRamm/qflow',
    packages=find_packages(include=['qflow']),
    include_package_data=True,
    install_requires=requirements,
    dependency_links=dependency_links,
    license="AGPL license",
    zip_safe=False,
    keywords=('QFlow', 'Tuflow', 'Flood Modelling'),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
