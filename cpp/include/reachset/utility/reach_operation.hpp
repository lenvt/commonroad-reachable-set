#pragma once

#include "shared_include.hpp"
#include "reachset/data_structure/reach/reach_polygon2.hpp"
#include "reachset/data_structure/reach/reach_node.hpp"
#include "reachset/data_structure/configuration.hpp"
#include "collision/collision_checker.h"

using CollisionCheckerPtr = collision::CollisionCheckerPtr;
using RectangleAABBPtr = collision::RectangleAABBPtr;

namespace reach {
/// Creates the zero-state polygon of the system.
/// @param dt time duration (one step)
/// @param a_min minimum acceleration (maximum deceleration)
/// @param a_max maximum acceleration
/// @return pointer to zero-state polygon
ReachPolygon2Ptr create_zero_state_polygon(double const& dt, double const& a_min, double const& a_max);

/// Creates a box that has the absolute min/max reachable position and velocity as its bounds.
/// @param dt time duration (one step)
/// @param a_min minimum acceleration (maximum deceleration)
/// @param a_max maximum acceleration
/// @return pointer to bounding box
ReachPolygon2Ptr create_bounding_box(double const& dt, double const& a_min, double const& a_max);

/// Computes the coefficients of halfspaces to be intersected.
/// @param dt time duration (one step)
/// @param a_min minimum acceleration (maximum deceleration)
/// @param a_max maximum acceleration
/// @param gamma coefficient of switching time (0~1)
/// @return tuples of coefficients of halfspaces corresponding to upper and lower bounds
std::tuple<std::tuple<double, double, double>, std::tuple<double, double, double>>
compute_halfspace_coefficients(double const& dt, double const& a_min, double const& a_max, double const& gamma);

/// Returns tuple of vertices for the position rectangle construction.
std::tuple<double, double, double, double>
generate_tuple_vertices_position_rectangle_initial(ConfigurationPtr const& config);

/// Returns tuples of vertices for the initial polygons in two directions.
std::tuple<std::tuple<double, double, double, double>, std::tuple<double, double, double, double>>
generate_tuples_vertices_polygons_initial(ConfigurationPtr const& config);

/// Propagates the input polygon according to the system dynamic.
/// @param polygon polygon to be propagated
/// @param polygon_zero_state zero-state polygon (precomputed)
/// @param dt time duration
/// @param v_min minimum velocity
/// @param v_max maximum velocity
/// @return pointer to the propagated polygon
ReachPolygon2Ptr propagate_polygon(ReachPolygon2Ptr const& polygon, ReachPolygon2Ptr& polygon_zero_state,
                                   double const& dt, double const& v_min, double const& v_max);

/// Returns a list of rectangles in the position domain.
std::vector<ReachPolygon2Ptr>
project_base_sets_to_position_domain(std::vector<ReachNodePtr> const& vec_base_sets_propagated);

/// Repartitions the input vector of position rectangles.
/// @param vec_rectangles vector of position rectangles to be repartitioned
/// @param size_grid grid size during discretization
/// @return vector of pointers to repartitioned position rectangles
std::vector<ReachPolygon2Ptr>
create_repartitioned_rectangles(std::vector<ReachPolygon2Ptr> const& vec_rectangles, double const& size_grid);

/// Returns minimum lon/lat positions of the given list of rectangles.
std::tuple<double, double> compute_minimum_positions_of_rectangles(std::vector<ReachPolygon2Ptr> const& vec_rectangles);

/// Discretizes the given list of rectangles.
std::vector<ReachPolygon2Ptr> discretize_rectangles(std::vector<ReachPolygon2Ptr> const& vec_rectangles,
                                                    std::tuple<double, double> const& tuple_p_min_rectangles,
                                                    double const& size_grid);

/// Returns a list of repartitioned rectangles.
std::vector<ReachPolygon2Ptr> repartition_rectangle(std::vector<ReachPolygon2Ptr> const& vec_rectangles);

/// Restores previously discretized rectangles back to undiscretized ones.
std::vector<ReachPolygon2Ptr> undiscretize_rectangles(std::vector<ReachPolygon2Ptr> const& vec_rectangles,
                                                      std::tuple<double, double> const& tuple_p_min_rectangles,
                                                      double const& size_grid);

/// Check collision status of the rectangles and split them if colliding.
std::vector<ReachPolygon2Ptr> check_collision_and_split_rectangles(int const& time_step,
                                                                   CollisionCheckerPtr const& collision_checker,
                                                                   std::vector<ReachPolygon2Ptr> const& vec_rectangles,
                                                                   double const& radius_terminal_split,
                                                                   int const& num_threads);

/// Returns the bounding box of polygons
tuple<double, double, double, double>
obtain_extremum_coordinates_of_polygons(vector<ReachPolygon2Ptr> const& vec_polygons);

collision::RectangleAABB obtain_bounding_box_of_rectangles(std::vector<ReachPolygon2Ptr> const& vec_rectangles);

/// Converts a ReachPolygon to axis-aligned bounding box.
RectangleAABBPtr convert_reach_polygon_to_collision_aabb(ReachPolygon2Ptr const& rectangle);

/// Converts an axis-aligned bounding box to a ReachPolygon.
vector<ReachPolygon2Ptr> convert_collision_aabbs_to_reach_polygons(vector<RectangleAABBPtr> const& vec_rectangles);

/// Recursively creates a list of collision-free rectangles.
std::vector<RectangleAABBPtr> create_collision_free_rectangles(CollisionCheckerPtr const& collision_checker,
                                                               RectangleAABBPtr const& rectangle,
                                                               double const& radius_terminal_squared);

inline double diagonal_squared(RectangleAABBPtr const& rectangle) {
    return 4 * pow(rectangle->r_x(), 2) + 4 * pow(rectangle->r_y(), 2);
}

/// Returns two rectangles each of which is a half of the initial rectangle.
std::tuple<RectangleAABBPtr, RectangleAABBPtr> split_rectangle_into_two(RectangleAABBPtr const& rectangle);

/// Creates adapted base sets from the computed drivable area.
///The nodes of the reachable set of the current time step is later created from these adapted base sets.
std::vector<ReachNodePtr> adapt_base_sets_to_drivable_area(std::vector<ReachPolygon2Ptr> const& drivable_area,
                                                           std::vector<ReachNodePtr> const& vec_base_sets_propagated,
                                                           int const& num_threads);

/// Creates a map indicating the adjacency (overlapping) status of two lists of rectangles.
std::unordered_map<int, vector<int>> create_adjacency_map(std::vector<ReachPolygon2Ptr> const& vec_rectangles_a,
                                                          std::vector<ReachPolygon2Ptr> const& vec_rectangles_b);

/// Returns adapted base set created from a rectangle of the drivable area.
ReachNodePtr adapt_base_set_to_drivable_area(ReachPolygon2Ptr const& rectangle_drivable_area,
                                             std::vector<ReachNodePtr> const& vec_base_sets_propagated,
                                             std::vector<int> const& vec_idx_base_sets_adjacent);

/// Creates list of reachable set nodes of the current time step (continuous reachability analysis).
std::vector<ReachNodePtr>
create_reachable_set_nodes(int const& time_step, std::vector<ReachNodePtr> const& vec_base_sets_adapted,
                           int const& num_threads);
}
