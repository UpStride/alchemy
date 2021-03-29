import setuptools

setuptools.setup(
    name='upstride-alchemy',
    version="1.0.0a1",
    author="Upstride",
    author_email="pypi@upstride.io",
    py_modules=['alchemy'],
    entry_points={
        'console_scripts': ['alchemy_cli = alchemy.bin.alchemy_cli.py:main', ], },
    packages=setuptools.find_packages(),
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=[
        'requests',
    ],
)
