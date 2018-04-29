import re

from setuptools import setup

with open('garmin_to_geojson.py') as f:
    metadata = dict(re.findall(r'__(.*)__ = [\']([^\']*)[\']', f.read()))

setup(
    name=metadata['title'],
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    maintainer=metadata['author'],
    maintainer_email=metadata['email'],
    license=metadata['license'],
    url='https://github.com/jochenklar/garmin-to-geojson',
    description=u'Converts GPX or TCX files to geojson',
    long_description=open('README.md').read(),
    install_requires=[
        'geopy>=1.13.0',
    ],
    entry_points={
        'console_scripts': [
            'garmin2geojson=garmin_to_geojson:garmin2geojson'
        ]
    }
)
