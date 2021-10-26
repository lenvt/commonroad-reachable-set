#include <iostream>
#include <chrono>
#include <pybind11/embed.h>
#include <pybind11/stl.h>
#include <pybind11/eigen.h>
#include <pybind11/numpy.h>

#include "collision/collision_checker.h"
#include "reachset/common/reachable_set_interface.hpp"
#include "reachset/common/collision_checker.hpp"
#include "geometry/curvilinear_coordinate_system.h"
#include "reachset/utility/miscellaneous.hpp"

using namespace reach;
using std::chrono::high_resolution_clock;
using std::chrono::duration_cast;
using std::chrono::milliseconds;
namespace py = pybind11;

using CollisionCheckerPtr = collision::CollisionCheckerPtr;

int main() {
    // start the python interpreter and keep it alive
    py::scoped_interpreter python{};

    // ======== settings
    //string name_scenario = "DEU_Test-1_1_T-1";
    //string name_scenario = "USA_US101-15_1_T-1";
    //string name_scenario = "ARG_Carcarana-1_1_T-1";
    string name_scenario = "ZAM_Tjunction-1_313_T-1";
    string path_root = "/home/edmond/Softwares/commonroad/commonroad-reachable-set/";

    // append path to interpreter
    py::module_ sys = py::module_::import("sys");
    sys.attr("path").attr("append")(path_root);

    // ======== configuration via python ConfigurationBuilder
    auto cls_ConfigurationBuilder_py =
            py::module_::import("commonroad_reachset.common.configuration_builder").attr("ConfigurationBuilder");
    cls_ConfigurationBuilder_py.attr("set_root_path")(path_root);
    auto obj_config_py = cls_ConfigurationBuilder_py.attr("build_configuration")(name_scenario);
    auto config = obj_config_py.attr("convert_to_cpp_configuration")().cast<ConfigurationPtr>();

    // ======== CurvilinearCoordinateSystem
    auto CLCS = make_shared<geometry::CurvilinearCoordinateSystem>(
            obj_config_py.attr("planning").attr("reference_path").cast<geometry::EigenPolyline>(),
            25.0, 0.1);

    // ======== collision checker via python collision checker
    auto cls_CollisionChecker_py = py::module_::import("commonroad_reachset.common.collision_checker").attr(
            "CollisionChecker");
    auto obj_collision_checker_py = cls_CollisionChecker_py(obj_config_py);
    auto collision_checker = create_curvilinear_collision_checker(
            obj_collision_checker_py.attr("list_vertices_polygons_static").cast<vector<Polyline>>(),
            obj_collision_checker_py.attr(
                    "dict_time_step_to_list_vertices_polygons_dynamic").cast<map<int, vector<Polyline>>>(),
            CLCS,
            obj_config_py.attr("vehicle").attr("ego").attr("radius_disc").cast<double>(),
            4);

    // ======== ReachableSetInterface
    auto reach_interface = ReachableSetInterface::continuous(config, collision_checker);

    auto start = high_resolution_clock::now();
    reach_interface.compute();
    auto end = high_resolution_clock::now();
    cout << "Computation time: " << duration_cast<milliseconds>(end - start).count() << "ms" << endl;

    // ======== visualization of results
    auto utils_visualization = py::module_::import("commonroad_reachset.common.utility.visualization");
    utils_visualization.attr("draw_scenario_with_reach_cpp")(obj_config_py, reach_interface,
                                                             py::arg("save_gif") = true,
                                                             py::arg("save_fig") = false);

    cout << "Done." << endl;

    return 0;
}