import setuptools
from pathlib import Path


with Path("src/contour/info.py").open() as info_file:
    exec(info_file.read())

# with open("README.md", "r") as fh:
#     long_description = fh.read()

requirements = [
    "numpy>=1.21.2",
    "scipy>=1.7.1",
    "Pillow>=8.3.2",
    "psutil>=5.8.0"
]

setuptools.setup(
    name="Contour",
    version=__version__,
    author="kamallouisnahas",
    author_email="contourqueries@gmail.com",
    description="A semi-automated segmentation and quantitation tool for cyro-soft-X-ray tomography in Python 3",
    # long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNU",
    license_files=["LICENSE"],
    url="https://github.com/kamallouisnahas/Contour",
    install_requires=requirements,
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GNU License",
        "Operating System :: OS Independent",
    ],
    python_requires=">3.5",
    entry_points={
        "console_scripts": [
            "contour-console = contour:main",
            "contour-usage = contour.main:usage"
            ],
        "gui_scripts":
            ["contour = contour:main"]},
)
