import argparse
import json

from datetime import datetime, timedelta

import xml.etree.ElementTree as et

from geopy.distance import geodesic


__title__ = 'garmin-to-geojson'
__version__ = '0.1.0'
__author__ = 'Jochen Klar'
__email__ = 'jochenklar@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright 2018 Jochen Klar'
__description__ = 'Converts GPX or TCX files to geojson'


def garmin2geojson():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('input', help='VOTable file to be processed')

    args = parser.parse_args()

    tree = et.parse(args.input)
    root = tree.getroot()

    if root.tag.endswith('gpx'):
        geojson = gpx2geojson(root)
    elif root.tag.endswith('TrainingCenterDatabase'):
        geojson = tcx2geojson(root)
    else:
        raise ValueError('Input is not a GPX or TCX file.')


    #print(json.dumps(geojson))


def gpx2geojson(root):
    ns = {
        'gpx': 'http://www.topografix.com/GPX/1/1',
        'gpxtrkx': 'http://www.garmin.com/xmlschemas/TrackStatsExtension/v1'
    }

    features, p0, t0 = [], None, None

    for trk in root.findall('gpx:trk', ns):

        properties = {}
        coordinates = []

        properties['name'] = trk.find('gpx:name', ns).text
        print(properties['name'])
        for extension in trk.findall('gpx:extensions', ns):
            for node in extension.find('gpxtrkx:TrackStatsExtension', ns):
                properties[node.tag.replace('{%(gpxtrkx)s}' % ns, '')] = int(node.text)

        for trkseg in trk.findall('gpx:trkseg', ns):
            for trkpt in trkseg.findall('gpx:trkpt', ns):
                lat = float(trkpt.attrib['lat'])
                lon = float(trkpt.attrib['lon'])
                ele = float(trkpt.find('gpx:ele', ns).text)
                time = trkpt.find('gpx:time', ns).text

                p = (lon, lat)
                t = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

                if p0 is None:
                    dist = 0
                else:
                    dist = geodesic(p, p0).km

                if t0 is None:
                    vel = 0
                else:
                    vel = dist / ((t - t0).seconds / 3600.0)

                p0 = p
                t0 = t

                coordinates.append((lon, lat, ele, time, dist, vel))

        features.append({
            'type': 'Feature',
            'properties': properties,
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates
            }
        })

    return {
        'type': 'FeatureCollection',
        'features': features
    }


def tcx2geojson(root):
    ns = {
        'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
    }

    features, p0, t0, d = [], None, None, 0.0

    activities = root.find('tcx:Activities', ns)
    for activity in activities.findall('tcx:Activity', ns):

        for lap in activity.findall('tcx:Lap', ns):

            properties = {
                'TotalTimeSeconds': float(lap.find('tcx:TotalTimeSeconds', ns).text),
                'DistanceMeters': float(lap.find('tcx:DistanceMeters', ns).text),
                'MaximumSpeed': float(lap.find('tcx:MaximumSpeed', ns).text),
                'Calories': int(lap.find('tcx:Calories', ns).text),
                'Intensity': lap.find('tcx:Intensity', ns).text,
                'TriggerMethod': lap.find('tcx:TriggerMethod', ns).text
            }
            coordinates = []

            track = lap.find('tcx:Track', ns)
            for trackpoint in track.findall('tcx:Trackpoint', ns):

                position = trackpoint.find('tcx:Position', ns)
                if position:
                    lat = float(position.find('tcx:LatitudeDegrees', ns).text)
                    lon = float(position.find('tcx:LongitudeDegrees', ns).text)
                else:
                    # skip this point
                    continue

                ele = float(trackpoint.find('tcx:AltitudeMeters', ns).text)
                dist = float(trackpoint.find('tcx:DistanceMeters', ns).text)
                time = trackpoint.find('tcx:Time', ns).text

                p = (lat, lon)
                t = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

                if p0 is not None:
                    d += geodesic(p, p0).m

                if t0 is None:
                    vel = 0
                else:
                    vel = dist / ((t - t0).seconds / 3600.0)

                p0 = p
                t0 = t

                coordinates.append((lon, lat, ele, time, dist, vel))

        features.append({
            'type': 'Feature',
            'properties': properties,
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates
            }
        })

    return {
        'type': 'FeatureCollection',
        'features': features
    }
