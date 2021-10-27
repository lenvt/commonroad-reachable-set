import os
import time
from commonroad_reachset.data_structure.configuration_builder import ConfigurationBuilder
from commonroad_reachset.data_structure.reach.reachable_set_interface import ReachableSetInterface
from commonroad_reachset.utility import visualization as util_visualization


def main():
    # ==== Entry point of reachable set computation
    # specify the name of scenario
    # name_scenario = "DEU_Test-1_1_T-1"
    # name_scenario = "ARG_Carcarana-1_1_T-1"
    name_scenario = "ZAM_Tjunction-1_313_T-1"
    # build configuration
    config = ConfigurationBuilder.build_configuration(name_scenario)

    # ==== construct reachability interface and compute reachable sets
    reach_interface = ReachableSetInterface(config)
    reach_interface.compute_reachable_sets()

    # plot computation results
    util_visualization.plot_scenario_with_reachable_sets(reach_interface, as_svg=False)


if __name__ == "__main__":
    main()