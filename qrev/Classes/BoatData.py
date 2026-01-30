import copy
import numpy as np
from qrev.MiscLibs.common_functions import (
    cosd,
    sind,
    cart2pol,
    iqr,
    pol2cart,
    nan_less_equal,
    nan_greater_equal,
    nan_greater,
    nan_less,
    rotate_coordinates
)
from qrev.MiscLibs.robust_loess import rloess


class BoatData(object):
    """Class to process and store boat velocity data.

    Attributes
    ----------

    Original data provided to the class
        raw_vel_mps: np.array
            Contains the raw unfiltered velocity data in m/s.

            First index is 1-4 are beams 1,2,3,3 if beam or u,v,w,d if
             otherwise.
        frequency_khz: np.array or float
            Defines ADCP frequency used for velocity Measurement.
        orig_coord_sys: str

            Defines the original raw data velocity Coordinate, "Beam", "Inst",
            "Ship", "Earth".
        nav_ref: str
            Defines the original raw data navigation reference, "None", "BT",
            "GGA" "VTG".
        corr: np.array
            Correlation values for bottom track
        rssi: np.array
            Returned signal strength for bottom track
        corr: np.array
            Correlation values for bottom track
        rssi: np.array
            Returned signal strength for bottom track

    Coordinate transformed data
        coord_sys: str
            Defines the current coordinate system "Beam", "Inst", "Ship",
            "Earth" used to compute u, v, w, and d.
        u_mps: np.array(float)
            Horizontal velocity in x-direction, in m/s.
        v_mps: np.array(float)
            Horizontal velocity in y-direction, in m/s.
        w_mps: np.array(float)
            Vertical velocity (+ up), m/s.
        d_mps: np.array(float)
            Difference in vertical velocities compute from opposing beam
            pairs in m/s.
        num_invalid: float
            Number of ensembles with invalid velocity data.
        bottom_mode: str
            BT mode for TRDI, 'Variable' for SonTek.

    Processed data
        u_processed_mps: np.array(float)
            Horizontal velocity in x-direction filtered and interpolated.
        v_processed_mps: np.array(float)
            Horizontal velocity in y-direction filtered and interpolated.
        processed_source: np.array(object)
            Source of velocity: BT, VTG, GGA, INT.

    Settings variables
        d_filter: str
            Difference velocity filter "Manual", "Off", "Auto".
        d_filter_thresholds: dict
            Threshold for difference velocity filter.
        w_filter: str
            Vertical velocity filter "Manual", "Off", "Auto".
        w_filter_thresholds: dict
            Threshold for vertical velocity filter.
        gps_diff_qual_filter: integer
            Differential correction quality (1,2,4).
        gps_altitude_filter: str
            Change in altitude filter "Auto", "Manual", "Off".
        gps_altitude_filter_change: float
            Threshold from mean for altitude filter.
        gps_HDOP_filter: str
            HDOP filter "Auto", "Manual", "Off".
        gps_HDOP_filter_max: float
            Max acceptable value for HDOP.
        gps_HDOP_filter_change: float
            Maximum change allowed from mean.
        smooth_filter: str
            Setting to use filter based on smoothing function ("On", "Off")
        smooth_speed: np.array(float)
            Smoothed boat speed.
        smooth_upper_limit: np.array(float)
            Smooth function upper limit of window.
        smooth_lower_limit: np.array(float)
            Smooth function lower limit of window.
        interpolate: str
            Type of interpolation: "None", "Linear", "Smooth" etc.
        beam_filter: integer
            Minimum number of beams for valid data, 3 for 3-beam solutions,
            4 for 4-beam.
        valid_data: np.array(bool)
            Logical array of identifying valid and invalid data for each
            filter applied.
                Row 1 [0] - composite
                Row 2 [1] - original
                Row 3 [2] - d_filter of diff_qual
                Row 4 [3] - w_filter or altitude
                Row 5 [4] - smooth_filter
                Row 6 [5] - beam_filter or HDOP
        ping_type: np.array(int)
            Indicates type of ping for each cell: 0-incoherent, 1-coherent,
             2-surface
        d_meas_thresholds: dict
            Dictionary of difference velocity thresholds computed using the
            whole measurement
        w_meas_thresholds: dict
            Dictionary of vertical velocity thresholds computed using the
            whole measurement
        use_measurement_thresholds: bool
            Indicates if the measurement based thresholds should be used
    """

    def __init__(self):
        """Initialize instance variables."""

        # Variables passed to the constructor
        self.raw_vel_mps = None
        self.frequency_khz = None
        self.orig_coord_sys = None
        self.nav_ref = None
        self.corr = np.array([])
        self.rssi = np.array([])
        self.corr = np.array([])
        self.rssi = np.array([])
        self.coord_sys = None
        self.u_mps = None
        self.v_mps = None
        self.w_mps = None
        self.d_mps = None
        self.num_invalid = None
        self.bottom_mode = None

        # Processed data
        self.u_processed_mps = None
        self.v_processed_mps = None
        self.w_processed_mps = None
        self.processed_source = None

        # Filter and interpolation properties
        self.d_filter = None
        self.d_filter_thresholds = {}
        self.w_filter = None
        self.w_filter_thresholds = {}
        self.gps_diff_qual_filter = None
        self.gps_altitude_filter = None
        self.gps_altitude_filter_change = None
        self.gps_HDOP_filter = None
        self.gps_HDOP_filter_max = None
        self.gps_HDOP_filter_change = None
        self.smooth_filter = None
        self.smooth_speed = None
        self.smooth_upper_limit = None
        self.smooth_lower_limit = None
        self.interpolate = None
        self.beam_filter = None
        self.valid_data = None
        self.ping_type = np.array([])

        # Filter settings populated from Measurement.create_filter_composites
        self.d_meas_thresholds = {}
        self.w_meas_thresholds = {}

        self.use_measurement_thresholds = False

    def populate_data(
        self,
        source,
        vel_in,
        freq_in,
        coord_sys_in,
        nav_ref_in,
        beam_filter_in=3,
        bottom_mode_in="Variable",
        corr_in=None,
        rssi_in=None,
        ping_type=None,
    ):
        """Assigns data to instance variables.

        Parameters
        ----------
        source: str
            Manufacturer (TRDI, SonTek)
        vel_in: np.array(float)
            Boat velocity array
        freq_in: np.array(float)
            Acoustic frequency boat velocity
        coord_sys_in: str
            Coordinate system of boat velocity
        nav_ref_in: str
            Source of boat velocity (BT, GGA, VTG)
        beam_filter_in: int
            Minimum number of valid beams for valid data.
        bottom_mode_in: str
            Bottom mode for TRDI ADCP
        corr_in: np.array
            Correlation values for bottom track
        rssi_in: np.array
            Returned signal strength for bottom track
        ping_type: np.array(str)
            Indicates type of ping used for bottom tracking
        """

        # Identify invalid ensembles for SonTek data.
        if source == "SonTek" or source == "rsq":
            vel_in = BoatData.filter_sontek(vel_in)

        # Store input data
        self.raw_vel_mps = vel_in
        self.frequency_khz = freq_in
        self.ping_type = ping_type
        self.coord_sys = coord_sys_in
        self.orig_coord_sys = coord_sys_in
        self.nav_ref = nav_ref_in
        self.beam_filter = beam_filter_in
        self.bottom_mode = bottom_mode_in
        if corr_in is not None:
            self.corr = corr_in
        if rssi_in is not None:
            self.rssi = rssi_in

        if nav_ref_in == "BT":
            # Boat velocities are referenced to ADCP not the streambed and
            # thus must be reversed
            self.u_mps = np.copy(-1 * vel_in[0, :])
            self.v_mps = np.copy(-1 * vel_in[1, :])
            self.w_mps = np.copy(-1 * vel_in[2, :])
            self.d_mps = np.copy(vel_in[3, :])

            # Default filtering applied during initial construction of object
            self.d_filter = "Off"
            self.d_filter_thresholds = {}
            self.w_filter = "Off"
            self.w_filter_thresholds = {}
            self.smooth_filter = "Off"
            self.interpolate = "None"

        else:
            # GPS referenced boat velocity
            self.u_mps = np.copy(vel_in[0, :])
            self.v_mps = np.copy(vel_in[1, :])
            self.w_mps = np.nan
            self.d_mps = np.nan

            # Default filtering
            self.gps_diff_qual_filter = 2
            self.gps_altitude_filter = "Off"
            self.gps_altitude_filter_change = 3
            self.gps_HDOP_filter = "Off"
            self.gps_HDOP_filter_max = 2.5
            self.gps_HDOP_filter_change = 1
            self.smooth_filter = "Off"
            self.interpolate = "None"

        # Assign data to processed property
        self.u_processed_mps = np.copy(self.u_mps)
        self.v_processed_mps = np.copy(self.v_mps)

        # Preallocate arrays
        n_ensembles = vel_in.shape[1]
        self.valid_data = np.tile([True], (6, n_ensembles))
        self.smooth_speed = np.nan
        self.smooth_upper_limit = np.nan
        self.smooth_lower_limit = np.nan

        # Determine number of raw invalid
        # --------------------------------
        # Find invalid raw data
        valid_vel = np.tile([True], self.raw_vel_mps.shape)
        valid_vel[np.isnan(self.raw_vel_mps)] = False

        # Identify invalid ensembles
        if nav_ref_in == "BT":
            self.valid_data[1, np.sum(valid_vel, 0) < 3] = False
        else:
            self.valid_data[1, np.sum(valid_vel, 0) < 2] = False

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))
        self.processed_source = np.array([""] * self.u_mps.shape[0], dtype=object)
        self.processed_source[np.where(self.valid_data[0, :])] = nav_ref_in
        self.processed_source[np.where(np.logical_not(self.valid_data[0, :]))] = "INT"

    def populate_from_qrev_mat(self, mat_data):
        """Populates the object using data from previously saved QRev Matlab
        file.

        Parameters
        ----------
        mat_data: mat_struct
           Matlab data structure obtained from sio.loadmat
        """

        # Variables passed to the constructor

        if type(mat_data.frequency_hz) is np.ndarray:
            self.frequency_khz = mat_data.frequency_hz
        elif np.isnan(mat_data.frequency_hz):
            self.frequency_khz = None
        else:
            self.frequency_khz = np.array([mat_data.frequency_hz])

        if hasattr(mat_data, "ping_type"):
            if type(mat_data.ping_type) is np.ndarray:
                if np.size(mat_data.ping_type):
                    self.ping_type = mat_data.ping_type
                    self.ping_type = np.char.strip(self.ping_type)
                else:
                    self.ping_type = None
        else:
            self.ping_type = None

        self.orig_coord_sys = mat_data.origCoordSys
        self.nav_ref = mat_data.navRef

        # Data requiring manipulation if only 1 ensemble
        if type(mat_data.u_mps) is float:
            self.raw_vel_mps = mat_data.rawVel_mps.reshape(
                mat_data.rawVel_mps.shape[0], 1
            )
            # Coordinate transformed data
            self.coord_sys = np.array([mat_data.coordSys])
            self.u_mps = np.array([mat_data.u_mps])
            self.v_mps = np.array([mat_data.v_mps])
            self.w_mps = np.array([mat_data.w_mps])
            self.d_mps = np.array([mat_data.d_mps])
            if hasattr(mat_data, "corr"):
                self.corr = mat_data.corr.reshape(mat_data.corr.shape[0], 1)
            if hasattr(mat_data, "rssi"):
                self.rssi = mat_data.rssi.reshape(mat_data.rssi.shape[0], 1)

            # Processed data
            self.u_processed_mps = np.array([mat_data.uProcessed_mps])
            self.v_processed_mps = np.array([mat_data.vProcessed_mps])
            self.processed_source = np.array([mat_data.processedSource])
            self.valid_data = np.array([mat_data.validData]).astype(bool)
            if self.valid_data.shape[1] > 1:
                self.valid_data = self.valid_data.reshape(-1, 1)
            self.smooth_speed = np.array([mat_data.smoothSpeed])
            self.smooth_upper_limit = np.array([mat_data.smoothUpperLimit])
            self.smooth_lower_limit = np.array([mat_data.smoothLowerLimit])
        else:
            self.raw_vel_mps = mat_data.rawVel_mps
            # Coordinate transformed data
            self.coord_sys = mat_data.coordSys
            self.u_mps = mat_data.u_mps.astype("float64")
            self.v_mps = mat_data.v_mps.astype("float64")
            try:
                self.w_mps = mat_data.w_mps.astype("float64")
            except AttributeError:
                self.w_mps = np.array(mat_data.w_mps)
            try:
                self.d_mps = mat_data.d_mps.astype("float64")
            except AttributeError:
                self.d_mps = np.array(mat_data.d_mps)

            if hasattr(mat_data, "corr"):
                self.corr = mat_data.corr
            if hasattr(mat_data, "rssi"):
                self.rssi = mat_data.rssi

            # Processed data
            self.u_processed_mps = mat_data.uProcessed_mps
            self.v_processed_mps = mat_data.vProcessed_mps
            self.processed_source = mat_data.processedSource
            self.valid_data = mat_data.validData.astype(bool)
            self.smooth_speed = mat_data.smoothSpeed
            self.smooth_upper_limit = mat_data.smoothUpperLimit
            self.smooth_lower_limit = mat_data.smoothLowerLimit

        self.bottom_mode = mat_data.bottomMode
        self.num_invalid = mat_data.numInvalid
        # Error velocity filter
        if type(mat_data.dFilter) is np.ndarray:
            self.d_filter = None
        else:
            self.d_filter = mat_data.dFilter

        # Error velocity threshold
        if type(mat_data.dFilterThreshold) is np.ndarray:
            self.d_filter_thresholds = {}
        else:
            self.d_filter_thresholds = self.struct_to_dict(mat_data.dFilterThreshold)

        # Vertical velocity filter
        if type(mat_data.wFilter) is np.ndarray:
            self.w_filter = None
        else:
            self.w_filter = self.struct_to_dict(mat_data.wFilter)

        # Vertical velocity threshold
        if type(mat_data.wFilterThreshold) is np.ndarray:
            self.w_filter_thresholds = {}
        else:
            self.w_filter_thresholds = self.struct_to_dict(mat_data.wFilterThreshold)

        # GPS quality filter
        if type(mat_data.gpsDiffQualFilter) is np.ndarray:
            self.gps_diff_qual_filter = None
        else:
            self.gps_diff_qual_filter = mat_data.gpsDiffQualFilter

        # GPS altitude filter
        if type(mat_data.gpsAltitudeFilter) is np.ndarray:
            self.gps_altitude_filter = None
        else:
            self.gps_altitude_filter = mat_data.gpsAltitudeFilter

        # GPS altitude threshold
        if type(mat_data.gpsAltitudeFilterChange) is np.ndarray:
            self.gps_altitude_filter_change = None
        else:
            self.gps_altitude_filter_change = mat_data.gpsAltitudeFilterChange

        # HDOP filter
        if type(mat_data.gpsHDOPFilter) is np.ndarray:
            self.gps_HDOP_filter = None
        else:
            self.gps_HDOP_filter = mat_data.gpsHDOPFilter

        # HDOP max threshold
        if type(mat_data.gpsHDOPFilterMax) is np.ndarray:
            self.gps_HDOP_filter_max = None
        else:
            self.gps_HDOP_filter_max = mat_data.gpsHDOPFilterMax

        # HDOP change threshold
        if type(mat_data.gpsHDOPFilterChange) is np.ndarray:
            self.gps_HDOP_filter_change = None
        else:
            self.gps_HDOP_filter_change = mat_data.gpsHDOPFilterChange

        # Other filters
        self.smooth_filter = mat_data.smoothFilter
        self.interpolate = mat_data.interpolate
        self.beam_filter = mat_data.beamFilter

        # Use measurement for filter
        if hasattr(mat_data, "use_measurement_thresholds"):
            self.use_measurement_thresholds = mat_data.use_measurement_thresholds
            self.d_meas_thresholds = self.struct_to_dict(mat_data.d_meas_thresholds)
            self.w_meas_thresholds = self.struct_to_dict(mat_data.w_meas_thresholds)
        else:
            self.use_measurement_thresholds = False
            self.d_meas_thresholds = {}
            self.w_meas_thresholds = {}

    @staticmethod
    def struct_to_dict(struct):
        """If input is a mat structure it converts it into a dictionary.

        Parameters
        ----------
        struct: mat.struct or other
            Data to be converted

        Returns
        -------
        result: dict or other
            Result of conversion
        """

        try:
            keys = struct._fieldnames
            result = {}
            for key in keys:
                result[key] = struct.__dict__[key]
        except AttributeError:
            result = struct
        return result

    def change_coord_sys(self, new_coord_sys, sensors, adcp):
        """This function allows the coordinate system to be changed.

        Current implementation is only to allow change to a higher order
        coordinate system Beam - Inst - Ship - Earth

        Parameters
        ----------
        new_coord_sys: str
            New coordinate_sys (Beam, Inst, Ship, Earth)
        sensors: Sensors
            Object of Sensors
        adcp: InstrumentData
            Object of InstrumentData
        """

        # Initialize variables
        if type(self.orig_coord_sys) is list or type(self.orig_coord_sys) is np.ndarray:
            orig_coord_sys = self.orig_coord_sys[0].strip()
        else:
            orig_coord_sys = self.orig_coord_sys.strip()
        orig_sys_code = adcp.get_coordinate_system_code(coord_sys=orig_coord_sys)
        new_sys_code = adcp.get_coordinate_system_code(coord_sys=new_coord_sys)

        # Check to ensure the new coordinate system is a higher order
        # than the original system
        if new_sys_code - orig_sys_code > 0:
            h, p, r = sensors.get_hpr()
            n_ens = self.raw_vel_mps.shape[1]

            if orig_coord_sys == "Beam":
                # Transform beam coordinates to new coordinates
                for ii in range(n_ens):
                    transformation_matrix = adcp.get_transformation_matrix(
                        self.frequency_khz[ii]
                    )
                    vel_beams = np.copy(np.squeeze(self.raw_vel_mps[:, ii]))

                    # Adjust beam velocities for 3 beam solution, if necessary
                    idx_3_beam = np.where(np.isnan(vel_beams))
                    if len(idx_3_beam[0]) == 1:
                        adcp.adjust_for_3_beam_solution(
                            transformation_matrix=transformation_matrix,
                            beam_velocities=vel_beams,
                            idx_3_beam=idx_3_beam,
                        )

                    # Compute instrument coordinates
                    inst_coordinates = adcp.compute_inst_coordinates(
                        transformation_matrix=transformation_matrix,
                        beam_velocities=vel_beams,
                    )

                    # Set error velocity to nan for 3-beam solutions
                    if len(idx_3_beam[0]) == 1:
                        inst_coordinates[3] = np.nan

                    # Compute new coordinates
                    (
                        self.u_mps[ii],
                        self.v_mps[ii],
                        self.w_mps[ii],
                        self.d_mps[ii],
                    ) = adcp.transform_instrument_coordinates(
                        manufacturer=adcp.manufacturer,
                        inst_coordinates=inst_coordinates,
                        h=h[ii],
                        p=p[ii],
                        r=r[ii],
                        new_coord_sys=new_coord_sys
                    )

            elif orig_coord_sys == "Inst":
                # Transform instrument coordinates to new coordinates
                for ii in range(n_ens):
                    inst_coordinates = np.copy(np.squeeze(self.raw_vel_mps[:, ii]))

                    # Compute new coordinates
                    (
                        self.u_mps[ii],
                        self.v_mps[ii],
                        self.w_mps[ii],
                        self.d_mps[ii],
                    ) = adcp.transform_instrument_coordinates(
                        manufacturer=adcp.manufacturer,
                        inst_coordinates=inst_coordinates,
                        h=h[ii],
                        p=p[ii],
                        r=r[ii],
                        new_coord_sys=new_coord_sys
                    )

            elif orig_coord_sys == "Ship":
                # Transform ship coordinates
                for ii in range(n_ens):
                    ship_coordinates = np.copy(np.squeeze(self.raw_vel_mps[:, ii]))

                    if new_coord_sys == "Earth":
                        # Generate matrix for earth coordinates
                        hpr_matrix = adcp.create_hpr_matrix(
                            manufacturer=adcp.manufacturer,
                            heading=h[ii],
                            pitch=0,
                            roll=0,
                        )

                        # Compute coordinates
                        (
                            self.u_mps[ii],
                            self.v_mps[ii],
                            self.w_mps[ii],
                            self.d_mps[ii],
                        ) = adcp.compute_new_coordinates(hpr_matrix, ship_coordinates)

            # Convert boat coordinates relative to stable streambed
            self.u_mps = -1 * self.u_mps
            self.v_mps = -1 * self.v_mps
            self.w_mps = -1 * self.w_mps

        elif new_sys_code - orig_sys_code < 0:
            # Transforming to lower order not supported
            self.u_mps = np.nan
            self.v_mps = np.nan
            self.w_mps = np.nan
            self.d_mps = np.nan

        # Assign processed object properties
        self.coord_sys = new_coord_sys
        self.u_processed_mps = np.copy(self.u_mps)
        self.v_processed_mps = np.copy(self.v_mps)
        self.w_processed_mps = np.copy(self.w_mps)

    def change_heading(self, heading_change):
        """Rotates the boat velocities for a change in heading due to a change
        in magnetic variation, heading offset, or heading source.

        Parameters
        ----------
        heading_change: float
            Change in the magnetic variation in degrees
        """

        # Apply change to processed data
        self.u_processed_mps, self.v_processed_mps = rotate_coordinates(
            self.u_processed_mps, self.v_processed_mps, heading_change
        )

        self.u_mps, self.v_mps = rotate_coordinates(
            self.u_mps, self.v_mps, heading_change
        )

    def apply_interpolation(self, transect, interpolation_method=None):
        """Function to apply interpolations to navigation data.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        interpolation_method: str
            Specified interpolation method if different from that in self
        """

        # Reset processed data
        if self.u_mps is not None:
            self.u_processed_mps = np.copy(self.u_mps)
            self.v_processed_mps = np.copy(self.v_mps)
            self.u_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan
            self.v_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan

            # Determine interpolation methods to apply
            if interpolation_method is None:
                interpolation_method = self.interpolate
            else:
                self.interpolate = interpolation_method

            # Apply specified interpolation method

            if interpolation_method == "None":
                # Sets invalid data to nan with no interpolation
                self.interpolate_none()

            elif interpolation_method == "ExpandedT":
                # Set interpolate to none as the interpolation done is in
                # the QComp
                self.interpolate_next()

            elif interpolation_method == "Hold9":
                # Interpolates using SonTek method of holding last valid
                # for up to 9 samples
                self.interpolate_hold_9()

            elif interpolation_method == "HoldLast":
                # Interpolates by holding last valid indefinitely
                self.interpolate_hold_last()

            elif interpolation_method == "Linear":
                # Interpolates using linear interpolation
                self.interpolate_linear(transect)

            elif interpolation_method == "Smooth":
                # Interpolates using smooth interpolation
                self.interpolate_smooth(transect)

            elif interpolation_method == "TRDI":
                # TRDI interpolation is done in discharge.
                # For TRDI the interpolation is done on discharge not on
                # velocities
                self.interpolate_none()

    def apply_composite(self, u_composite, v_composite, composite_source):
        """Stores composite velocities and sources.

        Parameters
        ----------
        u_composite: np.array(float)
            Composite u-velocity component, in m/s
        v_composite: np.array(float)
            Composite v-velocity component, in m/s
        composite_source: np.array()
            Reference used for each ensemble velocity.
        """

        self.u_processed_mps = u_composite
        self.v_processed_mps = v_composite
        self.processed_source[composite_source == 1] = "BT"
        self.processed_source[composite_source == 2] = "GGA"
        self.processed_source[composite_source == 3] = "VTG"
        self.processed_source[composite_source == 0] = "INT"
        self.processed_source[composite_source == -1] = "INV"

    def sos_correction(self, ratio):
        """Correct boat velocity for a change in speed of sound.

        Parameters
        ----------
        ratio: float
            Ratio of new and old speed of sound
        """

        # Correct velocities
        self.u_mps = self.u_mps * ratio
        self.v_mps = self.v_mps * ratio
        self.w_mps = self.w_mps * ratio

    def interpolate_hold_9(self):
        """This function applies Sontek's approach to maintaining the last
        valid boat speed for up to 9 invalid samples.
        """

        # Initialize variables
        n_ensembles = self.u_mps.shape[0]

        # Get data from object
        self.u_processed_mps = np.copy(self.u_mps)
        self.v_processed_mps = np.copy(self.v_mps)
        self.u_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan
        self.v_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan

        n_invalid = 0
        # Process data by ensembles
        for n in range(n_ensembles):
            # Check if ensemble is invalid and number of consecutive
            # invalids is less than 9
            if self.valid_data[0, n] is False and n_invalid < 9:
                self.u_processed_mps[n] = self.u_processed_mps[n - 1]
                self.v_processed_mps[n] = self.v_processed_mps[n - 1]
                n_invalid += 1
            else:
                n_invalid = 0

    def interpolate_none(self):
        """This function removes any interpolation from the data and sets
        filtered data to nan."""

        # Reset processed data
        self.u_processed_mps = np.copy(self.u_mps)
        self.v_processed_mps = np.copy(self.v_mps)
        self.u_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan
        self.v_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan

    def interpolate_hold_last(self):
        """This function holds the last valid value until the next valid data
        point."""

        if self.u_mps is not None:
            # Initialize variables
            n_ensembles = len(self.u_mps)

            # Get data from object
            self.u_processed_mps = np.copy(self.u_mps)
            self.v_processed_mps = np.copy(self.v_mps)
            self.u_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan
            self.v_processed_mps[np.logical_not(self.valid_data[0, :])] = np.nan

            n_invalid = 0
            # Process data by ensembles
            for n in range(1, n_ensembles):
                # Check if ensemble is invalid and number of consecutive
                # invalids is less than 9
                if (self.valid_data[0, n] is False) and (n_invalid < 9):
                    self.u_processed_mps[n] = self.u_processed_mps[n - 1]
                    self.v_processed_mps[n] = self.v_processed_mps[n - 1]

    def interpolate_next(self):
        """This function uses the next valid data to backfill for invalid"""

        # Get valid ensembles
        valid_ens = self.valid_data[0, :]

        # Process ensembles
        n_ens = len(valid_ens)

        for n in np.arange(0, n_ens - 1)[::-1]:
            if not valid_ens[n]:
                self.u_processed_mps[n] = self.u_processed_mps[n + 1]
                self.v_processed_mps[n] = self.v_processed_mps[n + 1]

    def interpolate_smooth(self, transect):
        """This function interpolates data flagged invalid using the smooth
        function.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        """

        # Get data from object
        u = np.copy(self.u_mps)
        v = np.copy(self.v_mps)
        u[np.logical_not(self.valid_data[0, :])] = np.nan
        v[np.logical_not(self.valid_data[0, :])] = np.nan

        # Compute ens_time
        ens_time = np.nancumsum(transect.date_time.ens_duration_sec)

        # Apply smooth to each component
        u_smooth = rloess(ens_time, u, 10)
        v_smooth = rloess(ens_time, v, 10)

        # Save data in object
        self.u_processed_mps = u
        self.v_processed_mps = v
        self.u_processed_mps[np.isnan(u)] = u_smooth[np.isnan(u)]
        self.v_processed_mps[np.isnan(v)] = v_smooth[np.isnan(v)]

    def interpolate_linear(self, transect):
        """This function interpolates data flagged invalid using linear
        interpolation.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        """

        u = np.copy(self.u_mps)
        v = np.copy(self.v_mps)

        valid = np.logical_not(np.isnan(u))

        # Check for valid data
        if sum(valid) > 1 and sum(self.valid_data[0, :]) > 1:
            # Compute ens_time
            ens_time = np.nancumsum(transect.date_time.ens_duration_sec)

            # Apply linear interpolation
            self.u_processed_mps = np.interp(
                x=ens_time,
                xp=ens_time[self.valid_data[0, :]],
                fp=u[self.valid_data[0, :]],
                left=np.nan,
                right=np.nan,
            )
            # Apply linear interpolation
            self.v_processed_mps = np.interp(
                x=ens_time,
                xp=ens_time[self.valid_data[0, :]],
                fp=v[self.valid_data[0, :]],
                left=np.nan,
                right=np.nan,
            )

    def interpolate_composite(self, transect):
        """This function interpolates processed data flagged invalid using
        linear interpolation.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        """

        u = np.copy(self.u_processed_mps)
        v = np.copy(self.v_processed_mps)

        valid = np.logical_not(np.isnan(u))

        # Check for valid data
        if np.sum(valid) > 1:
            # Compute ensTime
            ens_time = np.nancumsum(transect.date_time.ens_duration_sec)

            # Ensure monotonic input
            diff_time = np.diff(ens_time[valid])
            idx = np.where(diff_time == 0)[0]
            mono_array = np.vstack([ens_time[valid], u[valid], v[valid]])

            # Replace non-monotonic times with average values
            for i in idx[::-1]:
                mono_array[1, i] = np.nanmean(mono_array[1, i : i + 2])
                mono_array[2, i] = np.nanmean(mono_array[2, i : i + 2])
                mono_array = np.delete(mono_array, i + 1, 1)

            # Apply linear interpolation
            self.u_processed_mps = np.interp(
                ens_time, mono_array[0, :], mono_array[1, :]
            )
            # Apply linear interpolation
            self.v_processed_mps = np.interp(
                ens_time, mono_array[0, :], mono_array[2, :]
            )
            
            idx_invalid = np.where(valid == False)[0]
            for idx in idx_invalid:
                if np.logical_not(np.isnan(self.u_processed_mps[idx])):
                    self.processed_source[idx] = "INT"
            
    def apply_filter(
        self,
        transect,
        beam=None,
        difference=None,
        difference_threshold=None,
        vertical=None,
        vertical_threshold=None,
        other=None,
    ):
        """Function to apply filters to navigation data.

        More than one filter can be applied during a single call.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        beam: int
            Setting for beam filter (3, 4, -1)
        difference: str
            Setting for difference velocity filter (Auto, Manual, Off)
        difference_threshold: float
            Threshold for manual setting
        vertical: str
            Setting for vertical velocity filter (Auto, Manual, Off)
        vertical_threshold: float
            Threshold for manual setting
        other: bool
            Setting to other filter
        """

        if (
            len(
                {
                    beam,
                    difference,
                    difference_threshold,
                    vertical,
                    vertical_threshold,
                    other,
                }
            )
            > 1
        ):
            # Filter based on number of valid beams
            if beam is not None:
                self.filter_beam(setting=beam)

            # Filter based on difference velocity
            if difference is not None:
                if difference == "Manual":
                    self.filter_diff_vel(
                        setting=difference, threshold=difference_threshold
                    )
                else:
                    self.filter_diff_vel(setting=difference)

            # Filter based on vertical velocity
            if vertical is not None:
                if vertical == "Manual":
                    self.filter_vert_vel(setting=vertical, threshold=vertical_threshold)
                else:
                    self.filter_vert_vel(setting=vertical)

            # Filter based on robust loess smooth
            if other is not None:
                self.filter_smooth(setting=other, transect=transect)

        else:
            self.filter_beam(setting=self.beam_filter)
            self.filter_diff_vel(
                setting=self.d_filter, threshold=self.d_filter_thresholds
            )
            self.filter_vert_vel(
                setting=self.w_filter, threshold=self.w_filter_thresholds
            )
            self.filter_smooth(setting=self.smooth_filter, transect=transect)

        # Apply previously specified interpolation method
        self.apply_interpolation(transect)

    def filter_beam(self, setting):
        """Applies beam filter.

        The determination of invalid data depends on whether
        3-beam or 4-beam solutions are acceptable. This function can be
        applied by specifying 3 or 4 beam solutions are setting
        obj.beamFilter to -1 which will trigger an automatic mode. The
        automatic mode will find all 3 beam solutions and then compare
        the velocity of the 3 beam solutions to nearest 4 beam solution
        before and after the 3 beam solution. If the 3 beam solution is
        within 50% of the average of the neighboring 3 beam solutions the
        data are deemed valid if not invalid. Thus, in automatic mode only
        those data from 3 beam solutions that appear sufficiently
        than the 4 beam solutions are marked invalid. The process happens
        for each ensemble. If the number of beams is specified manually
        it is applied uniformly for the whole transect.

        Parameters
        ----------
        setting: int
            Setting for beam filter (3, 4, -1)
        """

        self.beam_filter = setting

        # In manual mode determine number of raw invalid and number of 3
        # beam solutions
        # 3 beam solutions if selected
        if self.beam_filter > 0:
            # Find invalid raw data
            valid_vel = np.ones(self.raw_vel_mps.shape)
            valid_vel[np.isnan(self.raw_vel_mps)] = 0

            # Determine how many beams transformed coordinates are valid
            valid_vel_sum = np.sum(valid_vel, 0)
            valid = np.ones(valid_vel_sum.shape)

            # Compare number of valid beams or coordinates to filter value
            valid[valid_vel_sum < self.beam_filter] = False

            # Save logical of valid data to object
            self.valid_data[5, :] = valid

        else:
            # Apply automatic filter
            # ----------------------
            # Find all 3 beam solutions
            self.filter_beam(3)
            beam_3_valid_data = copy.deepcopy(self.valid_data)
            self.filter_beam(4)
            valid_3_beams = np.logical_xor(
                beam_3_valid_data[5, :], self.valid_data[5, :]
            )
            n_ens = len(self.valid_data[5, :])
            idx = np.where(valid_3_beams)[0]

            # If 3 beam solutions exist evaluate there validity
            if len(idx) > 0:
                # Identify 3 beam solutions that appear to be invalid
                n3_beam_ens = len(idx)

                # Check each three beam solution for validity
                for m in range(n3_beam_ens):
                    # Use before and after values to check 3-beam solution
                    # but make sure the ensemble is not the first or last.
                    if (idx[m] > 1) and (idx[m] < n_ens):
                        # Find nearest 4 beam solutions before and after
                        # 3 beam solution
                        ref_idx_before = np.where(self.valid_data[5, : idx[m]])[0]
                        if len(ref_idx_before) > 0:
                            ref_idx_before = ref_idx_before[-1]
                        else:
                            ref_idx_before = None

                        ref_idx_after = np.where(self.valid_data[5, idx[m] :])[0]
                        if len(ref_idx_after) > 0:
                            ref_idx_after = idx[m] + ref_idx_after[0]
                        else:
                            ref_idx_after = None

                        if (ref_idx_after is not None) and (ref_idx_before is not None):
                            u_ratio = (self.u_mps[idx[m]]) / (
                                (self.u_mps[ref_idx_before] + self.u_mps[ref_idx_after])
                                / 2.0
                            ) - 1
                            v_ratio = (self.v_mps[idx[m]]) / (
                                (self.v_mps[ref_idx_before] + self.v_mps[ref_idx_after])
                                / 2.0
                            ) - 1
                        else:
                            u_ratio = 1
                            v_ratio = 1

                        # If 3-beam differs from 4-beam by more than 50% mark
                        # it invalid
                        if (np.abs(u_ratio) > 0.5) and (np.abs(v_ratio) > 0.5):
                            self.valid_data[5, idx[m]] = False
                        else:
                            self.valid_data[5, idx[m]] = True

            self.beam_filter = -1

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    def filter_diff_vel(self, setting, threshold=None):
        """Applies either manual or automatic filtering of the difference
        (error) velocity.

        The automatic mode is based on the following:
        This filter is based on the assumption that the water error velocity
        should follow a gaussian distribution. Therefore, 5 iqr
        should encompass all the valid data. The standard deviation and
        limits (multiplier*standard deviation) are computed in an iterative
        process until filtering out additional data does not change the
        computed standard deviation.

        Parameters
        ----------
        setting: str
            Difference velocity setting (Off, Manual, Auto)
        threshold: float, dict
            If manual, the user specified threshold
        """

        self.d_filter = setting
        if setting == "Manual":
            self.d_filter_thresholds = threshold

        # Apply selected method
        if self.d_filter == "Manual":
            d_vel_max_ref = np.abs(self.d_filter_thresholds)
            d_vel_min_ref = -1 * d_vel_max_ref
            invalid_idx = np.where(
                np.logical_or(
                    nan_greater(self.d_mps, d_vel_max_ref),
                    nan_less(self.d_mps, d_vel_min_ref),
                )
            )[0]
        elif self.d_filter == "Off":
            invalid_idx = np.array([])

        elif self.d_filter == "Auto":
            if self.use_measurement_thresholds:
                if self.ping_type is None:
                    freq_ensembles = self.frequency_khz.astype(int).astype(str)
                else:
                    freq_ensembles = self.ping_type
                invalid_idx = np.array([])
                for freq in self.d_meas_thresholds.keys():
                    filter_data = np.copy(self.d_mps)
                    filter_data[freq_ensembles != freq] = np.nan
                    idx = np.where(
                        np.logical_or(
                            np.greater(filter_data, self.d_meas_thresholds[freq][0]),
                            np.less(filter_data, self.d_meas_thresholds[freq][1]),
                        )
                    )[0]
                    if idx.size > 0:
                        if invalid_idx.size > 0:
                            invalid_idx = np.hstack((invalid_idx, idx))
                        else:
                            invalid_idx = idx
            else:
                if self.ping_type is None:
                    freq_used = np.unique(self.frequency_khz).astype(int).astype(str)
                    freq_ensembles = self.frequency_khz.astype(int).astype(str)
                else:
                    freq_used = np.unique(self.ping_type)
                    freq_ensembles = self.ping_type
                self.d_filter_thresholds = {}
                invalid_idx = np.array([])
                for freq in freq_used:
                    filter_data = np.copy(self.d_mps)
                    filter_data[freq_ensembles != freq] = np.nan
                    d_vel_max_ref, d_vel_min_ref = self.iqr_filter(filter_data)
                    self.d_filter_thresholds[freq] = [d_vel_max_ref, d_vel_min_ref]
                    idx = np.where(
                        np.logical_or(
                            nan_greater(filter_data, d_vel_max_ref),
                            nan_less(filter_data, d_vel_min_ref),
                        )
                    )[0]
                    if idx.size > 0:
                        if invalid_idx.size > 0:
                            invalid_idx = np.hstack((invalid_idx, idx))
                        else:
                            invalid_idx = idx
        else:
            invalid_idx = np.array([])

        # Set valid data row 3 for difference velocity filter results
        self.valid_data[2, :] = True
        if invalid_idx.size > 0:
            self.valid_data[2, invalid_idx] = False

        # Combine all filter data to composite filter data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    def filter_vert_vel(self, setting, threshold=None):
        """Applies either manual or automatic filtering of the vertical
        velocity.  Uses same assumptions as difference filter.

        Parameters
        ----------
        setting: str
            Filter setting (Off, Manual, Auto)
        threshold: float, dict
            If setting is manual, the user specified threshold
        """

        # Set vertical velocity filter properties
        self.w_filter = setting
        if setting == "Manual":
            self.w_filter_thresholds = threshold

        # Apply selected method
        if self.w_filter == "Manual":
            w_vel_max_ref = np.abs(self.w_filter_thresholds)
            w_vel_min_ref = -1 * w_vel_max_ref
            invalid_idx = np.where(
                np.logical_or(
                    nan_greater(self.w_mps, w_vel_max_ref),
                    nan_less(self.w_mps, w_vel_min_ref),
                )
            )[0]

        elif self.w_filter == "Off":
            invalid_idx = np.array([])

        elif self.w_filter == "Auto":
            if self.use_measurement_thresholds:
                if self.ping_type is None:
                    freq_ensembles = self.frequency_khz.astype(int).astype(str)
                else:
                    freq_ensembles = self.ping_type
                invalid_idx = np.array([])
                for freq in self.w_meas_thresholds.keys():
                    filter_data = np.copy(self.w_mps.astype(float))
                    filter_data[freq_ensembles != freq] = np.nan
                    idx = np.where(
                        np.logical_or(
                            np.greater(filter_data, self.w_meas_thresholds[freq][0]),
                            np.less(filter_data, self.w_meas_thresholds[freq][1]),
                        )
                    )[0]
                    if idx.size > 0:
                        if invalid_idx.size > 0:
                            invalid_idx = np.hstack((invalid_idx, idx))
                        else:
                            invalid_idx = idx
            else:
                if self.ping_type is None:
                    freq_used = np.unique(self.frequency_khz).astype(int).astype(str)
                    freq_ensembles = self.frequency_khz.astype(int).astype(str)
                else:
                    freq_used = np.unique(self.ping_type)
                    freq_ensembles = self.ping_type
                self.w_filter_thresholds = {}
                invalid_idx = np.array([])
                for freq in freq_used:
                    filter_data = np.copy(self.w_mps)
                    filter_data[freq_ensembles != freq] = np.nan
                    w_vel_max_ref, w_vel_min_ref = self.iqr_filter(filter_data)
                    self.w_filter_thresholds[freq] = [w_vel_max_ref, w_vel_min_ref]
                    idx = np.where(
                        np.logical_or(
                            nan_greater(filter_data, w_vel_max_ref),
                            nan_less(filter_data, w_vel_min_ref),
                        )
                    )[0]
                    if idx.size > 0:
                        if invalid_idx.size > 0:
                            invalid_idx = np.hstack((invalid_idx, idx))
                        else:
                            invalid_idx = idx
        else:
            invalid_idx = np.array([])

        # Set valid data row 3 for difference velocity filter results
        self.valid_data[3, :] = True
        if invalid_idx.size > 0:
            self.valid_data[3, invalid_idx] = False

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    @staticmethod
    def iqr_filter(data, multiplier=5, minimum_window=0.01):
        """Apply the iqr filter to bt data.

        Parameters
        ----------
        data: np.ndarray(float)
            Array of difference or vertical velocity data
        multiplier: int
            Number of IQR's to use to set the threshold
        minimum_window: float
            Minimum allowable threshold

        Returns
        -------
        data_max_ref: float
            Maximum threshold
        data_min_ref: float
            Minimum threshold
        """
        data_max_ref = np.nan
        data_min_ref = np.nan

        # Check to make sure there are data to process
        if data.size > 0 and np.any(np.logical_not(np.isnan(data))):
            # Initialize loop controllers
            k = 0
            iqr_diff = 1

            # Loop until no additional data are removed
            while iqr_diff != 0 and k < 1000:
                k += 1

                # Compute inner quartile range
                data_iqr = iqr(data)
                threshold_window = multiplier * data_iqr
                if threshold_window < minimum_window:
                    threshold_window = minimum_window

                # Compute maximum and minimum thresholds
                data_max_ref = np.nanmedian(data) + threshold_window
                data_min_ref = np.nanmedian(data) - threshold_window

                # Identify valid and invalid data
                data_less_idx = np.where(nan_less_equal(data, data_max_ref))[0]
                data_greater_idx = np.where(nan_greater_equal(data, data_min_ref))[0]
                data_good_idx = list(np.intersect1d(data_less_idx, data_greater_idx))

                # Update filtered data array
                data = copy.deepcopy(data[data_good_idx])

                # Determine differences due to last filter iteration
                if len(data) > 0:
                    data_iqr2 = iqr(data)
                    iqr_diff = data_iqr2 - data_iqr
                else:
                    iqr_diff = 0

        return data_max_ref, data_min_ref

    def filter_smooth(self, transect, setting):
        """This filter employs a running trimmed standard deviation filter to
        identify and mark spikes in the boat speed.

        First a robust Loess smooth is fitted to the boat speed time series and
        residuals between the raw data and the smoothed line are computed. The
        trimmed standard deviation is computed by selecting the number of
        residuals specified by "halfwidth" before the target point and
        after the target point,  but not including the target point.
        These values are then sorted, and the points
        with the highest and lowest values are removed from the subset, and the
        standard deviation of the trimmed subset is computed. The filter
        criteria are determined by multiplying the standard deviation by a user
        specified multiplier. These criteria define a maximum and minimum
        acceptable residual. Data falling outside the criteria are set to nan.

        Recommended filter setting are:
        filterWidth=10;
        halfWidth=10;
        multiplier=9;

        David S. Mueller, USGS, OSW
        9/8/2005

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        setting: bool
            Filter setting (True, False)
        """

        # Set property
        self.smooth_filter = setting

        # Compute ens_time
        ens_time = np.nancumsum(transect.date_time.ens_duration_sec)
        n_ensembles = len(ens_time)

        # Determine if smooth filter should be applied
        if self.smooth_filter == "On":
            # Initialize arrays
            self.smooth_speed = np.tile([np.nan], (1, n_ensembles))
            self.smooth_upper_limit = np.tile([np.nan], (1, n_ensembles))
            self.smooth_lower_limit = np.tile([np.nan], (1, n_ensembles))

            # Boat velocity components
            b_vele = np.copy(self.u_mps)
            b_veln = np.copy(self.v_mps)

            # Set filter parameters
            filter_width = 10
            half_width = 10
            multiplier = 9
            cycles = 3

            # Initialize variables
            bt_bad_idx = []
            upper_limit = 0
            lower_limit = 0

            # Compute speed and direction of boat
            direct, speed = cart2pol(b_vele, b_veln)

            # Compute residuals from a robust Loess smooth
            speed_smooth = rloess(ens_time, speed, filter_width)
            speed_res = speed - speed_smooth

            # Apply a trimmed standard deviation filter multiple times
            for i in range(cycles):
                filter_array = BoatData.run_std_trim(half_width, speed_res.T)

                # Compute filter bounds
                upper_limit = speed_smooth + multiplier * filter_array
                lower_limit = speed_smooth - multiplier * filter_array

                # Apply filter to residuals
                bt_bad_idx = np.where(
                    np.logical_or(
                        np.greater(speed, upper_limit), np.less(speed, lower_limit)
                    )
                )[0]
                speed_res[bt_bad_idx] = np.nan

            # Update valid_data property
            self.valid_data[4, :] = True
            self.valid_data[4, bt_bad_idx] = False
            self.valid_data[4, np.logical_not(self.valid_data[1, :])] = True
            self.smooth_upper_limit = upper_limit
            self.smooth_lower_limit = lower_limit
            self.smooth_speed = speed_smooth

        else:
            # No filter applied all data assumed valid
            self.valid_data[4, :] = True
            self.smooth_upper_limit = np.nan
            self.smooth_lower_limit = np.nan
            self.smooth_speed = np.nan

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(
            self.valid_data[1:,],
            0,
        )
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]), 0)

    def apply_gps_filter(
        self,
        transect,
        differential=None,
        altitude=None,
        altitude_threshold=None,
        hdop=None,
        hdop_max_threshold=None,
        hdop_change_threshold=None,
        other=None,
    ):
        """Applies filters to GPS referenced boat velocity data.

        Parameters
        ----------
        transect: TransectData
            Object of TransectData
        differential: str
            Differential filter setting (1, 2, 4)
        altitude: str
            New setting for altitude filter (Off, Manual, Auto)
        altitude_threshold: float
            Threshold provide by user for manual altitude setting
        hdop: str
            Filter setting (On, off, Auto)
        hdop_max_threshold: float
            Maximum HDOP threshold
        hdop_change_threshold: float
            HDOP change threshold
        other: bool
            Other filter typically a smooth.
        """

        if (
            len(
                {
                    differential,
                    altitude,
                    altitude_threshold,
                    hdop,
                    hdop_max_threshold,
                    hdop_change_threshold,
                    other,
                }
            )
            > 0
        ):
            # Differential filter only applies to GGA data, defaults to 1
            # for VTG
            if differential is not None:
                if self.nav_ref == "GGA":
                    self.filter_diff_qual(
                        gps_data=transect.gps, setting=int(differential)
                    )
                else:
                    self.filter_diff_qual(gps_data=transect.gps, setting=1)

            # Altitude filter only applies to GGA data
            if altitude is not None:
                if (altitude == "Manual") and (self.nav_ref == "GGA"):
                    self.filter_altitude(
                        gps_data=transect.gps,
                        setting=altitude,
                        threshold=altitude_threshold,
                    )
                elif self.nav_ref == "GGA":
                    self.filter_altitude(gps_data=transect.gps, setting=altitude)

            if hdop is not None:
                if hdop == "Manual":
                    self.filter_hdop(
                        gps_data=transect.gps,
                        setting=hdop,
                        max_threshold=hdop_max_threshold,
                        change_threshold=hdop_change_threshold,
                    )
                else:
                    self.filter_hdop(gps_data=transect.gps, setting=hdop)

            if other is not None:
                self.filter_smooth(transect=transect, setting=other)
        else:
            self.filter_diff_qual(gps_data=transect.gps)
            self.filter_altitude(gps_data=transect.gps)
            self.filter_hdop(gps_data=transect.gps)
            self.filter_smooth(transect=transect, setting=self.smooth_filter)

        # Apply previously specified interpolation method
        self.apply_interpolation(transect=transect)

    def filter_diff_qual(self, gps_data, setting=None):
        """Filters GPS data based on the minimum acceptable differential
        correction quality.

        Parameters
        ----------
        gps_data: GPSData
            Object of GPSData
        setting: int
            Filter setting (1, 2, 4).
        """

        # New filter setting if provided
        if setting is not None:
            self.gps_diff_qual_filter = setting

        # Reset valid_data property
        self.valid_data[2, :] = True
        self.valid_data[5, :] = True

        # Determine and apply appropriate filter type
        if gps_data.diff_qual_ens is not None:
            self.valid_data[2, np.isnan(gps_data.diff_qual_ens)] = False
            if self.gps_diff_qual_filter is not None:
                # Autonomous
                if self.gps_diff_qual_filter == 1:
                    self.valid_data[2, gps_data.diff_qual_ens < 1] = False
                # Differential correction
                elif self.gps_diff_qual_filter == 2:
                    self.valid_data[2, gps_data.diff_qual_ens < 2] = False
                # RTK
                elif self.gps_diff_qual_filter == 4:
                    self.valid_data[2, gps_data.diff_qual_ens < 4] = False

                # If there is no indication of the quality assume 1 fot vtg
                if self.nav_ref == "VTG":
                    self.valid_data[2, np.isnan(gps_data.diff_qual_ens)] = True
            else:
                self.valid_data[2, :] = False

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    def filter_altitude(self, gps_data, setting=None, threshold=None):
        """Filter GPS data based on a change in altitude.

        Assuming the data are collected on the river the altitude should not
        change substantially during the transect. Since vertical resolution is
        about 3 x worse that horizontal resolution the automatic filter
        threshold is set to 3 m, which should ensure submeter horizontal
        accuracy.

        Parameters
        ----------
        gps_data: GPSData
            Object of GPSData
        setting: str
            New setting for filter (Off, Manual, Auto)
        threshold: float
            Threshold provide by user for manual setting
        """

        # New filter settings if provided
        if setting is not None:
            self.gps_altitude_filter = setting
            if setting == "Manual":
                self.gps_altitude_filter_change = threshold

        # Set threshold for Auto
        if self.gps_altitude_filter == "Auto":
            self.gps_altitude_filter_change = 3

        # Set all data to valid
        self.valid_data[3, :] = True

        # Manual or Auto is selected, apply filter
        if not self.gps_altitude_filter == "Off":
            # Initialize variables
            num_valid_old = np.sum(self.valid_data[3, :])
            k = 0
            change = 1
            # Loop until no change in the number of valid ensembles
            while k < 100 and change > 0.1:
                # Compute mean using valid ensembles
                if self.valid_data.shape[1] == 1:
                    if self.valid_data[1, 0]:
                        alt_mean = gps_data.altitude_ens_m
                    else:
                        alt_mean = np.nan
                else:
                    alt_mean = np.nanmean(
                        gps_data.altitude_ens_m[self.valid_data[1, :]]
                    )

                # Compute difference for each ensemble
                diff = np.abs(gps_data.altitude_ens_m - alt_mean)

                # Mark invalid those ensembles with differences greater than
                # the change threshold
                self.valid_data[3, diff > self.gps_altitude_filter_change] = False
                k += 1
                num_valid = np.sum(self.valid_data[3, :])
                change = num_valid_old - num_valid

        # Combine all filter data to composite valid data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    def filter_hdop(
        self, gps_data, setting=None, max_threshold=None, change_threshold=None
    ):
        """Filter GPS data based on both a maximum HDOP and a change in HDOP
        over the transect.

        Parameters
        ----------
        gps_data: GPSData
            Object of GPSData
        setting: str
            Filter setting (On, off, Auto)
        max_threshold: float
            Maximum threshold
        change_threshold: float
            Change threshold
        """

        if gps_data.hdop_ens is None or gps_data.hdop_ens.size == 0:
            self.valid_data[5, : self.valid_data.shape[1]] = True
        else:
            # New settings if provided
            if setting is not None:
                self.gps_HDOP_filter = setting
                if self.gps_HDOP_filter == "Manual":
                    self.gps_HDOP_filter_max = max_threshold
                    self.gps_HDOP_filter_change = change_threshold

            # Settings for auto mode
            if self.gps_HDOP_filter == "Auto":
                self.gps_HDOP_filter_change = 3
                self.gps_HDOP_filter_max = 4

            # Set all ensembles to valid
            self.valid_data[5, :] = True

            # Apply filter for manual or auto
            if not self.gps_HDOP_filter == "Off":
                # Initialize variables
                num_valid_old = np.sum(self.valid_data[5, :])
                k = 0
                change = 1

                # Apply max filter
                self.valid_data[
                    5, np.greater(gps_data.hdop_ens, self.gps_HDOP_filter_max)
                ] = False

                # Loop until the number of valid ensembles does not change
                while k < 100 and change > 0.1:
                    # Compute mean HDOP for all valid ensembles
                    if self.valid_data.shape[1] == 1:
                        if self.valid_data[5, 0]:
                            hdop_mean = gps_data.hdop_ens
                        else:
                            hdop_mean = np.nan
                    else:
                        hdop_mean = np.nanmean(gps_data.hdop_ens[self.valid_data[5, :]])

                    # Compute the difference in HDOP and the mean for
                    # all ensembles
                    diff = np.abs(gps_data.hdop_ens - hdop_mean)

                    # If the change is HDOP or the value of HDOP is greater
                    # than the threshold setting mark the data invalid
                    self.valid_data[
                        5, np.greater(diff, self.gps_HDOP_filter_change)
                    ] = False

                    k += 1
                    num_valid = np.sum(self.valid_data[5, :])
                    change = num_valid_old - num_valid
                    num_valid_old = num_valid

        # Combine all filter data to composite data
        self.valid_data[0, :] = np.all(self.valid_data[1:, :], 0)
        self.num_invalid = np.sum(np.logical_not(self.valid_data[0, :]))

    @staticmethod
    def filter_sontek(vel_in):
        """Determines invalid raw bottom track samples for SonTek data.

        Invalid data are those that are zero or where the velocity doesn't
        change between ensembles.

        Parameters
        ----------
        vel_in: np.array(float)
            Bottom track velocity data, in m/s.

        Returns
        -------
        vel_out: np.array(float)
            Filtered bottom track velocity data with all invalid data set to
            np.nan.
        """

        # Identify all samples where the velocity did not change
        test1 = np.abs(np.diff(vel_in, 1, 1)) < 0.00001

        # Identify all samples with all zero values
        test2 = np.nansum(np.abs(vel_in), 0) < 0.00001
        # using 1: makes the array dimension
        # consistent with test1 as diff results in 1 less.
        test2 = test2[1:] * 4

        # Combine criteria
        test_sum = np.nansum(test1, 0) + test2

        # Develop logical vector of invalid ensembles
        invalid_bool = np.full(test_sum.size, False)
        invalid_bool[test_sum >= 3] = True

        # Handle first ensemble
        invalid_bool = np.concatenate((np.array([False]), invalid_bool), 0)
        if np.nansum(vel_in[:, 0]) == 0:
            invalid_bool[0] = True

        # Set invalid ensembles to nan
        vel_out = np.copy(vel_in)
        vel_out[:, invalid_bool] = np.nan

        if vel_out.shape[0] > 2:
            # Set difference velocity to nan for 3-beam solutions, BT only
            vel_out[3, np.abs(vel_out[3, :]) < 0.000001] = np.nan

        return vel_out

    @staticmethod
    def run_std_trim(half_width, my_data):
        """Computes a standard deviation over +/- halfwidth of points.

        The routine accepts a column vector as input.
        "halfWidth" number of data
        points for computing the standard deviation are selected before and
        after the target data point, but not including the target data point.
        Near the ends of the series the number of points before or after are
        reduced. nan in the data are counted as points. The selected subset of
        points is sorted and the points with the highest and lowest values are
        removed from the subset and the standard deviation computed on the
        remaining points in the subset.
        The process occurs for each point in the
        provided column vector. A column vector with the computed standard
        deviation at each point is returned.

        Parameters
        ----------
        half_width: int
             Number of ensembles on each side of target ensemble to used
             for computing trimmed standard deviation
        my_data: np.array(float)
             Data to be processed

        Returns
        -------
        filter_array: np.array(float)
             Vector with computed standard
        """

        # Determine number of points to process
        n_pts = my_data.shape[0]
        if n_pts < 20:
            half_width = np.floor(n_pts / 2.0)

        filter_array = []
        # Compute standard deviation for each point
        for n in range(n_pts):
            # Sample selection for 1st point
            if n == 0:
                sample = my_data[1 : 1 + half_width]

            # Sample selection at end of data set
            elif n + half_width > n_pts:
                sample = np.hstack(
                    (my_data[n - half_width - 1 : n - 1], my_data[n:n_pts])
                )

            # Sample selection at beginning of data set
            elif half_width >= n + 1:
                sample = np.hstack((my_data[0:n], my_data[n + 1 : n + half_width + 1]))

            # Samples selection in body of data set
            else:
                sample = np.hstack(
                    (my_data[n - half_width : n], my_data[n + 1 : n + half_width + 1])
                )

            # Sort and compute trimmed standard deviation
            sample = np.sort(sample)
            filter_array.append(np.nanstd(sample[1 : sample.shape[0] - 1], ddof=1))

        return np.array(filter_array)
