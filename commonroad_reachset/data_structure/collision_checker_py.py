from typing import List

import numpy as np
from commonroad.geometry.shape import Rectangle, Shape, Polygon, ShapeGroup
from commonroad.scenario.obstacle import StaticObstacle, DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State
from commonroad_dc.boundary import boundary
from commonroad_dc.pycrccosy import CurvilinearCoordinateSystem
from commonroad_reachset.data_structure.configuration import Configuration
from commonroad_reachset.data_structure.reach.reach_polygon import ReachPolygon


class PyCollisionChecker:
    """Collision checker for the reachable sets with Python backend.

    It handles collision checks in both Cartesian and Curvilinear coordinate systems.
    """

    def __init__(self, config: Configuration):
        self.config = config
        self.scenario_cc = None
        self._initialize_collision_checker()

    def _initialize_collision_checker(self):
        """Initializes the collision checker based on the specified coordinate system."""
        if self.config.planning.coordinate_system == "CART":
            self.scenario_cc = self._create_cartesian_scenario_for_collision_check(self.config)

        elif self.config.planning.coordinate_system == "CVLN":
            self.scenario_cc = self._create_scenario_for_curvilinear_collision_check(self.config)

        else:
            raise Exception("<PyCollisionChecker> Undefined coordinate system.")

    @staticmethod
    def _create_cartesian_scenario_for_collision_check(config: Configuration):
        """Returns a scenario with obstacles in Cartesian coordinate system.

        Elements included: obstacles, road boundaries.
        The obstacles (vehicles and road boundaries) are converted into Curvilinear coordinate system.
        """
        scenario: Scenario = config.scenario
        scenario_cc = Scenario(scenario.dt, scenario.scenario_id)

        # add lanelet network
        scenario_cc.add_objects(scenario.lanelet_network)

        list_obstacles_CART = []
        # add obstacles
        if config.reachable_set.consider_traffic:
            list_obstacles_CART += config.scenario.obstacles

        # add road boundary
        object_road_boundary, _ = boundary.create_road_boundary_obstacle(scenario_cc, method="triangulation")
        list_obstacles_CART.append(object_road_boundary)

        scenario_cc.add_objects(list_obstacles_CART)

        return scenario_cc

    def _create_scenario_for_curvilinear_collision_check(self, config: Configuration):
        """Returns a scenario with obstacles in Curvilinear coordinate system.

        Elements included: obstacles, road boundaries.
        The obstacles (vehicles and road boundaries) are converted into Curvilinear coordinate system.
        """
        scenario: Scenario = config.scenario
        scenario_cc = Scenario(scenario.dt, scenario.scenario_id)

        # add lanelet network
        scenario_cc.add_objects(scenario.lanelet_network)

        list_obstacles_CART = []
        # add obstacles
        if config.reachable_set.consider_traffic:
            list_obstacles_CART += config.scenario.obstacles

        # add road boundary
        object_road_boundary, _ = boundary.create_road_boundary_obstacle(scenario_cc, method="triangulation")
        list_obstacles_CART.append(object_road_boundary)

        # convert obstacles into curvilinear coordinate system
        list_obstacles_CVLN = self.convert_obstacles_to_curvilinear_coordinate_system(list_obstacles_CART,
                                                                                      config.planning.CLCS)

        scenario_cc.add_objects(list_obstacles_CVLN)

        return scenario_cc

    def convert_obstacles_to_curvilinear_coordinate_system(self, list_obstacles_CART, CLCS):
        """Returns a list of obstacles converted into curvilinear coordinate system.

        Splitting obstacles in the Cartesian coordinate system into smaller rectangles (rasterization) reduces over-
        approximation in the curvilinear coordinate system, since they are converted into axis-aligned rectangles.
        """

        list_obstacles_static_CART = [obs for obs in list_obstacles_CART if isinstance(obs, StaticObstacle)]
        list_obstacles_dynamic_CART = [obs for obs in list_obstacles_CART if isinstance(obs, DynamicObstacle)]

        list_obstacles_static_CVLN = self.convert_to_curvilinear_static_obstacles(list_obstacles_static_CART, CLCS)
        # todo: implement this
        # list_obstacles_dynamic_CVLN = self.convert_to_curvilinear_dynamic_obstacles(list_obstacles_dynamic_CART, CLCS)

        # return list_obstacles_static_CVLN + list_obstacles_dynamic_CVLN
        return list_obstacles_static_CVLN

    def convert_to_curvilinear_static_obstacles(self, list_obstacles_static_CART, CLCS: CurvilinearCoordinateSystem):
        """Converts a list of static obstacles to obstacle under Curvilinear coordinate system."""
        list_obstacles_static_CVLN = []

        for obstacle in list_obstacles_static_CART:
            time_step_initial = obstacle.initial_state.time_step

            occupancy = obstacle.occupancy_at_time(time_step_initial)

            if isinstance(occupancy.shape, ShapeGroup):
                for shape in occupancy.shape.shapes:
                    shape_obstacle_CVLN, position_CVLN = self.convert_to_curvilinear_shape(shape, CLCS)

                    if shape_obstacle_CVLN is None or position_CVLN is None:
                        continue

                    id_obstacle = self.config.scenario.generate_object_id()
                    type_obstacle = obstacle.obstacle_type

                    state_initial_obstacle_CVLN = State(position=np.array([0,0]), orientation=0.00,
                                                        time_step=time_step_initial)

                    # feed in the required components to construct a static obstacle
                    static_obstacle = StaticObstacle(id_obstacle, type_obstacle,
                                                     shape_obstacle_CVLN, state_initial_obstacle_CVLN)

                    list_obstacles_static_CVLN.append(static_obstacle)

            elif isinstance(occupancy.shape, Shape):
                shape_obstacle_CVLN, _ = self.convert_to_curvilinear_shape(occupancy.shape, CLCS)

                id_obstacle = obstacle.obstacle_id
                type_obstacle = obstacle.obstacle_type
                position = obstacle.initial_state.position
                position_obstacle_CVLN = CLCS.convert_to_curvilinear_coords(position[0], position[1])

                state_initial_obstacle_CVLN = State(position=position_obstacle_CVLN, orientation=0.00,
                                                    time_step=time_step_initial)

                # feed in the required components to construct a static obstacle
                static_obstacle = StaticObstacle(id_obstacle, type_obstacle,
                                                 shape_obstacle_CVLN, state_initial_obstacle_CVLN)

                list_obstacles_static_CVLN.append(static_obstacle)

        return list_obstacles_static_CVLN

    def convert_to_curvilinear_shape(self, shape: Shape, CLCS):
        """Converts a rectangle or polygon to Curvilinear coordinate system."""
        if isinstance(shape, Rectangle):
            list_vertices_CVLN = self.convert_to_curvilinear_vertices(shape.vertices, CLCS)
            rectangle, position = self.create_rectangle_from_vertices(list_vertices_CVLN)

            return rectangle, position

        elif isinstance(shape, Polygon):
            try:
                position = CLCS.convert_to_curvilinear_coords(shape.center[0], shape.center[1])
                list_vertices_CVLN = self.convert_to_curvilinear_vertices(shape.vertices, CLCS)
                polygon = self.create_polygon_from_vertices(list_vertices_CVLN)

                return polygon, position

            except ValueError:
                return None, None

        else:
            return None

    @staticmethod
    def convert_to_curvilinear_vertices(list_vertices_CART, CLCS: CurvilinearCoordinateSystem):
        """Converts a list of vertices to Curvilinear coordinate system."""
        try:
            list_vertices_CVLN = [CLCS.convert_to_curvilinear_coords(vertex[0], vertex[1])
                                  for vertex in list_vertices_CART]

        except ValueError:
            return []

        else:
            return list_vertices_CVLN

    @staticmethod
    def create_rectangle_from_vertices(list_vertices):
        """Returns a rectangle and its position for the given list of vertices."""
        if not list_vertices:
            return None, None

        list_p_lon = [vertex[0] for vertex in list_vertices]
        list_p_lat = [vertex[1] for vertex in list_vertices]

        p_lon_min = min(list_p_lon)
        p_lat_min = min(list_p_lat)
        p_lon_max = max(list_p_lon)
        p_lat_max = max(list_p_lat)

        length = p_lon_max - p_lon_min
        width = p_lat_max - p_lat_min
        position = np.array([(p_lon_min + p_lon_max) / 2.0, (p_lat_min + p_lat_max) / 2.0])

        return Rectangle(length=length, width=width), position

    @staticmethod
    def create_polygon_from_vertices(list_vertices):
        """Returns a polygon and its position for the given list of vertices."""
        if not list_vertices:
            return None

        return Polygon(np.array(list_vertices))

    def collides_at_time_step(self, time_idx: int, rectangle: ReachPolygon) -> bool:
        """Checks for collision with obstacles in the scenario at time step."""

        list_polygons_collision_at_time_step = self.list_polygons_collision_at_time_step(time_idx)

        return self.rectangle_collides_with_obstacles(rectangle, list_polygons_collision_at_time_step)

    def list_polygons_collision_at_time_step(self, time_step: int):
        list_polygons = []

        list_occupancies = self.scenario_cc.occupancies_at_time_step(time_step)
        for occ in list_occupancies:
            if isinstance(occ.shape, ShapeGroup):
                for shape in occ.shapes:
                    list_polygons.append(shape.shapely_object)

            elif isinstance(occ.shape, Rectangle) or isinstance(occ.shape, Polygon):
                list_polygons.append(occ.shape.shapely_object)

        return list_polygons

    @staticmethod
    def rectangle_collides_with_obstacles(rectangle: ReachPolygon, list_polygons: List[Polygon]):
        for polygon in list_polygons:
            if rectangle.intersects(polygon):
                return True

        return False
