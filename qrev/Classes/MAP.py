# from profilehooks import profile
import copy
import math
from datetime import datetime

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
import simplekml
import utm
# from profilehooks import profile
from scipy.stats import linregress
from scipy.interpolate import griddata
from scipy.optimize.minpack import curve_fit

from qrev import __qrev_version__
from qrev.MiscLibs.abba_2d_interpolation import abba_idw_interpolation
from qrev.MiscLibs.common_functions import cart2pol, pol2cart, nan_greater, \
    sfrnd


# Todo add ability to specify flow direction like in AdvGraph


class MAP(object):
    """Multi-transect Averaged Profile (MAP) generates an average profile of selected transects.

    Attributes
    ----------
    auto_node_horz: float
        Minimum horizontal node size.
    auto_node_vert: float
        Minimum vertical node size.
    slope: float
        Slope of the average cross-section
    intercept: float
        Intercept of the average cross-section
    x_raw_coordinates: np.list(np.array(float))
        East distance from left bank for each selected transect
    y_raw_coordinates: np.list(np.array(float))
        North distance from left bank for each selected transect
    x_projected: np.list(np.array(float))
        East distance after projection on average cross-section
    y_projected: np.list(np.array(float))
        North distance after projection on average cross-section
    _x_left: float or nd.array(float)
        Edge x-coordinates
    _y_left: float or nd.array(float)
        Edge y-coordinates
    acs_distance: np.list(np.array(float))
        Distance from the left bank on average cross-section
    primary_velocity: np.array(float)
        Primary velocity of each MAP cell
    secondary_velocity: np.array(float)
        Secondary velocity of each MAP cell
    vertical_velocity: np.array(float)
        Vertical velocity of each MAP cell
    streamwise_velocity: np.array(float)
        Streamwise velocity of each MAP cell
    east_velocity: np.array(float)
        Velocity component in East direction
    north_velocity: np.array(float)
        Velocity component in North direction
    transverse_velocity: np.array(float)
        Transverse velocity of each MAP cell
    depths: np.array(float) 1D
        Depths for each MAP vertical
    transverse_mixing_coefficient: np.array(float) 1D
        Transverse mixing coefficient (from Jung 2019) for each MAP vertical
    direction_ens: np.array(float) 1D
        Main direction of each MAP ensemble
    borders_ens: np.array(float) 1D
        Borders of each MAP vertical (distance from left bank)
    x: np.array(float) 1D
        X coordinates from the average cross-section
    y: np.array(float) 1D
        Y coordinates from the average cross-section
    main_depth_layers: np.array(float) 1D
        Borders of each MAP depth layer (distance from surface)
    depth_cells_center: np.array(float)
        Depth of each MAP cell center
    distance_cells_center: np.array(float)
        Distance of each MAP cell center
    cells_area: np.array(float)
        Area of each MAP cell
    data_transects: list
        List of data_dictionary by transect
    n_transects: int
        Number of transects used

    cells_discharge: np.array(float) 1D
        MAP discharge for each cell
    settings: dict
        MAP settings for processing
    total_discharge: float
        MAP total discharge
    """

    def __init__(self):
        """Initialize class and instance variables."""

        self.n_transects = 0
        self.data_transects = None
        self.slope = np.nan  # Slope of the average cross-section
        self.intercept = np.nan  # Intercept of the average cross-section
        self.gps_zone_number = None  # Zone so GPS Coords can be converted
        # from UTM.
        self.gps_zone_letter = None  # Zone so GPS Coords can be converted
        # from UTM.
        self.x_raw_coordinates = (
            []
        )  # East distance from left bank for each selected transect
        self.y_raw_coordinates = (
            []
        )  # North distance from left bank for each selected transect
        # self.lat_gps_coordinate = []  # Latitude coordinates
        # self.lon_gps_coordinate = []  # Longitude coordinates
        self.x_projected = (
            None
            # East distance after projection on average cross-section
        )
        self.y_projected = (
            None
            # North distance after projection on average cross-section
        )

        self.primary_velocity = None  # Primary velocity (ROZ) of each MAP cell
        self.secondary_velocity = None  # Secondary velocity (ROZ) of each MAP cell
        self.vertical_velocity = None  # Vertical velocity of each MAP cell
        self.streamwise_velocity = None  # Streamwise velocity of each MAP cell
        self.transverse_velocity = None  # Transverse velocity of each MAP cell
        self.east_velocity = None  # Velocity component in East direction
        self.north_velocity = None  # Velocity component in North direction
        self.depths = None  # Depths for each MAP vertical
        self.temperature = None  # Temperature for each vertical
        self.transverse_mixing_coefficient = (
            None  # Transverse mixing coefficient from Jung 2019
        )

        self.rssi = None  # RSSI of each MAP cell
        self.count_valid = None  # Count used values to compute each cell
        self.direction_ens = None  # Main direction of each MAP ensemble
        self.borders_ens = (
            None  # Borders of each MAP vertical (distance from left bank)
        )
        self._unit = 1
        self._x_left = 0.0  # Default x position in m
        self._y_left = 0.0  # Default y position in m
        self.x = None  # x coordinates
        self.y = None  # y coordinates
        self.main_depth_layers = (
            None
            # Borders of each MAP depth layer (distance from surface)
        )
        self.depth_cells_center = None  # Depth of each MAP cell center
        self.depth_cells_layers = None  # Depth layers
        self.distance_cells_center = None  # Distance of each MAP cell center
        self.cells_area = np.nan  # Area of each MAP cell
        self.left_geometry = None  # Distance and shape coefficient of left bank
        self.right_geometry = None  # Distance and shape coefficient of right bank

        self.cells_discharge = None  # MAP discharge for each cell
        self.total_discharge = None  # MAP total discharge

        self.auto_node_horz = None
        self.auto_node_vert = None

        self.settings = {
            "ed_map_cell_width": False,
            "ed_map_cell_height": False,
            "cb_map_top_bottom": True,
            "cb_map_edges": True,
            "cb_map_interpolation": True,
            "ed_map_secondary_velocity": False,
            "cb_map_bed_profiles": True,
            "combo_map_data": "Primary velocity",
            "rb_map_contour": True,
            "rb_map_bathymetry": False,
            "rb_map_temp": False,
            "rb_map_stickship": False,
        }

    # @profile
    def populate_data(
        self,
        meas,
        node_horizontal_user=None,
        node_vertical_user=None,
        extrap_option=True,
        edges_option=True,
        n_burn=None,
    ):
        """

        Parameters
        ----------
        meas: Measurement
            Object of Measurement class
        node_horizontal_user: float
            Length of MAP cells, if None a value is selected automatically
        node_vertical_user: float
            Depth of MAP cells, if None a value is selected automatically
        extrap_option: bool
            Indicates if top/bottom extrapolation should be applied
        edges_option: bool
            Indicates if edge extrapolation should be applied
        n_burn: int
            Number of transects which need to detect an information to make it valid
        """

        # Get meas current parameters
        settings = meas.current_settings()

        # Get main data from selected transects
        self.collect_data(meas, settings["NavRef"])

        # Compute coefficients of the average cross-section
        self.compute_coef()

        # Project raw coordinates on average cross-section
        self.project_transect()

        # Compare bathymetry and translate transects on average cross-section if needed
        if settings["NavRef"] != "gga_vel":
            self.translated_transects()

        # Define horizontal and vertical mesh
        self.compute_auto_node_size()
        self.compute_node_size(
            node_horizontal_user,
            node_vertical_user,
        )

        param = {
            "x_velocity": "cell",
            "y_velocity": "cell",
            "vertical_velocity": "cell",
            "rssi": "cell",
            "depths": "ens",
            "temperature": "ens",
            "count": None,
        }

        # Compute transect median velocity on each mesh (North, East and
        # vertical velocities) and depth on each vertical
        data_bin_transects = self.compute_nodes_velocity(param)

        # Compute minimum number of transects required for valid data
        if n_burn is None:
            n_burn = int(1 + self.n_transects / 3)

        # Compute mesh mean value of selected transects
        self.compute_mean(data_bin_transects, n_burn, param)

        if self.east_velocity is not None:
            # Compute primary and secondary velocity according Rozovskii projection
            self.compute_rozovskii(self.east_velocity, self.north_velocity)

            # Interpolate empty values
            # removed as there should be no need to interpolate if using
            # QRev processed data.
            # if interp_option:
            # self.compute_interpolation()

            # Compute top/bottom extrapolation according QRevInt method/exponent
            if extrap_option:
                self.compute_extrap_velocity(settings)

            # Compute edge extrapolation
            if edges_option:
                self.compute_edges(settings)
            else:
                self.left_geometry = None
                self.right_geometry = None

            # Compute discharge
            self.compute_discharge()

        # Compute coordinates
        direction_section = np.arctan2(self.slope, 1)
        if self.left_geometry is not None:
            distance = self.borders_ens - self.left_geometry[0]
        else:
            distance = self.borders_ens
        x = self._unit * (distance * np.cos(direction_section))
        y = self._unit * (distance * np.sin(direction_section))
        self.x = self._x_left + x
        self.y = self._y_left + y

    def collect_data(self, meas, nav_ref="bt_vel"):
        """Collect data of valid position and depth for each selected transect

        Parameters
        ----------
        meas: Measurement
            Object of Measurement class
        nav_ref: str
            Current navigation reference from settings

        Returns
        -------
        data_transects: dict
            Dictionary of transects data loaded from Measurement
        """

        self.data_transects = []
        self.n_transects = len(meas.checked_transect_idx)
        data_dict = {}
        x_transect = np.nan
        y_transect = np.nan
        left_param = np.tile([np.nan], (self.n_transects, 2))
        right_param = np.tile([np.nan], (self.n_transects, 2))

        for id_transect in meas.checked_transect_idx:
            transect = meas.transects[id_transect]

            # Verify that the transect has heading data before computing
            if not all(deg == 0 for deg in transect.sensors.heading_deg.internal.data):
                ship_data = transect.boat_vel.compute_boat_track(transect, nav_ref)

                # Set flip setting based on start edge so that all data reflect
                # starting on left bank
                flip = 1
                if transect.start_edge == "Right":
                    flip = -1

                # Check for using gga data
                if nav_ref == "gga_vel":
                    # utm conversion does not support nan values so only valid data
                    # can be converted
                    gps_valid_idx = np.where(
                        np.logical_not(np.isnan(transect.gps.gga_lat_ens_deg))
                    )[0]
                    coords = utm.from_latlon(
                        transect.gps.gga_lat_ens_deg[gps_valid_idx],
                        transect.gps.gga_lon_ens_deg[gps_valid_idx],
                    )

                    # Compute the x and y coordinate adjustment based on the first valid gps data
                    # This accounts for potential valid BT data prior to the first valid
                    # gps data.
                    x_coord = (
                        coords[0][gps_valid_idx[0]]
                        - ship_data["track_x_m"][gps_valid_idx[0]]
                    )
                    y_coord = (
                        coords[1][gps_valid_idx[0]]
                        - ship_data["track_y_m"][gps_valid_idx[0]]
                    )

                    # Adjust ship_data track for utm coordinates
                    x_track = ship_data["track_x_m"] + x_coord
                    y_track = ship_data["track_y_m"] + y_coord

                    # Save zone information for cvs output
                    self.gps_zone_number = coords[2]
                    self.gps_zone_letter = coords[3]
                    x_transect = x_track[::flip]
                    y_transect = y_track[::flip]
                elif flip == -1:
                    dmg_ind = np.where(
                        abs(ship_data["dmg_m"]) == max(abs(ship_data["dmg_m"]))
                    )[0][0]
                    x_track = ship_data["track_x_m"] - ship_data["track_x_m"][dmg_ind]
                    y_track = ship_data["track_y_m"] - ship_data["track_y_m"][dmg_ind]
                    x_transect = x_track[::flip]
                    y_transect = y_track[::flip]

                elif flip == 1:
                    x_transect = ship_data["track_x_m"]
                    y_transect = ship_data["track_y_m"]

                # Depth
                depth_selected = getattr(transect.depths, transect.depths.selected)
                depth_transect = depth_selected.depth_processed_m[::flip]
                cells_depth = depth_selected.depth_cell_depth_m[:, ::flip]

                # Temperature
                temp_selected = getattr(
                    transect.sensors.temperature_deg_c,
                    transect.sensors.temperature_deg_c.selected,
                )
                temp_transect = temp_selected.data[::flip]

                # Velocity data
                x_velocity = np.copy(transect.w_vel.u_processed_mps[:, ::flip])
                y_velocity = np.copy(transect.w_vel.v_processed_mps[:, ::flip])
                z_velocity = np.copy(transect.w_vel.w_processed_mps[:, ::flip])

                # RSSI data
                rssi_mean = np.nanmean(transect.w_vel.rssi, axis=0)[:, ::flip]

                # Edges parameters
                left = [
                    meas.transects[id_transect].edges.left.distance_m,
                    meas.discharge[id_transect].edge_coef(
                        "left", meas.transects[id_transect]
                    ),
                ]

                index_transect = meas.checked_transect_idx.index(id_transect)

                if isinstance(left[1], list):
                    left[1] = np.nan
                left_param[index_transect, :] = left

                right = [
                    meas.transects[id_transect].edges.right.distance_m,
                    meas.discharge[id_transect].edge_coef(
                        "right", meas.transects[id_transect]
                    ),
                ]
                if isinstance(right[1], list):
                    right[1] = np.nan
                right_param[index_transect, :] = right

                data_dict = {
                    "x_raw_coordinates": x_transect,
                    "y_raw_coordinates": y_transect,
                    "x_velocity": x_velocity,
                    "y_velocity": y_velocity,
                    "vertical_velocity": z_velocity,
                    "depths": depth_transect,
                    "start_edge": transect.start_edge,
                    "cell_depth": cells_depth,
                    "rssi": rssi_mean,
                    "temperature": temp_transect,
                }

            self.data_transects.append(data_dict)

        self.left_geometry = np.nanmedian(left_param, axis=0)
        self.right_geometry = np.nanmedian(right_param, axis=0)

    def compute_coef(self):
        """Compute straight average cross-section from edges coordinates."""

        # Compute median coordinates of left and right banks
        x_left = [arr["x_raw_coordinates"][0] for arr in self.data_transects]
        x_right = [arr["x_raw_coordinates"][-1] for arr in self.data_transects]
        y_left = [arr["y_raw_coordinates"][0] for arr in self.data_transects]
        y_right = [arr["y_raw_coordinates"][-1] for arr in self.data_transects]

        self._x_left = float(np.nanmedian(x_left))
        self._y_left = float(np.nanmedian(y_left))

        self.slope = (float(np.nanmedian(y_right)) - self._y_left) / (
            float(np.nanmedian(x_right)) - self._x_left
        )
        self.intercept = self._y_left - self.slope * self._x_left

        self.intercept = self._y_left - self.slope * self._x_left

        # if LEW is > the start bank was REW. If not REW was
        # the start and velocities should be inversed.
        if self._x_left > np.nanmedian(x_right):
            self._unit = -1
        else:
            self._unit = 1

    def project_transect(self):
        """Project transects on the average cross-section."""

        x_min = []
        x_max = []
        y_min = []
        y_max = []

        for transect in self.data_transects:
            # Projected x-coordinate
            transect["x_projected"] = (
                transect["x_raw_coordinates"]
                - self.slope * self.intercept
                + self.slope * transect["y_raw_coordinates"]
            ) / (self.slope**2 + 1)

            # Projected y-coordinate
            transect["y_projected"] = (
                self.intercept
                + self.slope * transect["x_raw_coordinates"]
                + self.slope**2 * transect["y_raw_coordinates"]
            ) / (self.slope**2 + 1)

            x_min.append(np.nanmin(transect["x_projected"]))
            x_max.append(np.nanmax(transect["x_projected"]))
            y_min.append(np.nanmin(transect["y_projected"]))
            y_max.append(np.nanmax(transect["y_projected"]))

        left_x = [transect["x_projected"][0] for transect in self.data_transects]
        left_y = [transect["y_projected"][0] for transect in self.data_transects]
        left_x = np.nanmedian(left_x)
        left_y = np.nanmedian(left_y)

        x_boundaries = [np.nanmin(x_min), np.nanmax(x_max)]
        y_boundaries = [np.nanmin(y_min), np.nanmax(y_max)]

        x_offset = min(x_boundaries, key=lambda x: abs(x - float(left_x)))
        y_offset = min(y_boundaries, key=lambda x: abs(x - float(left_y)))

        # Compute the distance on the average cross-section
        for transect in self.data_transects:
            x_distance = transect["x_projected"] - x_offset
            y_distance = transect["y_projected"] - y_offset
            transect["acs_distance"] = np.sqrt(x_distance**2 + y_distance**2)

    @staticmethod
    def compute_max_min_distance(transects):
        max_dist = []
        min_dist = []

        for transect in transects:
            max_dist.append(np.nanmax(transect["acs_distance"]))
            min_dist.append(np.nanmin(transect["acs_distance"]))

        return max_dist, min_dist

    def translated_transects(self):
        """Compare bathymetry and translate transects on average cross-section if needed."""

        # Use the transect with the maximum acs_distance as the reference.
        max_tr, min_tr = self.compute_max_min_distance(self.data_transects)
        transect_length = [x - y for x, y in zip(max_tr, min_tr)]

        id_max = np.argmax(transect_length)

        # Compute grid
        grid_acs = np.arange(
            np.nanmin(min_tr),
            np.nanmax(max_tr),
            (np.nanmax(max_tr) - np.nanmin(min_tr)) / 100,
        )

        # Compute reference depth grid
        acs_depth_ref = griddata(
            self.data_transects[id_max]["acs_distance"],
            self.data_transects[id_max]["depths"],
            grid_acs,
        )
        # Translated other transects to reference based on depths
        acs_translated = []
        min_dist = []
        for i, transect in enumerate(self.data_transects):
            if i == id_max:
                acs_translated.append(transect["acs_distance"])
                min_dist.append(np.nanmin(transect["acs_distance"]))
            else:
                # Interpolate depth on x grid
                acs_depth = griddata(
                    transect["acs_distance"], transect["depths"], grid_acs
                )
                if not np.all(np.isnan(acs_depth)):
                    acs_depth_valid = acs_depth[~np.isnan(acs_depth)]

                    # Find the best position to minimize median of sum square
                    default_acs_ssd = np.nanmean(
                        (acs_depth_ref[: acs_depth_valid.size] - acs_depth_valid) ** 2
                    )
                    lag_acs_idx = 0
                    for j in range(1, acs_depth_ref.size - acs_depth_valid.size + 1):
                        acs_ssd = np.nanmean(
                            (
                                acs_depth_ref[j : j + acs_depth_valid.size]
                                - acs_depth_valid
                            )
                            ** 2
                        )
                        if (
                            acs_ssd < default_acs_ssd or np.isnan(default_acs_ssd)
                        ) and np.count_nonzero(
                            np.isnan(acs_depth_ref[j : j + acs_depth_valid.size])
                        ) < 0.5 * acs_depth_valid.size:
                            default_acs_ssd = acs_ssd
                            lag_acs_idx = j

                    # Correct average cross-section distance by translation
                    first_valid_acs = int(np.argwhere(~np.isnan(acs_depth))[0])
                    transect["acs_distance"] = transect["acs_distance"] - (
                        grid_acs[first_valid_acs] - grid_acs[lag_acs_idx]
                    )
                    min_dist.append(np.nanmin(transect["acs_distance"]))

        # Start from 0
        min_dist = np.nanmin(min_dist)
        for transect in self.data_transects:
            transect["acs_distance"] -= min_dist

    def compute_auto_node_size(self):
        """Computes auto node sizes."""

        max_transect_horz = []
        max_transect_vert = []
        for transect in self.data_transects:
            max_transect_vert.append(
                np.nanmax(np.abs(np.diff(transect["cell_depth"], axis=0)))
            )
            max_transect_horz.append(
                np.nanmax(np.abs(np.diff(transect["acs_distance"])))
            )
        self.auto_node_vert = np.nanmax(max_transect_vert) * 1.10
        self.auto_node_horz = np.nanmax(max_transect_horz) * 1.10

    def compute_node_size(
        self,
        node_horizontal_user,
        node_vertical_user,
    ):
        """Define horizontal and vertical mesh

        Parameters:
        node_horizontal_user: float
            Horizontal size of the mesh define by the user
        node_vertical_user: float
            Vertical size of the mesh define by the user
        """

        # Mesh width
        max_dist, min_dist = self.compute_max_min_distance(self.data_transects)
        max_acs_distance = np.nanmax(max_dist)
        min_acs_distance = np.nanmin(min_dist)
        acs_total = max_acs_distance - min_acs_distance

        # Horizontal node
        node_horz = self.auto_node_horz
        if node_horizontal_user is None:
            if self.auto_node_horz is None:
                self.compute_auto_node_size()
            node_horz = self.auto_node_horz
        elif node_horizontal_user >= self.auto_node_horz:
            node_horz = node_horizontal_user

        self.borders_ens = np.linspace(
            min_acs_distance,
            max_acs_distance + 10**-5,
            max(2, int(acs_total / node_horz) + 1),
        )

        # Mesh height
        max_depth = np.nanmax([np.nanmax(arr["depths"]) for arr in self.data_transects])

        # Vertical node
        node_vert = self.auto_node_vert
        if node_vertical_user is None:
            if self.auto_node_vert is None:
                self.compute_auto_node_size()
        elif node_vertical_user >= self.auto_node_vert:
            node_vert = node_vertical_user

        self.main_depth_layers = np.round(
            np.arange(
                0,
                max_depth + node_vert,
                node_vert,
            ).tolist(),
            3,
        )

    def compute_nodes_velocity(self, param):
        """Compute transect median velocity on each mesh (North, East and
        vertical velocities) and depth on each vertical

        Attributes
        ----------
        param: dict
            Dictionary of parameters to plot

        Returns
        -------
        data_bins_transect_save: dict
            Dictionary of data by transects
        """

        # Create data_bin_transects dictionary containing key for each data type.
        data_bin_transects = {}
        data_bin_transects_save = {}
        len_key_cell = 0
        len_ens_cells = 0
        key_cell = []
        key_ens = []
        for key, value in param.items():
            # Create dictionary entries for cells
            if value == "cell":
                key_cell.append(key)
                len_key_cell += 1
                # data_bin_transects is created using empty so that later it is converted
                # to lists to contain all the data for a specified cell
                # data_bin_transects[key] = np.tile(
                #     np.empty,
                #     (
                #         self.n_transects,
                #         len(self.main_depth_layers) - 1,
                #         len(self.borders_ens) - 1,
                #     ),
                # )
                data_bin_transects[key] = np.empty(shape=(
                        self.n_transects,
                        len(self.main_depth_layers) - 1,
                        len(self.borders_ens) - 1,
                    ), dtype=object)
                # data_bin_transects_save will save the median values computed from the
                # lists in data_bin_transects
                data_bin_transects_save[key] = np.tile(
                    np.nan,
                    (
                        self.n_transects,
                        len(self.main_depth_layers) - 1,
                        len(self.borders_ens) - 1,
                    ),
                )
                # Convert data_bin_transect elements to lists
                for idx in np.ndindex(data_bin_transects[key].shape):
                    data_bin_transects[key][idx] = []
            # Create dictionary entries for ensemble based data
            elif value == "ens":
                key_ens.append(key)
                len_ens_cells += 1
                # data_bin_transects is created using empty so that later it is converted
                # to lists to contain all the data for a specified projected ensemble
                # data_bin_transects[key] = np.tile(
                #     np.array([np.nan]), (self.n_transects, len(self.borders_ens) - 1)
                # )
                data_bin_transects[key] = np.empty(shape=(self.n_transects, len(self.borders_ens) - 1), dtype=object)
                # data_bin_transects_save will save the median values computed from the
                # lists in data_bin_transects
                data_bin_transects_save[key] = np.tile(
                    np.nan, (self.n_transects, len(self.borders_ens) - 1)
                )
                # Convert data_bin_transect elements to lists
                for idx in np.ndindex(data_bin_transects[key].shape):
                    data_bin_transects[key][idx] = []

        # Compute bins
        bins_depths = np.array(copy.deepcopy(self.main_depth_layers))
        bins_distance = np.array(copy.deepcopy(self.borders_ens))
        bins_distance[0] = bins_distance[0] - 0.1

        # Browse through transects
        for transect_idx, transect in enumerate(self.data_transects):
            # Get current transect's cells depth and distance
            depth_cells_transect = transect["cell_depth"]
            distance_cells_transect = np.tile(
                transect["acs_distance"], [len(depth_cells_transect), 1]
            )
            # Get data which need to be binned
            data_cells = [transect[value] for value in key_cell]
            data_ens = [transect[value] for value in key_ens]

            # Flatten data
            list_param = [
                depth_cells_transect.flatten(),
                distance_cells_transect.flatten(),
            ]
            list_cells = [x.flatten() for x in data_cells]
            list_ens = [
                np.tile(x, [len(depth_cells_transect), 1]).flatten() for x in data_ens
            ]
            list_river = list_param + list_cells + list_ens
            # Create 2D array and remove rows with no valid data
            data_river = np.array(list_river).T
            data_river = data_river[
                np.logical_not(np.all(np.isnan(data_river[:, [2, 3, 4, 5, 6]]), axis=1))
            ]

            # 2D binning
            depths_idx = np.digitize(data_river[:, 0], bins_depths) - 1
            distance_idx = np.digitize(data_river[:, 1], bins_distance) - 1
            n_bin_depths = len(bins_depths) - 1

            # Process each row in data_river
            for row_idx in range(len(data_river)):
                # Only use row if the depths_idx is in range
                if depths_idx[row_idx] < n_bin_depths:
                    # Add cell data to corresponding list
                    j = -1
                    for key in key_cell:
                        j += 1
                        data = data_river[row_idx, j + 2]
                        data_bin_transects[key][
                            transect_idx, depths_idx[row_idx], distance_idx[row_idx]
                        ].append(data)

                    # Add items with binning on verticals only
                    k = -1
                    for key in key_ens:
                        k += 1
                        data = data_river[row_idx, k + len_key_cell + 2]
                        if (
                            data
                            not in data_bin_transects[key][
                                transect_idx, distance_idx[row_idx]
                            ]
                        ):
                            data_bin_transects[key][
                                transect_idx, distance_idx[row_idx]
                            ].append(data)

            # Define vectorized function to compute median
            median_func = np.vectorize(np.nanmedian, otypes=[float])

            # Compute median of each cell and convert to np.float
            for key in key_cell:
                data_bin_transects[key][transect_idx] = median_func(
                    data_bin_transects[key][transect_idx]
                )
                data_bin_transects_save[key][transect_idx] = np.asarray(
                    data_bin_transects[key][transect_idx], dtype=np.float64
                )
            # Compute the median of each ensemble and convert to np.float
            for key in key_ens:
                data_bin_transects[key][transect_idx] = median_func(
                    data_bin_transects[key][transect_idx]
                )
                data_bin_transects_save[key][transect_idx] = np.asarray(
                    data_bin_transects[key][transect_idx], dtype=np.float64
                )

        return data_bin_transects_save

        # Alternative approach using numpy indexing. However, it appears to be
        # slower than code above.
        # distance_idx_set = np.unique(bin_idx_distance)
        # max_bin_depth_idx = len(bins_depths) - 1
        # for idx in distance_idx_set:
        #     ens_indices = np.where(bin_idx_distance == idx)[0]
        #     if len(ens_indices) > 0:
        #         for n, key in enumerate(key_ens):
        #             data_bin_transects_dsm[key][transect_idx, idx] = np.nanmedian(
        #                 np.unique(data_river[ens_indices, n - len_ens_cells])
        #             )
        #
        #         depth_indices = bin_idx_depths[ens_indices]
        #         if len(depth_indices) > 0:
        #             depth_set = np.unique(depth_indices)
        #             for depth_idx in depth_set:
        #                 if depth_idx < max_bin_depth_idx:
        #                     cell_indices = ens_indices[depth_indices == depth_idx]
        #                     data = data_river[cell_indices]
        #                     cell_medians = np.nanmedian(data[:, 2:6], axis=0)
        #                     for n, key in enumerate(key_cell):
        #                         data_bin_transects_dsm[key][
        #                             transect_idx, depth_idx, idx
        #                         ] = cell_medians[n]

        # return data_bin_transects_dsm

    def compute_mean(self, data_bin_transects, n_burn, param):
        """Compute mesh mean value of selected transects

        Parameters
        ----------
        data_bin_transects: dict
            Dictionary of data by transects
        n_burn: int
            Number of transects which need to detect an information to make it valid
        param: dict
            Dictionary of parameters to plot
        """

        # Data to bin
        key_cell = [key for key, value in param.items() if value == "cell"]
        key_ens = [key for key, value in param.items() if value == "ens"]

        # Compute mean value on each cell
        data_bin_map = {
            key: np.nanmean(data_bin_transects[key], axis=0)
            for key in data_bin_transects.keys()
        }

        # Get index of streambed layer of mean bottom depth
        idx_streambed = np.digitize(data_bin_map["depths"], self.main_depth_layers)

        # Remove value below streambed
        for key in key_cell:
            for i in range(len(idx_streambed)):
                data_bin_map[key][idx_streambed[i] :, i] = np.nan

        # Count cells averaged
        data_bin_map["count"] = np.sum(
            ~np.isnan(
                data_bin_transects["x_velocity"] + data_bin_transects["y_velocity"]
            ),
            axis=0,
        )

        invalid_data = data_bin_map["count"] < n_burn
        invalid_ens = np.all(invalid_data, axis=0)

        # Remove value below streambed and invalid data
        for key in key_cell:
            data_bin_map[key][invalid_data] = np.nan

        key_cell.append("count")

        # Create cell depth array
        data_bin_map["cells_depth_layers"] = np.tile(
            np.nan, (len(self.main_depth_layers), data_bin_map["count"].shape[1])
        )

        idx_max = len(self.main_depth_layers)

        for i in range(data_bin_map["count"].shape[1]):
            data_bin_map["cells_depth_layers"][:, i] = self.main_depth_layers
            if idx_streambed[i] < idx_max:
                data_bin_map["cells_depth_layers"][idx_streambed[i] :, i] = np.nan
                data_bin_map["cells_depth_layers"][idx_streambed[i], i] = data_bin_map[
                    "depths"
                ][i]

        key_cell.append("cells_depth_layers")

        # Check for nan value and remove corresponding columns
        index_non_nan = np.where(~invalid_ens)[0]
        first_column_idx = 0
        last_column_idx = data_bin_map["count"].shape[1] - 1

        if len(index_non_nan) < len(invalid_ens):
            first_column_idx = int(np.nanmin(index_non_nan))
            last_column_idx = int(np.nanmax(index_non_nan))

            for key in key_cell:
                data_bin_map[key] = data_bin_map[key][
                    :, first_column_idx : last_column_idx + 1
                ]
            for key in key_ens:
                data_bin_map[key] = data_bin_map[key][
                    first_column_idx : last_column_idx + 1
                ]

        self.east_velocity = data_bin_map["x_velocity"]
        self.north_velocity = data_bin_map["y_velocity"]
        self.vertical_velocity = data_bin_map["vertical_velocity"]
        self.rssi = data_bin_map["rssi"]
        self.temperature = data_bin_map["temperature"]
        self.depths = data_bin_map["depths"]
        self.depth_cells_layers = data_bin_map["cells_depth_layers"]
        self.count_valid = data_bin_map["count"]

        temp_borders_ens = self.borders_ens[first_column_idx : last_column_idx + 2]
        distance_start = min(temp_borders_ens)
        temp_borders_ens -= distance_start
        for transect in self.data_transects:
            transect["acs_distance"] = transect["acs_distance"] - distance_start
        self.borders_ens = temp_borders_ens

        self.depth_cells_center = (
            data_bin_map["cells_depth_layers"][1:, :]
            + data_bin_map["cells_depth_layers"][:-1, :]
        ) / 2
        self.distance_cells_center = np.tile(
            [(self.borders_ens[1:] + self.borders_ens[:-1]) / 2],
            (self.depth_cells_center.shape[0], 1),
        )

        distance = np.diff(self.borders_ens)
        depth = np.diff(self.depth_cells_layers, axis=0)
        self.cells_area = distance * depth

    def compute_rozovskii(self, x_velocity, y_velocity):
        """Compute primary and secondary velocity according Rozovskii projection

        Parameters
        ----------
        x_velocity: np.array
            East velocity on each cell of the MAP section
        y_velocity: np.array
            North velocity on each cell of the MAP section
        """
        # Compute mean velocity components in each ensemble
        w_vel_mean_x = np.nanmean(x_velocity, axis=0)
        w_vel_mean_y = np.nanmean(y_velocity, axis=0)

        # Compute a unit vector
        self.direction_ens, _ = cart2pol(w_vel_mean_x, w_vel_mean_y)
        unit_vec_x, unit_vec_y = pol2cart(self.direction_ens, 1)

        # Compute the velocity magnitude in the direction of the mean velocity of each
        # ensemble using the dot product and unit vector
        self.primary_velocity = x_velocity * unit_vec_x + y_velocity * unit_vec_y
        self.secondary_velocity = x_velocity * unit_vec_y - y_velocity * unit_vec_x

    def compute_extrap_velocity(self, settings):
        """Compute top/bottom extrapolation according QRevInt velocity exponent

        Parameters
        ----------
        settings: dict
            Measurement current settings

        Returns
        -------
        idx_bot: np.array(int)
            Index to the bottom most valid depth cell in each ensemble
        idx_top: np.array(int)
            Index to the top most valid depth cell in each ensemble
        """

        # Assign local variables
        depths = self.depths
        depth_cells_border = self.depth_cells_layers
        depth_cells_center = self.depth_cells_center
        mid_bed_cells = depths - depth_cells_center
        w_vel_prim_extrap = np.copy(self.primary_velocity)
        w_vel_sec_extrap = np.copy(self.secondary_velocity)
        w_vel_z_extrap = np.copy(self.vertical_velocity)

        # Determine whole cells above streambed
        map_depth_cells_border = np.tile(
            self.main_depth_layers[:], (depth_cells_border.shape[1], 1)
        ).T
        map_depth_cells_border[map_depth_cells_border > depths] = np.nan
        map_depth_cells_center = (
            map_depth_cells_border[1:, :] + map_depth_cells_border[:-1, :]
        ) / 2
        blank = np.isnan(map_depth_cells_center)
        w_vel_prim_extrap[blank] = np.nan
        w_vel_sec_extrap[blank] = np.nan
        w_vel_z_extrap[blank] = np.nan

        # Identify valid data
        valid_data = np.logical_not(np.isnan(w_vel_prim_extrap))
        valid_cell_centers = depth_cells_center * valid_data
        valid_cell_centers[valid_cell_centers == 0] = np.nan

        idx_top = np.argmin(np.nan_to_num(valid_cell_centers, nan=float("inf")), axis=0)
        idx_bot = np.argmax(
            np.nan_to_num(valid_cell_centers, nan=float("-inf")), axis=0
        )

        # Preallocate variables
        n_ensembles = valid_data.shape[1]
        idx_top_3 = np.tile(-1, (3, valid_data.shape[1])).astype(int)

        # QRevInt extrapolation method
        idx_bed = copy.deepcopy(idx_bot)
        bot_method = settings["extrapBot"]
        top_method = settings["extrapTop"]
        exponent = settings["extrapExp"]

        # Bottom method is power
        coef_primary_bot = np.nanmean(w_vel_prim_extrap, 0)

        if bot_method == "No Slip":
            cutoff_depth = 0.8 * depths
            depth_ok = nan_greater(
                depth_cells_center,
                np.tile(cutoff_depth, (depth_cells_center.shape[0], 1)),
            )
            component_ok = np.logical_not(np.isnan(w_vel_prim_extrap))
            use_ns = depth_ok * component_ok
            for j in range(len(idx_bot)):
                if idx_bot[j] >= 0:
                    use_ns[idx_bot[j], j] = 1
            component_ns = np.copy(w_vel_prim_extrap)
            component_ns[np.logical_not(use_ns)] = np.nan

            coef_primary_bot = np.nanmean(component_ns, 0)

        # Extrapolation Bottom velocity
        for n in range(len(idx_bed)):
            if idx_bed[n] > -1:
                while (
                    idx_bed[n] < len(depth_cells_center[:, n])
                    and depth_cells_border[idx_bed[n] + 1, n] <= depths[n]
                ):
                    idx_bed[n] += 1
                # Shape of bottom cells
                bot_depth = mid_bed_cells[idx_bot[n] + 1 : (idx_bed[n]), n]

                # Extrapolation for Primary velocity
                bot_prim_value = (
                    coef_primary_bot[n]
                    * ((1 + 1 / exponent) / (1 / exponent))
                    * ((bot_depth / depths[n]) ** exponent)
                )
                w_vel_prim_extrap[(idx_bot[n] + 1) : (idx_bed[n]), n] = bot_prim_value

                # Constant extrapolation for Secondary velocity
                w_vel_sec_extrap[(idx_bot[n] + 1) : (idx_bed[n]), n] = w_vel_sec_extrap[
                    idx_bot[n], n
                ]
                # Linear extrapolation to 0 at streambed for Vertical velocity
                try:
                    w_vel_z_extrap[(idx_bot[n] + 1) : (idx_bed[n]), n] = griddata(
                        np.append(mid_bed_cells[idx_bot[n], n], 0),
                        np.append(self.vertical_velocity[idx_bot[n], n], 0),
                        mid_bed_cells[(idx_bot[n] + 1) : (idx_bed[n]), n],
                    )
                except Exception:
                    pass

        # Top power extrapolation (primary)
        if top_method == "Power":
            coef_primary_top = np.nanmean(w_vel_prim_extrap, 0)
            for n in range(len(idx_top)):
                top_depth = mid_bed_cells[: idx_top[n], n]
                top_prim_value = (
                    coef_primary_top[n]
                    * ((1 + 1 / exponent) / (1 / exponent))
                    * ((top_depth / depths[n]) ** exponent)
                )
                w_vel_prim_extrap[: idx_top[n], n] = top_prim_value

        # Top constant extrapolation (primary)
        elif top_method == "Constant":
            n_ensembles = len(idx_top)
            for n in range(n_ensembles):
                if idx_top[n] >= 0:
                    w_vel_prim_extrap[: idx_top[n], n] = w_vel_prim_extrap[
                        idx_top[n], n
                    ]

        elif top_method == "3-Point":
            for n in range(n_ensembles):
                # Identifying bottom most valid cell
                idx_temp = np.where(np.logical_not(np.isnan(w_vel_prim_extrap[:, n])))[
                    0
                ]
                if len(idx_temp) > 0:
                    if len(idx_temp) > 2:
                        idx_top_3[:, n] = idx_temp[0:3]

            # Determine number of bins available in each profile
            valid_data = np.logical_not(np.isnan(w_vel_prim_extrap))
            n_bins = np.nansum(valid_data, 0)
            # Determine number of ensembles
            n_ensembles = len(idx_top)

            for n in range(n_ensembles):
                if (n_bins[n] < 6) and (n_bins[n] > 0) and (idx_top[n] >= 0):
                    w_vel_prim_extrap[: idx_top[n], n] = w_vel_prim_extrap[
                        idx_top[n], n
                    ]

                # If 6 or more bins use 3-pt at top
                if n_bins[n] > 5:
                    top_depth = depth_cells_center[: idx_top[n], n]
                    top_3_depth = depth_cells_center[idx_top_3[0:3, n], n]
                    top_3_vel = w_vel_prim_extrap[idx_top_3[0:3, n], n]

                    slope, intercept, _, _, _ = linregress(top_3_depth,
                                                           top_3_vel)
                    w_vel_prim_extrap[: idx_top[n],
                    n] = slope * top_depth + intercept

        # Extrap top for second and vertical velocities
        for n in range(len(idx_top)):
            if idx_top[n] >= 0:
                w_vel_sec_extrap[: idx_top[n], n] = w_vel_sec_extrap[idx_top[n], n]
                try:
                    top_z_value = griddata(
                        np.append(mid_bed_cells[idx_top[n], n], self.depths[n]),
                        np.append(w_vel_z_extrap[idx_top[n], n], 0),
                        mid_bed_cells[: idx_top[n], n],
                    )
                    w_vel_z_extrap[: idx_top[n], n] = top_z_value
                except Exception:
                    pass

        self.primary_velocity = w_vel_prim_extrap
        self.secondary_velocity = w_vel_sec_extrap
        self.vertical_velocity = w_vel_z_extrap

    @staticmethod
    def group(data):
        # Todo need doc str
        first = last = data[0]
        for n in data[1:]:
            if n - 1 == last:
                last = n
            else:
                yield first, last
                first = last = n
        yield first, last

    def compute_interpolation(self):
        """Compute interpolation for missing data according QRevInt ABBA method"""

        # Interpolate depth
        valid_depths = np.logical_not(np.isnan(self.depths))
        if not np.all(valid_depths):
            indices_depths = np.arange(len(self.depths))
            self.depths = np.interp(
                indices_depths,
                indices_depths[valid_depths],
                self.depths[valid_depths],
            )

        # Interpolate direction
        valid_direction = np.logical_not(np.isnan(self.direction_ens))
        if not np.all(valid_direction):
            indices_direction = np.arange(len(self.direction_ens))
            self.direction_ens = np.interp(
                indices_direction,
                indices_direction[valid_direction],
                self.direction_ens[valid_direction],
            )

        # Interpolate Temperatures
        valid_temperature = np.logical_not(np.isnan(self.temperature))
        if not np.all(valid_temperature):
            indices_temperature = np.arange(len(self.temperature))
            self.temperature = np.interp(
                indices_temperature,
                indices_temperature[valid_temperature],
                self.temperature[valid_temperature],
            )

        data_list = [
            self.primary_velocity,
            self.secondary_velocity,
            self.vertical_velocity,
        ]
        # Identify valid data
        valid_data = np.logical_not(np.isnan(self.primary_velocity))
        cells_above_sl = np.full(self.primary_velocity.shape, True)

        # Preallocate variables
        n_ensembles = valid_data.shape[1]
        idx_bot = np.tile(-1, (valid_data.shape[1])).astype(int)
        idx_top = np.tile(-1, valid_data.shape[1]).astype(int)

        # Define valid cells, those that should have data between the topmost and
        # bottommost cells.
        invalid_ens = []
        for n in range(n_ensembles):
            # Identifying bottom most valid cell
            idx_temp = np.where(np.logical_not(np.isnan(self.primary_velocity[:, n])))[
                0
            ]
            if len(idx_temp) > 0:
                idx_top[n] = idx_temp[0]
                idx_bot[n] = idx_temp[-1]
                cells_above_sl[: idx_top[n], n] = False
                cells_above_sl[idx_bot[n] + 1 :, n] = False
            else:
                idx_top[n] = 0
                invalid_ens.append(n)

        # Remove top/bottom cells
        if len(invalid_ens) > 0:
            grouped_invalid = list(self.group(invalid_ens))
            for x in grouped_invalid:
                if x[0] == 0 or x[-1] == n_ensembles - 1:
                    for ens in range(x[0], x[1] + 1):
                        cells_above_sl[:, ens] = False
                else:
                    top = np.nanmin([idx_top[x[0] - 1], idx_top[x[1] + 1]])
                    bot = np.nanmax([idx_bot[x[0] - 1], idx_bot[x[1] + 1]])

                    for ens in range(x[0], x[1] + 1):
                        cells_above_sl[:top, ens] = False
                        cells_above_sl[bot + 1 :, ens] = False

        # Use bottom of cells as depth
        last_cell = []
        for n in range(len(self.depths)):
            last_cell.append(
                next(
                    (i, v)
                    for i, v in enumerate(self.main_depth_layers)
                    if v > self.depths[n]
                )
            )
        y_depth = [x[1] for x in last_cell]

        # Update depth data
        i = -1
        for x in last_cell:
            i += 1
            self.depth_cells_layers[x[0], i] = self.depths[i]
            self.depth_cells_layers[x[0] + 1 :, i] = np.nan

        y_cell_size = self.depth_cells_layers[1:, :] - self.depth_cells_layers[:-1, :]
        y_centers = self.depth_cells_layers[:-1, :] + 0.5 * y_cell_size
        x_shiptrack = self.distance_cells_center[0, :]
        search_loc = ["above", "below", "before", "after"]
        normalize = False

        # abba interpolation
        interpolated_data = abba_idw_interpolation(
            data_list=data_list,
            valid_data=valid_data,
            cells_above_sl=cells_above_sl,
            y_centers=y_centers,
            y_cell_size=y_cell_size,
            y_depth=y_depth,
            x_shiptrack=x_shiptrack,
            search_loc=search_loc,
            normalize=normalize,
        )

        # apply interpolated results
        if interpolated_data is not None:
            # Incorporate interpolated values
            for n in range(len(interpolated_data[0])):
                self.primary_velocity[interpolated_data[0][n][0]] = interpolated_data[
                    0
                ][n][1]
                self.secondary_velocity[interpolated_data[1][n][0]] = interpolated_data[
                    1
                ][n][1]
                self.vertical_velocity[interpolated_data[2][n][0]] = interpolated_data[
                    2
                ][n][1]

    def compute_edges(self, settings):
        """Compute edge extrapolation

        Parameters
        ----------
        settings: dict
            Measurement current settings

        Returns
        -------
        left_direction/right_direction: np.array
            Direction of the first/last ensemble applied to edge
        left_area/right_area: np.array
            Area of edge's cells
        left_mid_cells_x/right_mid_cells_x: np.array
            Longitudinal position of the middle of each cell
        left_mid_cells_y/right_mid_cells_y: np.array
            Depth position of the middle of each cell
        """
        exponent = settings["extrapExp"]

        left_distance, left_coef = self.left_geometry
        self.edge_velocity("left", left_distance, left_coef, exponent)

        right_distance, right_coef = self.right_geometry
        self.edge_velocity("right", right_distance, right_coef, exponent)

    @staticmethod
    def interpolation(data1, data2, data1_interp_value, style="linear"):
        # Todo add doc strings

        funcs = {
            "linear": lambda x, a, b: a * x + b,
            "power": lambda x, a, b: a * x**b,
            "power_rectangular": lambda x, a: a * x**0.1,
            "power_triangular": lambda x, a: a * x**0.41,
        }
        valid = ~(np.isnan(data2) | np.isinf(data2))
        if np.isnan(data2[valid]).all():
            value = np.nan
        elif len(data2[valid]) == 1:
            value = data2[valid]
        else:
            try:
                popt, _ = curve_fit(
                    funcs[style], data1[valid], data2[valid], maxfev=1000
                )
                value = funcs[style](data1_interp_value, *popt)
            except Exception:
                value = np.nan
        return value

    def edge_velocity(self, edge, edge_distance, edge_coef, exponent):
        """Compute edge extrapolation

        Parameters
        ----------
        edge: str
            'left' or 'right'
        edge_distance: float
            Edge distance
        edge_coef: float
            Shape coefficient of the edge
        exponent: float
            extrapolation exponent
        """

        # If left edge
        id_edge = 0
        node_size = abs(self.borders_ens[1] - self.borders_ens[0])
        if edge == "right":
            id_edge = -1
            node_size = abs(self.borders_ens[-1] - self.borders_ens[-2])

        nodes = edge_distance - np.arange(0, edge_distance, node_size)[::-1]
        nodes = np.insert(nodes, 0, 0)
        nb_nodes = len(nodes) - 1
        # Compute center of each horizontal node
        nodes_mid = (nodes[1:] + nodes[:-1]) / 2
        edge_size_raw = self.depth_cells_layers[:, id_edge]

        if edge_coef == 0.3535 and edge_distance > 0:
            depth_edge = self.depths[id_edge] * (
                edge_distance / (edge_distance + node_size / 2)
            )

            # Get depth at the border of each ensemble
            border_depths = np.multiply(nodes, depth_edge / edge_distance)
            cells_borders_depths_1 = np.transpose(
                [edge_size_raw] * (len(border_depths) - 1)
            )
            cells_borders_depths_2 = np.transpose(
                [edge_size_raw] * (len(border_depths))
            )

            for i in range(len(border_depths) - 1):
                sub_index = next(
                    x[0]
                    for x in cells_borders_depths_1[:, i]
                    if x[1] >= int(1000 * border_depths[i + 1]) / 1000.
                )
                cells_borders_depths_1[sub_index, i] = border_depths[i + 1]
                cells_borders_depths_1[sub_index + 1 :, i] = np.nan
                cells_borders_depths_2[sub_index - 1, i + 1] = border_depths[i + 1]
                cells_borders_depths_2[sub_index:, i] = np.nan

            # Distance arrays
            cut_x = (
                edge_distance * edge_size_raw[edge_size_raw <= depth_edge] / depth_edge
            )
            x_left = np.tile(nodes, (cells_borders_depths_1.shape[0], 1))

            for j in range(np.count_nonzero(~np.isnan(cut_x))):
                col, _ = next(x for x in enumerate(nodes) if x[1] > cut_x[j])
                row = np.where(edge_size_raw == edge_size_raw[j])[0][0]
                x_left[row, col - 1] = cut_x[j]
                x_left[row + 1, col - 1] = nodes[col]

            invalid_data = np.isnan(cells_borders_depths_2)
            x_left[invalid_data] = np.nan

            # Define the 5 points of the pentagon
            a_coordinates_x = copy.deepcopy(x_left[:-1, :-1])
            a_coordinates_y = copy.deepcopy(cells_borders_depths_1[:-1, :])
            b_coordinates_x = copy.deepcopy(x_left[:-1, 1:])
            b_coordinates_y = copy.deepcopy(cells_borders_depths_1[:-1, :])
            c_coordinates_x = copy.deepcopy(x_left[:-1, 1:])
            c_coordinates_y = copy.deepcopy(cells_borders_depths_1[1:, :])
            d_coordinates_x = copy.deepcopy(x_left[1:, :-1])
            d_coordinates_y = copy.deepcopy(cells_borders_depths_1[1:, :])
            e_coordinates_x = copy.deepcopy(x_left[:-1, :-1])
            e_coordinates_y = copy.deepcopy(cells_borders_depths_2[:-1, :-1])

            # Remove invalid points
            invalid_d = np.logical_or(
                np.logical_and(
                    d_coordinates_x == c_coordinates_x,
                    c_coordinates_y == d_coordinates_y,
                ),
                np.isnan(d_coordinates_x + d_coordinates_y),
            )
            d_coordinates_x[invalid_d] = np.nan
            d_coordinates_y[invalid_d] = np.nan
            invalid_e = np.logical_or(
                np.logical_and(
                    e_coordinates_x == a_coordinates_x,
                    e_coordinates_y == a_coordinates_y,
                ),
                np.isnan(e_coordinates_x + e_coordinates_y),
            )
            e_coordinates_x[invalid_e] = np.nan
            e_coordinates_y[invalid_e] = np.nan

            # Compute the center of the cell as the mean coordinates
            mid_cells_x = np.nanmean(
                [
                    a_coordinates_x,
                    b_coordinates_x,
                    c_coordinates_x,
                    d_coordinates_x,
                    e_coordinates_x,
                ],
                axis=0,
            )
            mid_cells_y = np.nanmean(
                [
                    a_coordinates_y,
                    b_coordinates_y,
                    c_coordinates_y,
                    d_coordinates_y,
                    e_coordinates_y,
                ],
                axis=0,
            )
            mid_cells_x[invalid_data[:-1, :-1]] = np.nan
            mid_cells_y[invalid_data[:-1, :-1]] = np.nan

            # Compute cell area
            area = 0.5 * np.abs(
                a_coordinates_x * b_coordinates_y
                - b_coordinates_x * a_coordinates_y
                + b_coordinates_x * c_coordinates_y
                - c_coordinates_x * b_coordinates_y
                + c_coordinates_x * d_coordinates_y
                - d_coordinates_x * c_coordinates_y
                + d_coordinates_x * e_coordinates_y
                - e_coordinates_x * d_coordinates_y
                + e_coordinates_x * a_coordinates_y
                - a_coordinates_x * e_coordinates_y
            )

            area[invalid_data[:-1, :-1]] = np.nan
            edge_exp = 2.41

            bed_distance = mid_cells_y * edge_distance / depth_edge
            vertical_depth = mid_cells_x * depth_edge / edge_distance

            is_edge = True

        elif edge_coef == 0.91 and edge_distance > 0:
            depth_edge = self.depths[id_edge]
            border_depths = np.tile(self.depths[id_edge], len(nodes))
            mid_cells_x = np.tile([nodes_mid], (len(edge_size_raw) - 1, 1))
            mid_cells_y = np.transpose([self.depth_cells_center[:, id_edge]] * nb_nodes)

            size_x = np.tile([nodes[1:] - nodes[:-1]], (len(edge_size_raw) - 1, 1))
            size_y = np.transpose([edge_size_raw[1:] - edge_size_raw[:-1]] * nb_nodes)
            area = size_x * size_y
            bed_distance = np.tile(0, area.shape)
            vertical_depth = np.tile([self.depths[id_edge]], area.shape)
            edge_exp = 10

            is_edge = True

        else:
            # Custom edge coefficient
            if edge_distance == 0:
                depth_edge = self.depths[id_edge]
            else:
                depth_edge = self.depths[id_edge] * (
                    edge_distance / (edge_distance + node_size / 2)
                )
            border_depths = np.tile(np.nan, len(nodes))
            mid_cells_x = np.tile([np.nan], (len(edge_size_raw) - 1, nb_nodes))
            mid_cells_y = np.tile([np.nan], (len(edge_size_raw) - 1, nb_nodes))
            area = np.tile([np.nan], (len(edge_size_raw) - 1, nb_nodes))
            bed_distance = np.tile([np.nan], (len(edge_size_raw) - 1, nb_nodes))
            vertical_depth = np.tile([np.nan], (len(edge_size_raw) - 1, nb_nodes))
            edge_exp = np.nan

            is_edge = False

        if np.all(np.isnan(self.primary_velocity[:, id_edge])) or not is_edge:
            edge_primary_velocity = np.tile(
                [np.nan], (len(edge_size_raw) - 1, nb_nodes)
            )
            edge_secondary_velocity = np.tile(
                [np.nan], (len(edge_size_raw) - 1, nb_nodes)
            )
            edge_vertical_velocity = np.tile(
                [np.nan], (len(edge_size_raw) - 1, nb_nodes)
            )
            # Added by Sana
            depth = (border_depths[1:] + border_depths[:-1]) / 2
            edge_layers = np.tile(self.main_depth_layers[:, np.newaxis], depth.shape)

        else:
            # Primary velocity : Power-power extrapolation from first ensemble
            # Mean velocity on the first valid ensemble
            primary_mean_valid = np.nanmean(self.primary_velocity[:, id_edge])
            is_nan = np.isnan(self.primary_velocity[:, id_edge])

            # Compute mean velocity according power law at middle_distance position
            vp_mean = primary_mean_valid * (mid_cells_x / edge_distance) ** (
                1 / edge_exp
            )
            # Compute velocity according power law on the chosen vertical
            edge_primary_velocity = (
                vp_mean
                * (((1 / exponent) + 1) / (1 / exponent))
                * ((vertical_depth - mid_cells_y) / vertical_depth) ** exponent
            )

            # Vertical velocity : linear extrapolation from first ensemble vertical distribution
            vertical_vel_first = np.insert(self.vertical_velocity[:, id_edge], 0, 0)
            vertical_vel_first = np.append(vertical_vel_first, 0)
            norm_depth_first = np.insert(
                self.depth_cells_center[:, id_edge] / depth_edge, 0, 0
            )
            norm_depth_first = np.append(norm_depth_first, 1)
            norm_depth_edge = mid_cells_y / vertical_depth
            edge_vertical_velocity = griddata(
                norm_depth_first, vertical_vel_first, norm_depth_edge
            )

            # Secondary velocity : linear interpolation to 0 at edge
            secondary_vel_first = np.insert(
                self.secondary_velocity[:, id_edge],
                0,
                self.secondary_velocity[0, id_edge],
            )
            secondary_vel_first = np.append(
                secondary_vel_first,
                secondary_vel_first[np.where(~np.isnan(secondary_vel_first))[-1][-1]],
            )
            depth_first = np.insert(self.depth_cells_center[:, id_edge], 0, 0)
            depth_first = np.append(depth_first, depth_edge)
            edge_secondary_vel_interp = griddata(
                depth_first, secondary_vel_first, mid_cells_y
            )

            edge_secondary_velocity = np.tile(np.nan, edge_primary_velocity.shape)

            for j in range(edge_primary_velocity.shape[1]):
                for i in range(
                    np.count_nonzero(~np.isnan(edge_secondary_vel_interp[:, j]))
                ):
                    edge_secondary_velocity[i, j] = MAP.interpolation(
                        np.array([bed_distance[i, j], edge_distance]),
                        np.array([0, edge_secondary_vel_interp[i, j]]),
                        mid_cells_x[i, j],
                    )
            edge_primary_velocity[is_nan] = np.nan
            edge_secondary_velocity[is_nan] = np.nan
            edge_vertical_velocity[is_nan] = np.nan

            # Get depth layers at the center of the ensemble
            depth = (border_depths[1:] + border_depths[:-1]) / 2
            edge_layers = np.tile(self.main_depth_layers[:, np.newaxis], depth.shape)
            for i in range(edge_layers.shape[1]):
                invalid_layer = edge_layers[:, i] > depth[i]
                edge_layers[invalid_layer, i] = np.nan
                edge_layers[np.argmax(invalid_layer), i] = depth[i]

        if edge == "right":
            self.primary_velocity = np.c_[
                self.primary_velocity, edge_primary_velocity[:, ::-1]
            ]
            self.secondary_velocity = np.c_[
                self.secondary_velocity, edge_secondary_velocity[:, ::-1]
            ]
            self.vertical_velocity = np.c_[
                self.vertical_velocity, edge_vertical_velocity[:, ::-1]
            ]
            self.rssi = np.c_[self.rssi, np.tile(np.nan, edge_primary_velocity.shape)]
            self.count_valid = np.c_[
                self.count_valid, np.tile(np.nan, edge_primary_velocity.shape)
            ]
            self.direction_ens = np.append(
                self.direction_ens,
                np.tile(self.direction_ens[id_edge], edge_primary_velocity.shape[1]),
            )

            depth = (border_depths[1:] + border_depths[:-1]) / 2
            self.depths = np.append(self.depths, depth[::-1])
            self.depth_cells_center = np.c_[
                self.depth_cells_center, mid_cells_y[:, ::-1]
            ]
            self.depth_cells_layers = np.c_[
                self.depth_cells_layers, edge_layers[:, ::-1]
            ]

            nan_array = np.tile(np.nan, len(depth))
            self.temperature = np.append(self.temperature, nan_array)

            max_dist = self.borders_ens[-1]

            self.borders_ens = np.append(
                self.borders_ens, max_dist + abs(edge_distance - nodes[:-1][::-1])
            )
            self.distance_cells_center = np.c_[
                self.distance_cells_center,
                max_dist + abs(edge_distance - mid_cells_x[:, ::-1]),
            ]

            self.cells_area = np.c_[self.cells_area, area[:, ::-1]]

        else:
            self.primary_velocity = np.c_[edge_primary_velocity, self.primary_velocity]
            self.secondary_velocity = np.c_[
                edge_secondary_velocity, self.secondary_velocity
            ]
            self.vertical_velocity = np.c_[
                edge_vertical_velocity, self.vertical_velocity
            ]
            self.rssi = np.c_[
                np.tile(np.nan, edge_primary_velocity.shape),
                self.rssi,
            ]
            self.count_valid = np.c_[
                np.tile(np.nan, edge_primary_velocity.shape),
                self.count_valid,
            ]

            self.direction_ens = np.insert(
                self.direction_ens,
                0,
                np.tile(self.direction_ens[id_edge], edge_primary_velocity.shape[1]),
            )

            depth = (border_depths[1:] + border_depths[:-1]) / 2
            self.depths = np.insert(self.depths, 0, depth)
            self.depth_cells_center = np.c_[mid_cells_y, self.depth_cells_center]
            self.depth_cells_layers = np.c_[edge_layers, self.depth_cells_layers]

            nan_array = np.tile(np.nan, len(depth))
            self.temperature = np.insert(self.temperature, 0, nan_array)

            self.borders_ens = np.insert(
                self.borders_ens + edge_distance, 0, nodes[:-1]
            )

            self.distance_cells_center = np.c_[
                mid_cells_x, self.distance_cells_center + edge_distance
            ]

            self.cells_area = np.c_[area, self.cells_area]

            for transect in self.data_transects:
                transect["acs_distance"] = transect["acs_distance"] + edge_distance

    def compute_discharge(self):
        """Compute streamwise velocity and discharge."""

        direction_meas = np.arctan2(-1, self.slope)

        distance = (self.borders_ens[1:] + self.borders_ens[:-1]) / 2

        if any(distance[~np.isnan(self.direction_ens)]):
            direction_ens = griddata(
                distance[~np.isnan(self.direction_ens)],
                self.direction_ens[~np.isnan(self.direction_ens)],
                distance,
            )

            streamwise_velocity = self.primary_velocity * np.cos(
                direction_ens - direction_meas
            ) + self.secondary_velocity * np.sin(direction_ens - direction_meas)

            transverse_velocity = self.primary_velocity * np.sin(
                direction_ens - direction_meas
            ) - self.secondary_velocity * np.cos(direction_ens - direction_meas)

            cells_discharge = self.cells_area * streamwise_velocity
            total_discharge = np.nansum(cells_discharge)

            self.streamwise_velocity = streamwise_velocity * -self._unit
            self.transverse_velocity = transverse_velocity * -self._unit
            self.cells_discharge = cells_discharge * -self._unit
            self.total_discharge = total_discharge * -self._unit
        else:
            self.streamwise_velocity = np.tile(np.nan, self.primary_velocity.shape)
            self.transverse_velocity = np.tile(np.nan, self.primary_velocity.shape)
            self.cells_discharge = np.tile(np.nan, self.primary_velocity.shape)
            self.total_discharge = np.nan

    def utm_2_distance(self):
        """Correct UTM coordinates to a (0, 0) starting point.

        Returns:
            x: np.array
            y: np.array
        """

        x = self.x - self.x[0]
        y = self.y - self.y[0]

        return x[1:], y[1:]

    def utm_2_decimaldegrees(self):
        """Convert UTM coordinates to decimal degrees.

        Returns:
            lat: np.array
            lon: np.array
        """

        try:
            lat, lon = utm.to_latlon(
                self.x,
                self.y,
                zone_number=self.gps_zone_number,
                zone_letter=self.gps_zone_letter,
            )

        except BaseException:
            lat = np.tile(np.nan, len(self.y))
            lon = np.tile(np.nan, len(self.x))

        return lat[1:], lon[1:]

    def compute_transverse_mixing_coef(self, karman=0.41, manning=0.026):
        """Compute Transverse Mixing Coefficient from Jung 2019 (DOI: 10.1061/(ASCE)HY.1943-7900.0001638)

        Parameters:
            karman: float
                Von Karman constant usually taken as 0.41
            manning: float
                 Manning’s roughness coefficient of the study area
        """
        # Constants
        g = 9.807

        # Average transverse velocity on ensembles
        tranverse_velocity_deviation = np.subtract(
            self.transverse_velocity, np.nanmean(self.transverse_velocity, axis=0)
        )

        mean_streamwise_velocity = np.nanmean(self.streamwise_velocity)
        distance_ens = (self.borders_ens[1:] + self.borders_ens[:-1]) / 2
        depth_ens = copy.deepcopy(self.depths)

        # Add left edge
        _, left_coef = self.left_geometry
        left_distance = self.borders_ens[0]
        if left_coef == 0.707:
            distance_ens = np.insert(distance_ens, 0, [left_distance, left_distance])
            depth_ens = np.insert(depth_ens, 0, [0, depth_ens[0]])
        else:
            distance_ens = np.insert(distance_ens, 0, left_distance)
            depth_ens = np.insert(depth_ens, 0, 0)

        # Add left edge
        _, right_coef = self.right_geometry
        right_distance = self.borders_ens[-1]
        if left_coef == 0.707:
            distance_ens = np.append(distance_ens, [right_distance, right_distance])
            depth_ens = np.append(depth_ens, [depth_ens[-1], 0])
        else:
            distance_ens = np.append(distance_ens, right_distance)
            depth_ens = np.append(depth_ens, 0)

        # Compute area following trapezoidal method
        area = np.abs(np.trapz(distance_ens, depth_ens))

        # Compute perimeter
        perimeter = self.compute_perimeter(distance_ens, depth_ens)

        # Compute hydraulic radius
        hydraulic_radius = area / perimeter

        # Compute shear velocity
        shear_velocity = np.sqrt(
            g * (manning * mean_streamwise_velocity) ** 2 * hydraulic_radius ** (-1 / 3)
        )

        # Compute distance from streambed
        z = self.depths - self.depth_cells_center
        z[z < 0] = np.nan

        # Compute vertical mixing coefficient
        vertical_mixing_coefficient = (
            karman * z * (1 - z / self.depths) * shear_velocity
        )

        # Compute transverse mixing coefficient
        depths = np.where(self.depths == 0, np.nan, self.depths)
        cells_height = self.depth_cells_layers[1:, :] - self.depth_cells_layers[:-1, :]
        transverse_mixing_coefficient = np.tile(np.nan, self.depths.shape[0])

        # Compute among ensembles
        for i in range(len(self.depths)):
            heights = cells_height[:, i]
            valid_cells = np.count_nonzero(~np.isnan(z[:, i]))
            total_ens = 0
            # Run among depth layers from current ensemble from the bottom
            for j in range(valid_cells):
                idx_j = valid_cells - j - 1
                total_mixing_coef = 0

                # Run among depth layers until current depth layer from the bottom
                for k in range(j + 1):
                    idx_k = valid_cells - k - 1
                    z_k = heights[idx_k]
                    total_transverse = 0

                    # Run among depth layers until previously selected depth layer
                    for l in range(k + 1):
                        idx_l = valid_cells - l - 1
                        z_l = heights[idx_l]
                        total_transverse += z_l * tranverse_velocity_deviation[idx_l, i]
                    total_mixing_coef += (
                        z_k * total_transverse / vertical_mixing_coefficient[idx_k, i]
                    )

                total_ens += (
                    heights[idx_j]
                    * tranverse_velocity_deviation[idx_j, i]
                    * total_mixing_coef
                )

            transverse_mixing_coefficient[i] = (-1 / depths[i]) * total_ens

        self.transverse_mixing_coefficient = copy.deepcopy(
            transverse_mixing_coefficient
        )

    @staticmethod
    def compute_perimeter(distance, depths):
        """Compute perimeter for MAP averaged profile

        Parameters:
            distance: array
                Distances from the left bank for each vertical
            depths: array
                 Depths for each vertical

        Return:
            perimeter: float
                Value of the perimeter

        """
        points = np.vstack((distance, depths)).T
        perimeter = 0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            d = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            perimeter += d

        return perimeter

    def create_map_df(self, units, manufacturer=None, verticals=False):
        """Create a pandas dataframe of data computed by MAP.

        Parameters
        ----------
        units: dict
            Specified unit labels and conversion
        manufacturer: str
            Identifies manufacturer
        verticals: bool
            Use only vertical data

        Returns
        -------
        df: pd.DataFrame
            Requested map data
        """

        distance_x, distance_y = self.utm_2_distance()
        lat, lon = self.utm_2_decimaldegrees()
        if manufacturer == "TRDI":
            intensity_label = "RSSI (counts)"
        elif manufacturer == "SonTek":
            intensity_label = "SNR (dB)"
        else:
            intensity_label = "Intensity"
        row, col = self.primary_velocity.shape
        ens_mid = (self.borders_ens[1:] + self.borders_ens[:-1]) * 0.5

        direction_section = np.arctan2(self.slope, 1)
        u = self.streamwise_velocity * np.sin(
            direction_section
        ) + self.transverse_velocity * np.cos(direction_section)
        v = self.transverse_velocity * np.sin(
            direction_section
        ) - self.streamwise_velocity * np.cos(direction_section)

        east_velocity = u * -1 * self._unit
        north_velocity = v * -1 * self._unit

        magnitude = np.sqrt(north_velocity**2 + east_velocity**2)

        if not verticals:
            data = {
                "Vertical": np.repeat(np.arange(col), row),
                "Distance (Left bank) "
                + units["label_L"]: np.repeat(ens_mid, row) * units["L"],
                "Distance X "
                + units["label_L"]: np.repeat(distance_x, row) * units["L"],
                "Distance Y "
                + units["label_L"]: np.repeat(distance_y, row) * units["L"],
                "Latitude": np.repeat(lat, row),
                "Longitude": np.repeat(lon, row),
                "Primary velocity "
                + units["label_V"]: self.primary_velocity.ravel(order="F") * units["V"],
                "Secondary velocity "
                + units["label_V"]: self.secondary_velocity.ravel(order="F")
                * units["V"],
                "Streamwise velocity "
                + units["label_V"]: self.streamwise_velocity.ravel(order="F")
                * units["V"],
                "Transverse velocity (Left to Right) "
                + units["label_V"]: self.transverse_velocity.ravel(order="F")
                * units["V"],
                "Vertical velocity "
                + units["label_V"]: self.vertical_velocity.ravel(order="F")
                * units["V"],
                "North velocity "
                + units["label_V"]: north_velocity.ravel(order="F") * units["V"],
                "East velocity "
                + units["label_V"]: east_velocity.ravel(order="F") * units["V"],
                "Magnitude" + units["label_V"]: magnitude.ravel(order="F") * units["V"],
                "Depth " + units["label_L"]: np.repeat(self.depths, row) * units["L"],
                "Cells discharge "
                + units["label_Q"]: self.cells_discharge.ravel(order="F") * units["Q"],
                "Cells area "
                + units["label_A"]: self.cells_area.ravel(order="F") * units["A"],
                "Distance cells center "
                + units["label_L"]: self.distance_cells_center.ravel(order="F")
                * units["L"],
                "Depth cells center "
                + units["label_L"]: self.depth_cells_center.ravel(order="F")
                * units["L"],
                "Temperature": np.repeat(self.temperature, row),
                intensity_label: self.rssi.ravel(order="F"),
                "Nb. of Transects averaged": self.count_valid.ravel(order="F"),
            }
        else:
            data = {
                "Vertical": np.arange(col),
                "Distance (Left bank) " + units["label_L"]: ens_mid * units["L"],
                "Distance X " + units["label_L"]: distance_x * units["L"],
                "Distance Y " + units["label_L"]: distance_y * units["L"],
                "Latitude": lat,
                "Longitude": lon,
                "Depth " + units["label_L"]: self.depths * units["L"],
            }

        df = pd.DataFrame(data)
        if "Cells discharge " + units["label_Q"] in df.columns:
            df = df[df["Cells discharge " + units["label_Q"]].notna()]

        return df

    def export_csv(
        self,
        path,
        units,
        delimiter="comma delimited",
        manufacturer=None,
        verticals=False,
    ):
        """Exports map data to ascii file with specified delimiter.

        Parameters
        ----------
        path: str
            path to exported file
        units: dict
            dictionary of unit labels and conversions
        delimiter: str
            type of delimiter to use
        manufacturer: str
            name of instrument manufacturer
        verticals: bool
            Indicates if only vertical data is used
        """
        date = datetime.today().strftime("%d-%b-%Y")
        header = ["# " + __qrev_version__ + "\n", "# Exported " + date + "\n"]

        with open(path, "w") as file:
            file.writelines(header)

        df = self.create_map_df(
            units=units, manufacturer=manufacturer, verticals=verticals
        )

        if "comma" in delimiter:
            sep = ","
        elif "colon" in delimiter:
            sep = ";"
        else:
            sep = " "

        df.to_csv(path, sep=sep, index=False, mode="a", header=True)

    def export_shiptrack_csv(
        self,
        path,
        units,
        delimiter="comma delimited",
    ):
        """Exports shiptrack data to ascii file with specified delimiter.

        Parameters
        ----------
            path: str
                path to exported file
            units: dict
                dictionary of unit labels and conversions
            delimiter: str
                type of delimiter to use

        """

        if self.streamwise_velocity is not None:
            direction_section = np.arctan2(self.slope, 1)

            u = self.streamwise_velocity * np.sin(
                direction_section
            ) + self.transverse_velocity * np.cos(direction_section)
            v = self.transverse_velocity * np.sin(
                direction_section
            ) - self.streamwise_velocity * np.cos(direction_section)

            u = u * -1 * self._unit
            v = v * -1 * self._unit

            u_mean = np.nanmean(u, axis=0) * units["V"]
            v_mean = np.nanmean(v, axis=0) * units["V"]

            x = (self.x[1:] + self.x[:-1]) / 2
            y = (self.y[1:] + self.y[:-1]) / 2

            df = pd.DataFrame({"x": x, "y": y, "u": u_mean, "v": v_mean})

        else:
            return

        # write file header
        date = datetime.today().strftime("%d-%b-%Y")

        # Set X/Y meta data for header
        if self.gps_zone_letter is None:
            xy_str = "# X/Y: Distance in " + units["label_L"]
        else:
            xy_str = "# X/Y: UTM North coordinates"

        # set velocity meta data for header
        vel_str = "# Velocity: " + units["label_V"]

        header = [
            "# " + __qrev_version__ + "\n",
            "# Exported " + date + "\n" + xy_str + "\n" + vel_str + "\n",
        ]

        with open(path, "w") as file:
            file.writelines(header)

        # set the delimiter
        if "comma" in delimiter:
            sep = ","
        elif "colon" in delimiter:
            sep = ";"
        else:
            sep = " "

        # write dataframe to file
        df.to_csv(path, sep=sep, index=False, mode="a", header=True)

    def export_kml(self, meas, path, units, palette="jet", arrow_scale=None, v_min=None, v_max=None,):
        """Create KML file for MAP, including color bar.

        Parameters
        ----------
        meas: Measurement
            Object of Measurement class
        path: str
            Path to save kml file
        units: dict
            Dictionary of unit labels and conversions
        palette: str
            Cmap palette to use for arrows color bar
        arrow_scale: float
            Equivalent scale (in meter) for 1m/s velocity
        v_min: float
            Min velocity of the gradient cbar
        v_max: float
            Max velocity of the gradient cbar
        """
        print(f"Starting KML export to: {path}")

        # Create KML object
        kml = simplekml.Kml(open=1)

        # Create a shiptrack for each checked transect
        lat = []
        lon = []

        try:
            for transect_idx in meas.checked_transect_idx:
                transect_lon = meas.transects[transect_idx].gps.gga_lon_ens_deg
                transect_lon = transect_lon[np.logical_not(np.isnan(transect_lon))]
                transect_lat = meas.transects[transect_idx].gps.gga_lat_ens_deg
                transect_lat = transect_lat[np.logical_not(np.isnan(transect_lat))]

                if len(transect_lat) > 0 and len(transect_lon) > 0:
                    lat.extend(transect_lat)
                    lon.extend(transect_lon)
                    line_name = meas.transects[transect_idx].file_name[:-4]
                    lon_lat = tuple(zip(transect_lon, transect_lat))
                    _ = kml.newlinestring(name=line_name, coords=lon_lat)
        except Exception as e:
            print(f"Error creating shiptracks: {e}")

        # Check if we have valid coordinates before proceeding
        if len(lat) == 0 or len(lon) == 0:
            print("Warning: No valid GPS coordinates found. KML file cannot be created.")
            kml.save(path)
            return

        # Convert lists to arrays
        lat = np.array(lat)
        lon = np.array(lon)

        # Get UTM zone from valid coordinates
        valid_lat_idx = np.logical_not(np.isnan(lat))
        valid_lon_idx = np.logical_not(np.isnan(lon))
        valid_idx = np.logical_and(valid_lat_idx, valid_lon_idx)

        if not np.any(valid_idx):
            print("Warning: No valid lat/lon coordinates. KML file cannot be created.")
            kml.save(path)
            return

        try:
            _, _, zone_number, zone_letter = utm.from_latlon(lat[valid_idx][0], lon[valid_idx][0])
            print(f"Using UTM zone: {zone_number}{zone_letter}")
        except Exception as e:
            print(f"Error getting UTM zone: {e}")
            kml.save(path)
            return

        # Plot mean section
        try:
            x = copy.deepcopy(self.x)
            y = copy.deepcopy(self.y)

            if len(x) > 0 and len(y) > 0 and not np.isnan(x).all() and not np.isnan(y).all():
                section_lat, section_lon = utm.to_latlon(x, y, zone_number, zone_letter)
                lon_lat = tuple(zip(section_lon, section_lat))
                lin = kml.newlinestring(name="MAP averaged cross-section", coords=lon_lat)
                lin.style.linestyle.color = "ff0000ff"  # Red line
                lin.style.linestyle.width = 3  # Make line more visible

                # Store for later use
                lat = section_lat
                lon = section_lon
            else:
                print("Warning: MAP data invalid. Using transect coordinates instead.")
        except Exception as e:
            print(f"Error plotting mean section: {e}")

        # Get mid ensemble coordinates for arrow placement
        try:
            if len(self.x) > 1 and len(self.y) > 1:
                x_kml = (self.x[1:] + self.x[:-1]) / 2
                y_kml = (self.y[1:] + self.y[:-1]) / 2
                lat_vec, lon_vec = utm.to_latlon(x_kml, y_kml, zone_number, zone_letter)
            else:
                print("Warning: Not enough MAP data points for velocity arrows.")
                kml.save(path)
                return
        except Exception as e:
            print(f"Error calculating mid ensemble coordinates: {e}")
            kml.save(path)
            return

        # Calculate arrow parameters
        try:
            # Always get all 6 return values from auto_arrow
            u_mean, v_mean, vel_norm, arrow_scale_auto, v_max_auto, v_min_auto = self.auto_arrow(
                lat=lat, lon=lon, meas=meas, zone_number=zone_number, zone_letter=zone_letter)

            # Use auto values if input parameters are None
            if arrow_scale is None:
                arrow_scale = arrow_scale_auto
                print(f"Using auto arrow scale: {arrow_scale}")
            if v_min is None:
                v_min = v_min_auto
                print(f"Using auto v_min: {v_min}")
            if v_max is None:
                v_max = v_max_auto
                print(f"Using auto v_max: {v_max}")

            print(f"Arrow parameters: scale={arrow_scale}, v_min={v_min}, v_max={v_max}")
        except Exception as e:
            print(f"Error calculating arrows: {e}")
            kml.save(path)
            return

        # Create folder to save water velocity arrows
        w_folder = kml.newfolder(name="Water velocity")

        # Get color map
        cmap = plt.get_cmap(palette)
        norm = mcolors.Normalize(vmin=v_min * units["V"], vmax=v_max * units["V"])

        # Check if velocity data is valid
        if vel_norm is None or len(vel_norm) == 0 or np.isnan(vel_norm).all():
            print("Warning: No valid velocity data for coloring arrows.")
        else:
            # Calculate colors for each arrow
            colors = np.round(cmap(norm(vel_norm * units["V"])) * 255).astype(int)

            # Replace NaN values with zeros for plotting
            u_mean = np.where(np.isnan(u_mean), 0, u_mean)
            v_mean = np.where(np.isnan(v_mean), 0, v_mean)

            # Plot arrows
            print(f"Creating {len(u_mean)} velocity arrows...")
            arrows_created = 0
            for i in range(len(u_mean)):
                try:
                    if np.isfinite(u_mean[i]) and np.isfinite(v_mean[i]) and np.isfinite(vel_norm[i]):
                        r, g, b, a = colors[i]
                        self.plot_arrow(
                            w_folder,
                            (lon_vec[i], lat_vec[i]),
                            u_mean[i],
                            v_mean[i],
                            f"Water Velocity {i+1}",
                            arrow_scale,
                            color=simplekml.Color.rgb(r, g, b, a),
                        )
                        arrows_created += 1
                except Exception as e:
                    print(f"Error plotting arrow {i}: {e}")
            print(f"Successfully created {arrows_created} arrows")

        # ===== Handle overlay image =====
        # Create colorbar image
        fig, ax = plt.subplots(figsize=(10, 1))
        cb_label = 'Velocity Vector Color Scale' + units['label_V']
        fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap),
                     cax=ax, orientation='horizontal', label=cb_label)
        overlay_image_path = path[:-4] + "_color_bar.png"
        fig.savefig(
            overlay_image_path, dpi=300, bbox_inches="tight"
        )

        # ==== Add as screen overlay (always visible) ====
        screen = kml.newscreenoverlay(name="Velocity Scale")
        screen.icon.href = overlay_image_path

        # Position in top-right corner
        screen.overlayxy = simplekml.OverlayXY(x=1, y=1, xunits=simplekml.Units.fraction, yunits=simplekml.Units.fraction)
        screen.screenxy = simplekml.ScreenXY(x=0.8, y=0.95, xunits=simplekml.Units.fraction, yunits=simplekml.Units.fraction)

        # Set fixed size for consistent appearance regardless of original image dimensions
        screen.size.x = 0.6  # Width is 80% of screen width
        screen.size.y = 0.10   # Height is 12% of screen height
        screen.size.xunits = simplekml.Units.fraction  # Use screen fraction instead of pixels
        screen.size.yunits = simplekml.Units.fraction  # Use screen fraction instead of pixels

        # Save the KML file
        kml.save(path)

    def auto_arrow(self, lat=None, lon=None, meas=None, zone_number=None, zone_letter=None):
        """Create KML file for MAP.

        Parameters
        ----------
        lat: Measurement
            'left' or 'right'
        lon: str
            Path to save kml file
        meas: Measurement
            Objet of Measurement class
        zone_number: int
            UTM zone number
        zone_letter: str
            UTM zone letter

        Returns
        ----------
        u_mean: array
            Mean North velocity on each vertical
        v_mean: array
            Mean East velocity on each vertical
        vel_norm: array
            Norm of mean velocity on each vertical
        arrow_length_m: float
            Automatic arrow size for 1m/s velocity
        v_min: float
            Automatic vmin value for arrows cbar
        v_max: float
            Automatic vmax value for arrows cbar

        """
        # Get mean velocity of each ensemble
        direction_section = np.arctan2(self.slope, 1)
        u = self.streamwise_velocity * np.sin(
            direction_section
        ) + self.transverse_velocity * np.cos(direction_section)
        v = self.transverse_velocity * np.sin(
            direction_section
        ) - self.streamwise_velocity * np.cos(direction_section)

        u = u * -1 * self._unit
        v = v * -1 * self._unit
        u_mean = np.nanmean(u, axis=0)
        v_mean = np.nanmean(v, axis=0)

        # Define length
        vel_norm = np.sqrt(u_mean**2 + v_mean**2)

        if lat is None or lon is None:
            if meas is not None:
                transect_idx = meas.checked_transect_idx[0]
                lon = meas.transects[transect_idx].gps.gga_lon_ens_deg
                lon = lon[np.logical_not(np.isnan(lon))]
                lat = meas.transects[transect_idx].gps.gga_lat_ens_deg
                lat = lat[np.logical_not(np.isnan(lat))]
                _, _, zone_number, zone_letter = utm.from_latlon(lat, lon)
                x = copy.deepcopy(self.x)
                y = copy.deepcopy(self.y)
                lat, lon = utm.to_latlon(x, y, zone_number, zone_letter)
            else:
                return u_mean, v_mean, vel_norm

        # Default arrow length : half the width of the section
        arrow_length = 0.5 * np.sqrt((lat[-1] - lat[0]) ** 2 + (lon[-1] - lon[0]) ** 2)
        start_point = utm.from_latlon(
            lat[0], lon[0], force_zone_number=zone_number, force_zone_letter=zone_letter
        )
        end_point = utm.from_latlon(
            lat[0] + arrow_length,
            lon[0],
            force_zone_number=zone_number,
            force_zone_letter=zone_letter,
        )
        arrow_length_m = sfrnd(
            np.sqrt(
                (end_point[0] - start_point[0]) ** 2
                + (end_point[1] - start_point[1]) ** 2
            ),
            2,
        )

        v_min = 0
        v_max = np.nanmax(vel_norm)

        return u_mean, v_mean, vel_norm, arrow_length_m, v_max, v_min

    def plot_arrow(self, folder, coord_start, ve, vn, name, arrow_scale, color=None):
        """
        Draw an arrow based on the North and East speed components.

        Parameters
        ----------
        folder: simplekml object
            kml folder to fold arrow (water velocity or moving-bed velocity)
        coord_start: tuple
            Arrow starting point coordinates (longitude, latitude)
        ve: float
            East velocity component
        vn: float
            North velocity component
        name: string
            Name of the arrow
        arrow_scale: float
            Scales arrow size
        color: string
            Kml Hex color of the arrow
        """
        distance = arrow_scale * np.sqrt(ve**2 + vn**2)
        coord_end = self.compute_new_coordinates(
            start_point=coord_start, distance=distance, bearing=math.atan2(ve, vn)
        )

        # Creation of the LineString tag for the arrow line
        line = folder.newlinestring(name=name, coords=[coord_start, coord_end])
        line.style.linestyle.width = 2

        # Creating the triangle at the tip of the arrow
        arrow_polygon = folder.newpolygon(name=name)
        arrow_coordinates_base = self.compute_arrow_coordinates_base(
            coord_start, coord_end, ve, vn
        )
        arrow_polygon.outerboundaryis = arrow_coordinates_base
        arrow_polygon.style.linestyle.width = 2

        if color is not None:
            line.style.linestyle.color = color
            arrow_polygon.style.linestyle.color = color

    @staticmethod
    def compute_arrow_coordinates_base(coord_start, coord_end, vx, vy):
        """
        Computes the coordinates of the points forming the angles of an arrow from the base.

        Parameters
        ----------
        coord_start: tuple
            Coordinates of the base of the arrow
        coord_end: tuple
            Coordinates of the head of the arrow
        vx: float
            East velocity component
        vy: float
            North velocity component

        Returns
        ----------
        arrow_coordinates: list(tuple)
            A list of tuples representing the coordinates of the points
            forming the head of the arrow
        """
        # Calculating the angle in radians from the speed components
        arrow_angle = math.atan2(vy, vx)

        # Coordinates of the arrowhead
        x_base, y_base = (
            0.2 * coord_start[0] + 0.8 * coord_end[0],
            0.2 * coord_start[1] + 0.8 * coord_end[1],
        )

        head_distance = np.sqrt(
            (coord_end[0] - x_base) ** 2 + (coord_end[1] - y_base) ** 2
        )
        head_size = head_distance * math.cos(math.radians(60))
        base_point2 = (
            x_base - head_size * math.sin(arrow_angle),
            y_base + head_size * math.cos(arrow_angle),
        )
        base_point3 = (
            x_base + head_size * math.sin(arrow_angle),
            y_base - head_size * math.cos(arrow_angle),
        )

        # Coordinates of the points forming the arrowhead
        arrow_coordinates = [coord_end, base_point2, coord_end, base_point3]

        return arrow_coordinates

    @staticmethod
    def compute_new_coordinates(start_point, distance, bearing):
        """
        Calculates the coordinates of the points forming the angles of an arrow from the base.

        Parameters
        ----------
        start_point: tuple
            Coordinates of the tail of the arrow
        distance: float
            Distance (in meters) to extend the arrow
        bearing: float
            Orientation of the arrow

        Returns
        ----------
        coord_end: tuple
            Coordinates of the head of the arrow
        """
        earth_radius = 6371000
        lat1, lon1 = math.radians(start_point[1]), math.radians(start_point[0])
        d_over_earth_radius = distance / earth_radius
        lat2 = math.asin(
            math.sin(lat1) * math.cos(d_over_earth_radius)
            + math.cos(lat1) * math.sin(d_over_earth_radius) * math.cos(bearing)
        )

        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(d_over_earth_radius) * math.cos(lat1),
            math.cos(d_over_earth_radius) - math.sin(lat1) * math.sin(lat2),
        )
        return math.degrees(lon2), math.degrees(lat2)
