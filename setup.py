# -*- coding: utf-8 -*-
import ast
import os
import re

from setuptools import find_packages, setup

setup(
    name='hailstorms',
    version='1.0.5',
    description="Distributed load testing framework",
    long_description="""Hailstorm is a simplified config based, distributed load testing framework""",
    classifiers=[
        "Topic :: Software Development :: Testing :: Traffic Generation",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    keywords=['loadtest', 'locustio', 'hailstorm', 'hailstorms'],
    author='Mikael Larsson',
    author_email='mikael.larsson@romram.se',
    url='https://github.com/romramse/hailstorms',
    license='MIT',
    packages=find_packages(
        include=['hailstorms', 'hailstorms.start'],
        exclude=['ez_setup', 'examples', 'tests', 'graphs', 'generated', 'labs', 'scripts', 'venv']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "locustio>=0.8.1",
        "gevent>=1.2.2",
        "flask>=0.10.1",
        "requests>=2.9.1",
        "msgpack>=0.4.2",
        "six>=1.10.0",
        "pyzmq>=16.0.2"
    ],
)

