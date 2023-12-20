import copy
from datetime import datetime

import numpy as np
import pandas as pd
import scipy as sc
import simplekml
import utm
from scipy.optimize.minpack import curve_fit
from sklearn.linear_model import LinearRegression

from Classes import __qrev_version__
from MiscLibs.abba_2d_interpolation import abba_idw_interpolation
from MiscLibs.common_functions import cart2pol, pol2cart, nan_greater


class MAP(object):
    """Multitransect Averaged Profile (MAP) generates an average profile of selected transects.

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
    depth_by_transect: np.list(np.array(float))
        Depth for each transect

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

    cells_discharge: np.array(float) 1D
        MAP discharge for each cell
    settings: dict
        MAP settings for processing
    total_discharge: float
        MAP total discharge
    """

    def __init__(self):
        """Initialize class and instance variables."""

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
            None  # East distance after projection on average cross-section
        )
        self.y_projected = (
            None  # North distance after projection on average cross-section
        )
        self.acs_distance = None  # Distance from the left bank on average cross-section

        self.primary_velocity = None  # Primary velocity (ROZ) of each MAP cell
        self.secondary_velocity = None  # Secondary velocity (ROZ) of each MAP cell
        self.vertical_velocity = None  # Vertical velocity of each MAP cell
        self.streamwise_velocity = None  # Streamwise velocity of each MAP cell
        self.transverse_velocity = None  # Transverse velocity of each MAP cell
        self.east_velocity = None  # Velocity component in East direction
        self.north_velocity = None  # Velocity component in North direction
        self.depths = None  # Depths for each MAP vertical
        self.depth_by_transect = None  # Depth for each transect
        self.temperature = None  # Temperature for each vertical
        self.temperature_by_transect = None  # Temperature for each transect

        self.rssi = None  # RSSI of each MAP cell
        self.count_valid = None  # Count used values to compute each cell
        self.direction_ens = None  # Main direction of each MAP ensemble
        self.borders_ens = (
            None  # Borders of each MAP vertical (distance from left bank)
        )
        self._unit = 1
        self._x_left = 0  # Default x position in m
        self._y_left = 0  # Default y position in m
        self.x = None  # x coordinates
        self.y = None  # y coordinates
        self.main_depth_layers = (
            None  # Borders of each MAP depth layer (distance from surface)
        )
        self.depth_cells_center = None  # Depth of each MAP cell center
        self.depth_cells_border = None  # Depth layers
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

    def populate_data(
        self,
        meas,
        node_horizontal_user=None,
        node_vertical_user=None,
        extrap_option=True,
        edges_option=True,
        interp_option=False,
        n_burn=None,
    ):
        """Attributes
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
        interp_option: bool
            Indicates if velocities interpolation should be applied
        """

        # Get meas current parameters
        settings = meas.current_settings()
        checked_transect_idx = meas.checked_transect_idx
        if n_burn is None:
            n_burn = int(1 + len(meas.checked_transect_idx) / 3)

        # Get main data from selected transects
        data_transects = self.collect_data(meas, settings["NavRef"])

        # Compute coefficients of the average cross-section
        self.compute_coef()

        # Project raw coordinates on average cross-section
        acs_distance_raw = self.project_transect()

        # Compare bathymetry and translate transects on average cross-section if needed
        if settings["NavRef"] == "gga_vel":
            self.acs_distance = acs_distance_raw
        else:
            self.translated_transects(acs_distance_raw, data_transects["depth_data"])

        # Define horizontal and vertical mesh
        self.compute_node_size(
            meas,
            data_transects,
            node_horizontal_user,
            node_vertical_user,
            extrap_option,
        )

        # Compute transect median velocity on each mesh (North, East and
        # vertical velocities) and depth on each vertical
        tr_nodes_data = self.compute_nodes_velocity(
            checked_transect_idx, data_transects
        )

        # Compute mesh mean value of selected transects
        self.compute_mean(tr_nodes_data, n_burn)

        if self.east_velocity is not None:
            # Compute primary and secondary velocity according Rozovskii projection
            self.compute_rozovskii(self.east_velocity, self.north_velocity)

            # Interpolate empty values
            if interp_option:
                self.compute_interpolation()

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
        Attributes
        ----------
        meas: Measurement
            Object of Measurement class
        interp_option: bool
            Indicates if velocities interpolation should be applied
        nav_ref: str
            Current navigation reference from settings
        Returns
        -------
        data_transects: dict
            Dictionary of transects data loaded from Measurement
        """

        # Create empty lists to iterate
        depth_data = []
        temperature_data = []
        w_vel_x = []
        w_vel_y = []
        w_vel_z = []
        orig_start_edge = []
        invalid_data = []
        cell_depth = []
        rssi = []
        self.x_raw_coordinates = []
        self.y_raw_coordinates = []

        checked_transect_idx = meas.checked_transect_idx

        left_param = np.tile([np.nan], (len(checked_transect_idx), 2))
        right_param = np.tile([np.nan], (len(checked_transect_idx), 2))

        for id_transect in checked_transect_idx:
            transect = meas.transects[id_transect]
            index_transect = checked_transect_idx.index(id_transect)
            in_transect_idx = transect.in_transect_idx

            # Verify that the transect has heading data before computing
            if not all(deg == 0 for deg in transect.sensors.heading_deg.internal.data):
                ship_data = transect.boat_vel.compute_boat_track(transect, nav_ref)

                if transect.orig_start_edge == "Right":
                    # Reverse transects in ordred to start at 0 on left edge
                    valid = transect.depths.bt_depths.valid_data[::-1]
                    if nav_ref == "gga_vel":
                        nan_idx = np.argwhere(
                            np.isnan(
                                transect.gps.gga_lat_ens_deg[::-1]
                                + transect.gps.gga_lon_ens_deg[::-1]
                            )
                        )
                        for i in nan_idx:
                            valid[i[0]] = False
                        lat = transect.gps.gga_lat_ens_deg[::-1][valid]
                        lon = transect.gps.gga_lon_ens_deg[::-1][valid]

                        coords = utm.from_latlon(lat, lon)
                        x_transect = coords[0]
                        y_transect = coords[1]
                        self.gps_zone_number = coords[2]
                        self.gps_zone_letter = coords[3]

                    else:
                        dmg_ind = np.where(
                            abs(ship_data["dmg_m"]) == max(abs(ship_data["dmg_m"]))
                        )[0][0]
                        x_track = (
                            ship_data["track_x_m"] - ship_data["track_x_m"][dmg_ind]
                        )
                        y_track = (
                            ship_data["track_y_m"] - ship_data["track_y_m"][dmg_ind]
                        )
                        x_transect = x_track[::-1]
                        y_transect = y_track[::-1]
                        x_transect = x_transect[valid]
                        y_transect = y_transect[valid]

                    # Depth
                    depth_selected = getattr(transect.depths, transect.depths.selected)
                    depth_transect = depth_selected.depth_processed_m[::-1]
                    cells_depth = depth_selected.depth_cell_depth_m[:, ::-1]

                    # Temperature
                    temp_selected = getattr(
                        transect.sensors.temperature_deg_c,
                        transect.sensors.temperature_deg_c.selected,
                    )
                    temp_transect = temp_selected.data[::-1]

                    # Velocity data
                    vel_x = np.copy(transect.w_vel.u_processed_mps[:, ::-1])
                    vel_y = np.copy(transect.w_vel.v_processed_mps[:, ::-1])
                    vel_z = np.copy(transect.w_vel.w_mps[:, ::-1])
                    invalid = np.logical_not(
                        transect.w_vel.valid_data[0, :, in_transect_idx]
                    ).T[:, ::-1]

                    vel_x[invalid] = np.nan
                    vel_y[invalid] = np.nan
                    vel_z[invalid] = np.nan
                    x_velocity = vel_x[:, valid]
                    y_velocity = vel_y[:, valid]
                    z_velocity = vel_z[:, valid]

                    # RSSI data
                    rssi_temp = np.nanmean(transect.w_vel.rssi, axis=0)[:, ::-1]
                    rssi_temp[invalid] = np.nan
                    rssi_mean = rssi_temp[:, valid]

                else:
                    valid = transect.depths.bt_depths.valid_data
                    if nav_ref == "gga_vel":
                        nan_idx = np.argwhere(
                            np.isnan(
                                transect.gps.gga_lat_ens_deg
                                + transect.gps.gga_lon_ens_deg
                            )
                        )
                        for i in nan_idx:
                            valid[i[0]] = False
                        lat = transect.gps.gga_lat_ens_deg[valid]
                        lon = transect.gps.gga_lon_ens_deg[valid]

                        coords = utm.from_latlon(lat, lon)
                        x_transect = coords[0]
                        y_transect = coords[1]
                        self.gps_zone_number = coords[2]
                        self.gps_zone_letter = coords[3]
                    else:
                        x_transect = ship_data["track_x_m"]
                        y_transect = ship_data["track_y_m"]
                        x_transect = x_transect[valid]
                        y_transect = y_transect[valid]

                    # Depth
                    depth_selected = getattr(transect.depths, transect.depths.selected)
                    depth_transect = depth_selected.depth_processed_m
                    cells_depth = depth_selected.depth_cell_depth_m

                    # Velocity data
                    vel_x = np.copy(transect.w_vel.u_processed_mps)
                    vel_y = np.copy(transect.w_vel.v_processed_mps)
                    vel_z = np.copy(transect.w_vel.w_mps)
                    invalid = np.logical_not(
                        transect.w_vel.valid_data[0, :, in_transect_idx]
                    ).T

                    vel_x[invalid] = np.nan
                    vel_y[invalid] = np.nan
                    vel_z[invalid] = np.nan
                    x_velocity = vel_x[:, valid]
                    y_velocity = vel_y[:, valid]
                    z_velocity = vel_z[:, valid]

                    # Temperature
                    temp_selected = getattr(
                        transect.sensors.temperature_deg_c,
                        transect.sensors.temperature_deg_c.selected,
                    )
                    temp_transect = temp_selected.data

                    # RSSI data
                    rssi_temp = np.nanmean(transect.w_vel.rssi, axis=0)
                    rssi_temp[invalid] = np.nan
                    rssi_mean = rssi_temp[:, valid]

                self.x_raw_coordinates.append(x_transect)
                self.y_raw_coordinates.append(y_transect)
                depth_data.append(depth_transect[valid])
                cell_depth.append(cells_depth[:, valid])
                temperature_data.append(temp_transect[valid])
                w_vel_x.append(x_velocity)
                w_vel_y.append(y_velocity)
                w_vel_z.append(z_velocity)
                invalid_data.append(invalid[:, valid])
                rssi.append(rssi_mean)

                # Edges parameters
                left = [
                    meas.transects[id_transect].edges.left.distance_m,
                    meas.discharge[id_transect].edge_coef(
                        "left", meas.transects[id_transect]
                    ),
                ]
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

                self.left_geometry = np.nanmedian(left_param, axis=0)
                self.right_geometry = np.nanmedian(right_param, axis=0)

                orig_start_edge.append(transect.orig_start_edge)

        data_transects = {
            "w_vel_x": w_vel_x,
            "w_vel_y": w_vel_y,
            "w_vel_z": w_vel_z,
            "depth_data": depth_data,
            "orig_start_edge": orig_start_edge,
            "invalid_data": invalid_data,
            "cell_depth": cell_depth,
            "rssi": rssi,
            "temperature_data": temperature_data,
        }
        self.depth_by_transect = depth_data
        self.temperature_by_transect = temperature_data

        return data_transects

    def compute_coef(self):
        """Compute straight average cross-section from edges coordinates."""

        x_left = [item[0] for item in self.x_raw_coordinates]
        x_right = [item[-1] for item in self.x_raw_coordinates]
        y_left = [item[0] for item in self.y_raw_coordinates]
        y_right = [item[-1] for item in self.y_raw_coordinates]

        x_med_left = np.nanmedian(x_left)
        y_med_left = np.nanmedian(y_left)

        self.slope = (np.nanmedian(y_right) - y_med_left) / (
            np.nanmedian(x_right) - x_med_left
        )
        self.intercept = y_med_left - self.slope * x_med_left

        self._x_left = x_med_left
        self._y_left = y_med_left

        # if LEW is > the start bank was REW. If not REW was
        # the start and velocities should be inversed.
        if x_med_left > np.nanmedian(x_right):
            self._unit = -1
        else:
            self._unit = 1

    def project_transect(self):
        """Project transects on the average cross-section.
        Returns
        -------
        acs_distance: list(np.array(float))
            List of 1D arrays of the distance (uncorrected) from left bank on the average cross-section
        """
        self.x_projected = list()
        self.y_projected = list()

        # Project transect
        for i in range(len(self.x_raw_coordinates)):
            # Project x and y coordinates on the cross-section
            self.x_projected.append(
                (
                    self.x_raw_coordinates[i]
                    - self.slope * self.intercept
                    + self.slope * self.y_raw_coordinates[i]
                )
                / (self.slope**2 + 1)
            )
            self.y_projected.append(
                (
                    self.intercept
                    + self.slope * self.x_raw_coordinates[i]
                    + self.slope**2 * self.y_raw_coordinates[i]
                )
                / (self.slope**2 + 1)
            )

        left_x = np.nanmedian([item[0] for item in self.x_projected])
        left_y = np.nanmedian([item[0] for item in self.y_projected])

        # Boundaries on x and y coordinates for the selected transects
        x_boundaries = [
            min([min(l) for l in self.x_projected]),
            max([max(l) for l in self.x_projected]),
        ]
        y_boundaries = [
            min([min(l) for l in self.y_projected]),
            max([max(l) for l in self.y_projected]),
        ]

        # Compute distance on the average cross-section
        acs_distance = list()
        x_distance = np.array(self.x_projected, dtype=object) - min(
            x_boundaries, key=lambda x: abs(x - left_x)
        )
        y_distance = np.array(self.y_projected, dtype=object) - min(
            y_boundaries, key=lambda x: abs(x - left_y)
        )
        for i in range(len(self.x_projected)):
            acs_distance.append((x_distance[i] ** 2 + y_distance[i] ** 2) ** 0.5)

        return acs_distance

    def translated_transects(self, acs_distance_raw, depth_data):
        """Compare bathymetry and translate transects on average cross-section if needed.
        Attributes
        ----------
        acs_distance_raw: list(np.array(float))
            List of 1D arrays of the distance (uncorrected) from left bank on the average cross-section
        depth_data: list(np.array(float))
            List of 1D arrays of bathymetry from selected transects
        """

        acs_translated = list()
        # Use the first transect as reference and define a homogeneous x grid across measurement
        acs_translated.append(copy.deepcopy(acs_distance_raw[0]))
        max_tr = [max(l) for l in acs_distance_raw]
        min_tr = [min(l) for l in acs_distance_raw]
        id_max = np.argmax([max_i - min_i for max_i, min_i in zip(max_tr, min_tr)])
        grid_acs = np.arange(
            min([min(l) for l in acs_distance_raw]),
            max([max(l) for l in acs_distance_raw]),
            (
                max([max(l) for l in acs_distance_raw])
                - min([min(l) for l in acs_distance_raw])
            )
            / 100,
        )
        acs_depth_ref = sc.interpolate.griddata(
            acs_distance_raw[id_max], depth_data[id_max], grid_acs
        )

        for i in range(1, len(acs_distance_raw)):
            if i == id_max:
                acs_translated.append(acs_distance_raw[i])
                continue
            # Interpolate depth on x grid
            acs_depth = sc.interpolate.griddata(
                acs_distance_raw[i], depth_data[i], grid_acs
            )
            if not np.all(np.isnan(acs_depth)):
                first_valid_acs = int(np.argwhere(~np.isnan(acs_depth))[0])
                last_valid_acs = int(np.argwhere(~np.isnan(acs_depth))[-1])
                valid_acs_depth = last_valid_acs - first_valid_acs + 1
                acs_depth_valid = acs_depth[first_valid_acs : last_valid_acs + 1]

                # Find the best position to minimize median of sum square
                default_acs_ssd = np.nanmean(
                    (acs_depth_ref[:valid_acs_depth] - acs_depth_valid) ** 2
                )
                lag_acs_idx = 0
                for j in range(1, len(acs_depth_ref) - valid_acs_depth + 1):
                    acs_ssd = np.nanmean(
                        (acs_depth_ref[j : j + valid_acs_depth] - acs_depth_valid) ** 2
                    )
                    if (
                        acs_ssd < default_acs_ssd or np.isnan(default_acs_ssd)
                    ) and np.count_nonzero(
                        np.isnan(acs_depth_ref[j : j + valid_acs_depth])
                    ) < 0.5 * valid_acs_depth:
                        default_acs_ssd = acs_ssd
                        lag_acs_idx = j
                # Correct average cross-section distance by translation
                acs_corrected = acs_distance_raw[i] - (
                    grid_acs[first_valid_acs] - grid_acs[lag_acs_idx]
                )
                acs_translated.append(acs_corrected)
            else:
                acs_translated.append(acs_distance_raw[i])

        # Start from 0
        min_dist = min([min(l) for l in acs_translated])
        for i in range(len(acs_translated)):
            acs_translated[i] -= min_dist

        self.acs_distance = acs_translated

    def compute_auto_node_size(self, data_transects):
        """Computes auto node sizes.

        Parameters:
            data_transects: dict
                Dictionary of transects data loaded from Measurement

        """

        # compute width widths
        acs_distance = self.acs_distance

        flat_acs = np.sort(np.concatenate(acs_distance).ravel())
        self.auto_node_horz = np.nanmax(
            [
                np.quantile(flat_acs[1:] - flat_acs[:-1], 0.95),
                np.nanmedian(
                    np.abs([np.quantile(l[1:] - l[:-1], 0.95) for l in acs_distance])
                ),
            ]
        )

        # compute vertical
        self.auto_node_vert = np.nanmax(
            [
                0.1,
                2
                * (
                    data_transects["cell_depth"][0][1, 0]
                    - data_transects["cell_depth"][0][0, 0]
                ),
            ]
        )

    def compute_node_size(
        self,
        meas,
        data_transects,
        node_horizontal_user,
        node_vertical_user,
        extrap_option,
    ):
        """Define horizontal and vertical mesh

        Parameters:
        meas: Measurement
            Object of Measurement class
        data_transects: dict
            Dictionary of transects data loaded from Measurement
        node_horizontal_user: float
            Horizontal size of the mesh define by the user
        node_vertical_user: float
            Vertical size of the mesh define by the user
        extrap_option: bool
            Indicates if top/bottom extrapolation should be applied
        """

        # Meshs widths
        acs_distance = self.acs_distance
        # Define number of meshs on the average cross-section
        acs_total = max([max(l) for l in acs_distance]) - min(
            [min(l) for l in acs_distance]
        )
        if node_horizontal_user is None:
            if self.auto_node_horz is None:
                self.compute_auto_node_size(data_transects)
            node_horz = self.auto_node_horz
        else:
            node_horz = node_horizontal_user

        # Divise total length in same size meshs
        # TODO see logspace and normalized depth layer
        if not extrap_option:
            transect = meas.transects[meas.checked_transect_idx[0]]
            top_cell = (
                np.nanmedian(transect.depths.bt_depths.depth_cell_depth_m[0, :])
                - np.nanmedian(transect.depths.bt_depths.depth_cell_size_m[0, :]) / 2
            )
        else:
            top_cell = 0

        nb_horz = int(acs_total / node_horz)
        self.borders_ens = np.linspace(
            min([min(l) for l in acs_distance]),
            max([max(l) for l in acs_distance]) + 10**-5,
            nb_horz,
        )

        # Meshes height
        depth_data = data_transects["depth_data"]
        all_depth = np.array([item for subarray in depth_data for item in subarray])
        if node_vertical_user:
            self.main_depth_layers = np.round(
                np.arange(
                    top_cell,
                    np.nanmax(all_depth) + node_vertical_user,
                    node_vertical_user,
                ).tolist(),
                3,
            )
        else:
            if self.auto_node_vert is None:
                self.compute_auto_node_size(data_transects)
            lag = self.auto_node_vert
            self.main_depth_layers = np.arange(
                top_cell, np.nanmax(all_depth) + lag, lag
            )

    def compute_nodes_velocity(self, checked_transect_idx, data_transects):
        """Compute transect median velocity on each mesh (North, East and
        vertical velocities)
        and depth on each vertical

        Attributes
        ----------
        checked_transect_idx: list(int)
            List of selected transects
        data_transects: dict
            Dictionary of transects data loaded from Measurement

        Returns
        -------
        tr_nodes_data: dict
            Dictionary of data by transects
        """

        w_vel_x = data_transects["w_vel_x"]
        w_vel_y = data_transects["w_vel_y"]
        w_vel_z = data_transects["w_vel_z"]
        rssi_data = data_transects["rssi"]
        cell_depth = data_transects["cell_depth"]
        depth_data = data_transects["depth_data"]
        temperature_data = data_transects["temperature_data"]
        acs_distance = self.acs_distance

        node_mid = (self.borders_ens[1:] + self.borders_ens[:-1]) / 2
        # Create list to save transects interpolated on mesh grid
        transects_nodes = list()
        transects_node_x_velocity = np.tile(
            np.nan,
            (len(checked_transect_idx), len(self.main_depth_layers) - 1, len(node_mid)),
        )
        transects_node_y_velocity = np.tile(
            np.nan,
            (len(checked_transect_idx), len(self.main_depth_layers) - 1, len(node_mid)),
        )
        transects_node_vertical_velocity = np.tile(
            np.nan,
            (len(checked_transect_idx), len(self.main_depth_layers) - 1, len(node_mid)),
        )
        transects_node_rssi = np.tile(
            np.nan,
            (len(checked_transect_idx), len(self.main_depth_layers) - 1, len(node_mid)),
        )
        transects_node_depth = np.tile(
            np.nan, (len(checked_transect_idx), len(node_mid))
        )

        transects_node_temperature = np.tile(
            np.nan, (len(checked_transect_idx), len(node_mid))
        )

        for id_transect in checked_transect_idx:
            index_transect = checked_transect_idx.index(id_transect)
            w_vel_x_tr = w_vel_x[index_transect]
            w_vel_y_tr = w_vel_y[index_transect]
            w_vel_z_tr = w_vel_z[index_transect]
            cell_depth_tr = cell_depth[index_transect]
            depth_ens_tr = depth_data[index_transect]
            rssi_tr = rssi_data[index_transect]
            temperature_ens_tr = temperature_data[index_transect]

            # Find the representative mesh of each transect's vertical
            lag_distance = self.borders_ens[1] - self.borders_ens[0]
            data = {
                "Index_ensemble": np.arange(len(acs_distance[index_transect])),
                "Index_Node": [
                    int(i) for i in acs_distance[index_transect] / lag_distance
                ],
                "Distance_ensemble": acs_distance[index_transect],
            }
            df = pd.DataFrame(data)

            # Transect's nodes
            id_proj = list(np.unique(df["Index_Node"]))
            transects_nodes.append(id_proj)

            # Run through nodes to determine each parameters
            for node in id_proj:
                index_node = np.array(df[df["Index_Node"] == node]["Index_ensemble"])
                w_vel_x_node = w_vel_x_tr[:, index_node]
                w_vel_y_node = w_vel_y_tr[:, index_node]
                w_vel_z_node = w_vel_z_tr[:, index_node]
                rssi_node = rssi_tr[:, index_node]
                mid_cell_node = cell_depth_tr[:, index_node]
                depth_node = depth_ens_tr[index_node]
                temperature_node = temperature_ens_tr[index_node]

                transects_node_depth[index_transect, node] = np.nanmedian(depth_node)
                transects_node_temperature[index_transect, node] = np.nanmedian(
                    temperature_node
                )
                # Determine every transect's cells in the mesh
                for id_vert in range(len(self.main_depth_layers) - 1):
                    (id_x, id_y) = np.where(
                        np.logical_and(
                            mid_cell_node >= self.main_depth_layers[id_vert],
                            mid_cell_node < self.main_depth_layers[id_vert + 1],
                        )
                    )
                    w_vel_x_loc = w_vel_x_node[id_x, id_y]
                    w_vel_y_loc = w_vel_y_node[id_x, id_y]
                    w_vel_z_loc = w_vel_z_node[id_x, id_y]
                    rssi_loc = rssi_node[id_x, id_y]

                    transects_node_x_velocity[
                        index_transect, id_vert, node
                    ] = np.nanmedian(w_vel_x_loc)
                    transects_node_y_velocity[
                        index_transect, id_vert, node
                    ] = np.nanmedian(w_vel_y_loc)
                    transects_node_vertical_velocity[
                        index_transect, id_vert, node
                    ] = np.nanmedian(w_vel_z_loc)
                    transects_node_rssi[index_transect, id_vert, node] = np.nanmedian(
                        rssi_loc
                    )

        tr_nodes_data = {
            "x_velocity": transects_node_x_velocity,
            "y_velocity": transects_node_y_velocity,
            "vertical_velocity": transects_node_vertical_velocity,
            "depth": transects_node_depth,
            "rssi": transects_node_rssi,
            "nodes": transects_nodes,
            "temperature": transects_node_temperature,
        }

        return tr_nodes_data

    def compute_mean(self, tr_nodes_data, n_burn):
        """Compute mesh mean value of selected transects

        Parameters
        ----------
        tr_nodes_data: dict
            Dictionary of data by transects
        n_burn: int
            Number of transects which need to detect an information to make it valid
        """

        transects_nodes = tr_nodes_data["nodes"]
        transects_node_x_velocity = tr_nodes_data["x_velocity"]
        transects_node_y_velocity = tr_nodes_data["y_velocity"]
        transects_node_vertical_velocity = tr_nodes_data["vertical_velocity"]
        transects_node_rssi = tr_nodes_data["rssi"]
        transects_node_depth = tr_nodes_data["depth"]
        transects_node_temperature = tr_nodes_data["temperature"]

        # Define meshs detected by enough transects
        unique_node = list(np.unique([x for l in transects_nodes for x in l]))
        node_selected = copy.deepcopy(unique_node)
        if n_burn is None:
            n_burn = int(len(transects_nodes) / 3)
        valid_cell = max(n_burn, 1)

        for node in unique_node:
            if (
                sum(x.count(node) for x in transects_nodes) < valid_cell
                or np.isnan(transects_node_depth[:, node]).all()
            ):
                node_selected.remove(node)

        if len(node_selected) > 0:
            node_min = np.nanmin(node_selected)
            node_max = np.nanmax(node_selected)
            node_range = list(range(node_min, node_max + 1))
            node_range_border = list(range(node_min, node_max + 2))

            borders_ens = self.borders_ens[node_range_border]
            dist_start = min(borders_ens)
            borders_ens -= dist_start
            self.acs_distance -= dist_start

            map_depth_cells_border = np.tile(
                np.nan, (len(self.main_depth_layers), len(node_range))
            )
            for i in range(len(node_range)):
                map_depth_cells_border[:, i] = self.main_depth_layers

            # Initialize MAP data
            self.east_velocity = np.tile(
                np.nan, (len(self.main_depth_layers) - 1, len(node_range))
            )
            self.north_velocity = np.tile(
                np.nan, (len(self.main_depth_layers) - 1, len(node_range))
            )
            map_vertical_velocity = np.tile(
                np.nan, (len(self.main_depth_layers) - 1, len(node_range))
            )
            map_rssi = np.tile(
                np.nan, (len(self.main_depth_layers) - 1, len(node_range))
            )
            map_count = np.tile(
                np.nan, (len(self.main_depth_layers) - 1, len(node_range))
            )
            map_depth = np.tile(np.nan, len(node_range))
            map_temperature = np.tile(np.nan, len(node_range))

            # Previous version
            for node in node_selected:
                index_node = node_range.index(node)
                row = np.array(
                    [j for (j, sub) in enumerate(transects_nodes) if node in sub]
                )

                x_map_cell = transects_node_x_velocity[row, :, node]
                y_map_cell = transects_node_y_velocity[row, :, node]
                vertical_map_cell = transects_node_vertical_velocity[row, :, node]
                rssi_map_cell = transects_node_rssi[row, :, node]
                depth_map_cell = transects_node_depth[row, node]
                temp_map_cell = transects_node_temperature[row, node]

                map_depth[index_node] = np.nanmean(depth_map_cell)
                map_temperature[index_node] = np.nanmean(temp_map_cell)

                # Cut values under streambed
                if np.isnan(map_depth[index_node]):
                    depth_limit = 0
                else:
                    depth_limit = next(
                        x[0]
                        for x in enumerate(self.main_depth_layers)
                        if x[1] > map_depth[index_node]
                    )

                x_map_cell[:, depth_limit:] = np.nan
                y_map_cell[:, depth_limit:] = np.nan
                vertical_map_cell[:, depth_limit:] = np.nan
                rssi_map_cell[:, depth_limit:] = np.nan

                self.east_velocity[:, index_node] = np.nanmean(x_map_cell, axis=0)
                self.north_velocity[:, index_node] = np.nanmean(y_map_cell, axis=0)
                map_vertical_velocity[:, index_node] = np.nanmean(
                    vertical_map_cell, axis=0
                )
                map_rssi[:, index_node] = np.nanmean(rssi_map_cell, axis=0)
                map_count[:, index_node] = np.count_nonzero(
                    ~np.isnan(x_map_cell), axis=0
                )
                map_depth_cells_border[depth_limit, index_node] = map_depth[index_node]
                map_depth_cells_border[depth_limit + 1 :, index_node] = np.nan

            self.vertical_velocity = map_vertical_velocity
            self.rssi = map_rssi
            self.temperature = map_temperature
            self.count_valid = map_count
            self.depths = map_depth
            self.depth_cells_border = map_depth_cells_border
            self.depth_cells_center = (
                map_depth_cells_border[1:] + map_depth_cells_border[:-1]
            ) / 2
            self.borders_ens = borders_ens
            self.distance_cells_center = np.tile(
                [(borders_ens[1:] + borders_ens[:-1]) / 2],
                (self.depth_cells_center.shape[0], 1),
            )

            distance = self.borders_ens[1:] - self.borders_ens[:-1]
            depth = self.depth_cells_border[1:, :] - self.depth_cells_border[:-1, :]

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
        w_vel_mean_1 = np.nanmean(x_velocity, 0)
        w_vel_mean_2 = np.nanmean(y_velocity, 0)

        # Compute a unit vector
        direction, _ = cart2pol(w_vel_mean_1, w_vel_mean_2)
        unit_vec_1, unit_vec_2 = pol2cart(direction, 1)
        unit_vec = np.vstack([unit_vec_1, unit_vec_2])

        # Compute the velocity magnitude in the direction of the mean velocity of each
        # ensemble using the dot product and unit vector
        w_vel_prim = np.tile([np.nan], x_velocity.shape)
        w_vel_sec = np.tile([np.nan], x_velocity.shape)
        for i in range(x_velocity.shape[0]):
            w_vel_prim[i, :] = np.sum(
                np.vstack([x_velocity[i, :], y_velocity[i, :]]) * unit_vec, 0
            )
            w_vel_sec[i, :] = (
                unit_vec_2 * x_velocity[i, :] - unit_vec_1 * y_velocity[i, :]
            )

        self.primary_velocity = w_vel_prim
        self.secondary_velocity = w_vel_sec
        self.direction_ens = direction

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
        depths = self.depths
        depth_cells_border = self.depth_cells_border
        depth_cells_center = self.depth_cells_center
        mid_bed_cells = depths - depth_cells_center
        w_vel_prim_extrap = np.copy(self.primary_velocity)
        w_vel_sec_extrap = np.copy(self.secondary_velocity)
        w_vel_z_extrap = np.copy(self.vertical_velocity)

        map_depth_cells_border = np.tile(np.nan, depth_cells_border.shape)
        for i in range(depth_cells_border.shape[1]):
            map_depth_cells_border[:, i] = self.main_depth_layers

        map_depth_cells_center = (
            map_depth_cells_border[1:, :] + map_depth_cells_border[:-1, :]
        ) / 2

        # Blanking on the bottom
        blanking_depth = depths * 0.9
        for i in range(map_depth_cells_center.shape[1]):
            invalid = map_depth_cells_center[:, i] > blanking_depth[i]
            if np.sum(~np.isnan(w_vel_prim_extrap[~invalid, i])) > 0:
                w_vel_prim_extrap[invalid, i] = np.nan
                w_vel_sec_extrap[invalid, i] = np.nan
                w_vel_z_extrap[invalid, i] = np.nan

            # Identify valid data
            valid_data = np.logical_not(np.isnan(w_vel_prim_extrap))
            # Preallocate variables
            n_ensembles = valid_data.shape[1]
            idx_bot = np.tile(-1, (valid_data.shape[1])).astype(int)
            idx_top = np.tile(-1, valid_data.shape[1]).astype(int)
            idx_top_3 = np.tile(-1, (3, valid_data.shape[1])).astype(int)

            for n in range(n_ensembles):
                # Identifying bottom most valid cell
                idx_temp = np.where(np.logical_not(np.isnan(w_vel_prim_extrap[:, n])))[
                    0
                ]
                if len(idx_temp) > 0:
                    idx_top[n] = idx_temp[0]
                    idx_bot[n] = idx_temp[-1]
                    if len(idx_temp) > 2:
                        idx_top_3[:, n] = idx_temp[0:3]
                else:
                    idx_top[n] = 0

        for n in range(n_ensembles):
            # Identifying bottom most valid cell
            idx_temp = np.where(np.logical_not(np.isnan(w_vel_prim_extrap[:, n])))[0]
            if len(idx_temp) > 0:
                idx_top[n] = idx_temp[0]
                idx_bot[n] = idx_temp[-1]
                if len(idx_temp) > 2:
                    idx_top_3[:, n] = idx_temp[0:3]
            else:
                idx_top[n] = 0

        # QRevInt extrapolation method
        idx_bed = copy.deepcopy(idx_bot)
        bot_method = settings["extrapBot"]
        top_method = settings["extrapTop"]
        exponent = settings["extrapExp"]

        if bot_method == "Power":
            coef_primary_bot = np.nanmean(w_vel_prim_extrap, 0)

        elif bot_method == "No Slip":
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

        # Extrapolation Bot velocity
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
                    w_vel_z_extrap[
                        (idx_bot[n] + 1) : (idx_bed[n]), n
                    ] = sc.interpolate.griddata(
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
                    WLS = LinearRegression()
                    WLS.fit(top_3_depth.reshape(-1, 1), top_3_vel.reshape(-1, 1))
                    w_vel_prim_extrap[: idx_top[n], n] = (
                        WLS.coef_ * top_depth + WLS.intercept_
                    )

        # Extrap top for second and vertical velocities
        for n in range(len(idx_top)):
            if idx_top[n] >= 0:
                w_vel_sec_extrap[: idx_top[n], n] = w_vel_sec_extrap[idx_top[n], n]
                try:
                    top_z_value = sc.interpolate.griddata(
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
    def group(L):
        # Todo need doc str
        first = last = L[0]
        for n in L[1:]:
            if n - 1 == last:
                last = n
            else:
                yield first, last
                first = last = n
        yield first, last

    def compute_interpolation(self):
        # Todo Add doc string

        # Interpolate depth
        not_nan = np.logical_not(np.isnan(self.depths))
        indices = np.arange(len(self.depths))
        self.depths = np.interp(indices, indices[not_nan], self.depths[not_nan])
        self.direction_ens = np.interp(
            indices, indices[not_nan], self.direction_ens[not_nan]
        )

        # Interpolate Temperatures
        not_nan = np.logical_not(np.isnan(self.temperature))
        indices = np.arange(len(self.temperature))
        self.temperature = np.interp(
            indices, indices[not_nan], self.temperature[not_nan]
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

        # Define valid cells
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
                top = min(idx_top[x[0] - 1], idx_top[x[1] + 1])
                bot = max(idx_bot[x[0] - 1], idx_bot[x[1] + 1])

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
            self.depth_cells_border[x[0], i] = self.depths[i]
            self.depth_cells_border[x[0] + 1 :, i] = np.nan

        y_cell_size = self.depth_cells_border[1:, :] - self.depth_cells_border[:-1, :]
        y_centers = self.depth_cells_border[:-1, :] + 0.5 * y_cell_size
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
        borders_ens: list(float)
            Horizontal grid length on the average cross-section
        mid_direction: np.array
            1D array of mean velocity direction of each MAP vertical
        settings: dict
            Measurement current settings
        edges_option: bool
            Option to define if edge's meshs should share the exact same length or if they should be
            the same length as those in the middle (except the last vertical which is shorter)

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
        """

        if edge == "left":
            id_edge = 0
            node_size = abs(self.borders_ens[1] - self.borders_ens[0])
        elif edge == "right":
            id_edge = -1
            node_size = abs(self.borders_ens[-1] - self.borders_ens[-2])

        nodes = edge_distance - np.arange(0, edge_distance, node_size)[::-1]
        nodes = np.insert(nodes, 0, 0)
        nb_nodes = len(nodes) - 1

        nodes_mid = (nodes[1:] + nodes[:-1]) / 2
        edge_size_raw = self.depth_cells_border[:, id_edge]

        if edge_coef == 0.3535 and edge_distance > 0:
            depth_edge = self.depths[id_edge] * (
                edge_distance / (edge_distance + node_size / 2)
            )
            # depth_edge = self.depths[id_edge]
            # Depth arrays
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
                    for x in enumerate(cells_borders_depths_1[:, i])
                    if x[1] >= int(1000 * border_depths[i + 1]) / 1000
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
                x_left[row + 1 :, col - 1] = nodes[col]

            # Cells separate in 2 rectangles and 1 triangle
            area_rec2 = (x_left[:-1, 1:] - x_left[1:, :-1]) * (
                cells_borders_depths_1[1:, :] - cells_borders_depths_1[:-1, :]
            )
            area_rec1 = (x_left[1:, :-1] - x_left[:-1, :-1]) * (
                cells_borders_depths_2[:-1, :-1] - cells_borders_depths_1[:-1, :]
            )
            area_tri1 = (
                (x_left[1:, :-1] - x_left[:-1, :-1])
                * (cells_borders_depths_1[1:, :] - cells_borders_depths_2[:-1, :-1])
                / 2
            )
            area_tra1 = area_rec1 + area_tri1
            area = area_tra1 + area_rec2

            # Compute mid of every shape
            mid_rec2_x = (x_left[:-1, 1:] + x_left[1:, :-1]) / 2
            mid_rec2_y = (
                cells_borders_depths_1[:-1, :] + cells_borders_depths_1[1:, :]
            ) / 2

            mid_rec1_x = (x_left[:-1, :-1] + x_left[1:, :-1]) / 2
            mid_rec1_y = (
                cells_borders_depths_1[:-1, :] + cells_borders_depths_2[:-1, :-1]
            ) / 2

            mid_tri1_x = (x_left[:-1, :-1] + 2 * x_left[1:, :-1]) / 3
            mid_tri1_y = (
                2 * cells_borders_depths_2[:-1, :-1] + cells_borders_depths_1[1:, :]
            ) / 3

            mid_tra1_x = (area_rec1 * mid_rec1_x + area_tri1 * mid_tri1_x) / (area_tra1)
            mid_tra1_y = (area_rec1 * mid_rec1_y + area_tri1 * mid_tri1_y) / (area_tra1)
            mid_tra1_x[area_tra1 == 0] = 0
            mid_tra1_y[area_tra1 == 0] = 0

            # Compute cell's mid
            mid_cells_x = (area_rec2 * mid_rec2_x + area_tra1 * mid_tra1_x) / area
            mid_cells_y = (area_rec2 * mid_rec2_y + area_tra1 * mid_tra1_y) / area
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
            edge_vertical_velocity = sc.interpolate.griddata(
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
            edge_secondary_vel_interp = sc.interpolate.griddata(
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
            self.direction_ens = np.append(
                self.direction_ens,
                np.tile(self.direction_ens[id_edge], edge_primary_velocity.shape[1]),
            )

            depth = (border_depths[1:] + border_depths[:-1]) / 2
            self.depths = np.append(self.depths, depth[::-1])
            self.depth_cells_center = np.c_[
                self.depth_cells_center, mid_cells_y[:, ::-1]
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

            self.direction_ens = np.insert(
                self.direction_ens,
                0,
                np.tile(self.direction_ens[id_edge], edge_primary_velocity.shape[1]),
            )

            depth = (border_depths[1:] + border_depths[:-1]) / 2
            self.depths = np.insert(self.depths, 0, depth)
            self.depth_cells_center = np.c_[mid_cells_y, self.depth_cells_center]

            nan_array = np.tile(np.nan, len(depth))
            self.temperature = np.insert(self.temperature, 0, nan_array)

            self.borders_ens = np.insert(
                self.borders_ens + edge_distance, 0, nodes[:-1]
            )

            self.distance_cells_center = np.c_[
                mid_cells_x, self.distance_cells_center + edge_distance
            ]

            self.cells_area = np.c_[area, self.cells_area]

            self.acs_distance += edge_distance

    def compute_discharge(self):
        """Compute streamwise velocity and discharge."""

        direction_meas = np.arctan2(-1, self.slope)

        distance = (self.borders_ens[1:] + self.borders_ens[:-1]) / 2

        direction_ens = sc.interpolate.griddata(
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

    def create_map_df(self, units):
        """Create a pandas dataframe of data computed by MAP.

        Parameters:
            units: dict

        Returns:
            df: pd.DataFrame

        """

        distance_x, distance_y = self.utm_2_distance()
        lat, lon = self.utm_2_decimaldegrees()

        row, col = self.primary_velocity.shape
        ens_mid = (self.borders_ens[1:] + self.borders_ens[:-1]) * 0.5
        data = {
            "Distance (Left bank) "
            + units["label_L"]: np.repeat(ens_mid, row) * units["L"],
            "Distance X " + units["label_L"]: np.repeat(distance_x, row) * units["L"],
            "Distance Y " + units["label_L"]: np.repeat(distance_y, row) * units["L"],
            "Latitude": np.repeat(lat, row),
            "Longitude": np.repeat(lon, row),
            "Primary velocity "
            + units["label_V"]: self.primary_velocity.ravel(order="F") * units["V"],
            "Secondary velocity "
            + units["label_V"]: self.secondary_velocity.ravel(order="F") * units["V"],
            "Streamwise velocity "
            + units["label_V"]: self.streamwise_velocity.ravel(order="F") * units["V"],
            "Transverse velocity (Left to Right) "
            + units["label_V"]: self.transverse_velocity.ravel(order="F") * units["V"],
            "Vertical velocity "
            + units["label_V"]: self.primary_velocity.ravel(order="F") * units["V"],
            "Depth " + units["label_L"]: np.repeat(self.depths, row) * units["L"],
            "Cells discharge "
            + units["label_Q"]: self.cells_discharge.ravel(order="F") * units["Q"],
            "Cells area "
            + units["label_A"]: self.cells_area.ravel(order="F") * units["A"],
            "Distance cells center "
            + units["label_L"]: self.distance_cells_center.ravel(order="F")
            * units["L"],
            "Depth cells center "
            + units["label_L"]: self.depth_cells_center.ravel(order="F") * units["L"],
            "Temperature": np.repeat(self.temperature, row),
        }

        df = pd.DataFrame(data)
        df = df[df["Cells discharge " + units["label_Q"]].notna()]

        return df

    def export_csv(self, path, units, delimiter="comma delimited"):
        """Exports map data to ascii file with specified delimiter.

        Parameters:
            path: str
            units: dict
            delimiter: str
        """
        date = datetime.today().strftime("%d-%b-%Y")
        header = ["# " + __qrev_version__ + "\n", "# Exported " + date + "\n"]

        with open(path, "w") as file:
            file.writelines(header)

        df = self.create_map_df(units=units)

        if "comma" in delimiter:
            sep = ","
        elif "colon" in delimiter:
            sep = ";"
        else:
            sep = " "

        df.to_csv(path, sep=sep, index=False, mode="a", header=True)

    def export_kml(self, meas, path):
        """Create KML file for MAP.

        Parameters:
            meas: Measurement
            path: str
        """

        kml = simplekml.Kml(open=1)
        # Create a shiptrack for each checked transect
        lat = np.nan
        lon = np.nan
        for transect_idx in meas.checked_transect_idx:
            lon = meas.transects[transect_idx].gps.gga_lon_ens_deg
            lon = lon[np.logical_not(np.isnan(lon))]
            lat = meas.transects[transect_idx].gps.gga_lat_ens_deg
            lat = lat[np.logical_not(np.isnan(lat))]
            line_name = meas.transects[transect_idx].file_name[:-4]
            lon_lat = tuple(zip(lon, lat))
            _ = kml.newlinestring(name=line_name, coords=lon_lat)

        # Get utm zone
        _, _, zone_number, zone_letter = utm.from_latlon(lat, lon)
        # Define average ship track
        left_x = np.nanmedian([item[0] for item in meas.map.x_raw_coordinates])
        x_boundaries = [
            min([min(x) for x in meas.map.x_projected]),
            max([max(x) for x in meas.map.x_projected]),
        ]

        x_utm = np.array(
            [
                min(x_boundaries, key=lambda x: abs(x - left_x)),
                max(x_boundaries, key=lambda x: abs(x - left_x)),
            ]
        )
        y_utm = np.array([i * self.slope + self.intercept for i in x_utm])

        lat, lon = utm.to_latlon(x_utm, y_utm, zone_number, zone_letter)
        line_name = "MAP average ship track"
        lon_lat = tuple(zip(lon, lat))
        lin = kml.newlinestring(name=line_name, coords=lon_lat)
        lin.style.linestyle.color = "ff0000ff"

        kml.save(path)
