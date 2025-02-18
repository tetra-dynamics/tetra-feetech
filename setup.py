from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as req:
        content = req.read()
        requirements = content.split('\n')
    return [r.strip() for r in requirements if r.strip() and not r.startswith('#')]

setup(
    name="tetra-feetech",
    version="0.0.1",
    packages=find_packages(),
    install_requires=read_requirements(),
)