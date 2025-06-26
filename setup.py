#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mvt-gui",
    version="0.1.0",
    author="MVT GUI Contributors",
    author_email="your-email@example.com",
    description="GUI for Mobile Verification Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mvt-gui",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: Qt",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        "mvt>=2.5.0",
        "PyQt5>=5.15.4",
    ],
    entry_points={
        "console_scripts": [
            "mvt-gui=mvt_gui:main",
        ],
    },
)
