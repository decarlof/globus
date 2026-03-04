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
    package_data={'globus': ['*.txt']},
    description='cli to manage APS beamline experiments',
    zip_safe=False,
)
