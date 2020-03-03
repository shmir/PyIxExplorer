#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
from setuptools import setup
import io

import ixexplorer


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')

with open('requirements.txt') as f:
    required = f.read().splitlines()
install_requires = [r for r in required if r and r[0] != '#' and not r.startswith('git')]

setup(
    name='pyixexplorer',
    version=ixexplorer.__version__,
    url='https://github.com/shmir/PyIxExplorer/',
    license='Apache Software License',
    author='Yoram Shamir',
    install_requires=install_requires,
    author_email='yoram@ignissoft.com',
    description='Python OO API package to automate Ixia IxExplorer traffic generator',
    long_description=long_description,
    packages=['ixexplorer', 'ixexplorer.tests', 'ixexplorer.api'],
    include_package_data=True,
    platforms='any',
    tests_require=['pytest'],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing :: Traffic Generation'],
)
