import numpy as np

class IsoVel(object):

    def __init__(self, transect, exponent, normalize, invalid_ensembles):

        self.exponent = exponent
        self.normalize = normalize
        self.field = None

        # Compute mean cross section ranges and ensemble widths
        self.compute_mean_cross_section(transect=transect)

        depth_data = getattr(transect.depths, transect.depths.selected)
        self.depth_cell_depth = depth_data.depth_cell_depth_m
        self.depth_cell_size = depth_data.depth_cell_size_m
        self.depths=depth_data.depths_processed_m,

        boat_data = getattr(transect.boat_vel, transect.boat_vel.selected)
        self.boat_u = boat_data.u_processed_mps
        self.boat_v = boat_data.v_processed_mps

        self.u = transect.w_vel.u_processed_mps
        self.v = transect.w_vel.v_processed_mps

        self.start_edge = transect.start_edge
        self.dt = transect.date_time.ens_duration_sec
        self.cells_above_sl=transect.w_vel.cells_above_sl
        self.invalid_ensembles = invalid_ensembles

        # Create initial isovel field
        self.contour(
            left_edge_shape=transect.edges.left.type,
            left_edge_distance=transect.edges.left.distance_m,
            right_edge_shape=transect.edges.right.type,
            right_edge_distance=transect.edges.right.distance_m,
        )

        top_depth_cell_depth = depth_data.depth_cell_depth_m[0, :]
        bottom_cell_number = np.nansum(cells_above_sl, axis=0)
        bottom_depth_cell_depth = np.array([dcdini[bottom_cell_number[ens], ens] for ens in range(dcdini.shape[1])])

        # Compute seed values
        u_seed, v_seed, seed_ensemble_idx, depth_cell_depth_idx = self.compute_seed_values(
            top_cell_depth=top_depth_cell_depth,
            bottom_cell_depth=bottom_depth_cell_depth,
        )

        # Compute velocity field based on seed values
        self.compute_velocity_fields(
            u_seed=u_seed,
            v_seed=v_seed,
            ensemble_idx=seed_ensemble_idx,
            depth_cell_depth_idx=depth_cell_depth_idx,
        )

        self.compute_isovel_discharge()

    def contour(
        self,
        left_edge_shape,
        left_edge_distance,
        right_edge_shape,
        right_edge_distance,
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
            n_top,
        ) = self.update_geometry_isovel(
            start_edge_distance,
            start_edge_shape,
            end_edge_distance,
            end_edge_shape,
        )

        # Initialisation
        velocity_field = nan * np.zeros(depth_cell_depth_iso.shape)
        q = 0
        area = 0
        for cell_idx in range(depth_cell_depth_iso.shape[0]):
            for ens_idx in range(depth_cell_depth_iso.shape[1]):
                # Compute for depths above ensemble depth
                if depth_cell_depth_iso[cell_idx, ens_idx] < depth_iso[ens_idx]:
                    # Contribution for streambed
                    x = self.cross_section_rng[0:-1] - self.cross_section_rng[ens_idx]
                    y = depth_iso[0:-1] - depth_cell_depth_iso[cell_idx, ens_idx]
                    radial_dist_b = np.sqrt(x**2 + y**2)
                    cell_vel = np.nansum(
                        (radial_dist_b[radial_dist_b > 0] ** (self.exponent - 1))
                        * y
                        * ensemble_widths_iso[1:]
                    )

                    # Contribution from a rectangular edge at the start bank
                    if start_edge_shape == "Rectangular":
                        x = self.cross_section_rng[ens_idx]
                        y = (
                            np.arange(int(depth_iso[0] / depth_cell_size_iso[cell_idx, ens_idx]))
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
                            np.arange(int(depth_iso[-1] / depth_cell_size_iso[cell_idx, ens_idx]))
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
                    cell_area = depth_cell_size_iso[cell_idx, ens_idx] * ensemble_widths_iso[ens_idx]
                    q = q + cell_vel * cell_area
                    area = area + cell_area
        # Normalize velocity field
        mean_vel = q / area
        self.field = velocity_field / mean_vel  # isovel field

        # Remove added top and edge areas
        self.field = self.field[n_top:, n_left:-n_right]
        self.field = self.field * cells_above_sl

        # Restrict isovel_field to only the cells above sidelobe
        cells_to_use = self.cells_above_sl.astype(float)
        cells_to_use[cells_to_use == 0] = np.nan
        self.field = self.field * cells_to_use

    @staticmethod
    def update_geometry_isovel(
        self,
        start_edge_distance,
        start_edge_shape,
        end_edge_distance,
        end_edge_shape,
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
        """

        # Add depth cells between water surface and first cell
        top_cell_size = self.depth_cell_depth[0, :] / 4
        depth_cell_size_top = np.tile(top_cell_size, (4, 1))
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
            n_left,
            n_right,
        ) = add_edges(
            start_edge_distance=start_edge_distance,
            start_edge_shape=start_edge_shape,
            end_edge_distance=end_edge_distance,
            end_edge_shape=end_edge_shape,
            depth=self.depth,
            ensemble_widths=self.ensemble_widths,
            depth_cell_depth=depth_cell_depth_iso,
            depth_cell_size_iso=depth_cell_size_iso,
        )

        # normalization or not
        if self.normalize == 1:
            depth_cell_depth_iso = depth_cell_depth_iso / depth_iso
            depth_cell_size_iso = depth_cell_size_iso / depth_iso

        return (
            depth_cell_depth_iso,
            depth_cell_size_iso,
            depth_iso,
            ensemble_widths_iso,
            n_start,
            n_end,
            n_top,
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
        n_start = round(start_edge_distance / mean_ensemble_width)
        n_end = round(end_edge_distance / mean_ensemble_width)

        # Add cell widths
        start_ensemble_widths = np.tile(ensemble_widths, (1, n_start))[0]
        end_ensemble_widths = np.tile(ensemble_widths, (1, n_end))[0]
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
                    depth[0] * ((mean_cell_width * i) / start_edge_distance)
                    for i in range(n_start)
                ]
            )

        if end_edge_shape == "Rectangular":
            end_edge_depths = depth[-1] * np.ones(n_end)
        else:
            end_edge_depths = np.array(
                [
                    depth[-1] / start_edge_distance * mean_cell_width * (n_end - i - 1)
                    for i in range(n_end)
                ]
            )

        depth_iso = np.concatenate((start_edge_depths, depth))
        depth_iso = np.concatenate((depth_iso, end_edge_depths))

        # Add depth cell depths
        start_cell_depths = np.tile(depth_cell_depth[:, 0], (n_start, 1))
        end_cell_depths = np.tile(depth_cell_depth[:, -1], (n_right, 1))
        depth_cell_depth_iso = np.hstack(
            (np.transpose(start_cell_depths), depth_cell_depth)
        )
        depth_cell_depth_iso = np.hstack(
            (depth_cell_depth_iso, np.transpose(end_cell_depths))
        )

        # Add depth cell size
        start_cell_size = np.tile(depth_cell_size[:, 0], (n_start, 1))
        end_cell_size = np.tile(depth_cell_size[:, -1], (n_right, 1))
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

    def compute_seed_values(
            self,
            top_cell_depth,
            bottom_cell_depth,
            ):
        """Compute the seed values using center of mass and the center
        of the measured area.

        Parameters
        ----------
        top_cell_depth: np.array(float)
            Depth of top cell in each ensemble
        bottom_cell_depth: np.array(float)
            Depth of bottom cell in each ensemble

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

        # Compute seed values
        seed_ensembles = select_seed_ensembles()

        u_seed, v_seed, ensemble_idx, depth_cell_depth_idx = isovel_seed(
            top_cell_depth=top_cell_depth,
            bottom_cell_depth=bottom_cell_depth,
            seed_ensembles=seed_ensembles,
            seed_ensemble_idx=seed_ensemble_idx,
        )

        return u_seed, v_seed, ensemble_idx, depth_cell_depth_idx

    def compute_velocity_fields(
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
        u_iso = u_seed * self.field / self.field[depth_cell_depth_idx, ensemble_idx]
        v_iso = v_seed * self.field / self.field[depth_cell_depth_idx, ensemble_idx]

        # Identify ensembles in the center 40% of the cross section
        rng_30, rng_70 = 0.3 * np.nanmax(self.cross_section_rng), 0.7 * np.nanmax(self.cross_section_rng)
        i_start, i_max = np.argmax(self.cross_section_rng > rng_30), np.argmin(self.cross_section_rng < rng_70)
        idx = [i for i in range(i_start, i_max) if i not in self.invalid_ensembles]

        # Compute the discharge using the measured data
        q = self.compute_discharge(
            u=self.u[:, idx],
            v=self.v[:, idx],
            boat_u=self.boat_u[idx],
            boat_v=self.boat_v[idx],
            depth_cell_size=self.depth_cell_size[:, idx],
            dt=self.dt[idx],
            start_edge=self.start_edge
        )

        # Compute the difference in discharge using the isovel field
        u_diff = u_iso - u
        v_diff = v_iso - v
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
            u_iso = u_seed * isovel_field / self.field[depth_cell_depth_idx, ensemble_idx]
            v_iso = v_seed * isovel_field / self.field[depth_cell_depth_idx, ensemble_idx]
            u_diff = u_iso - u
            v_diff = v_iso - v
            dq = compute_inter_discharge(
                u=u_diff[:, idx],
                v=v_diff[:, idx],
                boat_u=self.boat_u[idx],
                boat_v=self.boat_v[idx],
                depth_cell_size=self.depth_cell_size[:, idx],
                dt=self.dt[idx],
                start_edge=self.start_edge,
            )
            q_ratio = dq / q
        self.u_field = u_iso
        self.v_field = v_iso

    @staticmethod
    def select_seed_ensembles():
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
            new_idx += - 1
            if new_idx not in self.invalid_ensembles:
                before.apppend(new_idx)
                before_count += 1
        after = []
        after_count = 0
        new_idx = starting_idx
        while after_count < 5 and new_idx < self.u.shape[1] - 1:
            new_idx += 1
            if new_idx not in self.invalid_ensembles:
                after.apppend(new_idx)
                after_count += 1

        selected_ensembles = np.sort(np.hstack((starting_idx, before, after)))

        return selected_ensembles

    @staticmethod
    def isovel_seed(
            top_cell_depth, bottom_cell_depth, seed_ensembles,
    ):
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
        d_min, d_max = top_cell_depth_mean + 0.375 * (
            bottom_cell_depth_mean - top_cell_depth_mean
        ), bottom_cell_depth_mean - 0.375 * (bottom_cell_depth_mean - top_cell_depth_mean)

        # Create array of depth cells from selected ensembles that represent 25% of the measured area
        depth_cells_selected_depth = self.depth_cell_depth[:, seed_ensembles]
        depth_cells_selected_depth[d_min > depth_cells_selected_depth] = np.nan
        depth_cells_selected_depth[d_max < depth_cells_selected_depth] = np.nan

        # Create array to identify selected depth cells
        selected_data = np.copy(depth_cells_selected_depth)
        selected_data[np.logical_not(np.isnan(selected_data))] = 1

        # Compute mean velocity
        u_mean = np.nanmean(np.nanmean(self.u[:, seed_ensembles] * selected_data, axis=0))
        v_mean = np.nanmean(np.nanmean(self.v[:, seed_ensembles] * selected_data, axis=0))

        # Compute depth location
        depth_cell_idx = np.nanargmin(
            np.abs(depth_cells_selected_depth[:, 2] - np.nanmean(depth_cells_selected_depth))
        )

        # Compute ensemble location
        ensemble_idx = np.argmin(self.cross_section_rng - np.nanmean(self.cross_section_rng[seed_ensembles]))

        return u_mean, v_mean, ensemble_idx, depth_cell_idx

    @staticmethod
    def compute_discharge(u, v, boat_u, boat_v, depth_cell_size, dt, start_edge):

        x_prod = u * boat_v - v * boat_u
        if start_edge == "Left":
            x_prod = -x_prod
        q = np.nansum(x_prod * depth_cell_size * dt)

        return q

    def compute_isovel_discharge(self):

        self.inter_replace()
        self.q_isovel = self.compute_discharge(
            u=self.u_interpolated,
            v=self.v_interpolated,
            boat_u=self.boat_u,
            boat_v=self.boat_v,
            depth_cell_size=self.depth_cell_size,
            dt=self.dt,
            start_edge=self.start_edge,
        )

    def inter_replace(self):
        """
        Replace velocities of unprocessed fields by the interpolated values

        """
        self.u_interpolated = np.copy(self.u)
        self.v_interpolated = np.copy(self.v)
        self.u_interpolated[:, self.invalid_ensembles] = self.u_field[:, self.invalid_ensembles]
        self.v_interpolated[:, self.invalid_ensembles] = self.v_field[:, self.invalid_ensembles]

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
        self.ensemble_width = np.diff(cross_section)
        self.ensemble_width = np.hstack((0, self.ensemble_width))
