from typing import List, Union

import commonroad_dc.pycrcc as pycrcc
import numpy as np
import pycrccosy
import pycrreachset as reach
from commonroad.geometry.shape import ShapeGroup, Shape, Rectangle, Circle
from commonroad_dc.collision.collision_detection.minkowski_sum import minkowski_sum_circle

import commonroad_reachset.utility.geometry as util_geometry
from commonroad_reachset.data_structure.reach.reach_polygon import ReachPolygon


def create_curvilinear_aabb_from_obstacle(
        obstacle, CLCS: pycrccosy.CurvilinearCoordinateSystem,
        radius_disc: float, time_step: int = None, resolution: int = 5, ) -> List[pycrcc.RectAABB]:
    """Returns a list of axis-aligned bounding boxes from an obstacle in Curvilinear coordinate system.

    The shapes are dilated with the disc radius of the ego vehicle to consider its shape.
    """
    list_aabb_CVLN = []

    if time_step is None:
        time_step = obstacle.initial_state.time_step

    occupancy = obstacle.occupancy_at_time(time_step)
    if not occupancy:
        return []

    if isinstance(occupancy.shape, ShapeGroup):
        for shape in occupancy.shape.shapes:
            shape_dilated = minkowski_sum_circle(shape, radius_disc, resolution)
            list_aabb_CVLN += create_curvilinear_and_rasterized_aabb_from_shape(shape_dilated, CLCS)

    else:
        shape_dilated = minkowski_sum_circle(occupancy.shape, radius_disc, resolution)
        list_aabb_CVLN = create_curvilinear_and_rasterized_aabb_from_shape(shape_dilated, CLCS)

    return list_aabb_CVLN


def create_curvilinear_and_rasterized_aabb_from_shape(
        shape: Shape, CLCS: pycrccosy.CurvilinearCoordinateSystem) -> List[pycrcc.RectAABB]:
    """Returns a list of axis-aligned and rasterized boxes from a CommonRoad shape in Curvilinear coordinate system.

    Since we use axis-aligned rectangles (bounding boxes) for collision checks in Curvilinear coordinate system,
    simply using the rectangle with min/max lon/lat vertices converted from the Cartesian coordinates incurs a large
    over-approximation of the shape of the obstacle. We therefore rasterize (partition) the converted rectangle in
    the longitudinal direction and adjust their lateral coordinates to reduce the over-approximation.
    """
    list_aabb_CVLN = []

    # adapt circle to rectangle
    if isinstance(shape, Circle):
        # over-approximate the circle with a rectangle
        shape = Rectangle(shape.radius * 2, shape.radius * 2, shape.center)

    # convert to curvilinear vertices
    list_vertices_CVLN = convert_to_curvilinear_vertices(shape.vertices, CLCS)
    if not list_vertices_CVLN:
        return []

    # get the bounding box of the converted vertices
    p_lon_min, p_lat_min, p_lon_max, p_lat_max = util_geometry.obtain_extremum_coordinates_of_vertices(
        list_vertices_CVLN)

    # obtain a list of longitudinal positions for rasterization
    step = 2
    list_p_lon = list(np.arange(p_lon_min, p_lon_max, step))
    if not np.isclose(list_p_lon[-1], p_lon_max):
        list_p_lon.append(p_lon_max)

    # this polygon will later be used to find the intersection with partitioned bounding boxes
    polygon_obstacle_CART = ReachPolygon(shape.vertices)

    # iterate through each partition, convert to Cartesian, and find the intersection with the polygon of the shape.
    # then, convert the vertices of the intersected polygon again to Curvilinear, and find out the new lateral
    # extremum coordinates.
    for p_lon_min_partition, p_lon_max_partition in zip(list_p_lon[:-1], list_p_lon[1:]):
        vertex1 = CLCS.convert_to_cartesian_coords(p_lon_min_partition, p_lat_min)
        vertex2 = CLCS.convert_to_cartesian_coords(p_lon_max_partition, p_lat_min)
        vertex3 = CLCS.convert_to_cartesian_coords(p_lon_max_partition, p_lat_max)
        vertex4 = CLCS.convert_to_cartesian_coords(p_lon_min_partition, p_lat_max)

        # Cartesian polygon of the partition
        polygon_partition_CART = ReachPolygon([vertex1, vertex2, vertex3, vertex4])

        # find the intersection with the polygon of the obstacle
        polygon_intersection = polygon_obstacle_CART.intersection(polygon_partition_CART)
        if polygon_intersection.is_empty:
            continue

        polygon_intersection = ReachPolygon.from_polygon(polygon_intersection)

        # convert the vertices of the intersected polygon to CVLN and find the new lateral extremum coordinates
        list_p_lat = []
        for vertex in polygon_intersection.vertices:
            _, p_lat = CLCS.convert_to_curvilinear_coords(vertex[0], vertex[1])
            list_p_lat.append(p_lat)

        p_lat_min_partition = min(list_p_lat)
        p_lat_max_partition = max(list_p_lat)

        list_aabb_CVLN.append(util_geometry.create_aabb_from_coordinates(p_lon_min_partition, p_lat_min_partition,
                                                                         p_lon_max_partition, p_lat_max_partition))

    return list_aabb_CVLN


def convert_to_curvilinear_vertices(vertices_CART: np.ndarray, CLCS: pycrccosy.CurvilinearCoordinateSystem):
    """Converts a list of Cartesian vertices to Curvilinear vertices."""
    try:
        list_vertices_CVLN = [CLCS.convert_to_curvilinear_coords(vertex[0], vertex[1]) for vertex in vertices_CART]

    except ValueError:
        return []

    else:
        return list_vertices_CVLN


def convert_to_cartesian_polygons(rectangle_CVLN: Union[ReachPolygon, reach.ReachPolygon],
                                  CLCS: pycrccosy.CurvilinearCoordinateSystem, split_wrt_angle):
    """Returns a list of rectangles converted to Cartesian coordinate system.

    If split_wrt_angle set to True, the converted rectangles will be further split into smaller ones if their
    upper and lower edges has a difference in angle greater than a threshold. This is to smoothen the plotting.
    """
    if isinstance(rectangle_CVLN, ReachPolygon):
        return convert_to_cartesian_polygon(rectangle_CVLN.bounds, CLCS, split_wrt_angle)

    elif isinstance(rectangle_CVLN, reach.ReachPolygon):
        p_lon_min = rectangle_CVLN.p_lon_min()
        p_lat_min = rectangle_CVLN.p_lat_min()
        p_lon_max = rectangle_CVLN.p_lon_max()
        p_lat_max = rectangle_CVLN.p_lat_max()

        return convert_to_cartesian_polygon((p_lon_min, p_lat_min, p_lon_max, p_lat_max), CLCS, split_wrt_angle)


def convert_to_cartesian_polygon(tuple_vertices, CLCS: pycrccosy.CurvilinearCoordinateSystem, split_wrt_angle):
    """
    1. Tries to convert into Cartesian rectangle.
    2. If split_wrt_angle set to True, the converted rectangle will be further split if its upper and lower edges
       have a difference in angle greater than the threshold.
    """
    p_lon_min, p_lat_min, p_lon_max, p_lat_max = tuple_vertices

    try:
        vertex1 = CLCS.convert_to_cartesian_coords(p_lon_min, p_lat_min)
        vertex2 = CLCS.convert_to_cartesian_coords(p_lon_max, p_lat_min)
        vertex3 = CLCS.convert_to_cartesian_coords(p_lon_max, p_lat_max)
        vertex4 = CLCS.convert_to_cartesian_coords(p_lon_min, p_lat_max)

    except ValueError:
        return []

    else:
        vector_p_lon_min = vertex1 - vertex4
        vector_p_lon_max = vertex2 - vertex3
        unit_vector_1 = vector_p_lon_min / np.linalg.norm(vector_p_lon_min)
        unit_vector_2 = vector_p_lon_max / np.linalg.norm(vector_p_lon_max)
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        angle = np.arccos(dot_product)

        if split_wrt_angle and np.abs(angle) > 0.2:
            p_lon_mid = (p_lon_min + p_lon_max) / 2

            list_polygons_p_lon_min = convert_to_cartesian_polygon((p_lon_min, p_lat_min, p_lon_mid, p_lat_max), CLCS,
                                                                   True)
            list_polygon_p_lon_max = convert_to_cartesian_polygon((p_lon_mid, p_lat_min, p_lon_max, p_lat_max), CLCS,
                                                                  True)

            return list_polygons_p_lon_min + list_polygon_p_lon_max

        else:
            return [ReachPolygon([vertex1, vertex2, vertex3, vertex4])]