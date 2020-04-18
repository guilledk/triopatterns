#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name="triopatterns",
    packages=find_packages(),
    version="0.1.0",
    description="Useful async patterns I repeat everywere when using trio.",
    install_requires=[
        "trio"
    ]
)
