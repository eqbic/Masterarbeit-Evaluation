import argparse
from dataclasses import dataclass
from typing import List
from pathlib import Path
import gpxpy
import gpxpy.gpx
from pyproj import Proj
import numpy as np
from scipy.spatial import cKDTree
import itertools
import math
import statistics as st
from datetime import datetime, timezone, MINYEAR


def utm_to_gpx(position: tuple, projection: Proj):
    """Convert a single UTM cooordinate, passed as tuple, to lat, lon"""
    lon, lat = projection(position[0], position[1], inverse=True)
    return lat, lon


def distance(a, b):
    """Calculate euclidian distance between 2 points which are (x, y) tuples"""
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def is_on_line(crosspt, r1, r2):
    # In fact it only checks if crosspt is in the bounding box defined
    # by R1 and R2 but since we know this is a solution of the two
    # linear equations, if it's in the box, it's also on the line.
    flag = False
    if crosspt[0] > min(r1[0], r2[0]) and crosspt[0] < max(r1[0], r2[0]):
        if crosspt[1] > min(r1[1], r2[1]) and crosspt[1] < max(r1[1], r2[1]):
            flag = True
    # dbg_print("cross: {}, r1: {}, r2: {}, valid: {}".format(crosspt, r1, r2, flag))
    return flag


def intersection(t, r1, r2):
    """Given two route points, r1, r2, find the perpendicular intersection from track point t"""
    # Calculate the gradient and intercept of the route vector.
    try:     # there's a risk of divide by zero errors
        r_grad = (r1[1] - r2[1]) / (r1[0] - r2[0])
        r_intercept = r1[1] - r_grad * r1[0]
        # gradient of the perpendicular error bar is -1/m
        e_grad = -1.0 / r_grad
        e_intercept = t[1] - e_grad * t[0]
        # solve the two equations of form y = mx + c to find the
        # intersection
        multiplier = - r_grad / e_grad
        y = (r_intercept + multiplier * e_intercept) / (multiplier + 1)
        x = (y - r_intercept) / r_grad
    except ZeroDivisionError:
        # R1 and R2 must be either due N-S or due E-W
        if r1[0] == r2[0]:
            # due N-S. Intersection point is X from R1 & R2, Y from T
            x = r1[0]
            y = t[1]
        elif r1[1] == r2[1]:
            # due E-W. Intersection is X from T and Y from R1 & R2
            x = t[0]
            y = r1[1]

    return is_on_line((x, y), r1, r2), x, y, distance((x, y), t)


class GpxResult:
    def __init__(self, track: gpxpy.mod_gpx.GPX, errors: List[float]):
        self.name = track.name
        self.start_time, self.end_time = track.get_time_bounds()
        self.time = track.get_duration()
        self.mean = np.mean(errors)
        self.median = np.median(errors)
        self.percentile = np.percentile(errors, 95)

    def __str__(self):
        return (f"name:            \t{self.name}s\n"
                f"start_time:      \t{self.start_time}s\n"
                f"end_time:        \t{self.end_time}s\n"
                f"time:            \t{self.time: .2f}s\n"
                f"errors.mean      \t{self.mean: .2f}m\n"
                f"errors.median    \t{self.median: .2f}m\n"
                f"errors.percentile\t{self.percentile: .2f}m")


class GpxEvaluator:
    def __init__(self, reference_file: Path, recorded_file: Path):
        self.projection = Proj(proj='utm', zone='32', ellps='WGS84', preserve_units=False)
        self.route_gpx = gpxpy.parse(open(reference_file))
        self.track_gpx = gpxpy.parse(open(recorded_file))
        self.route = self.gpx_to_utm(self.route_gpx)
        self.track = self.gpx_to_utm(self.track_gpx, "track")

    def gpx_to_utm(self, gpx_track: gpxpy.mod_gpx.GPX, prefix: str = None):
        """Return arrays X and Y, which are UTM coordinates of points in the GPX"""
        # convert points to XY in Universal Transverse Mercator - assume England
        coords = []
        prev = None
        distance = 0
        end_time = None
        start_time = None
        intervals = []

        # if prefix is not None:
        #     print("{}.filename\t{}".format(prefix, filename))

        for track in gpx_track.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point != prev:  # prevent identical successive coordinates
                        coords.append(self.projection(point.longitude, point.latitude))
                        if prev is not None and prefix is not None:
                            intervals.append(point.time - prev.time)
                    prev = point

            distance = distance + track.length_2d()
            track_start, end_time = track.get_time_bounds()
            if not start_time:
                start_time = track_start

        # if prefix is not None:
        #     print("{}.num_points\t{}".format(prefix, len(coords)))
        #     print("{0}.distance\t{1: .0f}".format(prefix, distance))
        #     print("{}.start\t{}".format(prefix, start_time))
        #     print("{}.end\t{}".format(prefix, end_time))
        #     print("{}.intervals.mean\t{}".format(
        #         prefix,
        #         np.mean(intervals)))
        #     print("{}.intervals.max\t{}".format(
        #         prefix, np.max(intervals)))
        return coords

    def evaluate(self) -> GpxResult:
        vis = VisGpx()
        errors = []
        # Our task is to find the nearest adjacent pair of points in the route
        # for each point in the track, so set up a KD tree of route points and
        # query the nearest neighbour or each point in the current track
        distances, indexes = cKDTree(self.route).query(self.track)

        for (t, d, i) in zip(self.track, distances, indexes):
            nearest = self.route[i]

            # Two cases:
            # 1. Closest distance from track point T to route is directly to
            #    point 'nearest'
            # 2. Closest distance from track point T to route is to a point on a
            #    line between successive nearby route points. It's indeterminate
            #    now many route points to check, but in practice we seem to
            #    correctly find the shortest distance by considering (i-2, i-1),
            #    (i-1, i), (i, i+1), (i+1, i+2)

            # Set up for case 1.
            shortest_d = d
            closest_x = nearest[0]
            closest_y = nearest[1]

            # Check for case 2. We can find the potential closest point by
            # expressing each line R1-R2 as an equation in the form y = mx + c,
            # then describing another line through T, perpendicular to R1-R2
            # (which will have gradient -1/m), and solving the two equations to
            # find the point of intersection.
            for r1 in range(max(0, i-2), min(i+2, len(self.route)-1)):
                valid, x, y, d = intersection(t, self.route[r1], self.route[r1+1])
                if valid and d < shortest_d:
                    closest_x = x
                    closest_y = y
                    shortest_d = d

            errors.append(shortest_d)
            vis.append(t, (closest_x, closest_y))
        return GpxResult(self.track_gpx, errors)


# For debug / test purposes, create a GPX file that visualises the
# track and the error bar for each track point
class VisGpx:
    def __init__(self):
        self.projection = self.projection = Proj(proj='utm', zone='32', ellps='WGS84', preserve_units=False)
        self.gpx = gpxpy.gpx.GPX()
        self.gpx_track = gpxpy.gpx.GPXTrack()
        self.gpx.tracks.append(self.gpx_track)
        self.gpx_segment = gpxpy.gpx.GPXTrackSegment()
        self.gpx_track.segments.append(self.gpx_segment)

    def append(self, t, e_point):
        # Add three points to the track: T, the calculated error, and T again.
        e_point_lat, e_point_lon = utm_to_gpx(e_point, self.projection)
        t_lat, t_lon = utm_to_gpx(t, self.projection)
        self.gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(t_lat, t_lon))
        self.gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(e_point_lat, e_point_lon))
        self.gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(t_lat, t_lon))

    def finish(self):
        path = pathlib.Path(__file__).parent.resolve()
        path.joinpath("__VisGPX.gpx")
        with open(path, "w+") as f:
            f.write(self.gpx.to_xml())
