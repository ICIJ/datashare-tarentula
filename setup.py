from setuptools import setup, find_packages

setup(name='tarentula',
    version='0.6.0',
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=['nose', 'responses'],
    include_package_data=True,
    install_requires=[
        'Click',
        'requests==2.22.0',
        'bumpversion',
        'elasticsearch>=6.0.0,<7.0.0'
    ],
    entry_points='''
        [console_scripts]
        tarentula-cli=tarentula.cli:cli
    ''')
