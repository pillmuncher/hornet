# Copyright (c) 2021 Mick Krippendorf <m.krippendorf@freenet.de>

from setuptools import setup, find_packages
import versioneer

if __name__ == '__main__':
    setup(
        packages=find_packages(where='src'),
        package_dir={'':'src'},
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
    )
