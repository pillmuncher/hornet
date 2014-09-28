import os
from setuptools import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name = "hornet",
    version = "0.2.3a",
    author = "Mick Krippendorf",
    author_email = "m.krippendorf@freenet.de",
    description = "Horn clauses via Expression Trees",
    license = "MIT",
    keywords = "logic-programming prolog",
    url = "https://github.com/pillmuncher/hornet",
    packages=['hornet', 'hornet.test', 'hornet.examples'],
    install_requires=['nose', 'codegen'],
    package_data={'hornet': ['../*.md']},
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Libraries",
        "License :: OSI Approved :: MIT License",
    ],
)
