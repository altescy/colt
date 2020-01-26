from setuptools import find_packages, setup


VERSION = {}
with open("pob/version.py", "r") as version_file:
    exec(version_file.read(), VERSION)

setup(
    name="pob",
    version=VERSION["VERSION"],
    author="altescy",
    author_email="altescy@fastmail.com",
    description="pob: Python Object Builder",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="json python object",
    url="https://github.com/altescy/pob",
    license='MIT License',
    packages=find_packages(),
    install_requires=[],
    entry_points={},
    tests_require=["pytest"],
    python_requires=">=3.7.3",
)
