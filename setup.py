from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='tarentula',
    version='1.4.0',
    packages=find_packages(),
    description="Cli toolbelt for Datashare.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/icij/datashare-tarentula",
    test_suite='nose.collector',
    tests_require=['nose', 'responses'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    install_requires=[
        'Click',
        'requests==2.22.0',
        'bumpversion',
        'elasticsearch>=6.0.0,<7.0.0',
        'coloredlogs',
        'tqdm',
    ],
    python_requires='>=3.8',
    entry_points='''
        [console_scripts]
        tarentula-cli=tarentula.cli:cli
    ''')
