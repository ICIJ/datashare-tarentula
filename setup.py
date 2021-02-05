import sys

from setuptools import setup, find_packages
from tarentula import __version__

py_version = sys.version_info[:2]
if py_version < (3, 6):
    raise Exception("tarentula requires Python >= 3.6.")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='tarentula',
      version=__version__,
      packages=find_packages(),
      description="Cli toolbelt for Datashare.",
      use_pipfile=True,
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/icij/datashare-tarentula",
      test_suite='nose.collector',
      tests_require=['nose', 'responses'],
      include_package_data=True,
      keywords=['datashare', 'api', 'text-mining', 'elasticsearch'],
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Affero General Public License v3",
          "Operating System :: OS Independent",
          "Topic :: Scientific/Engineering :: Information Analysis",
      ],
      python_requires='>=3.6',
      entry_points='''
        [console_scripts]
        tarentula=tarentula.cli:cli
        graph_es=tarentula.graph_realtime:graph
    ''')
