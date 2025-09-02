import numpy as np
from qrev.MiscLibs.common_functions import weighted_mean
from scipy.interpolate import Rbf
import skgstat as skg


class FlowFieldInterpolation(object):
    def __init__(self, transect, exponent):
        # Store input data
        self.exponent = exponent

        # Initialize isovel flow fields
        self.isovel_field = None
        self.u_isovel_field = None
        self.v_isovel_field = None

        # Compute mean cross section ranges and ensemble widths
        self.cross_section_rng = None
        self.ensemble_width = None
        self.compute_mean_cross_section(transect=transect)

        # Store depth data from transect
        depth_data = getattr(transect.depths, transect.depths.selected)
        self.depth_cell_depth = depth_data.depth_cell_depth_m
        self.depth_cell_size = depth_data.depth_cell_size_m
        self.depths = depth_data.depth_processed_m

        # Store boat data from transect
        boat_data = getattr(transect.boat_vel, transect.boat_vel.selected)
        self.boat_u = boat_data.u_processed_mps
        self.boat_v = boat_data.v_processed_mps

        # Store water data from transect
        self.u = transect.w_vel.u_processed_mps
        self.v = transect.w_vel.v_processed_mps

        # Cells above side lobe
        self.cells_above_sl = transect.w_vel.cells_above_sl
        self.cells_to_use = self.cells_above_sl.astype(float)
        self.cells_to_use[self.cells_to_use == 0] = np.nan

        # Store edge data from transect
        self.start_edge = transect.start_edge
        self.left_edge_type = transect.edges.left.type
        self.right_edge_type = transect.edges.right.type
        self.left_edge_distance = transect.edges.left.distance_m
        self.right_edge_distance = transect.edges.right.distance_m

        # Store ensemble duration
        self.dt = transect.date_time.ens_duration_sec

        # Indentify invalid ensembles between the first and last valid ensemble
        invalid_ens = np.nansum(transect.w_vel.valid_data[0, :, :], axis=0)
        self.invalid_ensembles = np.where(invalid_ens < 1)[0]
        valid_ens = np.where(invalid_ens > 0)[0]
        self.invalid_ensembles = self.invalid_ensembles[
            valid_ens[0] < self.invalid_ensembles
        ]
        self.invalid_ensembles = self.invalid_ensembles[
            self.invalid_ensembles < valid_ens[-1]
        ]
        # Compute top and bottom cell depths
        self.top_depth_cell_depth = depth_data.depth_cell_depth_m[0, :]
        bottom_cell_number = np.nansum(self.cells_above_sl, axis=0)
        self.bottom_depth_cell_depth = np.array(
            [
                depth_data.depth_cell_depth_m[bottom_cell_number[ens], ens]
                for ens in range(depth_data.depth_cell_depth_m.shape[1])
            ]
        )

        # Compute ensembles used to compute seed values
        self.seed_ensembles = self.select_seed_ensembles()

    # isovel interpolation
    # ====================

    def isovel_interpolation(self, normalize=False):
        """Compute the discharge using isovel interpolation for invalid
        ensembles.

        Returns
        -------
        q: float
            Middle discharge
        """

        # Create initial isovel field
        self.isovel_contour(
            left_edge_shape=self.left_edge_type,
            left_edge_distance=self.left_edge_distance,
            right_edge_shape=self.right_edge_type,
            right_edge_distance=self.right_edge_distance,
            normalize=normalize
        )

        # Compute seed values
        u_seed, v_seed, seed_ensemble_idx, depth_cell_depth_idx = self.isovel_seed(
            top_cell_depth=self.top_depth_cell_depth,
            bottom_cell_depth=self.bottom_depth_cell_depth,
            seed_ensembles=self.seed_ensembles,
        )

        # Compute velocity field based on seed values
        self.isovel_compute_velocity_fields(
            u_seed=u_seed,
            v_seed=v_seed,
            ensemble_idx=seed_ensemble_idx,
            depth_cell_depth_idx=depth_cell_depth_idx,
        )

        q = self.isovel_compute_discharge()

        return q

    def isovel_contour(
        self,
        left_edge_shape,
        left_edge_distance,
        right_edge_shape,
        right_edge_distance,
        normalize
    ):
        """Compute isovel field

        Parameters
        ----------
        left_edge_shape: str
            Shape of left edge
        left_edge_distance: float
            Distance to left edge
        right_edge_shape: str
            Shape of right edge
        right_edge_distance: float
            Distance to right edge
        """

        # Set start and end edge characteristics
        if self.start_edge == "Left":
            start_edge_distance = left_edge_distance
            start_edge_shape = left_edge_shape
            end_edge_distance = right_edge_distance
            end_edge_shape = right_edge_shape
        else:
            start_edge_distance = right_edge_distance
            start_edge_shape = right_edge_shape
            end_edge_distance = left_edge_distance
            end_edge_shape = left_edge_shape

        # update data geometry adding edges and top cells
        (
            depth_cell_depth_iso,
            depth_cell_size_iso,
            depth_iso,
            ensemble_widths_iso,
            n_start,
            n_end,
            n_top
        ) = self.isovel_update_geometry(
            start_edge_distance,
            start_edge_shape,
            end_edge_distance,
            end_edge_shape,
            normalize
        )
        rng_iso = np.nancumsum(ensemble_widths_iso)
        # Initialisation
        velocity_field = np.nan * np.zeros(depth_cell_depth_iso.shape)
        q = 0
        area = 0
        for cell_idx in range(depth_cell_depth_iso.shape[0]):
            for ens_idx in range(depth_cell_depth_iso.shape[1]):
                # Compute for depths above ensemble depth
                if depth_cell_depth_iso[cell_idx, ens_idx] < depth_iso[ens_idx]:
                    # Contribution for streambed
                    x = rng_iso - rng_iso[ens_idx]
                    y = depth_iso - depth_cell_depth_iso[cell_idx, ens_idx]
                    radial_dist_b = np.sqrt(x**2 + y**2)
                    cell_vel = np.nansum(
                        (radial_dist_b[radial_dist_b > 0] ** (self.exponent - 1))
                        * y[radial_dist_b > 0]
                        * ensemble_widths_iso[radial_dist_b > 0]
                    )

                    # Contribution from a rectangular edge at the start bank
                    if start_edge_shape == "Rectangular":
                        x = self.cross_section_rng[ens_idx]
                        y = (
                            np.arange(
                                int(
                                    depth_iso[0]
                                    / depth_cell_size_iso[cell_idx, ens_idx]
                                )
                            )
                            * depth_cell_size_iso[cell_idx, ens_idx]
                            - depth_cell_depth_iso[cell_idx, ens_idx]
                        )
                        radial_dist_s = np.sqrt(x**2 + y**2)
                        cell_vel = cell_vel + np.nansum(
                            (radial_dist_s[radial_dist_s > 0] ** (self.exponent - 1))
                            * x
                            * depth_cell_size_iso[cell_idx, ens_idx]
                        )

                    # Contribution from a rectangular edge at the end bank
                    if end_edge_shape == "Rectangular":
                        x = self.cross_section_rng[-1] - self.cross_section_rng[ens_idx]
                        y = (
                            np.arange(
                                int(
                                    depth_iso[-1]
                                    / depth_cell_size_iso[cell_idx, ens_idx]
                                )
                            )
                            * depth_cell_size_iso[cell_idx, ens_idx]
                            - depth_cell_depth_iso[cell_idx, ens_idx]
                        )
                        radial_dist_e = np.sqrt(x**2 + y**2)
                        cell_vel = cell_vel + np.nansum(
                            (radial_dist_e[radial_dist_e > 0] ** (self.exponent - 1))
                            * x
                            * depth_cell_size_iso[cell_idx, ens_idx]
                        )
                    # Compute cross-sectional value
                    velocity_field[cell_idx, ens_idx] = cell_vel
                    cell_area = (
                        depth_cell_size_iso[cell_idx, ens_idx]
                        * ensemble_widths_iso[ens_idx]
                    )
                    q = q + cell_vel * cell_area
                    area = area + cell_area
        # Normalize velocity field
        mean_vel = q / area
        self.isovel_field = velocity_field / mean_vel  # isovel field

        # Remove added top and edge areas
        self.isovel_field = self.isovel_field[n_top::, n_start:-n_end]
        self.isovel_field = self.isovel_field * self.cells_above_sl

        # Restrict isovel_field to only the cells above sidelobe
        self.isovel_field = self.isovel_field * self.cells_to_use

    def isovel_update_geometry(
        self,
        start_edge_distance,
        start_edge_shape,
        end_edge_distance,
        end_edge_shape,
        normalize,
        n_top=4
    ):
        """
        Update velocity and geometry data adding edges and top areas

        Parameters
        ----------
        start_edge_distance: float
            Distance from start edge to first ensemble
        start_edge_shape: str
            Shape of start edge
        end_edge_distance: float
            Distance from last ensemble to end edge
        end_edge_shape: str
            Shape of end edge

        Returns
        -------
        depth_cell_depth_iso: np.array(float)
            Depth cell depths updated with edges
        depth_cell_size: np.array(float)
            Depth cell size update with edges
        depth_iso: np.array(float)
            Depth data updated with edges
        ensemble_widths_iso : list
            Ensemble width updated with edges
        n_right_edge: int
            Number of right edge ensembles
        n_left_edge: int
            Number of left edge ensembles
        n_top: int
            Number of top depth cells
        """

        # Add depth cells between water surface and first cell
        top_cell_size = self.depth_cell_depth[0, :] / n_top
        depth_cell_size_top = np.tile(top_cell_size, (n_top, 1))
        depth_cell_depth_top = np.nancumsum(depth_cell_size_top, axis=0) - top_cell_size
        depth_cell_size_iso = np.concatenate(
            (depth_cell_size_top, self.depth_cell_size), axis=0
        )
        depth_cell_depth_iso = np.concatenate(
            (depth_cell_depth_top, self.depth_cell_depth), axis=0
        )

        # Add edges
        (
            depth_iso,
            ensemble_widths_iso,
            depth_cell_depth_iso,
            depth_cell_size_iso,
            n_start,
            n_end,
        ) = self.add_edges(
            start_edge_distance=start_edge_distance,
            start_edge_shape=start_edge_shape,
            end_edge_distance=end_edge_distance,
            end_edge_shape=end_edge_shape,
            depth=self.depths,
            ensemble_widths=self.ensemble_width,
            depth_cell_depth=depth_cell_depth_iso,
            depth_cell_size=depth_cell_size_iso,
        )

        # normalization or not
        if normalize:
            depth_cell_depth_iso = depth_cell_depth_iso / depth_iso
            depth_cell_size_iso = depth_cell_size_iso / depth_iso

        return (
            depth_cell_depth_iso,
            depth_cell_size_iso,
            depth_iso,
            ensemble_widths_iso,
            n_start,
            n_end,
            n_top
        )

    @staticmethod
    def add_edges(
        start_edge_distance,
        start_edge_shape,
        end_edge_distance,
        end_edge_shape,
        depth,
        ensemble_widths,
        depth_cell_depth,
        depth_cell_size,
    ):
        """
        Update iso data with edges

        Parameters
        ----------
        start_edge_distance: float
            Distance from start edge
        start_edge_shape: str
            Shape of start edge
        end_edge_distance: float
            Distance from end edge
        end_edge_shape: str
            Shape of end edge
        depth: np.array(float)
            Total depth of ensembles
        ensemble_widths: np.array(float)
            Width of each ensemble
        depth_cell_depth: np.array(float)
            Depth cell depths for each cell and ensemble
        depth_cell_size: np.array(float)
            Depth cell size for each cell and ensemble

        Returns
        -------
        depth_iso: np.array(float)
            Depth for each ensemble with data for edges
        ensemble_widths_iso: np.array(float)
            Width of each ensemble with data for edges
        depth_cell_depth_iso: np.array(float)
            Depth cell depths for each ensemble with data for edges
        depth_cell_size_iso: np.array(float)
            Depth cell size for each ensemble with data for edges
        n_start: int
            Number of ensembles in start edge
        n_end: int
            Number of ensembles in end edge
        """

        # Compute number of edge ensembles to be added
        mean_ensemble_width = np.nanmean(ensemble_widths)
        if start_edge_distance > 0:
            if start_edge_distance > mean_ensemble_width:
                n_start = round(start_edge_distance / mean_ensemble_width)
            else:
                n_start = 1
                start_ensemble_width = start_edge_distance
        else:
            n_start = 0
            start_ensemble_width = start_edge_distance
        if end_edge_distance > 0:
            if end_edge_distance > mean_ensemble_width:
                n_end = round(end_edge_distance / mean_ensemble_width)
            else:
                n_end = 1
                end_ensemble_width = end_edge_distance
        else:
            n_end = 0
            end_ensemble_width = end_edge_distance

        # Add cell widths
        start_ensemble_widths = np.tile(start_ensemble_width, (1, n_start))[0]
        end_ensemble_widths = np.tile(end_ensemble_width, (1, n_end))[0]
        ensemble_widths_iso = np.concatenate(
            (start_ensemble_widths, ensemble_widths[1:])
        )
        ensemble_widths_iso = np.concatenate((ensemble_widths_iso, end_ensemble_widths))
        ensemble_widths_iso = np.concatenate((np.zeros(1), ensemble_widths_iso))

        # Add depths
        if start_edge_shape == "Rectangular":
            start_edge_depths = depth[0] * np.ones(n_start)
        else:
            start_edge_depths = np.array(
                [
                    depth[0] * ((mean_ensemble_width * i) / start_edge_distance)
                    for i in range(n_start)
                ]
            )

        if end_edge_shape == "Rectangular":
            end_edge_depths = depth[-1] * np.ones(n_end)
        else:
            end_edge_depths = np.array(
                [
                    depth[-1] / start_edge_distance * mean_ensemble_width * (n_end - i - 1)
                    for i in range(n_end)
                ]
            )

        depth_iso = np.concatenate((start_edge_depths, depth))
        depth_iso = np.concatenate((depth_iso, end_edge_depths))

        # Add depth cell depths
        start_cell_depths = np.tile(depth_cell_depth[:, 0], (n_start, 1))
        end_cell_depths = np.tile(depth_cell_depth[:, -1], (n_end, 1))
        depth_cell_depth_iso = np.hstack(
            (np.transpose(start_cell_depths), depth_cell_depth)
        )
        depth_cell_depth_iso = np.hstack(
            (depth_cell_depth_iso, np.transpose(end_cell_depths))
        )

        # Add depth cell size
        start_cell_size = np.tile(depth_cell_size[:, 0], (n_start, 1))
        end_cell_size = np.tile(depth_cell_size[:, -1], (n_end, 1))
        depth_cell_size_iso = np.hstack(
            (np.transpose(start_cell_size), depth_cell_size)
        )
        depth_cell_size_iso = np.hstack(
            (depth_cell_size_iso, np.transpose(end_cell_size))
        )

        return (
            depth_iso,
            ensemble_widths_iso,
            depth_cell_depth_iso,
            depth_cell_size_iso,
            n_start,
            n_end,
        )

    def isovel_seed(self, top_cell_depth, bottom_cell_depth, seed_ensembles):
        """
        Return seed value and location for the velocity field computation
        The seed value will be the mean over the 25% middle area over the amount
        of ensemble defined by the parameter method.

        Parameters
        ----------
        top_cell_depth: np.array(float)
            Array of depth cell depths for the top depth cell
        bottom_cell_depth: np.array(float)
            Array of depth cell depths for the bottom depth cell
        seed_ensembles: np.array(int)
            Array of ensembles numbers used to compute the seed value for isovel

        Returns
        -------
        u_mean: float
            Seed value of u velocity component
        v_mean: float
            Seed value of v velocity component
        ensemble_idx: int
            Ensemble index for seed
        depth_cell_idx: int
            Depth cell index for seed
        """

        bottom_cell_depth_mean = np.nanmean(bottom_cell_depth[seed_ensembles])
        top_cell_depth_mean = np.nanmean(top_cell_depth[seed_ensembles])
        d_min, d_max = (
            top_cell_depth_mean
            + 0.375 * (bottom_cell_depth_mean - top_cell_depth_mean),
            bottom_cell_depth_mean
            - 0.375 * (bottom_cell_depth_mean - top_cell_depth_mean),
        )

        # Create array of depth cells from selected ensembles that represent 25% of the measured area
        depth_cells_selected_depth = self.depth_cell_depth[:, seed_ensembles]
        depth_cells_selected_depth[d_min > depth_cells_selected_depth] = np.nan
        depth_cells_selected_depth[d_max < depth_cells_selected_depth] = np.nan

        # Create array to identify selected depth cells
        selected_data = np.copy(depth_cells_selected_depth)
        selected_data[np.logical_not(np.isnan(selected_data))] = 1

        # Compute mean velocity
        u_mean = np.nanmean(
            np.nanmean(self.u[:, seed_ensembles] * selected_data, axis=0)
        )
        v_mean = np.nanmean(
            np.nanmean(self.v[:, seed_ensembles] * selected_data, axis=0)
        )

        # Compute depth location
        depth_cell_idx = np.nanargmin(
            np.abs(
                depth_cells_selected_depth[:, 2]
                - np.nanmean(depth_cells_selected_depth)
            )
        )

        # Compute ensemble location
        ensemble_idx = np.argmin(
            np.abs(self.cross_section_rng - np.nanmean(self.cross_section_rng[seed_ensembles]))
        )

        return u_mean, v_mean, ensemble_idx, depth_cell_idx

    def isovel_compute_velocity_fields(
        self,
        u_seed,
        v_seed,
        ensemble_idx,
        depth_cell_depth_idx,
    ):
        """
        Compute velocity fields from isovel method using a middle seed
        and by adjusting its value on the 40% middle area.

        Parameters
        ----------
        u_seed: float
            u velocity component to seed isovel field
        v_seed: float
            v velocity component to seed isovel field
        ensemble_idx: int
            Ensemble index for seed
        depth_cell_depth_idx: int
            Depth cell index for seed
        """

        # Compute seed values

        # Adjust iso field to seed values
        u_iso = u_seed * self.isovel_field / self.isovel_field[depth_cell_depth_idx, ensemble_idx]
        v_iso = v_seed * self.isovel_field / self.isovel_field[depth_cell_depth_idx, ensemble_idx]

        # Identify ensembles in the center 40% of the cross section
        rng_30, rng_70 = (
            0.3 * np.nanmax(self.cross_section_rng),
            0.7 * np.nanmax(self.cross_section_rng),
        )
        i_start, i_max = (
            np.argmax(self.cross_section_rng > rng_30),
            np.argmin(self.cross_section_rng < rng_70),
        )
        idx = [i for i in range(i_start, i_max) if i not in self.invalid_ensembles]

        # Compute the discharge using the measured data
        q = self.compute_discharge(
            u=self.u[:, idx],
            v=self.v[:, idx],
            boat_u=self.boat_u[idx],
            boat_v=self.boat_v[idx],
            depth_cell_size=self.depth_cell_size[:, idx],
            dt=self.dt[idx],
            start_edge=self.start_edge,
        )

        # Compute the difference in discharge using the isovel field
        u_diff = u_iso - self.u
        v_diff = v_iso - self.v
        dq = self.compute_discharge(
            u=u_diff[:, idx],
            v=v_diff[:, idx],
            boat_u=self.boat_u[idx],
            boat_v=self.boat_v[idx],
            depth_cell_size=self.depth_cell_size[:, idx],
            dt=self.dt[idx],
            start_edge=self.start_edge,
        )

        # Reduce discharge error of iso field to within 5%, ignoring 30% of the cross section at each edge
        n = 0
        q_ratio = dq / q
        while np.abs(q_ratio) > 0.05 and n < 25:
            n = n + 1
            u_seed = (1 - q_ratio) * u_seed
            v_seed = (1 - q_ratio) * v_seed
            u_iso = (
                u_seed * self.isovel_field / self.isovel_field[depth_cell_depth_idx, ensemble_idx]
            )
            v_iso = (
                v_seed * self.isovel_field / self.isovel_field[depth_cell_depth_idx, ensemble_idx]
            )
            u_diff = u_iso - self.u
            v_diff = v_iso - self.v
            dq = self.compute_discharge(
                u=u_diff[:, idx],
                v=v_diff[:, idx],
                boat_u=self.boat_u[idx],
                boat_v=self.boat_v[idx],
                depth_cell_size=self.depth_cell_size[:, idx],
                dt=self.dt[idx],
                start_edge=self.start_edge,
            )
            q_ratio = dq / q
        self.u_isovel_field = u_iso
        self.v_isovel_field = v_iso

    def isovel_compute_discharge(self):
        """Compute discharge field from isovel method."""
        u_combined, v_combined = self.iso_combine_data(
            u_field=self.u_isovel_field,
            v_field=self.v_isovel_field,
        )
        q = self.compute_discharge(
            u=u_combined,
            v=v_combined,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

        return q

    def iso_combine_data(self, u_field, v_field):
        """
        Combines the valid and interpolated velocity data.

        Parameters
        ----------
        u_field: np.array(float)
            Array containing fit u velocities
        v_field: np.array(float)
            Array containing fit v velocities

        Returns
        -------
        u_combined: np.array(float)
            Water velocity u-component with interpolated values
        v_combined: np.array(float)
            Water velocity v-component with interpolated values
        """
        u_combined = np.copy(self.u)
        v_combined = np.copy(self.v)
        u_combined[:, self.invalid_ensembles] = u_field[:, self.invalid_ensembles]
        v_combined[:, self.invalid_ensembles] = v_field[
                                                :, self.invalid_ensembles
                                                ]

        return u_combined, v_combined

    # Froude number interpolation
    # ===========================

    def froude_interpolation(self):
        """Compute the discharge using froude number interpolation."""

        u_froude, v_froude, ensemble_idx = self.froude_interpolation_initialization()
        q_constant = self.froude_constant_interpolation(u_froude[1], v_froude[1])
        q_linear = self.froude_linear_interpolation(u_froude, v_froude, ensemble_idx)
        return q_constant, q_linear

    def froude_interpolation_initialization(self):
        """Compute froude numbers to allow interpolation."""

        # Initialize
        u_froude = np.tile(np.nan, 3)
        v_froude = np.tile(np.nan, 3)
        ensemble_idx = np.tile(-1, 3)

        # Compute froude number at center of mass
        u_froude[1], v_froude[1], ensemble_idx[1] = self.froude_compute_reference(
            ensembles=self.seed_ensembles
        )

        # Compute froude number near start bank using 5% valid ensembles
        n_ensembles_5_per = 0.05 * self.u.shape[1]
        valid_start_ensembles = []
        for n in range(self.u.shape[1]):
            if n not in self.invalid_ensembles:
                valid_start_ensembles.append(n)
                if len(valid_start_ensembles) >= n_ensembles_5_per:
                    break
        u_froude[0], v_froude[0], _ = self.froude_compute_reference(
            ensembles=valid_start_ensembles
        )
        ensemble_idx[0] = valid_start_ensembles[0]

        # Compute fround number near end bank
        valid_end_ensembles = []
        for n in range(self.u.shape[1] - 1, -1, -1):
            if n not in self.invalid_ensembles:
                valid_end_ensembles.append(n)
                if len(valid_end_ensembles) >= n_ensembles_5_per:
                    break
        u_froude[2], v_froude[2], _ = self.froude_compute_reference(
            ensembles=valid_end_ensembles
        )
        ensemble_idx[2] = valid_end_ensembles[-1]

        return u_froude, v_froude, ensemble_idx

    def froude_compute_reference(self, ensembles):
        """Compute the mean froude number for each velocity component using the
        specified ensembles.

        Parameters
        ----------
        ensembles: list or np.array(int)
            List or array of ensemble ids.

        Returns
        -------
        u_froude_number: float
            Mean froude number for u velocity component.
        v_fround_number: float
            Mean froude number for v velocity component.
        ensemble_idx: int
            Ensemble id for froude numbers.
        """

        # Compute mean velocity for each ensemble
        u_mean_ens = weighted_mean(
            data=self.u[:, ensembles],
            axis=0,
            weights=self.depth_cell_size[:, ensembles],
        )
        v_mean_ens = weighted_mean(
            data=self.v[:, ensembles],
            axis=0,
            weights=self.depth_cell_size[:, ensembles],
        )

        # Compute the mean froude number for the velocity components
        u_froude_number = np.nanmean(
            u_mean_ens / np.sqrt(self.depths[ensembles] * 9.81)
        )
        v_fround_number = np.nanmean(
            v_mean_ens / np.sqrt(self.depths[ensembles] * 9.81)
        )

        # Compute ensemble location
        ensemble_idx = np.argmin(
            np.abs(
                self.cross_section_rng - np.nanmean(self.cross_section_rng[ensembles])
            )
        )

        return u_froude_number, v_fround_number, ensemble_idx

    def froude_linear_interpolation(self, u_froude, v_froude, ensemble_idx):
        """Linear interpolation using multiple froude numbers with associated
        ensemble indices.

        Parameter
        ---------
        u_froude: np.array(float)
            Array of froude numbers for the u velocity component
        v_froude: np.array(float)
            Array of froude numbers for the v velocity component
        ensemble_idx: np.array(int)
            Array of ensemble ids associated with froude numbers

        Returns
        -------
        q: float
            Middle discharge computed using interpolated velocities
        """

        # Interpolate u
        data = np.vstack((self.cross_section_rng[ensemble_idx], u_froude)).T
        data_sorted = np.sort(data, axis=0)
        u_interpolated = np.interp(
            self.cross_section_rng[self.invalid_ensembles],
            data_sorted[:, 0],
            data_sorted[:, 1],
        ) * np.sqrt(self.depths[self.invalid_ensembles] * 9.81)
        u_combined = np.copy(self.u)
        u_combined[:, self.invalid_ensembles] = (
            u_interpolated * self.cells_to_use[:, self.invalid_ensembles]
        )

        # Interpolate v
        data = np.vstack((self.cross_section_rng[ensemble_idx], v_froude)).T
        data_sorted = np.sort(data, axis=0)
        v_interpolated = np.interp(
            self.cross_section_rng[self.invalid_ensembles],
            data_sorted[:, 0],
            data_sorted[:, 1],
        ) * np.sqrt(self.depths[self.invalid_ensembles] * 9.81)
        v_combined = np.copy(self.v)
        v_combined[:, self.invalid_ensembles] = (
            v_interpolated * self.cells_to_use[:, self.invalid_ensembles]
        )
        # Compute discharge
        q = self.compute_discharge(
            u=u_combined,
            v=v_combined,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

        return q

    def froude_constant_interpolation(self, u_froude, v_froude):
        """Compute the discharge using a constant froude number to interpolate
        velocity for invalid ensembles.

        Parameter
        --------
        u_froude: float
            Froude number for u velocity component.
        v_froude: float
            Froude number for v velocity component.

        Returns
        -------
        q: float
            Middel discharge computed using interpolated values
        """

        u_interpolated = u_froude * np.sqrt(
            self.depths[self.invalid_ensembles] * 9.81
        )
        v_interpolated = v_froude * np.sqrt(
            self.depths[self.invalid_ensembles] * 9.81
        )

        u_combined = np.copy(self.u)
        u_combined[:, self.invalid_ensembles] = (
            u_interpolated * self.cells_to_use[:, self.invalid_ensembles]
        )
        v_combined = np.copy(self.v)
        v_combined[:, self.invalid_ensembles] = (
            v_interpolated * self.cells_to_use[:, self.invalid_ensembles]
        )

        q = self.compute_discharge(
            u=u_combined,
            v=v_combined,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

        return q

    # Thin plate spline
    # =================
    def tps_interpolation(self):

        # Compute 1d arrays for use in Rdf
        u_1d, v_1d, x_1d, y_1d, z_1d = self.no_slip_coordinates(
            u=self.u,
            v=self.v,
            depths=self.depths,
            depth_cell_depth=self.depth_cell_depth,
            rng=self.cross_section_rng
        )

        x_invalid, y_invalid, z_invalid, invalid_indices = self.invalid_data_coordinates(
            depths=self.depths,
            depth_cell_depth=self.depth_cell_depth,
            top_cell_depth=self.top_depth_cell_depth,
            bottom_cell_depth=self.bottom_depth_cell_depth,
            rng=self.cross_section_rng
        )

        # Create Rdf models for u and v
        tps_u = Rbf(x_1d, y_1d, z_1d, u_1d, function='thin_plate')
        tps_v = Rbf(x_1d, y_1d, z_1d, v_1d, function='thin_plate')

        # Interpolate u and v for invalid ensemblescccccbggncvenlcvuguiniicfinhjnruugiiguttvbhf

        u_interpolated = tps_u(x_invalid, y_invalid, z_invalid)
        v_interpolated = tps_v(x_invalid, y_invalid, z_invalid)

        # Combine valid and interpolated data
        u_combined, v_combined = self.combine_data(u_interpolated, v_interpolated, invalid_indices)

        # Compute discharge
        q = self.compute_discharge(
            u=u_combined,
            v=v_combined,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

        return q

    # Kriging
    # =======
    def kriging_interpolation(self):
        depth_cell_depth_normalized = self.depth_cell_depth / self.depths
        rng_normalized = self.cross_section_rng / np.nanmax(self.cross_section_rng)
        depths_normalized = self.depths / self.depths
        top_cell_depth_normalized = self.top_depth_cell_depth / self.depths
        bottom_cell_depth_normalized = self.bottom_depth_cell_depth / self.depths

        u_1d, v_1d, x_1d, y_1d, z_1d = self.no_slip_coordinates(
            u=self.u,
            v=self.v,
            depths=depths_normalized,
            depth_cell_depth=depth_cell_depth_normalized,
            rng=rng_normalized,
        )
        coordinates = np.vstack((x_1d, y_1d)).T
        # Compute spherical variogram
        variogram_u = skg.Variogram(
            coordinates,
            u_1d,
            model="spherical",
            maxlag=0.6,
            n_lags=25,
            normalize=False,
            use_nugget=True,
        )
        variogram_v = skg.Variogram(
            coordinates,
            v_1d,
            model="spherical",
            maxlag=0.6,
            n_lags=25,
            normalize=False,
            use_nugget=True,
        )

        # Compute kriging model
        kriging_u = skg.OrdinaryKriging(variogram_u, max_points=10, mode='exact')
        kriging_v = skg.OrdinaryKriging(variogram_v, max_points=10, mode="exact")

        # Compute interpolated values for invalid ensembles
        x_invalid, y_invalid, _, invalid_indices = self.invalid_data_coordinates(
            depths=depths_normalized,
            depth_cell_depth=depth_cell_depth_normalized,
            top_cell_depth=top_cell_depth_normalized,
            bottom_cell_depth=bottom_cell_depth_normalized,
            rng=rng_normalized,
        )
        u_interpolated = kriging_u.transform(x_invalid, y_invalid)
        v_interpolated = kriging_v.transform(x_invalid, y_invalid)

        u_combined, v_combined = self.combine_data(
            u_interpolated=u_interpolated,
            v_interpolated=v_interpolated,
            invalid_indices=invalid_indices,
        )

        q = self.compute_discharge(
            u=u_combined,
            v=v_combined,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

        return q
    # Supporting methods
    # ==================

    def select_seed_ensembles(self):
        """Compute the starting ensemble using the center of mass method.

        Returns
        -------
        selected_ensembles: np.array(int)
            Ensembles used to compute the seed value for isovel
        """
        # Compute center of mass
        x_prod = self.u * self.boat_v - self.v * self.boat_u
        q = x_prod * self.depth_cell_size * self.ensemble_width
        q_ens = np.nansum(q, axis=0)
        center_of_mass = np.nansum((self.cross_section_rng * q_ens)) / np.nansum(q_ens)
        starting_idx = np.argmin(np.abs(self.cross_section_rng - center_of_mass))

        # Compute indexes of the area to average 5 valid ensembles before and after starting ensemble
        before = []
        before_count = 0
        new_idx = starting_idx

        while before_count < 5 and new_idx > 0:
            new_idx += -1
            if new_idx not in self.invalid_ensembles:
                before.append(new_idx)
                before_count += 1
        after = []
        after_count = 0
        new_idx = starting_idx
        while after_count < 5 and new_idx < self.u.shape[1] - 1:
            new_idx += 1
            if new_idx not in self.invalid_ensembles:
                after.append(new_idx)
                after_count += 1

        selected_ensembles = np.sort(np.hstack((starting_idx, before, after)))

        return selected_ensembles

    @staticmethod
    def compute_discharge(u, v, boat_u, boat_v, depth_cell_size, dt, start_edge):
        x_prod = u * boat_v - v * boat_u
        if start_edge == "Left":
            x_prod = -x_prod
        q = np.nansum(x_prod * depth_cell_size * dt)

        return q

    def combine_data (self, u_interpolated, v_interpolated, invalid_indices):
        """ Combine the valid and invalid data.
        Parameters
        ----------
        u_interpolated: np.array(float)
            Array containing interpolated u velocities
        v_interpolated: np.array(float)
            Array containing interpolated v velocities
        invalid_indices: np.array(tuple)
            Array of index pairs of interpolated data

        Returns
        -------
        u_combined: np.array(float)
            Water velocity u-component with interpolated values
        v_combined: np.array(float)
            Water velocity v-component with interpolated values
        """
        u_combined = np.copy(self.u)
        v_combined = np.copy(self.v)
        for n, coord in enumerate(invalid_indices):
            u_combined[coord] = u_interpolated[n]
            v_combined[coord] = v_interpolated[n]

        return u_combined, v_combined

    def no_slip_coordinates(self, u, v, depths, depth_cell_depth, rng):
        """Create 1D arrays with no slip velocity condition at the
        streambed for data used in tsp.

        Parameters
        ----------
        u: np.array(float)
            Array containing u velocities
        v: np.array(float)
            Array containing v velocities
        depths: np.array(float)
            Array containing streambed depths
        depth_cell_depth: np.array(float)
            Array containing depth cell depths
        rng: np.array(float)
            Array containing cross section ranges to each ensemble

        Returns
        -------
        u_1d: np.array(float)
            1D array of u velocity component
        v_1d: np.array(float)
            1D array of v velocity component
        x_1d: np.array(float)
            1D array of range along cross section
        y_1d: np.array(float)
            1D array of depth cell depths
        z_1d: np.array(float)
            1D array of streambed depths
        """
        # Construct u velocity 1d array
        u_1d = u.flatten(order="F")
        u_1d = u_1d[np.logical_not(np.isnan(u_1d))]
        u_1d = np.hstack((u_1d, np.zeros((u.shape[1]))))

        # Construct v velocity 1d array
        v_1d = v.flatten(order="F")
        v_1d = v_1d[np.logical_not(np.isnan(v_1d))]
        v_1d = np.hstack((v_1d, np.zeros((v.shape[1]))))

        # Construct x 1d array
        x_1d = self.cells_to_use * rng
        x_1d[np.isnan(u)] = np.nan
        x_1d = x_1d.flatten(order="F")
        x_1d = x_1d[np.logical_not(np.isnan(x_1d))]
        x_1d = np.hstack((x_1d, rng))

        # Construct y 1d array
        y_1d = np.copy(depth_cell_depth)
        y_1d[np.isnan(u)] = np.nan
        y_1d = y_1d.flatten(order="F")
        y_1d = y_1d[np.logical_not(np.isnan(y_1d))]
        y_1d = np.hstack((y_1d, depths))

        # Construct z 1d array
        z_1d= self.cells_to_use * depths
        z_1d[np.isnan(u)] = np.nan
        z_1d = z_1d.flatten(order="F")
        z_1d = z_1d[np.logical_not(np.isnan(z_1d))]
        z_1d = np.hstack((z_1d, depths))

        u_1d = u_1d[np.logical_not(np.isnan(z_1d))]
        v_1d = v_1d[np.logical_not(np.isnan(z_1d))]
        x_1d = x_1d[np.logical_not(np.isnan(z_1d))]
        y_1d = y_1d[np.logical_not(np.isnan(z_1d))]
        z_1d = z_1d[np.logical_not(np.isnan(z_1d))]

        return u_1d, v_1d, x_1d, y_1d, z_1d

    def invalid_data_coordinates(self, depths, depth_cell_depth, top_cell_depth, bottom_cell_depth, rng):
        """Compute 1D array of coordinates for invalid ensembles.

        Parameters
        ----------
        depths: np.array(float)
            Array containing streambed depths
        depth_cell_depth: np.array(float)
            Array containing depth cell depths
        top_cell_depth: np.array(float)
            Array containing top cell depths
        bottom_cell_depth: np.array(float)
            Array containing bottom cell depths
        rng: np.array(float)
            Array containing cross section ranges to each ensemble
        Returns
        -------
        x: np.array(float)
            1D array of cross section range for invalid ensembles
        y: np.array(float)
            1D array of depth cell depths for invalid ensembles
        z: np.array(float)
            1D array of streambed depths for invalid ensembles
        invalid_indices: np.array(tuple)
            1D array of indices of depth cells of invalid ensembles
        """
        x, y, z = [], [] ,[]
        invalid_indices = []
        for ens in self.invalid_ensembles:
            for cell in range (len(depth_cell_depth[:, ens])):
                if top_cell_depth[ens]<depth_cell_depth[cell, ens]<bottom_cell_depth[ens]:
                    x.append(rng[ens])
                    y.append(depth_cell_depth[cell, ens])
                    z.append(depths[ens])
                    invalid_indices.append((cell , ens))
        x, y, z = np.array(x), np.array(y), np.array(z)
        return x, y, z, invalid_indices

    def compute_mean_cross_section(self, transect):
        """Computes a mean cross section projected on a line from the first to the last shiptrack points.

        Parameters
        ----------
        transect: TransectData
            Transect object
        """

        boat_track = transect.boat_vel.compute_boat_track(transect=transect, ref=None)
        unit_x = boat_track["track_x_m"][-1] / boat_track["dmg_m"][-1]
        unit_y = boat_track["track_y_m"][-1] / boat_track["dmg_m"][-1]
        track_x_cum_sum = np.nancumsum(boat_track["track_x_m"])
        track_y_cum_sum = np.nancumsum(boat_track["track_y_m"])
        self.cross_section_rng = unit_x * track_x_cum_sum + unit_y * track_y_cum_sum
        self.ensemble_width = np.hstack((0, np.diff(self.cross_section_rng)))
