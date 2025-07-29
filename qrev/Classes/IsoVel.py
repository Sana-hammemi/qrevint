import numpy as np


class IsoVel(object):

    def __init__(transect, ensemble_widths, exp, normalize):
        depth_data = getattr(transect.depths, transect.depths.selected)
        self.field = self.contour(
            depths=depth_data.depths_processed_m,
            depth_cell_depth=depth_data.depth_cell_depth_m,
            depth_cell_size=depth_data.depth_cell_size_m,
            ensemble_widths=ensemble_widths,
            exp=exp,
            left_edge_shape=transect.edges.left.type,
            left_edge_distance=transect.edges.left.distance_m,
            right_edge_shape=transect.edges.right.type,
            right_edge_distance=transect.edges.right.distance_m,
            start_edge=transect.start_edge,
            normalize=normalize,
        )

    def contour(
        self,
        depths,
        depth_cell_depth,
        depth_cell_size,
        ensemble_widths,
        exp,
        left_edge_shape,
        left_edge_distance,
        right_edge_shape,
        right_edge_distance,
        start_edge,
        normalize,
    ):
        """Compute isovel field

        Parameters
        ----------
        depths: np.array(float)
            Total depth for each ensemble
        depth_cell_depth: np.array(float)
            Depth to center of each cell
        depth_cell_size: np.array(float)
            Vertical size of each cell
        ensemble_widths: np.array(float)
            Width of each cell
        exp: float
            Power exponent (typically 1/7)
        left_edge_shape: str
            Shape of left edge
        left_edge_distance: float
            Distance to left edge
        right_edge_shape: str
            Shape of right edge
        right_edge_distance: float
            Distance to right edge
        start_edge: str
            Edge that transect started
        normalize: bool
            Whether to normalize the isovel field
        """

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
            depths,
            depth_cell_depth,
            depth_cell_size,
            ensemble_widths,
            right_edge_distance,
            left_edge_distance,
            right_edge_shape,
            left_edge_shape,
            start_edge,
            normalize,
        )
        [dcd_iso, dcs_iso] = depth_data_iso
        # initialisation
        n_i, n_j = len(dcd_iso), len(dcd_iso[0])
        uem = nan * np.zeros((n_i, n_j))
        Ue = 0
        A = 0
        xd = np.cumsum(w_iso)
        L = xd[-1]
        for i in range(n_i):
            for j in range(n_j):
                u = 0
                xm = xd[j]
                ym = dcd_iso[i][j]
                dy = dcs_iso[:, j][0]
                if dcd_iso[i, j] < yd[j]:
                    # bottom
                    for k in range(len(yd) - 1):
                        rb = sqrt((xd[k] - xm) ** 2 + (yd[k] - ym) ** 2)
                        if rb != 0:
                            ub = (rb ** (m - 1)) * (yd[k] - ym) * (xd[k + 1] - xd[k])
                            u = u + ub
                    # left
                    if geom == "Square":
                        for k in range(int(yd[0] / dy)):
                            rl = sqrt(xm**2 + (k * dy - ym) ** 2)
                            if rl != 0:
                                u = u + (rl ** (m - 1)) * xm * dy
                    # right
                    if geom == "Square":
                        for k in range(int(yd[-1] / dy)):
                            rr = sqrt((L - xm) ** 2 + (k * dy - ym) ** 2)
                            if rr != 0:
                                u = u + (rr ** (m - 1)) * (L - xm) * dy
                    uem[i, j] = u
                    Ue = Ue + u * dy * w_iso[j]
                    A = A + dy * w_iso[j]
        Ue = Ue / A
        isovel_field = uem / Ue  # isovel field
        # reshape the isovel field (remove added top and edges areas)
        isovel_field = isovel_field[n_top:]
        isovel_field = isovel_field[:, n_left:-n_right]
        return isovel_field

    @staticmethod
    def update_geometry_isovel(
        depth,
        depth_cell_depth,
        depth_cell_size,
        ensemble_widths,
        right_edge_distance,
        left_edge_distance,
        right_edge_shape,
        left_edge_shape,
        start_edge,
        normalize,
    ):
        """
        Update velocity and geometry data adding edges and top areas

        Parameters
        ----------
        depth: np.array(float)
            Total depth for each ensemble
        depth_cell_depth: np.array(float)
            Depth to center of each cell
        depth_cell_size: np.array(float)
            Vertical size of each cell
        ensemble_widths: np.array(float)
            Width of each cell
        left_edge_shape: str
            Shape of left edge
        left_edge_distance: float
            Distance to left edge
        right_edge_shape: str
            Shape of right edge
        right_edge_distance: float
            Distance to right edge
        start_edge: str
            Edge that transect started
        normalize: bool
            Whether to normalize the isovel field

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
        top_cell_size = depth_cell_depth[0, :] / 4
        depth_cell_size_top = np.tile(top_cell_size, (4, 1))
        depth_cell_depth_top = np.nancumsum(depth_cell_size_top, axis=0) - top_cell_size
        depth_cell_size_iso = np.concatenate(
            (depth_cell_size_top, depth_cell_size), axis=0
        )
        depth_cell_depth_iso = np.concatenate(
            (depth_cell_depth_top, depth_cell_depth), axis=0
        )

        # Add edges
        if start_edge == "Left":
            (
                depth_iso,
                ensemble_widths_iso,
                depth_cell_depth_iso,
                depth_cell_size_iso,
                n_left,
                n_right,
            ) = add_edges(
                start_edge_distance=left_edge_distance,
                start_edge_shape=left_edge_shape,
                end_edge_distance=right_edge_distance,
                end_edge_shape=right_edge_shape,
                depth=depth,
                ensemble_widths=ensemble_widths,
                depth_cell_depth=depth_cell_depth_iso,
                depth_cell_size_iso=depth_cell_size_iso,
            )
        else:
            (
                depth_iso,
                ensemble_widths_iso,
                depth_cell_depth_iso,
                depth_cell_size_iso,
                n_right,
                n_left,
            ) = add_edges(
                start_edge_distance=left_edge_distance,
                start_edge_shape=left_edge_shape,
                end_edge_distance=right_edge_distance,
                end_edge_shape=right_edge_shape,
                depth=depth,
                ensemble_widths=ensemble_widths,
                depth_cell_depth=depth_cell_depth_iso,
                depth_cell_size_iso=depth_cell_size_iso,
            )

        # normalization or not
        if normalize == 1:
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
