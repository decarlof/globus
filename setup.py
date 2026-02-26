from skbuild import setup
from setuptools import find_packages


setup(
    name='globus',
    version=open('VERSION').read().strip(),
    author='Francesco De Carlo',
    author_email='decarlof@gmail.com',
    url='https://github.com/xray-imaging/globus',
    package_dir={"": "src"},
    entry_points={'console_scripts':['globus = globus.__main__:main'],},
    packages=find_packages('src'),
    description='cli to run globus at 2-bm',
    zip_safe=False,
)