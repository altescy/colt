from setuptools import find_packages, setup


VERSION = {}
with open("colt/version.py", "r") as version_file:
    exec(version_file.read(), VERSION)

setup(
    name="colt",
    version=VERSION["VERSION"],
    author="altescy",
    author_email="altescy@fastmail.com",
    description="A configuration utility for Python object.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="config python object",
    url="https://github.com/altescy/colt",
    license='MIT License',
    packages=find_packages(),
    install_requires=[],
    entry_points={},
    tests_require=["pytest"],
    python_requires=">=3.7.3",
)
