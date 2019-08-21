from setuptools import setup, find_packages

setup(name='tarentula',
    version='0.0.0',
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose', 'responses'],
    include_package_data=True,
    install_requires=[
        'Click==7.0',
        'requests==2.22.0',
        'bumpversion'
    ],
    entry_points='''
        [console_scripts]
        tarentula=tarentula.cli:cli
    ''')
