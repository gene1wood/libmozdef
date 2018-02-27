from setuptools import setup

setup(
    name='libmozdef',
    version='0.5.0',
    packages=['libmozdef'],
    url='https://github.com/gene1wood/libmozdef',
    license='MPL-2.0',
    author='Gene Wood',
    author_email='gene_wood@cementhorizon.com',
    description='MozDef client',
    install_requires=[],
    extras_require={
        'aws': ['boto3'],
        'http': ['requests-futures']
    }
)
