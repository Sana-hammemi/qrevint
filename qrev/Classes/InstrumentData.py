import numpy as np
from qrev.Classes.TransformationMatrix import TransformationMatrix


class InstrumentData(object):
    """Container for characteristics of the ADCP used to make the measurement

    Attributes
    ----------
    serial_num: str
        Serial number of ADCP.
    manufacturer: str
        Name of manufacturer.
    model: str
        Model name of ADCP.
    firmware: str
        Firmware version in the ADCP.
    frequency_khz:
        Frequency or frequencies used by ADCP.
    beam_angle_deg:
        Angle of the beams from vertical in degrees.
    beam_pattern:
        Pattern of the beam angles, concave or convex.
    t_matrix: TransformationMatrix
        Object of TransformationMatrix.
    configuration_commands:
        Commands used to configure the instrument.
    """

    def __init__(self):
        """Constructor initializes the variables to None."""

        self.serial_num = None
        self.manufacturer = None
        self.model = None
        self.firmware = None
        self.frequency_khz = None
        self.beam_angle_deg = None
        self.beam_pattern = None
        self.t_matrix = None
        self.configuration_commands = np.array([])

    def populate_data(self, manufacturer, raw_data, mmt_transect=None, mmt=None):
        """Manages method calls for different manufacturers.

        Parameters
        ----------
        manufacturer: str
            Name of manufacturer.
        raw_data: object or dict
            Object of Pd0TRDI for TRDI or Object of MatSonTek for SonTek
        mmt_transect: MMT_Transect
            Object of Transect (mmt object)
        mmt: MMT_TRDI
            Object of MMT_TRDI
        """

        # Process based on manufacturer
        if manufacturer == "TRDI":
            self.manufacturer = manufacturer
            self.trdi(pd0=raw_data, mmt_transect=mmt_transect, mmt=mmt)
        elif manufacturer == "SonTek":
            self.manufacturer = manufacturer
            self.sontek(rs=raw_data)
        elif manufacturer == "Nortek":
            self.manufacturer = manufacturer
            self.nortek(rs=raw_data)
        elif manufacturer == "rsq":
            self.manufacturer = "SonTek"
            self.rsq(adcp_data=raw_data)

    def trdi(self, pd0, mmt_transect, mmt):
        """Populates the variables with data from TRDI ADCPs.

        Parameters
        ----------
        pd0: Pd0TRDI
            Object of Pd0TRDI
        mmt_transect: MMT_Transect
            Object of MMT_Transect
        mmt: MMT_Transect
            Object of MMT_Transect
        """

        # Instrument frequency
        self.frequency_khz = pd0.Inst.freq[0]

        # Firmware
        self.firmware = pd0.Inst.firm_ver[0]

        # Instrument beam angle and pattern
        self.beam_angle_deg = pd0.Inst.beam_ang[0]
        self.beam_pattern = pd0.Inst.pat[0]

        # Instrument characteristics
        mmt_site = getattr(mmt, "site_info")
        mmt_config = getattr(mmt_transect, "active_config")

        self.serial_num = mmt_site["ADCPSerialNmb"]
        if len(self.serial_num) == 0:
            if "RG_Test" in mmt.qaqc:
                for test in mmt.qaqc["RG_Test"]:
                    idx = test.find("Serial Number:")
                    if idx > 0:
                        idx_end = test[idx::].find("\n")
                        self.serial_num = test[idx + 15 : idx + idx_end].strip()
                        break

        # Determine TRDI model
        num = float(self.firmware)
        model_switch = np.floor(num)

        if model_switch == 10:
            self.model = "Rio Grande"
            if "Fixed_Commands" in mmt_config.keys():
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, mmt_config["Fixed_Commands"]
                )

        elif model_switch == 31:
            self.model = "StreamPro"
            self.frequency_khz = 2000
            if "Fixed_Commands_StreamPro" in mmt_config.keys():
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, mmt_config["Fixed_Commands_StreamPro"]
                )

        elif model_switch == 44:
            self.model = "RiverRay"
            if "Fixed_Commands_RiverRay" in mmt_config.keys():
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, mmt_config["Fixed_Commands_RiverRay"]
                )

        elif model_switch == 56:
            self.model = "RiverPro"
            if pd0.Cfg.n_beams[0] < 5:
                if "RG_Test" in mmt.qaqc.keys():
                    idx = mmt.qaqc["RG_Test"][0].find("RioPro")
                    if idx != -1:
                        self.model = "RioPro"
                    else:
                        self.model = "RiverPro"
                else:
                    # Assume RioPro based on number of beams
                    self.model = "RioPro"

            if "Fixed_Commands_RiverPro" in mmt_config.keys():
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, mmt_config["Fixed_Commands_RiverPro"]
                )
            else:
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, " "
                )

        else:
            self.model = "Unknown"
            if "Fixed_Commands" in mmt_config.keys():
                self.configuration_commands = np.append(
                    self.configuration_commands, "Fixed"
                )
                self.configuration_commands = np.append(
                    self.configuration_commands, mmt_config["Fixed_Commands"]
                )

        if "Wizard_Commands" in mmt_config.keys():
            self.configuration_commands = np.append(
                self.configuration_commands, ["Wizard"]
            )
            self.configuration_commands = np.append(
                self.configuration_commands, mmt_config["Wizard_Commands"]
            )

        if "User_Commands" in mmt_config.keys():
            self.configuration_commands = np.append(
                self.configuration_commands, ["User"]
            )
            self.configuration_commands = np.append(
                self.configuration_commands, mmt_config["User_Commands"]
            )

        # Obtain transformation matrix from one of the available sources
        if not np.isnan(pd0.Inst.t_matrix[0, 0]):
            self.t_matrix = TransformationMatrix()
            self.t_matrix.populate_data(manufacturer="TRDI", model="pd0", data_in=pd0)
        elif self.model == "RiverRay":
            self.t_matrix = TransformationMatrix()
            self.t_matrix.populate_data(
                manufacturer="TRDI", model=self.model, data_in="Nominal"
            )
        else:
            if isinstance(mmt.qaqc, dict) and len(mmt.qaqc) > 0:
                if "RG_Test" in mmt.qaqc.keys():
                    self.t_matrix = TransformationMatrix()
                    self.t_matrix.populate_data(
                        manufacturer="TRDI",
                        model=self.model,
                        data_in=mmt.qaqc["RG_Test"][0],
                    )

                elif "Compass_Calibration" in mmt.qaqc.keys():
                    self.t_matrix = TransformationMatrix()
                    self.t_matrix.populate_data(
                        manufacturer="TRDI",
                        model=self.model,
                        data_in=mmt.qaqc["Compass_Calibration"][0],
                    )

                elif "Compass_Eval_Timestamp" in mmt.qaqc.keys():
                    self.t_matrix = TransformationMatrix()
                    self.t_matrix.populate_data(
                        manufacturer="TRDI",
                        model=self.model,
                        data_in=mmt.qaqc["Compass_Evaluation"][0],
                    )

                else:
                    self.t_matrix = TransformationMatrix()
                    self.t_matrix.populate_data(
                        manufacturer="TRDI", model=self.model, data_in="Nominal"
                    )
            else:
                self.t_matrix = TransformationMatrix()
                self.t_matrix.populate_data(
                    manufacturer="TRDI", model=self.model, data_in="Nominal"
                )

    def sontek(self, rs):
        """Populates the variables with data from SonTek ADCPs.

        Parameters
        ----------
        rs: MatSonTek
        """

        self.serial_num = rs.System.SerialNumber
        if type(self.serial_num) == float:
            self.serial_num = str(int(self.serial_num))
        elif type(self.serial_num) == int:
            self.serial_num = str(self.serial_num)
        self.frequency_khz = rs.Transformation_Matrices.Frequency
        if self.frequency_khz[2] > 0:
            self.model = "M9"
        elif hasattr(rs.WaterTrack, "Vel_Expected_StdDev"):
            self.model = "RS5"
        else:
            self.model = "S5"
        if hasattr(rs, "SystemHW"):
            revision = str(rs.SystemHW.FirmwareRevision)
            if len(revision) < 2:
                revision = "0" + revision
            self.firmware = str(rs.SystemHW.FirmwareVersion) + "." + revision
        elif self.model == "RS5":
            try:
                self.firmware = str(rs.System.FirmwareVersion)
            except BaseException:
                self.firmware = ""
        else:
            self.firmware = ""
        self.beam_angle_deg = 25
        self.beam_pattern = "Convex"
        self.t_matrix = TransformationMatrix()
        self.t_matrix.populate_data("SonTek", data_in=rs.Transformation_Matrices.Matrix)
        self.configuration_commands = None

    def rsq(self, adcp_data):
        """Populates the variables with stationary data from SonTek RSQ.

        Parameters
        ----------
        adcp_data: dict
            Dictionary containing RSQ data
        """

        try:
            self.serial_num = adcp_data["InstrumentInfo"]["SerialNumber"]
        except KeyError:
            self.serial_num = ""

        self.frequency_khz = []
        beam_azimuth = []
        beam_elev = []
        for n in range(adcp_data["SensorConfiguration"]["Info"]["beamSetCount"]):
            freq = (
                adcp_data["SensorConfiguration"]["Info"]["beamSetInfo"][str(n)][
                    "systemFrequency (Hz)"
                ]
                / 1000
            )
            self.frequency_khz.append(freq)

            beam_azimuth.append(
                list(
                    adcp_data["SensorConfiguration"]["Info"]["beamSetInfo"][str(n)][
                        "beamAzimuth"
                    ].values()
                )
            )
            beam_elev.append(
                list(
                    adcp_data["SensorConfiguration"]["Info"]["beamSetInfo"][str(n)][
                        "beamElevation"
                    ].values()
                )
            )

        if len(self.frequency_khz) > 2:
            if self.frequency_khz[2] > 0:
                self.model = "M9"
            else:
                self.model = "S5"
        else:
            self.model = "RS5"

        self.firmware = adcp_data["InstrumentInfo"]["InstrumentVersion"] / 100.0

        self.frequency_khz = np.array(self.frequency_khz)
        self.beam_angle_deg = 25
        self.beam_pattern = "Convex"
        self.t_matrix = TransformationMatrix()
        self.t_matrix.populate_data("rsqst", data_in=(beam_elev, beam_azimuth))
        self.configuration_commands = None

    def nortek(self, rs):
        """Populates the variables with data from Nortek ADCPs.

        Parameters
        ----------
        rs: MatSonTek
        """

        self.serial_num = rs.System.SerialNumber
        self.frequency_khz = rs.Transformation_Matrices.Frequency
        self.model = rs.System.InstrumentModel
        if hasattr(rs, "SystemHW"):
            revision = str(rs.SystemHW.FirmwareRevision)
            if len(revision) < 2:
                revision = "0" + revision
            self.firmware = str(rs.SystemHW.FirmwareVersion) + "." + revision
        else:
            self.firmware = ""
        self.beam_angle_deg = 25
        self.beam_pattern = "Convex"
        self.t_matrix = TransformationMatrix()
        self.t_matrix.populate_data("SonTek", data_in=rs.Transformation_Matrices.Matrix)
        self.configuration_commands = None

    def populate_from_qrev_mat(self, transect, meas_struct):
        """Populates the object using data from previously saved QRev Matlab
         file.

         Parameters
        ----------
        transect: mat_struct
            Matlab data structure obtained from sio.loadmat
        """
        self.serial_num = str(transect.adcp.serialNum)
        if self.serial_num == "[]":
            self.serial_num = ""
            if hasattr(meas_struct, "sysTest"):
                if type(meas_struct.sysTest) == np.ndarray:
                    for test in meas_struct.sysTest:
                        idx = test.data.find("Serial Number:")
                        if idx > 0:
                            idx_end = test.data[idx::].find("\n")
                            self.serial_num = test.data[
                                idx + 15 : idx + idx_end
                            ].strip()
                            break
                elif len(meas_struct.sysTest.data) > 0:
                    idx = meas_struct.sysTest.data.find("Serial Number:")
                    if idx > 0:
                        idx_end = meas_struct.sysTest.data[idx::].find("\n")
                        self.serial_num = meas_struct.sysTest.data[
                            idx + 15 : idx + idx_end
                        ].strip()

        self.manufacturer = transect.adcp.manufacturer
        self.model = transect.adcp.model
        self.firmware = transect.adcp.firmware
        self.frequency_khz = transect.adcp.frequency_hz
        self.beam_angle_deg = transect.adcp.beamAngle_deg
        self.beam_pattern = transect.adcp.beamPattern
        self.t_matrix = TransformationMatrix()
        self.t_matrix.populate_from_qrev_mat(transect.adcp.tMatrix)

        if len(transect.adcp.configurationCommands) > 0:
            self.configuration_commands = []
            for command in transect.adcp.configurationCommands:
                if type(command) == str:
                    self.configuration_commands.append(command)
            self.configuration_commands = np.array(self.configuration_commands)

        else:
            self.configuration_commands = None

    @staticmethod
    def create_hpr_matrix(manufacturer, heading, pitch, roll):
        """Creates hpr_matrix for transforming instrument coordinates to earth coordinates.

        Parameters
        ----------
        manufacturer: str
            Name of manufacturer SonTek, TRDI, Nortek
        heading: float
            Heading including magnetic variation in degrees
        pitch: float
            Pitch in degrees
        roll: float
            Roll in degrees

        """

        ch = np.cos(np.deg2rad(heading))
        sh = np.sin(np.deg2rad(heading))
        cp = np.cos(np.deg2rad(pitch))
        sp = np.sin(np.deg2rad(pitch))
        cr = np.cos(np.deg2rad(roll))
        sr = np.sin(np.deg2rad(roll))

        if manufacturer == "SonTek":
            hpr_matrix = np.array(
                [
                    [
                        sh * cp + (ch * sp * sr),
                        -1 * ch * cr,
                        -1 * sh * sp + (ch * cp * sr),
                    ],
                    [
                        ch * cp + -1 * (sh * sp * sr),
                        sh * cr,
                        -1 * ch * sp + (-1 * sh * cp * sr),
                    ],
                    [sp * cr, sr, cp * cr],
                ]
            )
        else:
            hpr_matrix = np.array(
                [
                    [
                        ((ch * cr) + (sh * sp * sr)),
                        (sh * cp),
                        ((ch * sr) - sh * sp * cr),
                    ],
                    [
                        (-1 * sh * cr) + (ch * sp * sr),
                        ch * cp,
                        (-1 * sh * sr) - (ch * sp * cr),
                    ],
                    [(-1.0 * cp * sr), sp, cp * cr],
                ]
            )

        return hpr_matrix

    def get_transformation_matrix(self, frequency):
        # Determine frequency index for transformation matrix
        if len(self.t_matrix.matrix.shape) > 2:
            idx_freq = np.where(self.frequency_khz == frequency)
            if self.t_matrix.matrix.shape[0] == 4:
                matrix = np.copy(self.t_matrix.matrix[:, :, idx_freq[0][0]])
            else:
                matrix = np.copy(self.t_matrix.matrix[idx_freq[0][0], :, :])
        else:
            matrix = np.copy(self.t_matrix.matrix)
        return matrix

    @staticmethod
    def get_coordinate_system_code(coord_sys):
        """Returns the coordinate system code based on the coordinate system.

        Parameters
        ----------
        coord_sys: str
            Coordinate system (Beam, Inst, Ship, Earth)

        Returns
        -------
        coord_sys_code: int
            Integer representing the coordinate system
        """
        coord_sys_code = 0
        if coord_sys == "Beam":
            coord_sys_code = 1
        elif coord_sys == "Inst":
            coord_sys_code = 2
        elif coord_sys == "Ship":
            coord_sys_code = 3
        elif coord_sys == "Earth":
            coord_sys_code = 4
        return coord_sys_code

    @staticmethod
    def compute_inst_coordinates(transformation_matrix, beam_velocities):
        return transformation_matrix.dot(beam_velocities)

    @staticmethod
    def adjust_for_3_beam_solution(transformation_matrix, beam_velocities, idx_3_beam):
        vel_3_beam_zero = beam_velocities
        vel_3_beam_zero[np.isnan(beam_velocities)] = 0
        vel_error = np.matmul(transformation_matrix[3, :], vel_3_beam_zero)
        beam_velocities[idx_3_beam] = (
            -1 * vel_error / np.squeeze(transformation_matrix[3, idx_3_beam])
        )

    @staticmethod
    def compute_new_coordinates(hpr_matrix, current_coordinates):
        new_coordinates = hpr_matrix.dot(current_coordinates[:3])
        return (
            new_coordinates[0],
            new_coordinates[1],
            new_coordinates[2],
            current_coordinates[3],
        )

    @staticmethod
    def transform_instrument_coordinates(manufacturer, inst_coordinates, h, p, r, new_coord_sys):
        hpr_matrix = None
        if new_coord_sys == "Earth":
            # Generate matrix to compute earth coordinates
            hpr_matrix = InstrumentData.create_hpr_matrix(
                manufacturer=manufacturer,
                heading=h,
                pitch=p,
                roll=r,
            )

        elif new_coord_sys == "Ship":
            # Generate matrix to compute ship coordinates
            hpr_matrix = InstrumentData.create_hpr_matrix(
                manufacturer=manufacturer,
                heading=0,
                pitch=p,
                roll=r,
            )

        elif new_coord_sys == "Inst":
            # Identity matrix for instrument coordinates
            hpr_matrix = np.eye(3)

        return InstrumentData.compute_new_coordinates(hpr_matrix, inst_coordinates)
        # new_coordinates = hpr_matrix.dot(current_coordinates[:3])
        # return (
        #     new_coordinates[0],
        #     new_coordinates[1],
        #     new_coordinates[2],
        #     current_coordinates[3],
        # )
