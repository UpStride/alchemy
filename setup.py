from setuptools import setup

setup(
    name='Alchemy_cli',
    py_modules=['alchemy_cli'],
    entry_points={
    'console_scripts': ['alchemy_cli = alchemy_cli:main', ],},
    long_description=open('README.md').read(),
)