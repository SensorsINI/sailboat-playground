from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="sailboat_playground",
    version="0.1.1",
    license="GPL-3.0",
    description="A very simple framework for sailboat simulation and autonomous navigation algorithms development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    author="Gabriel Gazola Milan",
    author_email="gabriel.gazola@poli.ufrj.br",
    url="https://github.com/gabriel-milan/sailboat-playground",
    include_package_data=True,
    keywords=[
        "framework",
        "python",
        "sailboat",
        "simulation",
        "autonomous navigation",
    ],
    install_requires=[
        "cython",
        "numpy",
        "pyglet==1.5.17",
        "pandas",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
