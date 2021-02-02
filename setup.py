import setuptools

try:
    with open("readme.md", "r") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = ''

setuptools.setup(
    name="nextcloud-utils",
    version="1.0.0",
    author="Wannes Meert",
    author_email="wannes.meert@kuleuven.be",
    description="Nextcloud utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://people.cs.kuleuven.be/wannes.meert",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "webdavclient3"
    ],
)
