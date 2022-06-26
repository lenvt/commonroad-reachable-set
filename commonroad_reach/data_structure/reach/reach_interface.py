import logging
import time
from typing import List

from commonroad.geometry.shape import Shape

from commonroad_reach.data_structure.configuration import Configuration
from commonroad_reach.data_structure.driving_corridor import DrivingCorridor
from commonroad_reach.data_structure.driving_corridor_extractor import DrivingCorridorExtractor
from commonroad_reach.data_structure.reach.reach_set import ReachableSet
import commonroad_reach.utility.logger as util_logger

logger = logging.getLogger(__name__)


class ReachableSetInterface:
    """Interface for reachable set computation."""

    def __init__(self, config: Configuration):
        self.config = None
        self._reach = None
        self._reachable_set_computed = False
        self._driving_corridor_extractor = None

        self.reset(config)

        util_logger.print_and_log_debug(logger, "Reachable set interface initialized.")

    @property
    def step_start(self):
        return self._reach.step_start

    @property
    def step_end(self):
        return self._reach.step_end

    @property
    def drivable_area(self):
        return self._reach.drivable_area

    @property
    def reachable_set(self):
        return self._reach.reachable_set

    def reset(self, config: Configuration):
        """Resets configuration of the interface."""
        self.config = config
        self._reach = None
        self._reachable_set_computed = False
        self._driving_corridor_extractor = None

        if self.config.reachable_set.mode_computation in [1, 2, 3, 4]:
            self._reach = ReachableSet.instantiate(self.config)

        else:
            message = "Specified mode ID is invalid."
            util_logger.print_and_log_error(logger, message)
            raise Exception(message)

    def drivable_area_at_step(self, step: int):
        if not self._reachable_set_computed and step != 0:
            util_logger.print_and_log_warning(logger, "Reachable set is not computed, retrieving drivable area failed.")
            return []

        else:
            return self._reach.drivable_area_at_step(step)

    def reachable_set_at_step(self, step: int):
        if not self._reachable_set_computed and step != 0:
            util_logger.print_and_log_warning(logger, "Reachable set is not computed, retrieving reachable set failed.")
            return []

        else:
            return self._reach.reachable_set_at_step(step)

    def compute_reachable_sets(self, step_start: int = 1, step_end: int = 0):
        util_logger.print_and_log_info(logger, "* Computing reachable sets...")

        if not self._reach:
            util_logger.print_and_log_warning(logger, "Reachable set is not initialized, aborting computation.")
            return None

        step_end = step_end if step_end else self.step_end

        if not (0 < step_start < step_end):
            util_logger.print_and_log_warning(logger, "Time steps for computation are invalid, aborting computation.")
            return None

        time_start = time.time()
        self._reach.compute(step_start, step_end)
        self._reachable_set_computed = True
        time_computation = time.time() - time_start

        util_logger.print_and_log_info(logger, f"\tTook: \t{time_computation:.3f}s")

    def extract_driving_corridors(self, to_goal_region: bool = False, shape_terminal: Shape = None,
                                  is_cartesian_shape: bool = True, corridor_lon: DrivingCorridor = None,
                                  list_p_lon: List[float] = None) -> List[DrivingCorridor]:
        """Extracts driving corridors within the reachable sets."""
        if not self.reachable_set:
            util_logger.print_and_log_warning(logger, "Reachable sets are empty! "
                                                      "Compute reachable sets before extracting driving corridors.")
            return []

        if not self._driving_corridor_extractor:
            self._driving_corridor_extractor = DrivingCorridorExtractor(self.reachable_set, self.config)

        util_logger.print_and_log_info(logger, f"* Extracting driving corridors...")
        time_start = time.time()
        list_corridors = self._driving_corridor_extractor.extract(to_goal_region, shape_terminal, is_cartesian_shape,
                                                                  corridor_lon, list_p_lon)
        time_computation = time.time() - time_start
        util_logger.print_and_log_info(logger, f"\tTook: \t{time_computation:.3f}s")

        return list_corridors
