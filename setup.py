import os
import pathlib
import re
import shutil
import sys

import pkg_resources
import setuptools

if sys.version_info < (3, 9):
    sys.exit("Sorry, Python < 3.9 is not supported")


VERSIONFILE = "pome/_version.py"

with open(VERSIONFILE, "rt") as f:
    verstrline = f.read()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError(f"Unable to find version string in {VERSIONFILE}.")

with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]


if not os.path.exists("scripts"):
    os.makedirs("scripts")
shutil.copyfile("run_pome.py", "scripts/pome")

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pome",
    version=verstr,
    scripts=["scripts/pome"],
    author="Tristan Stérin",
    author_email="tristan@prgm.dev",
    description="Distributed accounting software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pome-gr/pome",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
