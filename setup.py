from typing import List
import setuptools


def _requires_from_file(filename: str) -> List[str]:
    return open(filename).read().splitlines()


setuptools.setup(
    name="smdconverter",
    version="1.3.0",
    install_requires=_requires_from_file('requirements.txt'),
    author="Hiroaki Takahashi",
    author_email="aphiloboe@gmail.com",
    url="https://github.com/MiLL4U/smd-converter",
    description="GUI application to convert smd files into ibw files",
    packages=setuptools.find_packages(),
    package_data={"smdconverter": ["image/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
