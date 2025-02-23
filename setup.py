from setuptools import setup, find_packages

setup(
    name="lukhed_stocks",
    version="0.0.4",
    description="A collection of stock analysis functions and api wrappers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="lukhed",
    author_email="lukhed.mail@gmail.com",
    url="https://github.com/lukhed/lukhed_stocks",
    packages=find_packages(),
    include_package_data=True,  # Ensures MANIFEST.in is used
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "lukhed-basic-utils>=1.4.1",
        "schwab-py>=1.4.0"
    ],
)