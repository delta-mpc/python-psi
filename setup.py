# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="delta_psi",
    version="0.0.2",
    packages=find_packages(),
    include_package_data=True,
    exclude_package_data={'': ['.gitignore']},
    install_requires=[
        'numpy~=1.20.2',
        'pycryptodome~=3.10.1',
        "pyyaml~=5.3"
    ],
    zip_safe=False,
    author="miaohong",
    author_email="miaohong@yuanben.org",
    description="package for private set intersection",
    entry_points={
        "console_scripts": [
            "psi_run=psi.main:main"
        ]
    },
    python_requires='>=3.6',
)
