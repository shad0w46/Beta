#!/usr/bin/env python3
"""Setuptools packaging configuration for Beta Assistant."""

from setuptools import setup, find_packages

setup(
    name="beta-assistant",
    version="1.0.0",
    description="Personal Assistant & GUI Control Center for AlphaOS",
    author="AlphaOS Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.5.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "beta-assistant=beta_assistant.__main__:main",
        ],
    },
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Systems Administration",
    ],
)
