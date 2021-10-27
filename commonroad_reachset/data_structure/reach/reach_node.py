import copy

from commonroad_reachset.data_structure.reach.reach_polygon import ReachPolygon


class ReachNode:
    """Node within the reachability graph.

    A node is constructed from a base set and has a time step, an ID, and holds a list of parent nodes
    and child nodes. Each base set is a Cartesian product of polygon_lon and polygon_lat. In Curvilinear
    coordinate system, polygon_lon is a polygon in the longitudinal p-v domain, and polygon_lat is a
    polygon in the lateral p-v domain; In Cartesian coordinate system, they represent polygons in the
    x-v and y-v domains, respectively. It stores the indices of all parent base sets from the previous time
    step from which the current base set is reachable.
    """
    cnt_id = 0

    def __init__(self, polygon_lon, polygon_lat, time_step: int = -1):
        self._polygon_lon = polygon_lon
        self._polygon_lat = polygon_lat
        self._bounds_lon = polygon_lon.bounds if polygon_lon else None
        self._bounds_lat = polygon_lat.bounds if polygon_lat else None

        self.id = ReachNode.cnt_id
        ReachNode.cnt_id += 1
        self.time_step = time_step
        self.list_nodes_parent = list()
        self.list_nodes_child = list()

        # the node from which the current node is propagated
        self.source_propagation = None

    def __repr__(self):
        return f"ReachNode(time_step={self.time_step}, id={self.id})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ReachNode):
            return self.id == other.id

        else:
            return False

    @property
    def polygon_lon(self) -> ReachPolygon:
        return self._polygon_lon

    @polygon_lon.setter
    def polygon_lon(self, polygon):
        self._polygon_lon = polygon

    @property
    def polygon_lat(self) -> ReachPolygon:
        return self._polygon_lat

    @polygon_lat.setter
    def polygon_lat(self, polygon):
        self._polygon_lat = polygon

    @property
    def p_lon_min(self):
        """Minimum longitudinal position."""
        return self._bounds_lon[0]

    @property
    def p_lon_max(self):
        """Maximum longitudinal position."""
        return self._bounds_lon[2]

    @property
    def v_lon_min(self):
        """Minimum longitudinal velocity."""
        return self._bounds_lon[1]

    @property
    def v_lon_max(self):
        """Maximum longitudinal velocity."""
        return self._bounds_lon[3]

    @property
    def p_lat_min(self):
        """Minimum lateral position."""
        return self._bounds_lat[0]

    @property
    def p_lat_max(self):
        """Maximum lateral position."""
        return self._bounds_lat[2]

    @property
    def v_lat_min(self):
        """Minimum lateral velocity."""
        return self._bounds_lat[1]

    @property
    def v_lat_max(self):
        """Maximum lateral velocity."""
        return self._bounds_lat[3]

    @property
    def p_x_min(self):
        return self.p_lon_min

    @property
    def p_x_max(self):
        return self.p_lon_max

    @property
    def v_x_min(self):
        return self.v_lon_min

    @property
    def v_x_max(self):
        return self.v_lon_max

    @property
    def p_y_min(self):
        return self.p_lat_min

    @property
    def p_y_max(self):
        return self.p_lat_max

    @property
    def v_y_min(self):
        return self.v_lat_min

    @property
    def v_y_max(self):
        return self.v_lat_max

    @property
    def position_rectangle(self):
        """Base set projected onto the position domain."""
        tuple_vertices_rectangle = (self.p_lon_min, self.p_lat_min, self.p_lon_max, self.p_lat_max)

        return ReachPolygon.from_rectangle_vertices(*tuple_vertices_rectangle)

    def clone(self):
        node_clone = ReachNode(self.polygon_lon.clone(convexify=False),
                               self.polygon_lat.clone(convexify=False),
                               self.time_step)
        node_clone.list_nodes_parent = copy.deepcopy(self.list_nodes_parent)
        node_clone.list_nodes_child = copy.deepcopy(self.list_nodes_child)
        node_clone.source_propagation = self.source_propagation

        return node_clone

    @classmethod
    def reset_class_id_counter(cls):
        cls.cnt_id = 0

    def add_parent_node(self, node_parent: "ReachNode") -> bool:
        """Adds a new parent node

        Args:
            node_parent (ReachNode): parent node to be added
        """
        if node_parent not in self.list_nodes_parent:
            self.list_nodes_parent.append(node_parent)
            return True

        return False

    def remove_parent_node(self, node_parent: "ReachNode") -> bool:
        """Removes a parent node

        Args:
            node_parent (ReachNode): parent node to be removed
        """
        if node_parent in self.list_nodes_parent:
            self.list_nodes_parent.remove(node_parent)
            return True

        return False

    def add_child_node(self, node_child: "ReachNode") -> bool:
        """Adds a new child node

        Args:
            node_child (ReachNode): child node to be added
        """
        if node_child not in self.list_nodes_child:
            self.list_nodes_child.append(node_child)
            return True

        return False

    def remove_child_node(self, node_child: "ReachNode") -> bool:
        """Removes a child node

        Args:
            node_child (ReachNode): child node to be removed
        """
        if node_child in self.list_nodes_child:
            self.list_nodes_child.remove(node_child)
            return True

        return False

    def intersect_in_position_domain(self, p_lon_min, p_lat_min, p_lon_max, p_lat_max):
        """Intersects with the given rectangle in position domain"""
        self._polygon_lon = self.polygon_lon.intersect_halfspace(1, 0, p_lon_max)
        self._polygon_lon = self.polygon_lon.intersect_halfspace(-1, 0, -p_lon_min)
        self._polygon_lat = self.polygon_lat.intersect_halfspace(1, 0, p_lat_max)
        self._polygon_lat = self.polygon_lat.intersect_halfspace(-1, 0, -p_lat_min)

    def intersect_in_velocity_domain(self, v_lon_min, v_lat_min, v_lon_max, v_lat_max):
        """Intersects with the given v-values in velocity domain """
        self._polygon_lon = self.polygon_lon.intersect_halfspace(0, 1, v_lon_max)
        self._polygon_lon = self.polygon_lon.intersect_halfspace(0, -1, -v_lon_min)
        self._polygon_lat = self.polygon_lat.intersect_halfspace(0, 1, v_lat_max)
        self._polygon_lat = self.polygon_lat.intersect_halfspace(0, -1, -v_lat_min)