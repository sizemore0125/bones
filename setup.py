from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="skeletonkey",
    version='{{VERSION_PLACEHOLDER}}',
    description="A bare-bones configuration managment tool.",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sizemore0125/skeletonkey",
    author="Logan Sizemore",
    author_email="sizemore0125@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=["pyYAML>=3.0.0"],
)
