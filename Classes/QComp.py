import numpy as np
from Classes.TransectData import TransectData
from Classes.BoatStructure import BoatStructure
from MiscLibs.common_functions import cart2pol, pol2cart, nan_less, nan_greater

# from profilehooks import profile
from DischargeFunctions.top_discharge_extrapolation import extrapolate_top
from DischargeFunctions.bottom_discharge_extrapolation import extrapolate_bot


class QComp(object):
    """Computes the discharge for each transect.

    Attributes
    ----------
    top: float
        Transect total extrapolated top discharge
    middle: float
        Transect total measured middle discharge including interpolations
    bottom: float
        Transect total extrapolated bottom discharge
    top_ens: np.array(float)
        Extrapolated top discharge by ensemble
    middle_cells: np.array(float)
        Measured middle discharge including interpolation by cell
    middle_ens: np.array(float)
        Measured middle discharge including interpolation by ensemble
    bottom_ens: np.array(float)
        Extrapolate bottom discharge by ensemble
    left: float
        Left edge discharge
    left_idx:
        Ensembles used for left edge
    right: float
        Right edge discharge
    right_idx:
        Ensembles used for right edge
    total_uncorrected: float
        Total discharge for transect uncorrected for moving-bed, if required
    total: float
        Total discharge with moving-bed correction applied if necessary
    correction_factor: float
        Moving-bed correction factor, if required
    int_cells: float
        Total discharge computed for invalid depth cells excluding invalid
        ensembles
    int_ens: float
        Total discharge computed for invalid ensembles
    """

    def __init__(self):
        """Initialize class and instance variables."""

        self.top = None
        self.middle = None
        self.bottom = None
        self.top_ens = None
        self.middle_cells = None
        self.middle_ens = None
        self.bottom_ens = None
        self.left = None
        self.left_idx = []
        self.right = None
        self.right_idx = []
        self.total_uncorrected = None
        self.total = None
        self.correction_factor = 1
        self.int_cells = None
        self.int_ens = None

    # @profile
    def populate_data(
        self,
        data_in,
        moving_bed_data=None,
        top_method=None,
        bot_method=None,
        exponent=None,
    ):
        """Discharge is computed using the data provided to the method.
        Water data provided are assumed to be corrected for the navigation
        reference.
        If a moving-bed correction is to be applied, it is computed and applied.
        The TRDI method using expanded delta time is applied if the
        processing method is WR2.

        Parameters
        ----------
        data_in: TransectData
            Object TransectData
        moving_bed_data: list
            List of MovingBedTests objects
        top_method: str
            Top extrapolation method
        bot_method: str
            Bottom extrapolation method
        exponent: float
            Extrapolation exponent
        """

        # Use bottom track interpolation settings to determine the
        # appropriate algorithms to apply
        if data_in.boat_vel.bt_vel.interpolate == "None":
            processing = "WR2"
        elif data_in.boat_vel.bt_vel.interpolate == "Linear":
            processing = "QRev"
        else:
            processing = "RSL"

        # Compute cross product
        x_prod = QComp.cross_product(data_in)

        # Get index of ensembles in moving-boat portion of transect
        in_transect_idx = data_in.in_transect_idx

        if processing == "WR2":
            # TRDI uses expanded delta time to handle invalid ensembles
            # which can be caused by invalid BT WT, or depth.  QRev by default
            # handles this invalid data through linear interpolation of the
            # invalid data through linear interpolation of the invalid data
            # type.  This if statement and associated code is required to
            # maintain compatibility with WinRiver II discharge computations.

            # Determine valid ensembles
            valid_ens = np.any(np.logical_not(np.isnan(x_prod)))
            valid_ens = valid_ens[in_transect_idx]

            # Compute the ensemble duration using TRDI approach of expanding
            # delta time to compensate for invalid ensembles
            n_ens = len(valid_ens)
            ens_dur = data_in.date_time.ens_duration_sec[in_transect_idx]
            delta_t = np.tile([np.nan], n_ens)
            cum_dur = 0
            idx = 1
            for j in range(idx, n_ens):
                cum_dur = np.nansum(np.hstack([cum_dur, ens_dur[j]]))
                if valid_ens[j]:
                    delta_t[j] = cum_dur
                    cum_dur = 0

        else:
            # For non-WR2 processing use actual ensemble duration
            delta_t = data_in.date_time.ens_duration_sec[in_transect_idx]

        # Compute measured or middle discharge
        self.middle_cells = QComp.discharge_middle_cells(x_prod, data_in, delta_t)
        self.middle_ens = np.nansum(self.middle_cells, 0)
        self.middle = np.nansum(self.middle_ens)

        # Compute the top discharge
        trans_select = getattr(data_in.depths, data_in.depths.selected)
        num_top_method = {"Power": 0, "Constant": 1, "3-Point": 2, None: -1}
        try:
            self.top_ens = extrapolate_top(
                x_prod,
                data_in.w_vel.valid_data[0, :, :],
                num_top_method[data_in.extrap.top_method],
                data_in.extrap.exponent,
                data_in.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                num_top_method[top_method],
                exponent,
            )
        except SystemError:
            self.top_ens = QComp.extrapolate_top(
                x_prod,
                data_in.w_vel.valid_data[0, :, :],
                num_top_method[data_in.extrap.top_method],
                data_in.extrap.exponent,
                data_in.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                num_top_method[top_method], exponent,
            )
        self.top = np.nansum(self.top_ens)

        # Compute the bottom discharge
        num_bot_method = {"Power": 0, "No Slip": 1, None: -1}
        try:
            self.bottom_ens = extrapolate_bot(
                x_prod,
                data_in.w_vel.valid_data[0, :, :],
                num_bot_method[data_in.extrap.bot_method],
                data_in.extrap.exponent,
                data_in.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                num_bot_method[bot_method],
                exponent,
            )
        except SystemError:
            self.bottom_ens = QComp.extrapolate_bot(
                x_prod,
                data_in.w_vel.valid_data[0, :, :],
                num_bot_method[data_in.extrap.bot_method],
                data_in.extrap.exponent,
                data_in.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                num_bot_method[bot_method],
                exponent,
            )
        self.bottom = np.nansum(self.bottom_ens)

        # Compute interpolated cell and ensemble discharge from computed
        # measured discharge
        self.interpolate_no_cells(data_in)
        self.middle = np.nansum(self.middle_ens)
        self.int_cells, self.int_ens = QComp.discharge_interpolated(
            self.top_ens, self.middle_cells, self.bottom_ens, data_in
        )

        # Compute right edge discharge
        if data_in.edges.right.type != "User Q":
            self.right, self.right_idx = QComp.discharge_edge(
                "right", data_in, top_method, bot_method, exponent
            )
        else:
            self.right = data_in.edges.right.user_discharge_cms
            self.right_idx = []

        # Compute left edge discharge
        if data_in.edges.left.type != "User Q":
            self.left, self.left_idx = QComp.discharge_edge(
                "left", data_in, top_method, bot_method, exponent
            )
        else:
            self.left = data_in.edges.left.user_discharge_cms
            self.left_idx = []

        # Compute moving-bed correction, if applicable.  Two checks are used
        # to account for the way the meas object is created.

        # Moving-bed corrections are only applied to bottom track referenced
        # computations
        mb_type = None
        if data_in.boat_vel.selected == "bt_vel":
            if moving_bed_data is not None:

                # Determine if a moving-bed test is to be used for correction
                use_2_correct = []
                for mb_idx, test in enumerate(moving_bed_data):
                    use_2_correct.append(test.use_2_correct)
                    if test.use_2_correct:
                        mb_type = test.type

                if any(use_2_correct):

                    # Make sure composite tracks are turned off
                    if data_in.boat_vel.composite == "Off":
                        # Apply appropriate moving-bed test correction method
                        if mb_type == "Stationary":
                            self.correction_factor = self.stationary_correction_factor(
                                self.top,
                                self.middle,
                                self.bottom,
                                data_in,
                                moving_bed_data,
                                delta_t,
                            )
                        else:
                            self.correction_factor = self.loop_correction_factor(
                                self.top,
                                self.middle,
                                self.bottom,
                                data_in,
                                moving_bed_data[use_2_correct.index(True)],
                                delta_t,
                            )

        self.total_uncorrected = (
            self.left + self.right + self.middle + self.bottom + self.top
        )

        # Compute final discharge using correction if applicable
        if (
            self.correction_factor is None
            or self.correction_factor == 1
            or np.isnan(self.correction_factor)
        ):
            self.total = self.total_uncorrected
        else:
            self.total = (
                self.left
                + self.right
                + (self.middle + self.bottom + self.top) * self.correction_factor
            )

    @staticmethod
    def qrev_mat_in(meas_struct):
        """Processes the Matlab data structure to obtain a list of QComp
        objects containing the discharge data from the Matlab data structure.

        Parameters
        ----------
        meas_struct: mat_struct
            Matlab data structure obtained from sio.loadmat

        Returns
        -------
        discharge: list
            List of QComp data objects
        """

        discharge = []
        if hasattr(meas_struct.discharge, "bottom"):
            # Measurement has discharge data from only one transect
            q = QComp()
            q.populate_from_qrev_mat(meas_struct.discharge)
            discharge.append(q)
        else:
            # Measurement has discharge data from multiple transects
            for q_data in meas_struct.discharge:
                q = QComp()
                q.populate_from_qrev_mat(q_data)
                discharge.append(q)
        return discharge

    def populate_from_qrev_mat(self, q_in):
        """Populated QComp instance variables with data from QRev Matlab file.

        Parameters
        ----------
        q_in: mat_struct
            mat_struct_object containing QComp class data
        """

        self.top = q_in.top
        self.middle = q_in.middle
        self.bottom = q_in.bottom

        if type(q_in.topEns) is not np.ndarray:
            self.top_ens = np.array([q_in.topEns])
            self.middle_ens = np.array([q_in.middleEns])
            self.bottom_ens = np.array([q_in.bottomEns])
        else:
            self.top_ens = q_in.topEns
            self.middle_ens = q_in.middleEns
            self.bottom_ens = q_in.bottomEns

        self.middle_cells = q_in.middleCells
        # Handle special case for 1 ensemble or 1 cell
        if len(self.middle_cells.shape) < 2:
            if self.middle_ens.size > 1:
                # Multiple ensembles, one cell
                self.middle_cells = self.middle_cells[np.newaxis, :]
            else:
                # One ensemble, multiple cells
                self.middle_cells = self.middle_cells[:, np.newaxis]

        # If only one value, it will be read in as int but needs to be an
        # array of len 1
        self.left = q_in.left
        # If only one value, it will be read in as int but needs to be an
        # array of len 1
        if type(q_in.leftidx) is int:
            self.left_idx = np.array([q_in.leftidx])
        else:
            self.left_idx = q_in.leftidx
        self.right = q_in.right
        # If only one value, it will be read in as int but needs to be an
        # array of len 1
        if type(q_in.rightidx) is int:
            self.right_idx = np.array([q_in.rightidx])
        else:
            self.right_idx = q_in.rightidx
        self.total_uncorrected = q_in.totalUncorrected
        self.total = q_in.total
        self.correction_factor = q_in.correctionFactor
        if type(self.correction_factor) is np.ndarray:
            if len(self.correction_factor) == 0:
                self.correction_factor = 1
            else:
                self.correction_factor = self.correction_factor[0]
        self.int_cells = q_in.intCells
        self.int_ens = q_in.intEns

    def interpolate_no_cells(self, transect_data):
        """Computes discharge for ensembles where the depth is too
        shallow for any valid depth cells. The computation is done
        using interpolation of unit discharge defined as the ensemble
        discharge divided by the depth of the ensemble and the
        duration of the ensemble. The independent variable for the
        interpolation is the track distance. After interpolation the
        discharge for the interpolated ensembles is computed by
        multiplying the interpolated value by the depth and duration
        of those ensembles to achieve discharge for those ensembles.

        Parameters
        ----------
        transect_data: TransectData
             Object of TransectData
        """

        # Compute the discharge in each ensemble
        q_ensemble = self.top_ens + self.middle_ens + self.bottom_ens
        valid_ens = np.where(np.logical_not(np.isnan(q_ensemble)))[0]
        if len(valid_ens) > 1:
            idx = np.where(np.isnan(q_ensemble))[0]

            if len(idx) > 0:

                # Compute the unit discharge by depth for each ensemble
                depth_selected = getattr(
                    transect_data.depths, transect_data.depths.selected
                )
                unit_q_depth = (
                    q_ensemble
                    / depth_selected.depth_processed_m[transect_data.in_transect_idx]
                ) / transect_data.date_time.ens_duration_sec[
                    transect_data.in_transect_idx
                ]

                # Compute boat track
                boat_track = BoatStructure.compute_boat_track(
                    transect_data, transect_data.boat_vel.selected
                )

                # Create strict monotonic vector for 1-D interpolation
                q_mono = unit_q_depth
                x_mono = boat_track["distance_m"][transect_data.in_transect_idx]

                # Identify duplicate values, and replace with an average
                dups = self.group_consecutives(x_mono)
                if len(dups):
                    for dup in dups:
                        q_avg = np.nanmean(q_mono[np.array(dup)])
                        q_mono[dup[0]] = q_avg
                        q_mono[dup[1::]] = np.nan
                        x_mono[dup[1::]] = np.nan

                valid_q_mono = np.logical_not(np.isnan(q_mono))
                valid_x_mono = np.logical_not(np.isnan(x_mono))
                valid = np.all(np.vstack([valid_q_mono, valid_x_mono]), 0)

                # Interpolate unit q
                if np.any(valid):
                    unit_q_int = np.interp(
                        boat_track["distance_m"][transect_data.in_transect_idx],
                        x_mono[valid],
                        q_mono[valid],
                        left=np.nan,
                        right=np.nan,
                    )
                else:
                    unit_q_int = 0

                # Compute the discharge in each ensemble based on
                # interpolated data
                q_int = (
                    unit_q_int
                    * depth_selected.depth_processed_m[transect_data.in_transect_idx]
                    * transect_data.date_time.ens_duration_sec[
                        transect_data.in_transect_idx
                    ]
                )
                self.middle_ens[idx] = q_int[idx]

    @staticmethod
    def group_consecutives(vals):
        """Return list of consecutive lists of numbers from vals (number list)."""

        run = []
        result = []
        expect = vals[0]
        j = 0
        for n in range(1, len(vals)):
            if vals[n] == expect:
                j += 1
                if j > 1:
                    run.append(n)
                elif j > 0:
                    run.append(n - 1)
                    run.append(n)
            elif j > 0:
                result.append(run)
                run = []
                j = 0
            expect = vals[n]
        return result

    @staticmethod
    def cross_product(
        transect=None,
        w_vel_x=None,
        w_vel_y=None,
        b_vel_x=None,
        b_vel_y=None,
        start_edge=None,
    ):
        """Computes the cross product of the water and boat velocity.

        Input data can be a transect or component vectors for the water and
        boat velocities with the start edge.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        w_vel_x: np.array(float)
            Array of water velocity in the x direction
        w_vel_y: np.array(float)
            Array of water velocity in the y direction
        b_vel_x: np.array(float)
            Vector of navigation velocity in x-direction
        b_vel_y: np.array(float)
            Vector of naviagation velocity in y-direction
        start_edge: str
            Starting edge of transect (Left or Right)

        Returns
        -------
        xprod: np.array(float)
            Cross product values
        """

        if transect is not None:
            # Prepare water track data
            cells_above_sl = np.array(transect.w_vel.cells_above_sl).astype(float)
            cells_above_sl[cells_above_sl < 0.5] = np.nan
            w_vel_x = transect.w_vel.u_processed_mps * cells_above_sl
            w_vel_y = transect.w_vel.v_processed_mps * cells_above_sl

            # Get navigation data from object properties
            trans_select = getattr(transect.boat_vel, transect.boat_vel.selected)
            if trans_select is not None:
                b_vel_x = trans_select.u_processed_mps
                b_vel_y = trans_select.v_processed_mps
            else:
                b_vel_x = np.tile(
                    [np.nan], transect.boat_vel.bt_vel.u_processed_mps.shape
                )
                b_vel_y = np.tile(
                    [np.nan], transect.boat_vel.bt_vel.v_processed_mps.shape
                )

            start_edge = transect.start_edge

        # Compute the cross product
        xprod = np.multiply(w_vel_x, b_vel_y) - np.multiply(w_vel_y, b_vel_x)

        # Correct the sign of the cross product based on the start edge
        if start_edge == "Right":
            direction = 1
        else:
            direction = -1
        xprod = xprod * direction

        return xprod

    @staticmethod
    def discharge_middle_cells(xprod, transect, delta_t):
        """Computes the discharge in the measured or middle portion of the
        cross section.

        Parameters
        ----------
        xprod: np.array(float)
            Cross product computed from the cross product method
        transect: TransectData
            Object of TransectData
        delta_t: np.array(float)
            Duration of each ensemble computed from QComp

        Returns
        -------
        q_mid_cells: np.array(float)
            Discharge in each bin or depth cell
        """

        # Assign properties from transect object to local variables
        in_transect_idx = transect.in_transect_idx
        trans_select = getattr(transect.depths, transect.depths.selected)
        cell_size = trans_select.depth_cell_size_m

        # Determine is xprod contains edge data and process appropriately
        q_mid_cells = np.multiply(
            xprod[:, in_transect_idx] * cell_size[:, in_transect_idx], delta_t
        )

        return q_mid_cells

    @staticmethod
    def discharge_edge(
        edge_loc, transect, top_method=None, bot_method=None, exponent=None
    ):
        """Computes edge discharge.

        Parameters
        ----------
        edge_loc: str
            Edge location (left or right)
        transect: TransectData
            Object of TransectData
        top_method: str
            Top extrapolation method
        bot_method: str
            Bottom extrapolation method
        exponent: float
            Exponent

        Returns
        -------
        edge_q: float
            Computed edge discharge
        edge_idx: list
            List of valid edge ensembles
        """

        # Determine what ensembles to use for edge computation.
        # The method of determining varies by manufacturer
        edge_idx = QComp.edge_ensembles(edge_loc, transect)

        # Average depth for the edge ensembles
        trans_select = getattr(transect.depths, transect.depths.selected)
        depth = trans_select.depth_processed_m[edge_idx]
        depth_avg = np.nanmean(depth)

        # Edge distance
        edge_selected = getattr(transect.edges, edge_loc)
        edge_dist = edge_selected.distance_m

        # Compute edge velocity and sign
        edge_vel_sign, edge_vel_mag = QComp.edge_velocity(
            edge_idx, transect, top_method, bot_method, exponent
        )

        # Compute edge coefficient
        coef = QComp.edge_coef(edge_loc, transect)

        # Compute edge discharge
        edge_q = coef * depth_avg * edge_vel_mag * edge_dist * edge_vel_sign
        if np.isnan(edge_q):
            edge_q = 0

        return edge_q, edge_idx

    @staticmethod
    def edge_ensembles(edge_loc, transect):
        """This function computes the starting and ending ensemble numbers
        for an edge.

         This method uses either the method used by TRDI which used the
         specified number of valid ensembles or SonTek
        which uses the specified number of ensembles prior to screening for
        valid data

        Parameters
        ----------
        edge_loc: str
            Edge location (left or right)
        transect: TransectData
            Object of TransectData

        Returns
        -------
        edge_idx: np.array
            Indices of ensembles used to compute edge discharge
        """

        # Assign number of ensembles in edge to local variable
        edge_select = getattr(transect.edges, edge_loc)
        num_edge_ens = int(edge_select.number_ensembles)

        # TRDI method
        if transect.adcp.manufacturer == "TRDI":
            # Determine the indices of the edge ensembles which contain
            # the specified number of valid ensembles noinspection PyTypeChecker
            valid_ens = QComp.valid_edge_ens(transect)
            if num_edge_ens > len(valid_ens):
                num_edge_ens = len(valid_ens)
            if edge_loc.lower() == transect.start_edge.lower():
                edge_idx = np.where(valid_ens)[0][0:num_edge_ens]
            else:
                edge_idx = np.where(valid_ens)[0][-num_edge_ens::]

        # Sontek Method
        else:
            # Determine the indices of the edge ensembles as collected by
            # RiverSurveyor.  There
            # is no check as to whether the ensembles contain valid data
            trans_select = getattr(transect.depths, transect.depths.selected)
            n_ensembles = len(trans_select.depth_processed_m)
            if num_edge_ens > n_ensembles:
                num_edge_ens = n_ensembles
            if edge_loc.lower() == transect.start_edge.lower():
                edge_idx = np.arange(0, num_edge_ens)
            else:
                edge_idx = np.arange(n_ensembles - num_edge_ens, n_ensembles)

        return edge_idx

    @staticmethod
    def edge_velocity(
        edge_idx, transect, top_method=None, bot_method=None, exponent=None
    ):
        """Computes the edge velocity.

        Different methods may be used depending on settings in transect.

        Parameters
        ----------
        edge_idx: np.array
            Indices of ensembles used to compute edge discharge
        transect: TransectData
            Object of TransectData
        top_method: str
            Top extrapolation method
        bot_method: str
            Bottom extrapolation method
        exponent: float
            Exponent

        Returns
        -------
        edge_vel_mag: float
            Magnitude of edge velocity
        edge_vel_sign: int
            Sign of edge velocity (discharge)
        """

        # Set default return
        edge_vel_sign = 1
        edge_vel_mag = 0

        # Check to make sure there is edge data
        if len(edge_idx) > 0:

            # Compute edge velocity using specified method
            # Used by TRDI
            if transect.edges.vel_method == "MeasMag":
                edge_vel_mag, edge_vel_sign = QComp.edge_velocity_trdi(
                    edge_idx, transect
                )

            # Used by Sontek
            elif transect.edges.vel_method == "VectorProf":
                edge_val_mag, edge_vel_sign = QComp.edge_velocity_sontek(
                    edge_idx, transect, top_method, bot_method, exponent
                )

            # USGS proposed method
            elif transect.edges.vel_method == "Profile":
                edge_vel_mag, edge_vel_sign = QComp.edge_velocity_profile(
                    edge_idx, transect
                )

        return edge_vel_sign, edge_vel_mag

    @staticmethod
    def edge_velocity_trdi(edge_idx, transect):
        """Computes edge velocity magnitude and sign using TRDI's method.

         This method uses only the measured data and no extrapolation

        Parameters
        ----------
        edge_idx: np.array
            Indices of ensembles used to compute edge discharge
        transect: TransectData
            Object of TransectData

        Returns
        -------
        edge_vel_mag: float
            Magnitude of edge velocity
        edge_vel_sign: int
            Sign of edge velocity (discharge)
        """

        # Assign water velocity to local variables
        x_vel = transect.w_vel.u_processed_mps[:, edge_idx]
        y_vel = transect.w_vel.v_processed_mps[:, edge_idx]

        # Use only valid data
        valid = np.copy(transect.w_vel.valid_data[0, :, edge_idx].T)
        x_vel[np.logical_not(valid)] = np.nan
        y_vel[np.logical_not(valid)] = np.nan

        # Compute the mean velocity components
        x_vel_avg = np.nanmean(np.nanmean(x_vel, 0))
        y_vel_avg = np.nanmean(np.nanmean(y_vel, 0))

        # Compute magnitude and direction
        edge_dir, edge_vel_mag = cart2pol(x_vel_avg, y_vel_avg)

        # Compute unit vector to help determine sign
        unit_water_x, unit_water_y = pol2cart(edge_dir, 1)
        if transect.start_edge == "Right":
            dir_sign = 1
        else:
            dir_sign = -1

        # Compute unit boat vector to help determine sign
        ens_delta_time = transect.date_time.ens_duration_sec
        in_transect_idx = transect.in_transect_idx
        trans_selected = getattr(transect.boat_vel, transect.boat_vel.selected)
        if trans_selected is not None:
            b_vel_x = trans_selected.u_processed_mps
            b_vel_y = trans_selected.v_processed_mps
        else:
            b_vel_x = np.tile([np.nan], transect.boat_vel.bt_vel.u_processed_mps.shape)
            b_vel_y = np.tile([np.nan], transect.boat_vel.bt_vel.v_processed_mps.shape)

        track_x = np.nancumsum(
            b_vel_x[in_transect_idx] * ens_delta_time[in_transect_idx]
        )
        track_y = np.nancumsum(
            b_vel_y[in_transect_idx] * ens_delta_time[in_transect_idx]
        )
        boat_dir, boat_mag = cart2pol(track_x[-1], track_y[-1])
        unit_track_x, unit_track_y = pol2cart(boat_dir, 1)
        unit_x_prod = (
            unit_water_x * unit_track_y - unit_water_y * unit_track_x
        ) * dir_sign
        edge_vel_sign = np.sign(unit_x_prod)

        return edge_vel_mag, edge_vel_sign

    @staticmethod
    def edge_velocity_sontek(
        edge_idx, transect, top_method=None, bot_method=None, exponent=None
    ):
        """Computes the edge velocity using SonTek's method.

        SonTek's method uses the profile extrapolation to estimate the
        velocities in the unmeasured top and bottom and then projects the velocity
        perpendicular to the course made good.

        Parameters
        ----------
        edge_idx: np.array
            Indices of ensembles used to compute edge discharge
        transect: TransectData
            Object of TransectData
        top_method: str
            Top extrapolation method
        bot_method: str
            Bottom extrapolation method
        exponent: float
            Exponent

        Returns
        -------
        edge_vel_mag: float
            Magnitude of edge velocity
        edge_vel_sign: int
            Sign of edge velocity (discharge)
        """

        if top_method is None:
            top_method = transect.extrap.top_method
            bot_method = transect.extrap.bot_method
            exponent = transect.extrap.exponent

        # Compute boat track excluding the start edge ensembles but
        # including the end edge ensembles. This the way SonTek does this
        # as of version 3.7
        ens_delta_time = transect.date_time.ens_duration_sec
        in_transect_idx = transect.in_transect_idx
        trans_selected = getattr(transect.boat_vel, transect.boat_vel.selected)

        if trans_selected is not None:
            b_vel_x = trans_selected.u_processed_mps
            b_vel_y = trans_selected.v_processed_mps
        else:
            b_vel_x = np.tile([np.nan], transect.boat_vel.u_processed_mps.shape)
            b_vel_y = np.tile([np.nan], transect.boat_vel.v_processed_mps.shape)

        track_x = np.nancumsum(
            b_vel_x[in_transect_idx] * ens_delta_time[in_transect_idx]
        )
        track_y = np.nancumsum(
            b_vel_y[in_transect_idx] * ens_delta_time[in_transect_idx]
        )

        # Compute the unit vector for the boat track
        boat_dir, boat_mag = cart2pol(track_x[-1], track_y[-1])
        unit_track_x, unit_track_y = pol2cart(boat_dir, 1)

        # Assign water velocity to local variables
        x_vel = transect.w_vel.u_processed_mps[:, edge_idx]
        y_vel = transect.w_vel.v_processed_mps[:, edge_idx]
        valid_vel_ens = np.nansum(transect.w_vel.valid_data[0, :, edge_idx])

        # Filter edge data
        # According to SonTek the RSL code does recognize that edge samples
        # can vary in their cell size.  It deals with this issue by
        # remembering the cell size and cell start for the first edge sample.
        # Any subsequent edge sample is included in the average only if it
        # has the same cell size and cell start as the first sample.
        transect_depths_select = getattr(transect.depths, transect.depths.selected)
        cell_size = transect_depths_select.depth_cell_size_m[:, edge_idx]
        cell_depth = transect_depths_select.depth_cell_depth_m[:, edge_idx]

        # Find first valid edge ensemble
        idx = np.where(valid_vel_ens > 0)[0]
        if len(idx) > 0:
            idx_first_valid_ensemble = idx[0]
            ref_cell_size = cell_size[0, idx_first_valid_ensemble]
            ref_cell_depth = cell_depth[0, idx_first_valid_ensemble]
            valid = np.tile(True, edge_idx.shape)
            valid[np.not_equal(cell_size[0, :], ref_cell_size)] = False
            valid[np.not_equal(cell_depth[0, :], ref_cell_depth)] = False

            # Compute profile components
            x_profile = np.nanmean(x_vel[:, valid], 1)
            y_profile = np.nanmean(y_vel[:, valid], 1)

            # Find first valid cell in profile
            idx = np.where(np.logical_not(np.isnan(x_profile)))[0]
            if len(idx) > 0:
                idx_first_valid_cell = idx[0]

                # Compute cell size and depth for mean profile
                cell_size[np.isnan(x_vel)] = np.nan
                cell_size[:, np.logical_not(valid)] = np.nan
                cell_size_edge = np.nanmean(cell_size, 1)
                cell_depth[np.isnan(x_vel)] = np.nan
                cell_depth[:, np.logical_not(valid)] = np.nan
                cell_depth_edge = np.nanmean(cell_size, 1)

                # SonTek cuts off the mean profile based on the side lobe
                # cutoff of the mean of the shallowest beams in
                # the edge ensembles.

                # Determine valid original beam and cell depths
                depth_bt_beam_orig = transect.depths.bt_depths.depth_orig_m[:, edge_idx]
                depth_bt_beam_orig[:, np.logical_not(valid)] = np.nan
                draft_bt_beam_orig = transect.depths.bt_depths.draft_orig_m
                depth_cell_depth_orig = (
                    transect.depths.bt_depths.depth_cell_depth_orig_m[:, edge_idx]
                )
                depth_cell_depth_orig[:, np.logical_not(valid)] = np.nan

                # Compute minimum mean depth
                min_raw_depths = np.nanmin(depth_bt_beam_orig)
                min_depth = np.nanmin(min_raw_depths)
                min_depth = min_depth - draft_bt_beam_orig

                # Compute last valid cell by computing the side lobe cutoff
                # based on the mean of the minimum beam depths
                # of the valid edge ensembles
                if transect.w_vel.sl_cutoff_type == "Percent":
                    sl_depth = min_depth - (
                        (transect.w_vel.sl_cutoff_percent / 100.0) * min_depth
                    )
                else:
                    sl_depth = (
                        min_depth
                        - ((transect.w_vel.sl_cutoff_percent / 100.0) * min_depth)
                        - (transect.w_vel.sl_cutoff_number * cell_size[0, 0])
                    )

                # Adjust side lobe depth for draft
                sl_depth = sl_depth + draft_bt_beam_orig
                above_sl = cell_depth < (sl_depth + np.nanmax(cell_size))
                above_sl_profile = np.nansum(above_sl, 1)
                # TODO this line doesn't make sense to me
                valid_idx = np.logical_and(
                    np.less(above_sl_profile, np.nanmax(above_sl_profile) + 1),
                    np.greater(above_sl_profile, 0),
                )

                # Compute the number of cells above the side lobe cutoff
                # remaining_depth = sl_depth - cell_depth_edge[
                # idx_first_valid_cell]
                idx = np.where(np.logical_not(np.isnan(cell_size)))[0]
                # TODO this is not consistent with Matlab code
                n_cells = 0
                if len(idx) > 0:
                    n_cells = idx
                    n_cells[n_cells > 0] = 0

                # Determine index of bottom most valid cells
                idx_last_valid_cell = idx_first_valid_cell + n_cells
                # TODO need to work and test this logic.
                if np.greater(idx_last_valid_cell, len(x_profile)):
                    x_profile[not valid_idx] = np.nan
                    y_profile[not valid_idx] = np.nan
                else:
                    idx_last_valid_cell = np.where(
                        np.logical_not(np.isnan(x_profile[:idx_last_valid_cell]))
                    )[0][0]
                    # Mark the cells in the profile below the sidelobe invalid
                    x_profile[(idx_last_valid_cell + 1) :] = np.nan
                    y_profile[(idx_last_valid_cell + 1) :] = np.nan

                # Find the top most 3 valid cells
                idx_first_3_valid_cells = np.where(np.logical_not(np.isnan(x_profile)))[
                    0
                ][:3]

                # Compute the mean measured velocity components for the edge
                # profile
                x_profile_mean = np.nanmean(x_profile)
                y_profile_mean = np.nanmean(y_profile)

                # Compute average depth of edge
                depth_ens = transect_depths_select.depth_processed_m(edge_idx)
                depth_ens[not valid] = np.nan
                depth_avg = np.nanmean(depth_ens)

                # Determine top, mid, bottom range for the profile
                top_rng_edge = (
                    cell_depth_edge[idx_first_valid_cell] - 0.5 * ref_cell_size
                )
                if idx_last_valid_cell > len(x_profile):
                    mid_rng_edge = np.nansum(cell_size_edge[valid_idx])
                else:
                    mid_rng_edge = np.nansum(
                        cell_size_edge[idx_first_valid_cell : idx_last_valid_cell + 1]
                    )

                # Compute z
                z_edge = depth_avg - cell_depth_edge
                z_edge[idx_last_valid_cell + 1 :] = np.nan
                z_edge[z_edge > 0] = np.nan
                idx_last_valid_cell = np.where(np.logical_not(np.isnan(z_edge)))[0][-1]
                bot_rng_edge = (
                    depth_avg
                    - cell_depth_edge[idx_last_valid_cell]
                    - 0.5 * cell_size_edge[idx_last_valid_cell]
                )

                # Compute the top extrapolation for x-component
                top_vel_x = QComp.discharge_top(
                    top_method=top_method,
                    exponent=exponent,
                    idx_top=idx_first_valid_cell,
                    idx_top_3=idx_first_3_valid_cells,
                    top_rng=top_rng_edge,
                    component=x_profile,
                    cell_size=cell_size_edge,
                    cell_depth=cell_depth_edge,
                    depth_ens=depth_avg,
                    delta_t=1,
                    z=z_edge,
                )
                top_vel_x = top_vel_x / top_rng_edge

                # Compute the bottom extrapolation for x-component
                bot_vel_x = QComp.discharge_bot(
                    bot_method=bot_method,
                    exponent=exponent,
                    idx_bot=idx_last_valid_cell,
                    bot_rng=bot_rng_edge,
                    component=x_profile,
                    cell_size=cell_size_edge,
                    cell_depth=cell_depth_edge,
                    depth_ens=depth_avg,
                    delta_t=1,
                    z=z_edge,
                )
                bot_vel_x = bot_vel_x / bot_rng_edge

                # Compute the top extrapolation for the y-component
                top_vel_y = QComp.discharge_top(
                    top_method=top_method,
                    exponent=exponent,
                    idx_top=idx_first_valid_cell,
                    idx_top_3=idx_first_3_valid_cells,
                    top_rng=top_rng_edge,
                    component=y_profile,
                    cell_size=cell_size_edge,
                    cell_depth=cell_depth_edge,
                    depth_ens=depth_avg,
                    delta_t=1,
                    z=z_edge,
                )
                top_vel_y = top_vel_y / top_rng_edge

                # Compute the bottom extrapolation for y-component
                bot_vel_y = QComp.discharge_bot(
                    bot_method=bot_method,
                    exponent=exponent,
                    idx_bot=idx_last_valid_cell,
                    bot_rng=bot_rng_edge,
                    component=y_profile,
                    cell_size=cell_size_edge,
                    cell_depth=cell_depth_edge,
                    depth_ens=depth_avg,
                    delta_t=1,
                    z=z_edge,
                )
                bot_vel_y = bot_vel_y / bot_rng_edge

                # Compute edge velocity vector including extrapolated
                # velocities
                v_edge_x = (
                    (top_vel_x * top_rng_edge)
                    + (x_profile_mean * mid_rng_edge)
                    + (bot_vel_x * bot_rng_edge) / depth_avg
                )
                v_edge_y = (
                    (top_vel_y * top_rng_edge)
                    + (y_profile_mean * mid_rng_edge)
                    + (bot_vel_y * bot_rng_edge) / depth_avg
                )

                # Compute magnitude of edge velocity perpendicular to course
                # made good
                edge_vel_mag = (v_edge_x * -1 * unit_track_y) + (
                    v_edge_y * unit_track_x
                )

                # Determine edge sign
                if transect.start_edge == "Right":
                    edge_vel_sign = -1
                else:
                    edge_vel_sign = 1
            else:
                edge_vel_mag = 0
                edge_vel_sign = 1
        else:
            edge_vel_mag = 0
            edge_vel_sign = 1

        return edge_vel_mag, edge_vel_sign

    @staticmethod
    def edge_velocity_profile(edge_idx, transect):
        """Compute edge velocity magnitude using the mean velocity of each
        ensemble.

        The mean velocity of each ensemble is computed by first
        computing the mean direction of the velocities in the ensemble,
        then projecting the velocity in each cell in that direction and
        fitting the 1/6th power curve to the projected profile. The mean
        velocity magnitude from each ensemble is then averaged.

        The sign of the velocity magnitude is computed using the same
        approach used in WinRiver II. The cross product of the unit
        vector of the ship track and the unit vector of the edge water
        samples computed from the mean u and v velocities is used to
        determine the sign of the velocity magnitude.

        Parameters
        ----------
        edge_idx: np.array
            Indices of ensembles used to compute edge discharge
        transect: TransectData
            Object of TransectData

        Returns
        -------
        edge_vel_mag: float
            Magnitude of edge velocity
        edge_vel_sign: int
            Sign of edge velocity (discharge)"""

        # Assign water velocity to local variables
        x_vel = transect.w_vel.u_processed_mps[:, edge_idx]
        y_vel = transect.w_vel.v_processed_mps[:, edge_idx]

        # Use only valid data
        valid = transect.w_vel.valid_data[0, :, edge_idx].astype(int)
        valid[valid == 0] = np.nan
        x_vel = x_vel * valid
        y_vel = y_vel * valid

        # Initialize local variables
        n_ensembles = len(edge_idx)
        vel_ensembles = np.tile(np.nan, n_ensembles)
        u = np.tile(np.nan, n_ensembles)
        v = np.tile(np.nan, n_ensembles)
        v_unit = np.array([np.nan, np.nan])

        # Process each ensemble
        for n in range(n_ensembles):

            # Use ensembles that have valid data
            selected_ensemble = edge_idx[n]
            valid_ensemble = np.nansum(np.isnan(x_vel[:, n]))

            if valid_ensemble > 0:

                # Setup variables
                v_x = x_vel[:, n]
                v_y = y_vel[:, n]
                depth_cell_size = transect.depths.bt_depths.depth_cell_size_m[
                    :, selected_ensemble
                ]
                depth_cell_depth = transect.depths.bt_depths.depth_cell_depth_m[
                    :, selected_ensemble
                ]
                depth = transect.depths.bt_depths.depth_processed_m[
                    :, selected_ensemble
                ]
                depth_cell_size[np.isnan(v_x)] = np.nan
                depth_cell_depth[np.isnan(v_x)] = np.nan

                # Compute projected velocity profile for an ensemble
                v_x_avg = np.nansum(v_x * depth_cell_size) / np.nansum(depth_cell_size)
                v_y_avg = np.nansum(v_y * depth_cell_size) / np.nansum(depth_cell_size)
                ens_dir, _ = cart2pol(v_x_avg, v_y_avg)
                v_unit[0], v_unit[1] = pol2cart(ens_dir, 1)
                v_projected_mag = np.dot(
                    np.hstack([v_x, v_y]), np.tile(v_unit, v_x.shape)
                )

                # Compute z value for each cell
                z = depth - depth_cell_depth
                z[np.isnan(v_projected_mag)] = np.nan

                # Compute coefficient for 1/6th power curve
                b = 1.0 / 6.0
                a = (b + 1) * (
                    np.nansum((v_projected_mag * depth_cell_size))
                    / (
                        np.nansum(
                            ((z + 0.5 * depth_cell_size) ** (b + 1))
                            - ((z - 0.5 * depth_cell_size) ** (b + 1))
                        )
                    )
                )

                # Compute mean water speed by integrating power curve
                vel_ensembles[n] = ((a / (b + 1)) * (depth ** (b + 1))) / depth

                # Compute the mean velocity components from the mean water
                # speed and direction
                u[n], v[n] = pol2cart(ens_dir, vel_ensembles)

            else:

                # No valid data in ensemble
                vel_ensembles[n] = np.nan
                u[n] = np.nan
                v[n] = np.nan

        # Compute the mean velocity components of the edge velocity as the
        # mean of the mean ensemble components
        u_avg = np.nanmean(u)
        v_avg = np.nanmean(v)

        # Compute the dge velocity magnitude
        edge_vel_dir, edge_vel_mag = cart2pol(u_avg, v_avg)

        # TODO this is the same as for TRDI need to put in separate method
        # Compute unit vector to help determine sign
        unit_water_x, unit_water_y = pol2cart(edge_vel_dir, 1)

        # Account for direction of boat travel
        if transect.start_edge == "Right":
            dir_sign = 1
        else:
            dir_sign = -1

        # Compute unit boat vector to help determine sign
        ens_delta_time = transect.date_time.ens_duration_sec
        in_transect_idx = transect.in_transect_idx
        trans_selected = getattr(transect.boat_vel, transect.boat_vel.selected)
        if trans_selected is not None:
            b_vel_x = trans_selected.u_proccesed_mps
            b_vel_y = trans_selected.v_processed_mps
        else:
            b_vel_x = np.tile([np.nan], transect.boat_vel.u_processed_mps.shape)
            b_vel_y = np.tile([np.nan], transect.boat_vel.v_processed_mps.shape)

        track_x = np.nancumsum(
            b_vel_x[in_transect_idx] * ens_delta_time[in_transect_idx]
        )
        track_y = np.nancumsum(
            b_vel_y[in_transect_idx] * ens_delta_time[in_transect_idx]
        )
        boat_dir, boat_mag = cart2pol(track_x[-1], track_y[-1])
        unit_track_x, unit_track_y = pol2cart(boat_dir, 1)

        # Compute cross product from unit vectors
        unit_x_prod = (
            unit_water_x * unit_track_y - unit_water_y * unit_track_x
        ) * dir_sign

        # Determine sign
        edge_vel_sign = np.sign(unit_x_prod)

        return edge_vel_mag, edge_vel_sign

    @staticmethod
    def edge_coef(edge_loc, transect):
        """Returns the edge coefficient based on the edge settings and
        transect object.

        Parameters
        ----------
        edge_loc: str
            Edge location (left_or right)
        transect: TransectData
            Object of TransectData

        Returns
        -------
        coef: float
            Edge coefficient for accounting for velocity distribution and
            edge shape
        """

        # Process appropriate edge type
        edge_select = getattr(transect.edges, edge_loc)
        if edge_select.type == "Triangular":
            coef = 0.3535

        elif edge_select.type == "Rectangular":
            # Rectangular edge coefficient depends on the rec_edge_method.
            # 'Fixed' is compatible with the method used by TRDI.
            # 'Variable is compatible with the method used by SonTek

            if transect.edges.rec_edge_method == "Fixed":
                # Fixed Method
                coef = 0.91

            else:
                # Variable method
                # Get edge distance
                dist = edge_select.dist_m

                # Get edge ensembles to use
                edge_idx = QComp.edge_ensembles(edge_loc, transect)

                # Compute the mean depth for edge
                trans_select = getattr(transect.depths, transect.depths.selected)
                depth_edge = np.nanmean(trans_select.depth_processed_m[edge_idx])

                # Compute coefficient using equation 34 from Principle of
                # River Discharge Measurement, SonTek, 2003
                coef = (
                    1
                    - (
                        (0.35 / 4)
                        * (depth_edge / dist)
                        * (1 - np.exp(-4 * (dist / depth_edge)))
                    )
                ) / (1 - 0.35 * np.exp(-4 * (dist / depth_edge)))

        elif edge_select.type == "Custom":
            # Custom user supplied coefficient
            coef = edge_select.cust_coef

        else:
            coef = []

        return coef

    @staticmethod
    def loop_correction_factor(top_q, middle_q, bottom_q, trans_data, mb_data, delta_t):
        """Computes the discharge correction factor from loop moving-bed tests

        Parameters
        ----------
        top_q: float
            Top discharge from extrapolation
        middle_q: float
            Computed middle discharge
        bottom_q: float
            Bottom discharge from extrapolation
        trans_data: TransectData
            Object of TransectData
        mb_data: MovingBedTests
            Object of MovingBedTests
        delta_t: np.array(float)
            Duration of each ensemble, computed in QComp

        Returns
        -------
        correction_factor: float
            Correction factor to be applied to the discharge to correct for
            moving-bed effects
        """

        # Assign object properties to local variables
        moving_bed_speed = mb_data.mb_spd_mps
        in_transect_idx = trans_data.in_transect_idx
        cells_above_sl = trans_data.w_vel.cells_above_sl[:, in_transect_idx]
        u = trans_data.w_vel.u_processed_mps[:, in_transect_idx] * cells_above_sl
        v = trans_data.w_vel.v_processed_mps[:, in_transect_idx] * cells_above_sl
        depths_select = getattr(trans_data.depths, trans_data.depths.selected)
        depth_cell_depth = depths_select.depth_cell_depth_m[:, in_transect_idx]
        depth = depths_select.depth_processed_m[in_transect_idx]
        bt_u = trans_data.boat_vel.bt_vel.u_processed_mps[in_transect_idx]
        bt_v = trans_data.boat_vel.bt_vel.v_processed_mps[in_transect_idx]

        # Compute uncorrected discharge excluding the edges
        q_orig = top_q + middle_q + bottom_q

        if q_orig != 0:
            # Compute near-bed velocities
            nb_u, nb_v, unit_nb_u, unit_nb_v = QComp.near_bed_velocity(
                u, v, depth, depth_cell_depth
            )
            nb_speed = np.sqrt(nb_u**2 + nb_v**2)
            nb_u_mean = np.nanmean(nb_u)
            nb_v_mean = np.nanmean(nb_v)
            nb_speed_mean = np.sqrt(nb_u_mean**2 + nb_v_mean**2)
            moving_bed_speed_ens = moving_bed_speed * (nb_speed / nb_speed_mean)
            u_mb = moving_bed_speed_ens * unit_nb_u
            v_mb = moving_bed_speed_ens * unit_nb_v

            # Correct water velocities
            u_adj = u + u_mb
            v_adj = v + v_mb

            bt_u_adj = bt_u + u_mb
            bt_v_adj = bt_v + v_mb

            # Compute corrected cross product
            xprod = QComp.cross_product(transect=trans_data)
            xprod_in = QComp.cross_product(
                w_vel_x=u_adj,
                w_vel_y=v_adj,
                b_vel_x=bt_u_adj,
                b_vel_y=bt_v_adj,
                start_edge=trans_data.start_edge,
            )
            xprod[:, in_transect_idx] = xprod_in

            # Compute corrected discharges
            q_middle_cells = QComp.discharge_middle_cells(
                xprod=xprod, transect=trans_data, delta_t=delta_t
            )
            trans_select = getattr(trans_data.depths, trans_data.depths.selected)
            num_top_method = {"Power": 0, "Constant": 1, "3-Point": 2, None: -1}
            q_top = extrapolate_top(
                xprod,
                trans_data.w_vel.valid_data[0, :, :],
                num_top_method[trans_data.extrap.top_method],
                trans_data.extrap.exponent,
                trans_data.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                -1,
                0.1667,
            )
            num_bot_method = {"Power": 0, "No Slip": 1, None: -1}
            q_bot = extrapolate_bot(
                xprod,
                trans_data.w_vel.valid_data[0, :, :],
                num_bot_method[trans_data.extrap.bot_method],
                trans_data.extrap.exponent,
                trans_data.in_transect_idx,
                trans_select.depth_cell_size_m,
                trans_select.depth_cell_depth_m,
                trans_select.depth_processed_m,
                delta_t,
                -1,
                0.1667,
            )
            q_adj = (
                np.nansum(np.nansum(q_middle_cells))
                + np.nansum(q_top)
                + np.nansum(q_bot)
            )

            # Compute correction factor
            correction_factor = q_adj / q_orig
        else:
            correction_factor = 1.0

        return correction_factor

    @staticmethod
    def stationary_correction_factor(
        top_q, middle_q, bottom_q, trans_data, mb_data, delta_t
    ):
        """Computes the discharge correction factor from stationary
        moving-bed tests.

        Parameters
        ----------
        top_q: float
            Top discharge from extrapolation
        middle_q: float
            Computed middle discharge
        bottom_q: float
            Bottom discharge from extrapolation
        trans_data: TransectData
            Object of TransectData
        mb_data: MovingBedTests
            Object of MovingBedTests
        delta_t: np.array(float)
            Duration of each ensemble, computed in QComp

        Returns
        -------
        correction_factor: float
            Correction factor to be applied to the discharge to correct for
            moving-bed effects
        """

        n_mb_tests = len(mb_data)
        n_sta_tests = 0
        mb_speed = np.array([0])
        near_bed_speed = np.array([0])
        for n in range(n_mb_tests):
            if (mb_data[n].type == "Stationary") and mb_data[n].use_2_correct:
                n_sta_tests += 1
                mb_speed = np.append(mb_speed, mb_data[n].mb_spd_mps)
                near_bed_speed = np.append(
                    near_bed_speed, mb_data[n].near_bed_speed_mps
                )

        if n_sta_tests > 0:

            # Compute linear regression coefficient forcing through zero to
            # relate near-bed velocity to moving-bed velocity
            x = np.vstack(near_bed_speed)
            corr_coef = np.linalg.lstsq(x, mb_speed, rcond=None)[0]

            # Assing object properties to local variables
            in_transect_idx = trans_data.in_transect_idx
            cells_above_sl = trans_data.w_vel.cells_above_sl[:, in_transect_idx]
            u = trans_data.w_vel.u_processed_mps[:, in_transect_idx] * cells_above_sl
            v = trans_data.w_vel.v_processed_mps[:, in_transect_idx] * cells_above_sl
            depths_select = getattr(trans_data.depths, trans_data.depths.selected)
            depth_cell_depth = depths_select.depth_cell_depth_m[:, in_transect_idx]
            depth = depths_select.depth_processed_m[in_transect_idx]
            bt_u = trans_data.boat_vel.bt_vel.u_processed_mps[in_transect_idx]
            bt_v = trans_data.boat_vel.bt_vel.v_processed_mps[in_transect_idx]

            # Compute near-bed velocities
            nb_u, nb_v, unit_nb_u, unit_nb_v = QComp.near_bed_velocity(
                u, v, depth, depth_cell_depth
            )

            # Compute moving-bed vector for each ensemble
            mb_u = corr_coef * nb_u
            mb_v = corr_coef * nb_v

            # Compute adjusted water and boat velocities
            u_adj = u + mb_u
            v_adj = v + mb_v
            bt_u_adj = bt_u + mb_u
            bt_v_adj = bt_v + mb_v

            # Compute uncorrected discharge excluding the edges
            q_orig = top_q + middle_q + bottom_q
            if q_orig != 0:
                # Compute corrected cross product
                xprod = QComp.cross_product(transect=trans_data)
                xprod_in = QComp.cross_product(
                    w_vel_x=u_adj,
                    w_vel_y=v_adj,
                    b_vel_x=bt_u_adj,
                    b_vel_y=bt_v_adj,
                    start_edge=trans_data.start_edge,
                )
                xprod[:, in_transect_idx] = xprod_in

                # Compute corrected discharges
                q_middle_cells = QComp.discharge_middle_cells(
                    xprod=xprod, transect=trans_data, delta_t=delta_t
                )
                trans_select = getattr(trans_data.depths, trans_data.depths.selected)
                num_top_method = {"Power": 0, "Constant": 1, "3-Point": 2, None: -1}
                q_top = extrapolate_top(
                    xprod,
                    trans_data.w_vel.valid_data[0, :, :],
                    num_top_method[trans_data.extrap.top_method],
                    trans_data.extrap.exponent,
                    trans_data.in_transect_idx,
                    trans_select.depth_cell_size_m,
                    trans_select.depth_cell_depth_m,
                    trans_select.depth_processed_m,
                    delta_t,
                    -1,
                    0.1667,
                )
                num_bot_method = {"Power": 0, "No Slip": 1, None: -1}
                q_bot = extrapolate_bot(
                    xprod,
                    trans_data.w_vel.valid_data[0, :, :],
                    num_bot_method[trans_data.extrap.bot_method],
                    trans_data.extrap.exponent,
                    trans_data.in_transect_idx,
                    trans_select.depth_cell_size_m,
                    trans_select.depth_cell_depth_m,
                    trans_select.depth_processed_m,
                    delta_t,
                    -1,
                    0.1667,
                )
                q_adj = (
                    np.nansum(np.nansum(q_middle_cells))
                    + np.nansum(q_top)
                    + np.nansum(q_bot)
                )

                # Compute correction factor
                correction_factor = q_adj / q_orig
            else:
                correction_factor = 1.0

            return correction_factor

    @staticmethod
    def near_bed_velocity(u, v, depth, bin_depth):
        """Compute near bed velocities.

        Parameters
        ----------
        u: np.array(float)
            Velocity in the x-direction, in m/s
        v: np.array(float)
            Velocity in the y-direction, in m/s
        depth: np.array(float)
            Depth for each ensemble, in m
        bin_depth: np.array(float)
            Depth cell depth for each depth cell, in m

        Returns
        -------
        nb_u: np.array(float)
            Near-bed velocity in the x-direction, in m/s.
        nb_v: np.array(float)
            Near-bed velocity in the y-direction, in m/s.
        unit_nbu: np.array(float)
            Unit vector component of near-bed velocity in x-direction.
        unit_nbv: np.array(float)
            Unit vector component of near-bed velocity in y-direction.
        """

        # Compute z near bed as 10% of depth
        z_near_bed = depth * 0.1

        # Begin computing near-bed velocities
        n_ensembles = u.shape[1]
        nb_u = np.tile([np.nan], n_ensembles)
        nb_v = np.tile([np.nan], n_ensembles)
        unit_nbu = np.tile([np.nan], n_ensembles)
        unit_nbv = np.tile([np.nan], n_ensembles)
        z_depth = np.tile([np.nan], n_ensembles)
        u_mean = np.tile([np.nan], n_ensembles)
        v_mean = np.tile([np.nan], n_ensembles)
        speed_near_bed = np.tile([np.nan], n_ensembles)
        for n in range(n_ensembles):
            idx = np.where(np.logical_not(np.isnan(u[:, n])))[0]
            if len(idx) > 0:
                idx = idx[-2:]

                # Compute near-bed velocity
                z_depth[n] = depth[n] - np.nanmean(bin_depth[idx, n], 0)
                u_mean[n] = np.nanmean(u[idx, n], 0)
                v_mean[n] = np.nanmean(v[idx, n], 0)
                nb_u[n] = (u_mean[n] / z_depth[n] ** (1.0 / 6.0)) * (
                    z_near_bed[n] ** (1.0 / 6.0)
                )
                nb_v[n] = (v_mean[n] / z_depth[n] ** (1.0 / 6.0)) * (
                    z_near_bed[n] ** (1.0 / 6.0)
                )
                speed_near_bed[n] = np.sqrt(nb_u[n] ** 2 + nb_v[n] ** 2)
                unit_nbu[n] = nb_u[n] / speed_near_bed[n]
                unit_nbv[n] = nb_v[n] / speed_near_bed[n]

        return nb_u, nb_v, unit_nbu, unit_nbv

    @staticmethod
    def valid_edge_ens(trans_data):
        """Determines which ensembles contain sufficient valid data to allow
        computation of discharge.

        Allows interpolated depth and boat velocity but requires valid
        non-interpolated water velocity.

        Parameters
        ----------
        trans_data: TransectData
            Object of TransectData

        Returns
        -------
        validEns: np.array(bool)
            Boolean vector
        """

        # Get index of ensembles in moving-boat portion of transect
        in_transect_idx = trans_data.in_transect_idx

        # Get selected navigation reference

        boat_vel_selected = getattr(trans_data.boat_vel, trans_data.boat_vel.selected)

        # Depending on type of interpolation determine the valid navigation
        # ensembles
        if boat_vel_selected is not None and len(boat_vel_selected.u_processed_mps) > 0:
            if boat_vel_selected.interpolate == "TRDI":
                nav_valid = boat_vel_selected.valid_data[0, in_transect_idx]
            else:
                nav_valid = np.logical_not(
                    np.isnan(boat_vel_selected.u_processed_mps[in_transect_idx])
                )
        else:
            nav_valid = np.tile(False, len(in_transect_idx))

        # Depending on type of interpolation determine the valid water track
        # ensembles
        if len(in_transect_idx) > 1:
            water_valid = np.any(trans_data.w_vel.valid_data[0, :, in_transect_idx], 1)
        else:
            water_valid = np.any(trans_data.w_vel.valid_data[0, :, in_transect_idx])

        # Determine the ensembles with valid depth
        depths_select = getattr(trans_data.depths, trans_data.depths.selected)
        if depths_select is not None:
            depth_valid = np.logical_not(
                np.isnan(depths_select.depth_processed_m[in_transect_idx])
            )

            # Determine the ensembles with valid depth, navigation,
            # and water data
            valid_ens = np.all(np.vstack((nav_valid, water_valid, depth_valid)), 0)
        else:
            valid_ens = []

        return valid_ens

    @staticmethod
    def discharge_interpolated(q_top_ens, q_mid_cells, q_bot_ens, transect):
        """Determines the amount of discharge in interpolated cells and
        ensembles.

        Parameters
        ----------
        q_top_ens: np.array(float)
            Top extrapolated discharge in each ensemble
        q_mid_cells: np.array(float)
            Middle of measured discharge in each ensemble
        q_bot_ens: np.array(flot)
            Bottom extrapolated discharge in each ensemble
        transect: TransectData
            Object of TransectData

        Returns
        -------
        q_int_cells: float
            Discharge in interpolated cells
        q_int_ens: float
            Discharge in interpolated ensembles
        """
        valid_ens, valid_wt = TransectData.raw_valid_data(transect)

        # Compute interpolated cell discharge
        q_int_cells = np.nansum(np.nansum(q_mid_cells[np.logical_not(valid_wt)]))

        #  Method to compute invalid ensemble discharge depends on if
        # navigation data are interpolated (QRev) or if expanded delta
        # time is used to compute discharge for invalid ensembles(TRDI)
        if transect.boat_vel.bt_vel.interpolate == "None":
            # Compute discharge in invalid ensembles for expanded delta time
            # situation
            # Find index of invalid ensembles followed by a valid ensemble
            idx_next_valid = np.where(np.diff(np.hstack((-2, valid_ens))) == 1)[0]
            if len(idx_next_valid) == 0:
                q_int_ens = 0
            else:
                # Increase index to reference valid ensembles
                idx_next_valid += 1

                # Sum discharge in valid ensembles following invalid ensemble
                q_int_ens = (
                    np.nansum(q_mid_cells[:, idx_next_valid])
                    + q_bot_ens[idx_next_valid]
                    + q_top_ens[idx_next_valid]
                )

                # Determine number of invalid ensembles preceding valid
                # ensemble
                run_length_false, _ = QComp.compute_run_length(valid_ens)

                # Adjust run_length_false for situation where the transect
                # ends with invalid ensembles
                if len(run_length_false) > len(q_int_ens):
                    run_length_false = run_length_false[:-1]

                # Adjust discharge to remove the discharge that would have
                # been measured in the valid ensemble
                q_int_ens = np.nansum(
                    q_int_ens * (run_length_false / (run_length_false + 1))
                )

        else:
            # Compute discharge in invalid ensembles where all data were
            # interpolated
            q_int_ens = (
                np.nansum(np.nansum(q_mid_cells[:, np.logical_not(valid_ens)]))
                + np.nansum(q_top_ens[np.logical_not(valid_ens)])
                + np.nansum(q_bot_ens[np.logical_not(valid_ens)])
            )

        return q_int_cells, q_int_ens

    @staticmethod
    def compute_run_length(bool_vector):
        """Compute how many false or true consecutive values are in every
        run of true or false in the
        provided boolean vector.

        Parameters
        ----------
        bool_vector: np.array(bool)
           Boolean vector.

        Returns
        -------
        run_length_false: np.array(int)
            Vector with lengths of false runs.
        run_length_true: np.array(int)
            Vector with lengths of true runs.
        """

        # Compute the indices of where changes occur
        valid_run = np.where(np.diff(np.hstack((-1, bool_vector, -1))) != 0)[0]
        # Determine length of each run
        run_length = np.diff(valid_run)

        # Determine length of runs
        if bool_vector[0]:
            true_start = 0
            false_start = 1
        else:
            true_start = 1
            false_start = 0
        run_length_false = run_length[bool_vector[false_start] :: 2]
        run_length_true = run_length[bool_vector[true_start] :: 2]

        return run_length_false, run_length_true

    # ========================================================================
    # The methods below are not being used in the discharge computations.
    # The methods for extrapolating the top and bottom discharge have been
    # moved to separate files and compiled using Numba AOT. The methods below
    # are included here forhistorical purposes and may provide an easier approach
    # to adding new features/algorithms prior to recoding them in a manner that
    # can be compiled using Numba AOT.
    # ========================================================================

    @staticmethod
    def extrapolate_top(
        xprod,
        w_valid_data,
        transect_top_method,
        transect_exponent,
        in_transect_idx,
        depth_cell_size_m,
        depth_cell_depth_m,
        depth_processed_m,
        delta_t,
        top_method=-1,
        exponent=0.1667,
    ):
        """Computes the extrapolated top discharge.

        Parameters
        ----------
        xprod: np.array(float)
            Cross product computed from the cross product method
        w_valid_data: np.array(bool)
            Valid water data
        transect_top_method: int
            Stored top method (power = 0, constant = 1, 3-point = 2)
        transect_exponent: float
            Exponent for power fit
        in_transect_idx: np.array(int)
            Indices of ensembles in transect to be used for discharge
        depth_cell_size_m: np.array(float)
            Size of each depth cell in m
        depth_cell_depth_m: np.array(float)
            Depth of each depth cell in m
        depth_processed_m: np.array(float)
            Depth for each ensemble in m
        delta_t: np.array(float)
            Duration of each ensemble computed from QComp
        top_method: int
            Specifies method to use for top extrapolation
        exponent: float
            Exponent to use for power extrapolation

        Returns
        -------
        q_top: np.array(float)
            Top extrapolated discharge for each ensemble
        """

        if top_method == -1:
            top_method = transect_top_method
            exponent = transect_exponent

        # Compute top variables
        idx_top, idx_top3, top_rng = QComp.top_variables(
            xprod, w_valid_data, depth_cell_size_m, depth_cell_depth_m
        )
        idx_top = idx_top[in_transect_idx]
        idx_top3 = idx_top3[:, in_transect_idx]
        top_rng = top_rng[in_transect_idx]

        # Get data from transect object
        cell_size = depth_cell_size_m[:, in_transect_idx]
        cell_depth = depth_cell_depth_m[:, in_transect_idx]
        depth_ens = depth_processed_m[in_transect_idx]

        # Compute z
        z = np.subtract(depth_ens, cell_depth)

        # Use only valid data
        valid_data = np.logical_not(np.isnan(xprod[:, in_transect_idx]))
        for row in range(valid_data.shape[0]):
            for col in range(valid_data.shape[1]):
                if valid_data[row, col] == False:
                    z[row, col] = np.nan
                    cell_size[row, col] = np.nan
                    cell_depth[row, col] = np.nan

        # Compute top discharge
        q_top = QComp.discharge_top(
            top_method,
            exponent,
            idx_top,
            idx_top3,
            top_rng,
            xprod[:, in_transect_idx],
            cell_size,
            cell_depth,
            depth_ens,
            delta_t,
            z,
        )

        return q_top

    @staticmethod
    def discharge_top(
        top_method,
        exponent,
        idx_top,
        idx_top_3,
        top_rng,
        component,
        cell_size,
        cell_depth,
        depth_ens,
        delta_t,
        z,
    ):
        """Computes the top extrapolated value of the provided component.

        Parameters
        ----------
        top_method: int
            Top extrapolation method (Power = 0, Constant = 1, 3-Point = 2)
        exponent: float
            Exponent for the power extrapolation method
        idx_top: np.array(int)
            Index to the topmost valid depth cell in each ensemble
        idx_top_3: np.array(int)
            Index to the top 3 valid depth cells in each ensemble
        top_rng: np.array(float)
            Range from the water surface to the top of the topmost cell
        component: np.array(float)
            The variable to be extrapolated (xprod, u-velocity, v-velocity)
        cell_size: np.array(float)
            Array of cell sizes (n cells x n ensembles)
        cell_depth: np.array(float)
            Depth of each cell (n cells x n ensembles)
        depth_ens: np.array(float)
            Bottom depth for each ensemble
        delta_t: np.array(float)
            Duration of each ensemble compute by QComp
        z: np.array(float)
            Relative depth from the bottom of each depth cell computed in
            discharge top method

        Returns
        -------
        top_value: np.array(float)
            total for the specified component integrated over the top range
        """

        # Initialize return
        top_value = np.array([0.0])

        # Top power extrapolation
        if top_method == 0:
            coef = np.repeat(np.nan, int(component.shape[1]))

            # Compute the coefficient for each ensemble
            # Loops are used for Numba compile purposes

            # Loop through ensembles
            for col in range(component.shape[1]):
                # Initialize variables
                numerator = 0.0
                numerator_valid = False
                denominator_valid = False
                denominator = 0.0

                # Loop through depth cells in an ensemble
                for row in range(component.shape[0]):

                    # Compute the numerator
                    numerator_temp = component[row, col] * cell_size[row, col]
                    if np.logical_not(np.isnan(numerator_temp)):
                        numerator_valid = True
                        numerator = numerator + numerator_temp

                    # Compute the denominator
                    denominator_temp = (
                        (z[row, col] + 0.5 * cell_size[row, col]) ** (exponent + 1)
                    ) - ((z[row, col] - 0.5 * cell_size[row, col]) ** (exponent + 1))
                    if np.logical_not(np.isnan(denominator_temp)) and denominator_temp != 0:
                        denominator_valid = True
                        denominator = denominator + denominator_temp

                # If both numerator and denominator are valid compute the coefficient
                if numerator_valid and denominator_valid:
                    coef[col] = (numerator * (1 + exponent)) / denominator

            # Compute the top discharge for each ensemble
            top_value = (
                delta_t
                * (coef / (exponent + 1))
                * (depth_ens ** (exponent + 1) - (depth_ens - top_rng) ** (exponent + 1))
            )

        # Top constant extrapolation
        elif top_method == 1:
            n_ensembles = len(delta_t)
            top_value = np.repeat(np.nan, n_ensembles)
            for j in range(n_ensembles):
                if idx_top[j] >= 0:
                    top_value[j] = delta_t[j] * component[idx_top[j], j] * top_rng[j]

        # Top 3-point extrapolation
        elif top_method == 2:
            # Determine number of bins available in each profile
            valid_data = np.logical_not(np.isnan(component))
            n_bins = np.sum(valid_data, axis=0)
            # Determine number of ensembles
            n_ensembles = len(delta_t)
            # Preallocate qtop vector
            top_value = np.repeat(np.nan, n_ensembles)

            # Loop through ensembles
            for j in range(n_ensembles):

                # Set default to constant
                if (n_bins[j] < 6) and (n_bins[j] > 0) and (idx_top[j] >= 0):
                    top_value[j] = delta_t[j] * component[idx_top[j], j] * top_rng[j]

                # If 6 or more bins use 3-pt at top
                if n_bins[j] > 5:
                    sumd = 0.0
                    sumd2 = 0.0
                    sumq = 0.0
                    sumqd = 0.0

                    # Use loop to sum data from top 3 cells
                    for k in range(3):
                        if np.isnan(cell_depth[idx_top_3[k, j], j]) == False:
                            sumd = sumd + cell_depth[idx_top_3[k, j], j]
                            sumd2 = sumd2 + cell_depth[idx_top_3[k, j], j] ** 2
                            sumq = sumq + component[idx_top_3[k, j], j]
                            sumqd = sumqd + (
                                component[idx_top_3[k, j], j]
                                * cell_depth[idx_top_3[k, j], j]
                            )
                    delta = 3 * sumd2 - sumd**2
                    a = (3 * sumqd - sumq * sumd) / delta
                    b = (sumq * sumd2 - sumqd * sumd) / delta

                    # Compute discharge for 3-pt fit
                    qo = (a * top_rng[j] ** 2) / 2 + b * top_rng[j]
                    top_value[j] = delta_t[j] * qo

        return top_value


    @staticmethod
    def top_variables(xprod, w_valid_data, depth_cell_size_m, depth_cell_depth_m):
        """Computes the index to the top and top three valid cells in each ensemble and
        the range from the water surface to the top of the topmost cell.

        Parameters
        ----------
        xprod: np.array(float)
            Cross product computed from the cross product method
        w_valid_data: np.array(bool)
            Valid water data
        depth_cell_size_m: np.array(float)
            Size of each depth cell in m
        depth_cell_depth_m: np.array(float)
            Depth of each depth cell in m

        Returns
        -------
        idx_top: np.array(int)
            Index to the topmost valid depth cell in each ensemble
        idx_top_3: np.array(int)
            Index to the top 3 valid depth cell in each ensemble
        top_rng: np.array(float)
            Range from the water surface to the top of the topmost cell
        """

        # Get data from transect object
        valid_data1 = np.copy(w_valid_data)
        valid_data2 = np.logical_not(np.isnan(xprod))
        valid_data = np.logical_and(valid_data1, valid_data2)

        # Preallocate variables
        # NOTE: Numba does not support np.tile
        n_ensembles = int(valid_data.shape[1])
        idx_top = np.repeat(-1, int(valid_data.shape[1]))
        idx_top_3 = np.ones((3, int(valid_data.shape[1])), dtype=np.int32)
        idx_top_3[:] = int(-1)
        top_rng = np.repeat(np.nan, n_ensembles)

        # Loop through ensembles
        for n in range(n_ensembles):
            # Identify topmost 1 and 3 valid cells
            idx_temp = np.where(np.logical_not(np.isnan(xprod[:, n])))[0]
            if len(idx_temp) > 0:
                idx_top[n] = idx_temp[0]
                if len(idx_temp) > 2:
                    for k in range(3):
                        idx_top_3[k, n] = idx_temp[k]
                # Compute top range
                top_rng[n] = (
                    depth_cell_depth_m[idx_top[n], n]
                    - 0.5 * depth_cell_size_m[idx_top[n], n]
                )
            else:
                top_rng[n] = 0
                idx_top[n] = 0

        return idx_top, idx_top_3, top_rng

    @staticmethod
    def extrapolate_bot(
            xprod,
            w_valid_data,
            transect_bot_method,
            transect_exponent,
            in_transect_idx,
            depth_cell_size_m,
            depth_cell_depth_m,
            depth_processed_m,
            delta_t,
            bot_method=-1,
            exponent=0.1667,
    ):
        """Computes the extrapolated bottom discharge

        Parameters
        ----------
        xprod: np.array(float)
            Cross product computed from the cross product method
        w_valid_data: np.array(bool)
            Valid water data
        transect_bot_method: int
            Stored bottom method (power = 0, no slip = 1)
        transect_exponent: float
            Exponent for power fit
        in_transect_idx: np.array(int)
            Indices of ensembles in transect to be used for discharge
        depth_cell_size_m: np.array(float)
            Size of each depth cell in m
        depth_cell_depth_m: np.array(float)
            Depth of each depth cell in m
        depth_processed_m: np.array(float)
            Depth for each ensemble in m
        delta_t: np.array(float)
            Duration of each ensemble computed from QComp
        bot_method: int
            Specifies method to use for top extrapolation
        exponent: float
            Exponent to use for power extrapolation

        Returns
        -------
        q_bot: np.array(float)
            Bottom extrapolated discharge for each ensemble
        """

        # Determine extrapolation methods and exponent
        if bot_method == -1:
            bot_method = transect_bot_method
            exponent = transect_exponent

        # Use only data in transect
        w_valid_data = w_valid_data[:, in_transect_idx]
        xprod = xprod[:, in_transect_idx]
        cell_size = depth_cell_size_m[:, in_transect_idx]
        cell_depth = depth_cell_depth_m[:, in_transect_idx]
        depth_ens = depth_processed_m[in_transect_idx]
        delta_t = delta_t[in_transect_idx]

        # Compute bottom variables
        bot_rng = QComp.bot_variables(xprod, w_valid_data, cell_size, cell_depth, depth_ens)

        # Compute z
        z = np.subtract(depth_ens, cell_depth)

        # Use only valid data
        valid_data = np.logical_not(np.isnan(xprod))
        for row in range(valid_data.shape[0]):
            for col in range(valid_data.shape[1]):
                if valid_data[row, col] == False:
                    z[row, col] = np.nan
                    cell_size[row, col] = np.nan
                    cell_depth[row, col] = np.nan

        # Compute bottom discharge
        q_bot = QComp.discharge_bot(bot_method, exponent, bot_rng, xprod, cell_size, cell_depth,
            depth_ens, delta_t, z, )

        return q_bot

    @staticmethod
    def discharge_bot(bot_method, exponent, bot_rng, component, cell_size, cell_depth,
            depth_ens, delta_t, z, ):
        """Computes the bottom extrapolated value of the provided component.

        Parameters
        ----------
        bot_method: int
            Bottom extrapolation method (Power, No Slip)
        exponent: float
            Exponent for power and no slip
        bot_rng: np.array(float)
            Range from the streambed to the bottom of the bottom most cell
        component: np.array(float)
            The variable to be extrapolated
        cell_size: np.array(float)
            Array of cell sizes (n cells x n ensembles)
        cell_depth: np.array(float)
            Depth of each cell (n cells x n ensembles)
        depth_ens: np.array(float)
            Bottom depth for each ensemble
        delta_t: np.array(float)
            Duration of each ensemble computed by QComp
        z: np.array(float)
            Relative depth from the bottom to each depth cell

        Returns
        -------
        bot_value: np.array(float)
            Total for the specified component integrated over the bottom range
            for each ensemble
        """

        # Initialize
        coef = np.repeat(np.nan, int(component.shape[1]))

        # Bottom power extrapolation
        if bot_method == 0:
            # Compute the coefficient for each ensemble
            # Loops are used for Numba compile purposes

            # Loop through ensembles
            for col in range(component.shape[1]):
                numerator = 0.0
                numerator_valid = False
                denominator_valid = False
                denominator = 0.0

                # Loop through depth cells in an ensemble
                for row in range(component.shape[0]):

                    # Compute the numerator
                    numerator_temp = component[row, col] * cell_size[row, col]
                    if np.logical_not(np.isnan(numerator_temp)):
                        numerator_valid = True
                        numerator = numerator + numerator_temp

                    # Compute the denominator
                    denominator_temp = ((z[row, col] + 0.5 * cell_size[row, col]) ** (
                                exponent + 1)) - ((z[row, col] - 0.5 * cell_size[
                        row, col]) ** (exponent + 1))
                    if np.logical_not(
                            np.isnan(denominator_temp)) and denominator_temp != 0:
                        denominator_valid = True
                        denominator = denominator + denominator_temp

                # If both numerator and denominator are valid compute the coefficient
                if numerator_valid and denominator_valid:
                    coef[col] = (numerator * (1 + exponent)) / denominator

        # Bottom no slip extrapolation
        elif bot_method == 1:
            # Valid data in the lower 20% of the water column or
            # the last valid depth cell are used to compute the no slip power fit
            cutoff_depth = 0.8 * depth_ens

            # Loop through the ensembles
            for col in range(cell_depth.shape[1]):
                numerator = 0.0
                denominator = 0.0
                numerator_valid = False
                denominator_valid = False
                cells_below_cutoff = False
                last_cell_depth = np.nan
                last_cell_size = np.nan
                last_z = np.nan
                last_component = np.nan

                # Verify there are valid depth cutoffs
                if np.any(np.logical_not(np.isnan(cutoff_depth))):

                    # Loop through depth cells
                    for row in range(cell_depth.shape[0]):

                        # Identify last valid cell by end of loop
                        if np.logical_not(np.isnan(cell_depth[row, col])):
                            last_cell_depth = cell_depth[row, col]
                            last_cell_size = cell_size[row, col]
                            last_z = z[row, col]
                            last_component = component[row, col]

                            # Use all depth cells below the cutoff (1 per loop)
                            if (cell_depth[row, col] - cutoff_depth[col]) >= 0:
                                cells_below_cutoff = True

                                # Compute numerator
                                numerator_temp = component[row, col] * cell_size[row, col]
                                if np.logical_not(np.isnan(numerator_temp)):
                                    numerator_valid = True
                                    numerator = numerator + numerator_temp

                                    # If numerator computed, compute denominator
                                    denominator_temp = ((z[row, col] + 0.5 * cell_size[
                                        row, col]) ** (exponent + 1)) - ((z[
                                                                              row, col] - 0.5 *
                                                                          cell_size[
                                                                              row, col]) ** (
                                                                                     exponent + 1))
                                    if (np.logical_not(np.isnan(
                                        denominator_temp)) and denominator_temp != 0):
                                        denominator_valid = True
                                        denominator = denominator + denominator_temp

                    # If there are not cells below the cutoff, use the last valid depth cell
                    if np.logical_not(cells_below_cutoff):
                        if np.logical_not(np.isnan(last_cell_depth)):
                            # Compute numerator
                            numerator_temp = last_component * last_cell_size
                            if np.logical_not(np.isnan(numerator_temp)):
                                numerator_valid = True
                                numerator = numerator + numerator_temp

                                # If numerator computed, compute denominator
                                denominator_temp = ((last_z + 0.5 * last_cell_size) ** (
                                            exponent + 1)) - ((
                                                                          last_z - 0.5 * last_cell_size) ** (
                                                                          exponent + 1))
                                if (np.logical_not(np.isnan(
                                    denominator_temp)) and denominator_temp != 0):
                                    denominator_valid = True
                                    denominator = denominator + denominator_temp

                    # If both numerator and denominator are valid compute the coefficient
                    if numerator_valid and denominator_valid:
                        coef[col] = (numerator * (1 + exponent)) / denominator

        # Compute the bottom discharge of each profile
        bot_value = delta_t * (coef / (exponent + 1)) * (bot_rng ** (exponent + 1))

        return bot_value

    @staticmethod
    def bot_variables(x_prod, w_valid_data, cell_size, cell_depth, depth_ens):
        """Computes the index to the bottom most valid cell in each ensemble
        and the range from the bottom to the bottom of the bottom most cell.

        Parameters
        ----------
        x_prod: np.array(float)
            Cross product computed from the cross product method
        w_valid_data: np.array(bool)
            Valid water data
        cell_size: np.array(float)
            Size of each depth cell in m
        cell_depth: np.array(float)
            Depth of each depth cell in m
        depth_ens: np.array(float)
            Processed depth for each ensemble

        Returns
        -------
        idx_bot: np.array(int)
            Index to the bottom most valid depth cell in each ensemble
        bot_rng: np.array(float)
            Range from the streambed to the bottom of the bottom most cell
        """

        # Identify valid data
        valid_data1 = np.copy(w_valid_data)
        valid_data2 = np.logical_not(np.isnan(x_prod))
        valid_data = np.logical_and(valid_data1, valid_data2)

        # Preallocate variables
        n_ensembles = int(valid_data.shape[1])
        bot_rng = np.repeat(np.nan, n_ensembles)

        # Loop through each ensemble
        for n in range(n_ensembles):

            # Identifying bottom most valid cell
            idx_temp = np.where(np.logical_not(np.isnan(x_prod[:, n])))[0]
            if len(idx_temp) > 0:
                idx_bot = idx_temp[-1]
                # Compute bottom range
                bot_rng[n] = (depth_ens[n] - cell_depth[idx_bot, n] - 0.5 * cell_size[
                    idx_bot, n])
            else:
                bot_rng[n] = 0

        return bot_rng

