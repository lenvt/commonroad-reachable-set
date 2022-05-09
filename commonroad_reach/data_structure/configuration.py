import logging

logger = logging.getLogger(__name__)

import numpy as np
from typing import Optional, Union

import commonroad_reach.pycrreach as reach
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.scenario.scenario import Scenario
from commonroad.common.solution import VehicleType
from commonroad_dc.feasibility.vehicle_dynamics import VehicleParameterMapping
from commonroad_route_planner.route_planner import RoutePlanner
from omegaconf import ListConfig, DictConfig

from commonroad_reach.utility import configuration as util_configuration


class Configuration:
    """Class holding all relevant configurations"""

    def __init__(self, config: Union[ListConfig, DictConfig]):
        self.name_scenario = config.general.name_scenario
        self.scenario: Optional[Scenario] = None
        self.planning_problem: Optional[PlanningProblem] = None

        self.general: GeneralConfiguration = GeneralConfiguration(config)
        self.vehicle: VehicleConfiguration = VehicleConfiguration(config)
        self.planning: PlanningConfiguration = PlanningConfiguration(config)
        self.reachable_set: ReachableSetConfiguration = ReachableSetConfiguration(config)
        self.debug: DebugConfiguration = DebugConfiguration(config)

    def complete_configuration(self, scenario: Scenario, planning_problem: PlanningProblem):
        self.scenario = scenario
        self.planning_problem = planning_problem

        self.vehicle.id_type_vehicle = planning_problem.planning_problem_id
        self.planning.complete_configuration(self)

    def print_configuration_summary(self):
        if self.planning.coordinate_system == "CART":
            CLCS = "cartesian"
        elif self.planning.coordinate_system == "CVLN":
            CLCS = "curvilinear"
        else:
            CLCS = "undefined"

        if self.reachable_set.mode_computation == 1:
            mode_computation = "polytopic, python backend"
        elif self.reachable_set.mode_computation == 2:
            mode_computation = "polytopic, c++ backend"
        elif self.reachable_set.mode_computation == 3:
            mode_computation = "graph-based (online)"
        elif self.reachable_set.mode_computation == 4:
            mode_computation = "graph-based (offline)"
        else:
            mode_computation = "undefined"

        if self.reachable_set.mode_repartition == 1:
            mode_repartition = "repartition, collision check"
        elif self.reachable_set.mode_repartition == 2:
            mode_repartition = "collision check, repartition"
        elif self.reachable_set.mode_repartition == 3:
            mode_repartition = "repartition, collision check, then repartition"
        else:
            mode_repartition = "undefined"

        if self.reachable_set.mode_inflation == 1:
            mode_inflation = "inscribed circle"
        elif self.reachable_set.mode_inflation == 2:
            mode_inflation = "circumscribed circle"
        else:
            mode_inflation = "undefined"

        string = "# ===== Configuration Summary ===== #\n"
        string += f"# {self.scenario.scenario_id}\n"
        string += "# Planning:\n"
        string += f"# \tdt: {self.planning.dt}\n"
        string += f"# \ttime steps: {self.planning.steps_computation}\n"
        string += f"# \tcoordinate system: {CLCS}\n"
        string += "# Reachable set:\n"
        string += f"# \tcomputation mode: {mode_computation}\n"
        string += f"# \trepartition mode: {mode_repartition}\n"
        string += f"# \tinflation mode: {mode_inflation}\n"
        string += f"# \tgrid size: {self.reachable_set.size_grid}\n"
        string += f"# \tsplit radius: {self.reachable_set.radius_terminal_split}\n"
        string += f"# \tprune: {self.reachable_set.prune_nodes_not_reaching_final_step}\n"
        string += "# ================================= #"

        print(string)
        for line in string.split("\n"):
            logger.info(line)

    def convert_to_cpp_configuration(self) -> reach.Configuration:
        """Converts to configuration that is readable by the C++ binding code."""
        config = reach.Configuration()

        config.general.name_scenario = self.name_scenario
        config.general.path_scenarios = self.general.path_scenarios

        config.vehicle.ego.id_type_vehicle = self.vehicle.ego.id_type_vehicle
        config.vehicle.ego.length = self.vehicle.ego.length
        config.vehicle.ego.width = self.vehicle.ego.width
        config.vehicle.ego.v_lon_min = self.vehicle.ego.v_lon_min
        config.vehicle.ego.v_lon_max = self.vehicle.ego.v_lon_max
        config.vehicle.ego.v_lat_min = self.vehicle.ego.v_lat_min
        config.vehicle.ego.v_lat_max = self.vehicle.ego.v_lat_max
        config.vehicle.ego.a_lon_min = self.vehicle.ego.a_lon_min
        config.vehicle.ego.a_lon_max = self.vehicle.ego.a_lon_max
        config.vehicle.ego.a_lat_min = self.vehicle.ego.a_lat_min
        config.vehicle.ego.a_lat_max = self.vehicle.ego.a_lat_max
        config.vehicle.ego.a_max = self.vehicle.ego.a_max
        config.vehicle.ego.radius_disc = self.vehicle.ego.radius_disc
        config.vehicle.ego.wheelbase = self.vehicle.ego.wheelbase

        config.vehicle.other.id_type_vehicle = self.vehicle.other.id_type_vehicle
        config.vehicle.other.length = self.vehicle.other.length
        config.vehicle.other.width = self.vehicle.other.width
        config.vehicle.other.v_lon_min = self.vehicle.other.v_lon_min
        config.vehicle.other.v_lon_max = self.vehicle.other.v_lon_max
        config.vehicle.other.v_lat_min = self.vehicle.other.v_lat_min
        config.vehicle.other.v_lat_max = self.vehicle.other.v_lat_max
        config.vehicle.other.a_lon_min = self.vehicle.other.a_lon_min
        config.vehicle.other.a_lon_max = self.vehicle.other.a_lon_max
        config.vehicle.other.a_lat_min = self.vehicle.other.a_lat_min
        config.vehicle.other.a_lat_max = self.vehicle.other.a_lat_max
        config.vehicle.other.a_max = self.vehicle.other.a_max
        config.vehicle.other.radius_disc = self.vehicle.other.radius_disc
        config.vehicle.other.wheelbase = self.vehicle.other.wheelbase

        config.planning.dt = self.planning.dt
        config.planning.step_start = self.planning.step_start
        config.planning.steps_computation = self.planning.steps_computation
        config.planning.p_lon_initial = self.planning.p_lon_initial
        config.planning.p_lat_initial = self.planning.p_lat_initial
        config.planning.uncertainty_p_lon = self.planning.uncertainty_p_lon
        config.planning.uncertainty_p_lat = self.planning.uncertainty_p_lat
        config.planning.v_lon_initial = self.planning.v_lon_initial
        config.planning.v_lat_initial = self.planning.v_lat_initial
        config.planning.uncertainty_v_lon = self.planning.uncertainty_v_lon
        config.planning.uncertainty_v_lat = self.planning.uncertainty_v_lat
        config.planning.step_start = self.planning.step_initial
        config.planning.id_lanelet_initial = self.planning.id_lanelet_initial

        if self.planning.coordinate_system == "CART":
            config.planning.coordinate_system = reach.CoordinateSystem.CARTESIAN

        else:
            config.planning.coordinate_system = reach.CoordinateSystem.CURVILINEAR

        if self.planning.reference_point == "REAR":
            config.planning.reference_point = reach.ReferencePoint.REAR

        else:
            config.planning.reference_point = reach.ReferencePoint.CENTER

        config.reachable_set.mode_repartition = self.reachable_set.mode_repartition
        config.reachable_set.size_grid = self.reachable_set.size_grid
        config.reachable_set.size_grid_2nd = self.reachable_set.size_grid_2nd
        config.reachable_set.radius_terminal_split = self.reachable_set.radius_terminal_split
        config.reachable_set.num_threads = self.reachable_set.num_threads
        config.reachable_set.prune_nodes = self.reachable_set.prune_nodes_not_reaching_final_step

        return config


class GeneralConfiguration:
    def __init__(self, config: Union[ListConfig, DictConfig]):
        config_relevant = config.general
        name_scenario = config_relevant.name_scenario

        self.path_scenarios = config_relevant.path_scenarios
        self.path_scenario = config_relevant.path_scenarios + name_scenario + ".xml"
        self.path_output = config_relevant.path_output + name_scenario + "/"
        self.path_logs = config_relevant.path_logs
        self.path_offline_data = config_relevant.path_offline_data


class VehicleConfiguration:
    class Ego:
        def __init__(self, config: Union[ListConfig, DictConfig]):
            config_relevant = config.vehicle.ego

            self.id_type_vehicle = config_relevant.id_type_vehicle
            self.id_vehicle = None

            #load vehicle parameters according to id_type_vehicle
            vehicle_parameters = VehicleParameterMapping.from_vehicle_type(VehicleType(self.id_type_vehicle))

            self.length = vehicle_parameters.l
            self.width = vehicle_parameters.w

            self.v_lon_min = vehicle_parameters.longitudinal.v_min
            self.v_lon_max = vehicle_parameters.longitudinal.v_max
            self.v_lat_min = config_relevant.v_lat_min # TODO:extract from vehicle parameters?
            self.v_lat_max = config_relevant.v_lat_max
            self.v_max = vehicle_parameters.longitudinal.v_max #config_relevant.v_max

            self.a_lon_max = vehicle_parameters.longitudinal.a_max # config_relevant.a_lon_max
            self.a_lon_min = -vehicle_parameters.longitudinal.a_max
            self.a_lat_max = vehicle_parameters.longitudinal.a_max
            self.a_lat_min = -vehicle_parameters.longitudinal.a_max
            self.a_max = vehicle_parameters.longitudinal.a_max

            self.wheelbase = vehicle_parameters.a + vehicle_parameters.b

            # overwrite if there exists parameter defined in config file
            for key, value in config_relevant.items():
                setattr(self, key, value)
            self.radius_disc, self.wheelbase = \
                util_configuration.compute_disc_radius_and_wheelbase(self.length, self.width, wheelbase=self.wheelbase)
            self.radius_inflation = util_configuration.compute_inflation_radius(config.reachable_set.mode_inflation,
                                                                                self.length, self.width)

    class Other:
        def __init__(self, config: Union[ListConfig, DictConfig]):
            config_relevant = config.vehicle.other

            self.id_type_vehicle = config_relevant.id_type_vehicle
            self.id_vehicle = None

            vehicle_parameters = VehicleParameterMapping.from_vehicle_type(VehicleType(self.id_type_vehicle))

            self.length = vehicle_parameters.l
            self.width = vehicle_parameters.w

            self.v_lon_min = vehicle_parameters.longitudinal.v_min
            self.v_lon_max = vehicle_parameters.longitudinal.v_max
            self.v_lat_min = config_relevant.v_lat_min # TODO:extract from vehicle parameters?
            self.v_lat_max = config_relevant.v_lat_max
            self.v_max = vehicle_parameters.longitudinal.v_max #config_relevant.v_max

            self.a_lon_max = vehicle_parameters.longitudinal.a_max # config_relevant.a_lon_max
            self.a_lon_min = -vehicle_parameters.longitudinal.a_max
            self.a_lat_max = vehicle_parameters.longitudinal.a_max
            self.a_lat_min = -vehicle_parameters.longitudinal.a_max
            self.a_max = vehicle_parameters.longitudinal.a_max

            self.wheelbase = vehicle_parameters.a + vehicle_parameters.b
            self.radius_disc, self.wheelbase = \
                util_configuration.compute_disc_radius_and_wheelbase(self.length, self.width, wheelbase=self.wheelbase)

    def __init__(self, config: Union[ListConfig, DictConfig]):
        self.ego = VehicleConfiguration.Ego(config)
        self.other = VehicleConfiguration.Other(config)


class PlanningConfiguration:
    def __init__(self, config: Union[ListConfig, DictConfig]):
        config_relevant = config.planning

        assert len(str(config_relevant.dt).split(".")[1]) == 1, \
            f"value of dt should be a multiple of 0.1, got {config_relevant.dt}."
        self.dt = config_relevant.dt
        self.step_start = config_relevant.step_start
        self.steps_computation = config_relevant.steps_computation

        self.p_lon_initial = None
        self.p_lat_initial = None
        self.uncertainty_p_lon = config_relevant.uncertainty_p_lon
        self.uncertainty_p_lat = config_relevant.uncertainty_p_lat

        self.v_lon_initial = None
        self.v_lat_initial = None
        self.uncertainty_v_lon = config_relevant.uncertainty_v_lon
        self.uncertainty_v_lat = config_relevant.uncertainty_v_lat

        self.o_initial = 0

        # related to specific planning problem
        self.step_initial = None
        self.id_lanelet_initial = 0
        self.route = None
        self.reference_path = None
        self.lanelet_network = None

        self.coordinate_system = config_relevant.coordinate_system
        self.reference_point = config_relevant.reference_point
        self.CLCS = None

    def complete_configuration(self, config: Configuration):
        scenario = config.scenario
        planning_problem = config.planning_problem

        self.lanelet_network = scenario.lanelet_network
        self.step_initial = planning_problem.initial_state.time_step

        if self.coordinate_system == "CART":
            p_initial, v_initial, o_initial = util_configuration.compute_initial_state_cart(config)
            self.p_lon_initial, self.p_lat_initial = p_initial
            self.v_lon_initial, self.v_lat_initial = v_initial
            self.o_initial = o_initial

        elif self.coordinate_system == "CVLN":
            # plans a route from the initial lanelet to the goal lanelet
            route_planner = RoutePlanner(scenario, planning_problem)
            candidate_holder = route_planner.plan_routes()
            route = candidate_holder.retrieve_first_route()

            self.route = route
            self.reference_path = route.reference_path
            self.id_lanelet_initial = route.list_ids_lanelets[0]

            self.CLCS = util_configuration.create_curvilinear_coordinate_system(self.reference_path)
            p_initial, v_initial = util_configuration.compute_initial_state_cvln(config)

            self.p_lon_initial, self.p_lat_initial = p_initial
            self.v_lon_initial, self.v_lat_initial = v_initial

    @property
    def p_lon_lat_initial(self):
        return np.array([self.p_lon_initial, self.p_lat_initial])

    @property
    def v_lon_lat_initial(self):
        return np.array([self.v_lon_initial, self.v_lat_initial])


class ReachableSetConfiguration:
    def __init__(self, config: Union[ListConfig, DictConfig]):
        config_relevant = config.reachable_set

        self.mode_computation = config_relevant.mode_computation
        self.mode_repartition = config_relevant.mode_repartition
        self.mode_inflation = config_relevant.mode_inflation
        self.consider_traffic = config_relevant.consider_traffic

        self.size_grid = config_relevant.size_grid
        self.size_grid_2nd = config_relevant.size_grid_2nd
        self.radius_terminal_split = config_relevant.radius_terminal_split
        self.prune_nodes_not_reaching_final_step = config_relevant.prune_nodes_not_reaching_final_step

        self.name_pickle_offline = config_relevant.name_pickle_offline
        self.n_multi_steps = config_relevant.n_multi_steps

        self.num_threads = config_relevant.num_threads


class DebugConfiguration:
    def __init__(self, config: Union[ListConfig, DictConfig]):
        config_relevant = config.debug

        self.save_plots = config_relevant.save_plots
        self.save_config = config_relevant.save_config
        self.draw_ref_path = config_relevant.draw_ref_path
        self.draw_planning_problem = config_relevant.draw_planning_problem
        self.draw_icons = config_relevant.draw_icons
        self.plot_limits = config_relevant.plot_limits
        self.plot_azimuth = config_relevant.plot_azimuth
        self.plot_elevation = config_relevant.plot_elevation
        self.ax_distance = config_relevant.ax_distance
