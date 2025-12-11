import getpass
import io
from datetime import datetime

import numpy as np
from matplotlib.figure import Figure
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)

from qrev.UI.AdvGraphs import AdvGraphs
from qrev.UI.DischargeTS import DischargeTS
from qrev.UI.ExtrapPlot import ExtrapPlot
from qrev.UI.MplCanvas import MplCanvas
from qrev.UI.ULollipopPlot import ULollipopPlot
from qrev.MiscLibs.local_time_utilities import tz_formatted_string


class Report:
    """Generates a PDF summary report."""

    def __init__(self, pdf_fullname, parent):
        """Constructs report doc.

        Parameters
        ----------
        pdf_fullname: str
            Filename of pdf file including path.
        parent: QRevInt
            Main object,
        """

        self.parent = parent
        self.doc = SimpleDocTemplate(
            pdf_fullname,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=90,
            bottomMargin=36,
        )
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter
        self.discharge = self.parent.meas.mean_discharges(parent.meas)
        self.tr = self.parent.tr

    def header(self, page, doc):
        """Create header for each page of report.

        Parameters
        ----------
        page: Canvas
            Object of Canvas
        doc: SimpleDocTemplate
            Object of SimpleDocTemplate, required
        """

        qrev_icon = self.parent.get_icon()
        # Configure for QRev and QRevInt
        self.tr("QRevInt Discharge Measurement Report")

        if "Int" in self.parent.version:
            title_str = self.tr("QRevInt Discharge Measurement Report")
        else:
            title_str = self.tr("QRev Discharge Measurement Report")

        logo = Image(qrev_icon, width=30, height=30)
        title = "<font size=14><b>" + title_str + "</b></font>"

        # Logo
        logo.wrapOn(page, self.width, self.height)
        logo.drawOn(page, 0.6 * inch, self.height - 0.65 * inch)

        # Title
        p = Paragraph(title, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 1.1 * inch, self.height - 0.5 * inch)

        # Line 2
        y = 0.85

        # Station Name
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Station Name")
            + ":</b> {}</font>".format(self.parent.meas.station_name)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 0.6 * inch, self.height - y * inch)

        # Line 3
        y = 1.05

        # Station Number
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Station Number")
            + ":</b>  {}</font>".format(self.parent.meas.station_number)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 0.6 * inch, self.height - y * inch)

        # Measurement Date
        start = self.parent.meas.transects[
            self.parent.meas.checked_transect_idx[0]
        ].date_time.start_serial_time
        utc_time_offset = self.parent.meas.transects[
            self.parent.meas.checked_transect_idx[0]
        ].date_time.utc_time_offset
        date = tz_formatted_string(start, utc_time_offset, self.parent.date_format)

        ptext = (
            "<font size = 10> <b>"
            + self.tr("Measurement Date")
            + ":</b> {}</font>".format(date)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 2.8 * inch, self.height - y * inch)

        # Measurement Number
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Measurement Number")
            + ":</b> {}</font>".format(self.parent.meas.meas_number)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 5.2 * inch, self.height - y * inch)

        # Line 4
        y = 1.25

        # Discharge
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Discharge")
            + ":</b> {:8} </font>".format(
                self.parent.q_digits(
                    self.discharge["total_mean"] * self.parent.units["Q"]
                )
            )
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 0.6 * inch, self.height - y * inch)

        # Stage
        if np.isnan(self.parent.meas.stage_meas_m):
            stage_mean = ""
        else:
            stage_mean = "{:.2f}".format(
                self.parent.meas.stage_meas_m * self.parent.units["L"]
            )
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Stage")
            + ":</b> {} </font>".format(stage_mean)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 2.4 * inch, self.height - y * inch)

        # User Rating
        ptext = (
            "<font size = 10><b>"
            + self.tr("User Rating")
            + ":</b> {} </font>".format(self.parent.meas.user_rating)
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 3.4 * inch, self.height - y * inch)

        # Processed
        ptext = (
            "<font size = 10> <b>"
            + self.tr("Processed")
            + ":</b> {}</font>".format(
                datetime.now().strftime(self.parent.date_format + " %H:%M:%S")
            )
        )
        p = Paragraph(ptext, self.styles["Normal"])
        p.wrapOn(page, self.width, self.height)
        p.drawOn(page, 5.2 * inch, self.height - y * inch)

    def top_table(self):
        """Create the top table consisting of 3 columns

        Returns
        -------
        table: Table
            Object of Table
        """

        # Build table data list
        data = [
            [
                self.measurement_information(),
                self.discharge_summary(),
                self.uncertainty(),
            ],
        ]

        # Create and style table
        table = Table(data, colWidths=None, rowHeights=None)
        table.setStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VAlIGN", (0, 1), (-1, 1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
        return table

    def discharge_summary(self):
        """Create discharge summary table.

        Returns
        -------
        q_summary_table: Table
            Object of Table
        """

        meas = self.parent.meas

        # Data prep

        trans_prop = meas.compute_measurement_properties(meas)

        nav_reference = meas.current_settings()["NavRef"]

        discharge = "{}".format(
            self.parent.q_digits(self.discharge["total_mean"] * self.parent.units["Q"])
        )

        if np.isnan(meas.stage_start_m):
            stage_start = ""
        else:
            stage_start = "{:.2f}".format(meas.stage_start_m * self.parent.units["L"])

        if np.isnan(meas.stage_end_m):
            stage_end = ""
        else:
            stage_end = "{:.2f}".format(meas.stage_end_m * self.parent.units["L"])

        if np.isnan(meas.stage_meas_m):
            stage_mean = ""
        else:
            stage_mean = "{:.2f}".format(meas.stage_meas_m * self.parent.units["L"])

        if meas.uncertainty is None or np.isnan(meas.uncertainty.cov):
            q_cov = self.tr("N/A")
        else:
            q_cov = "{:5.2f}".format(meas.uncertainty.cov)

        top_q = "{:.2f}".format(
            (self.discharge["top_mean"] / self.discharge["total_mean"]) * 100
        )
        measured_q = "{:.2f}".format(
            (self.discharge["mid_mean"] / self.discharge["total_mean"]) * 100
        )
        bottom_q = "{:.2f}".format(
            (self.discharge["bot_mean"] / self.discharge["total_mean"]) * 100
        )

        left = (self.discharge["left_mean"] / self.discharge["total_mean"]) * 100
        if np.isnan(left):
            left_q = self.tr("N/A")
        else:
            left_q = "{:5.2f}".format(left)

        right = (self.discharge["right_mean"] / self.discharge["total_mean"]) * 100
        if np.isnan(right):
            right_q = self.tr("N/A")
        else:
            right_q = "{:5.2f}".format(right)

        value = (self.discharge["int_cells_mean"] / self.discharge["total_mean"]) * 100
        if np.isnan(value):
            invalid_cells = self.tr("N/A")
        else:
            invalid_cells = "{:5.2f}".format(value)

        value = (
            self.discharge["int_ensembles_mean"] / self.discharge["total_mean"]
        ) * 100
        if np.isnan(value):
            invalid_ens = self.tr("N/A")
        else:
            invalid_ens = "{:5.2f}".format(value)

        transect_id = meas.checked_transect_idx[0]
        start = meas.transects[transect_id].date_time.start_serial_time
        utc_time_offset = meas.transects[transect_id].date_time.utc_time_offset
        start_time = tz_formatted_string(start, utc_time_offset, "%H:%M:%S")


        transect_id = meas.checked_transect_idx[-1]
        end = meas.transects[transect_id].date_time.end_serial_time
        utc_time_offset = meas.transects[transect_id].date_time.utc_time_offset
        end_time = tz_formatted_string(end, utc_time_offset, "%H:%M:%S")

        duration = "{:.1f}".format(meas.measurement_duration(self.parent.meas))

        top_extrap = meas.transects[meas.checked_transect_idx[-1]].extrap.top_method
        bottom_extrap = meas.transects[meas.checked_transect_idx[-1]].extrap.bot_method
        exponent = "{:.4f}".format(
            meas.transects[meas.checked_transect_idx[-1]].extrap.exponent
        )
        # extrap = "{}/{}/{:.4f}".format(top_extrap, bottom_extrap, exponent)

        mean_boat_speed = "{:.3f}".format(
            trans_prop["avg_boat_speed"][-1] * self.parent.units["V"]
        )

        # Build table data
        data = [
            [self.tr("Discharge Summary"), ""],
            [
                self.tr("Discharge") + " {}:".format(self.parent.units["label_Q"]),
                discharge,
            ],
            [self.tr("Navigation Ref.") + ":", nav_reference],
            [self.tr("Total Duration") + " (s):", duration],
            [self.tr("Time Zone") + ":", meas.time_zone],
            [self.tr("Start Time") + ":", start_time],
            [self.tr("End Time") + ":", end_time],
            [self.tr("Stage Start") + ":", stage_start],
            [self.tr("Stage End") + ":", stage_end],
            [self.tr("Mean Stage") + ":", stage_mean],
            [
                self.tr("Mean Boat Speed")
                + " {}:".format(self.parent.units["label_V"]),
                mean_boat_speed,
            ],
            [self.tr("Top Extrap") + ":", top_extrap],
            [self.tr("Bottom Extrap") + ":", bottom_extrap],
            [self.tr("Extrap Exponent") + ":", exponent],
            [self.tr("Discharg COV") + " (%): ", q_cov],
            [self.tr("Top Q") + " (%): ", top_q],
            ["Measured Q (%): ", measured_q],
            [self.tr("Left Q") + " (%): ", left_q],
            ["Right Q (%): ", right_q],
            [self.tr("Bottom Q") + " (%): ", bottom_q],
            [self.tr("Invalid Cells Q") + " (%): ", invalid_cells],
            [self.tr("Invalid Ensembles Q") + " (%): ", invalid_ens],
        ]

        # Create and style table
        q_summary_table = Table(
            data, colWidths=[1.7 * inch, 0.65 * inch], rowHeights=None
        )
        q_summary_table.setStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("FONT", (0, 0), (0, 0), "Helvetica-Bold", 10),
                ("SPAN", (0, 0), (1, 0)),
                ("LINEBELOW", (0, 0), (1, 0), 1, colors.black),
                ("LINEBELOW", (0, 12), (1, 12), 1, colors.black),
                ("VAlIGN", (0, 0), (-1, 1), "TOP")
                
            ]
        )

        return q_summary_table

    def measurement_information(self):
        """Creates the measurement information table.

        Returns
        -------
        meas_info_table: Table
            Object of Table
        """

        meas = self.parent.meas
        first_id = meas.checked_transect_idx[0]

        freq = meas.transects[first_id].adcp.frequency_khz
        if isinstance(freq, float) or isinstance(freq, int):
            freq = freq
        elif isinstance(freq, np.ndarray):
            freq = self.tr("Multi")
        else:
            freq = freq[0]

        # Data prep
        user_temp = meas.ext_temp_chk["user"]
        if np.isnan(user_temp):
            user_temp = ""

        adcp_temp = meas.ext_temp_chk["adcp"]
        if np.isnan(adcp_temp):
            adcp_temperature = np.array([])
            for idx in meas.checked_transect_idx:
                adcp_temperature = np.append(adcp_temperature, meas.transects[
                    idx].sensors.temperature_deg_c.internal.data)
            adcp_temp = "{:.1f}".format(np.nanmean(adcp_temperature))

        if meas.qa.depths["draft"]:
            draft = "Varies"
        else:
            depth_selected = getattr(meas.transects[first_id].depths, meas.transects[first_id].depths.selected)
            draft = "{:.3f}".format(depth_selected.draft_use_m * self.parent.units["L"])

        if len(meas.system_tst) == 0:
            system_test = self.tr("None")
        elif meas.system_tst[-1].result["sysTest"]["n_failed"]:
            system_test = self.tr("Failed")
        else:
            system_test = self.tr("Passed")

        # Compass cal / eval
        if meas.transects[first_id].adcp.manufacturer == "SonTek":
            evals = meas.compass_cal
        else:
            evals = meas.compass_eval

        if len(meas.compass_cal) == 0 and len(meas.compass_eval) == 0:
            compass = self.tr("None")
        elif len(evals) > 0:
            if type(evals[-1].result["compass"]["error"]) == str:
                compass = evals[-1].result["compass"]["error"]
            else:
                compass = "{:2.2f}".format(evals[-1].result["compass"]["error"])
        else:
            compass = self.tr("Cal")

        # MB test type
        n_tests = len(meas.mb_tests)
        if n_tests > 0:
            selected_idx = [
                i for (i, val) in enumerate(meas.mb_tests) if val.selected is True
            ]
            if len(selected_idx) >= 1:
                mb_test_type = meas.mb_tests[selected_idx[0]].type
            else:
                mb_test_type = meas.mb_tests[-1].type

            # Max moving bed
            percent_mb = []
            mb_duration = 0
            quality = []
            for idx in selected_idx:
                percent_mb.append(meas.mb_tests[idx].percent_mb)
                mb_duration = mb_duration + meas.mb_tests[idx].duration_sec
                quality.append(meas.mb_tests[idx].test_quality)
            if len(selected_idx) >= 1:
                max_mb_per = "{:.2f}".format(np.nanmax(np.array(percent_mb)))
            else:
                quality = [meas.mb_tests[-1].test_quality]
                max_mb_per = ""
            quality = list(set(quality))
            if len(quality) > 1:
                quality = self.tr("Varied")
            elif len(quality) == 1:
                quality = quality[0]
            else:
                quality = ""

            # Moving-bed messages
            mb_messages = ""
            for test in meas.mb_tests:
                test_file = test.transect.file_name[:-4]
                if len(test.messages) > 0:
                    mb_messages = mb_messages + test_file + ": "
                    for message in test.messages:
                        mb_messages = mb_messages + message
                mb_messages = mb_messages + ";"

            # Moving-bed percent correction
            per_correction = "{:.2f}".format(
                (
                    (self.discharge["total_mean"] / self.discharge["uncorrected_mean"])
                    - 1
                )
                * 100
            )
        else:
            mb_test_type = self.tr("None")
            quality = self.tr("N/A")
            mb_duration = 0
            max_mb_per = self.tr("N/A")
            per_correction = "0"

        # Build table data
        data = [
            [self.tr("Field Crew") + ":", Paragraph(meas.persons, self.styles["BodyText"])],
            [self.tr("Processed By") + ":", getpass.getuser()],
            [self.tr("Software") + ":", self.parent.version.split(" ")[0]],
            [self.tr("Version") + ":", self.parent.version.split(" ")[1]],
            [self.tr("ADCP"), ""],
            [self.tr("Manufacturer") + ":", meas.transects[first_id].adcp.manufacturer],
            [self.tr("Model") + ":", meas.transects[first_id].adcp.model],
            [self.tr("Serial Number") + ":", meas.transects[first_id].adcp.serial_num],
            [self.tr("Firmware") + ":", meas.transects[first_id].adcp.firmware],
            [self.tr("Frequency (kHz)") + ":", freq],
            [self.tr("Premeasurement"), ""],
            [self.tr("W. Temp.") + " (C):", user_temp],
            [self.tr("W. Temp. ADCP") + " (C):", adcp_temp],
            [self.tr("ADCP Draft") + "{}:".format(self.parent.units["label_L"]), draft],
            [self.tr("System Test") + ":", system_test],
            [self.tr("Compass Cal/Eval") + ":", compass],
            [
                self.tr("Magnetic Variaton") + ":",
                "{:.2f}".format(meas.transects[
                                    first_id].sensors.heading_deg.internal.mag_var_deg),
            ],
            [self.tr("MovBed Test Type") + ":", mb_test_type],
            [self.tr("MovBed Test Quality") + ":", quality],
            [self.tr("MovBed Test Dur.") + "(s):", "{:.1f}".format(mb_duration)],
            [self.tr("Avg MovBed") + " (%):", max_mb_per],
            [self.tr("Q Correction") + " (%):", per_correction],
        ]

        # Create and style table
        meas_info_table = Table(
            data, colWidths=[1.4 * inch, 0.7 * inch], rowHeights=None
        )
        meas_info_table.setStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("LINEABOVE", (0, 4), (1, 4), 1, colors.black),
                ("LINEBELOW", (0, 4), (1, 4), 1, colors.black),
                ("FONT", (0, 4), (0, 4), "Helvetica-Bold", 10),
                ("SPAN", (0, 4), (1, 4)),
                ("LINEABOVE", (0, 10), (1, 10), 1, colors.black),
                ("LINEBELOW", (0, 10), (1, 10), 1, colors.black),
                ("FONT", (0, 10), (0, 10), "Helvetica-Bold", 10),
                ("SPAN", (0, 10), (1, 10)),
                ("VAlIGN", (0, 0), (-1, 1), "TOP")
            ]
        )

        return meas_info_table

    def uncertainty(self):
        """Creates uncertainty table.

        Returns
        -------
        uncertainty_table: Table
            Object of Table
        """

        meas = self.parent.meas
        trans_prop = meas.compute_measurement_properties(meas)

        mean_velocity = "{:.3f}".format(
            trans_prop["avg_water_speed"][-1] * self.parent.units["V"]
        )
        max_velocity = "{:.3f}".format(
            trans_prop["max_water_speed"][-1] * self.parent.units["V"]
        )
        mean_depth = "{:.3f}".format(
            trans_prop["avg_depth"][-1] * self.parent.units["L"]
        )
        max_depth = "{:.3f}".format(
            trans_prop["max_depth"][-1] * self.parent.units["L"]
        )
        area = "{:.3f}".format(trans_prop["area"][-1] * self.parent.units["A"])
        width = "{:.3f}".format(trans_prop["width"][-1] * self.parent.units["L"])

        if np.isnan(trans_prop["width_cov"][-1]):
            width_cov = self.tr("N/A")
        else:
            width_cov = "{:5.2f}".format(trans_prop["width_cov"][-1])

        if np.isnan(trans_prop["area_cov"][-1]):
            area_cov = self.tr("N/A")
        else:
            area_cov = "{:5.2f}".format(trans_prop["area_cov"][-1])

        if self.parent.run_oursin:
            u_method = self.tr("Oursin")
        else:
            u_method = self.tr("QRev")

        # Build table data
        data = [
            [self.tr("Cross Section"), ""],
            [
                self.tr("Mean Velocity") + " {}:".format(self.parent.units["label_V"]),
                mean_velocity,
            ],
            [
                self.tr("Max. Velocity") + " {}:".format(self.parent.units["label_V"]),
                max_velocity,
            ],
            [
                self.tr("Mean Depth") + " {}:".format(self.parent.units["label_L"]),
                mean_depth,
            ],
            [
                self.tr("Max. Depth") + " {}:".format(self.parent.units["label_L"]),
                max_depth,
            ],
            [self.tr("Width") + " {}:".format(self.parent.units["label_L"]), width],
            [self.tr("Width COV") + " (%): ", width_cov],
            [self.tr("Area") + " {}:".format(self.parent.units["label_A"]), area],
            [self.tr("Area COV") + " (%): ", area_cov],
            [self.tr("Uncertainty"), ""],
            [self.tr("Uncertainty Method") + ":", u_method],
            [self.uncertainty_fig(), ""],
        ]

        # Create style list
        style_list = [
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (1, 0), 1, colors.black),
            ("FONT", (0, 0), (0, 0), "Helvetica-Bold", 10),
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 9), (1, 9), 1, colors.black),
            ("LINEBELOW", (0, 9), (1, 9), 1, colors.black),
            ("FONT", (0, 9), (0, 9), "Helvetica-Bold", 10),
            ("SPAN", (0, 9), (1, 9)),
            ("SPAN", (0, 11), (1, 11)),
            ("ALIGN", (0, 11), (1, 11), "RIGHT"),
        ]

        # Create and style table
        uncertainty_table = Table(
            data, colWidths=[1.5 * inch, 1.4 * inch], rowHeights=None
        )
        uncertainty_table.setStyle(style_list)

        return uncertainty_table

    def uncertainty_fig(self):
        """Generates lollipop plot of uncertainty contributions"""

        u_canvas = MplCanvas(parent=None, width=4, height=3.23, dpi=300)

        # Initialize the figure and assign to the canvas
        u_fig = ULollipopPlot(canvas=u_canvas)
        # Create the figure with the specified data
        u_fig.create(meas=self.parent.meas)
        u_fig.fig.subplots_adjust(
            left=0.35, bottom=0.15, right=0.97, top=0.93, wspace=0.1, hspace=0
        )
        return self.fig2image(u_fig.fig, 3.0)

    def discharge_plot(self):
        """Generates discharge time series plot for the main tab."""

        # Create the canvas
        q_canvas = MplCanvas(parent=None, width=6, height=4, dpi=300)

        # Initialize the figure and assign to the canvas
        q_fig = DischargeTS(canvas=q_canvas)
        # Create the figure with the specified data
        q_fig.create(
            meas=self.parent.meas,
            checked=self.parent.meas.checked_transect_idx,
            transect_idx=None,
            units=self.parent.units,
        )
        q_fig.fig.subplots_adjust(
            left=0.13, bottom=0.2, right=0.98, top=0.98, wspace=0.1, hspace=0
        )
        return self.fig2image(q_fig.fig, 6)

    def extrap_plot(self):
        """Generates extrapolation plot."""

        extrap_canvas = MplCanvas(parent=None, width=4, height=4, dpi=300)
        extrap_fig = ExtrapPlot(canvas=extrap_canvas)
        extrap_fig.create(
            meas=self.parent.meas,
            checked=self.parent.meas.checked_transect_idx,
            auto=True,
        )
        return self.fig2image(extrap_fig.fig, 4)

    def contour_plot(self, idx):
        """Generates a color contour plot for transect idx.

        Parameters
        idx: int
            Index of transect to plot.

        """
        transect = self.parent.meas.transects[idx]
        contour_canvas = MplCanvas(parent=None, width=7, height=2, dpi=300)

        contour_fig = AdvGraphs(canvas=contour_canvas)
        if self.parent.plot_extrapolated:
            contour_fig.create_main_contour(
                transect=transect,
                units=self.parent.units,
                color_map=self.parent.color_map,
                x_axis_type=self.parent.x_axis_type,
                discharge=self.parent.meas.discharge[idx],
            )
        else:
            contour_fig.create_main_contour(
                transect=transect,
                units=self.parent.units,
                color_map=self.parent.color_map,
                x_axis_type=self.parent.x_axis_type,
            )
        contour_fig.ax[0].set_title(transect.file_name)
        contour_fig.fig.subplots_adjust(
            left=0.13, bottom=0.2, right=0.80, top=0.87, wspace=0.1, hspace=0
        )
        return self.fig2image(contour_fig.fig, 7)

    @staticmethod
    def is_nan(data_in):
        """Format data while checking for nan

        Returns
        -------
        : str
        """

        if np.isnan(data_in):
            return ""

        return f"{data_in * 100:.2f}"

    def qa_messages(self):
        """Create table for QA messages.

        Returns
        -------
        messages_table: Table
            Object of Table
        """
        data = [["Automated QA Messages:"]]

        qa_check_keys = ["bt_vel", "compass", "depths", "edges", "extrapolation",
            "gga_vel", "movingbed", "system_tst", "temperature", "transects", "user",
            "vtg_vel", "w_vel", ]
        messages = self.parent.combine_selected_qa_messages(qa_check_keys)

        # Create each message as a list appended to data
        if len(messages) > 0:
            warning = []
            caution = []
            for line in messages:
                if line[1] == 1:
                    warning.append(line[0])
                else:
                    caution.append(line[0])

            data.append([Paragraph("<u> WARNINGS</u>")])
            style = ParagraphStyle(
                name="Normal", bulletIndent=20, leftIndent=35, bulletFontSize=14
            )
            for line in warning:
                data.append([Paragraph("<bullet>&bull;</bullet>" + line, style=style)])

            data.append([Paragraph("")])
            data.append([Paragraph("<u> Cautions</u>")])
            for line in caution:
                data.append([Paragraph("<bullet>&bull;</bullet>" + line, style=style)])

        # Create and style table
        messages_table = Table(
            data, colWidths=7.3 * inch, rowHeights=None, repeatRows=1
        )
        messages_table.setStyle([("FONT", (0, 0), (0, 0), "Helvetica-Bold", 10)])

        return messages_table

    def comments(self):
        """Create comments table.

        Returns
        -------
        comments_table: Table
            Object of Table
        """

        data = [["Comments:"]]

        # Create each comment as a list appended to data
        if len(self.parent.meas.comments) > 0:
            for line in self.parent.meas.comments:
                data.append([Paragraph("<bullet>&bull;</bullet>" + line)])
        else:
            data.append("")

        # Create and style table
        comments_table = Table(
            data, colWidths=7.3 * inch, rowHeights=None, repeatRows=1
        )
        comments_table.setStyle([("FONT", (0, 0), (0, 0), "Helvetica-Bold", 10)])

        return comments_table

    def file_name_table(self):
        """Creates a table of ID numbers to filename"""

        data = [
            [
                self.label(self.tr("ID"), bold=True, center=False),
                self.label(self.tr("File Name"), bold=True, center=False),
            ]
        ]
        meas = self.parent.meas
        for idx in meas.checked_transect_idx:
            file_name = meas.transects[idx].file_name
            row = [idx, file_name]
            data.append(row)

        # Create style list
        style_list = [
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
            ("ALIGN", (0, 1), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
        ]

        # Create and style table
        file_table = Table(
            data,
            colWidths=[0.3 * inch, 5 * inch],
            rowHeights=None,
            repeatRows=1,
            hAlign="LEFT",
        )
        table_style = TableStyle(style_list)
        file_table.setStyle(table_style)

        return file_table

    def summary_table_1(self):
        """Create 1st summary table containing discharge.

        Returns
        -------
        table_1: Table
            Object of Table
        """

        # Column labels
        data = [
            [
                self.label(self.tr("Transect") + "<br/>" + self.tr("ID"), bold=True),
                self.label(self.tr("Start") + "<br/>" + self.tr("Edge"), bold=True),
                self.label(self.tr("Start Time"), bold=True),
                self.label(self.tr("End Time"), bold=True),
                self.label(self.tr("Duration") + "<br/>(sec)", bold=True),
                self.label(
                    self.tr("Top Q") + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Middle Q")
                    + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Bottom Q")
                    + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Left Q") + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Right Q") + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Total Q") + "<br/>{}".format(self.parent.units["label_Q"]),
                    bold=True,
                ),
            ]
        ]

        meas = self.parent.meas

        total_duration = 0
        for idx in meas.checked_transect_idx:
            transect = meas.transects[idx]
            q = meas.discharge[idx]

            filename = idx
            start_edge = transect.start_edge
            start = transect.date_time.start_serial_time
            utc_time_offset = transect.date_time.utc_time_offset
            start_time = tz_formatted_string(start, utc_time_offset, "%H:%M:%S")

            end = transect.date_time.end_serial_time
            utc_time_offset = transect.date_time.utc_time_offset
            end_time = tz_formatted_string(end, utc_time_offset, "%H:%M:%S")

            duration = "{:5.1f}".format(transect.date_time.transect_duration_sec)

            top_q = "{:8}".format(self.parent.q_digits(q.top * self.parent.units["Q"]))
            middle_q = "{:8}".format(
                self.parent.q_digits(q.middle * self.parent.units["Q"])
            )
            bottom_q = "{:8}".format(
                self.parent.q_digits(q.bottom * self.parent.units["Q"])
            )
            left_q = "{:8}".format(
                self.parent.q_digits(q.left * self.parent.units["Q"])
            )
            right_q = "{:8}".format(
                self.parent.q_digits(q.right * self.parent.units["Q"])
            )
            total_q = "{:8}".format(
                self.parent.q_digits(q.total * self.parent.units["Q"])
            )

            row = [
                filename,
                start_edge,
                start_time,
                end_time,
                duration,
                top_q,
                middle_q,
                bottom_q,
                left_q,
                right_q,
                total_q,
            ]
            data.append(row)
            total_duration = total_duration + transect.date_time.transect_duration_sec
        top_q = "{:8}".format(
            self.parent.q_digits(self.discharge["top_mean"] * self.parent.units["Q"])
        )
        middle_q = "{:8}".format(
            self.parent.q_digits(self.discharge["mid_mean"] * self.parent.units["Q"])
        )
        bottom_q = "{:8}".format(
            self.parent.q_digits(self.discharge["bot_mean"] * self.parent.units["Q"])
        )
        left_q = "{:8}".format(
            self.parent.q_digits(self.discharge["left_mean"] * self.parent.units["Q"])
        )
        right_q = "{:8}".format(
            self.parent.q_digits(self.discharge["right_mean"] * self.parent.units["Q"])
        )
        total_q = "{:8}".format(
            self.parent.q_digits(self.discharge["total_mean"] * self.parent.units["Q"])
        )
        total_duration = "{:.1f}".format(total_duration)

        row = [
            "",
            "",
            "",
            "",
            total_duration,
            top_q,
            middle_q,
            bottom_q,
            left_q,
            right_q,
            total_q,
        ]

        data.append(row)

        # Create style list
        style_list = [
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
            ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
            ("NOSPLIT", (0, 0), (-1, -1)),
        ]

        # Create and style table
        table_1 = Table(data, colWidths=None, rowHeights=None, repeatRows=1)
        table_style = TableStyle(style_list)
        table_1.setStyle(table_style)

        return table_1

    def summary_table_2(self):
        """Create 2nd summary table containing other station characteristics

        Returns
        -------
        table_2: Table
            Object of Table
        """

        # Column labels
        data = [
            [
                self.label(self.tr("Transect") + "<br/>" + self.tr("ID"), bold=True),
                self.label(self.tr("Start") + "<br/>" + self.tr("Edge"), bold=True),
                self.label(
                    self.tr("Left")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("Type"),
                    bold=True,
                ),
                self.label(
                    self.tr("Left")
                    + "<br/>"
                    + self.tr("Dist.")
                    + "<br/>{}".format(self.parent.units["label_L"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Left")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("# Ens."),
                    bold=True,
                ),
                self.label(
                    self.tr("Left")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("Coeff."),
                    bold=True,
                ),
                self.label(
                    self.tr("Right")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("Type"),
                    bold=True,
                ),
                self.label(
                    self.tr("Right")
                    + "<br/>"
                    + self.tr("Dist")
                    + "<br/>{}".format(self.parent.units["label_L"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Right")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("# Ens."),
                    bold=True,
                ),
                self.label(
                    self.tr("Right")
                    + "<br/>"
                    + self.tr("Edge")
                    + "<br/>"
                    + self.tr("Coeff."),
                    bold=True,
                ),
            ]
        ]

        meas = self.parent.meas
        for idx in meas.checked_transect_idx:
            transect = meas.transects[idx]
            q = meas.discharge[idx]

            file_name = idx
            start_edge = transect.start_edge

            left_type = transect.edges.left.type
            left_dist = "{:.2f}".format(
                transect.edges.left.distance_m * self.parent.units["L"]
            )
            left_ens = "{:.0f}".format(q.left_idx.size)
            if transect.edges.left.type == "Triangular":
                left_coef = "0.3535"
            elif transect.edges.left.type == "Rectangular":
                left_coef = "0.91"
            elif transect.edges.left.type == "Custom":
                left_coef = "{:1.4f}".format(transect.edges.left.cust_coef)
            else:
                left_coef = ""
            left_coef = left_coef

            right_type = transect.edges.right.type
            right_dist = "{:.2f}".format(
                transect.edges.right.distance_m * self.parent.units["L"]
            )
            right_ens = "{:.0f}".format(q.right_idx.size)
            if transect.edges.right.type == "Triangular":
                right_coef = "0.3535"
            elif transect.edges.right.type == "Rectangular":
                right_coef = "0.91"
            elif transect.edges.right.type == "Custom":
                right_coef = "{:1.4f}".format(transect.edges.right.cust_coef)
            else:
                right_coef = ""

            row = [
                file_name,
                start_edge,
                left_type,
                left_dist,
                left_ens,
                left_coef,
                right_type,
                right_dist,
                right_ens,
                right_coef,
            ]
            data.append(row)
        # Create and style table
        table_2 = Table(
            data, colWidths=None, rowHeights=None, repeatRows=1, spaceBefore=25
        )
        table_2.setStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
                ("NOSPLIT", (0, 0), (-1, -1)),
            ]
        )
        return table_2

    def summary_table_3(self):
        """Create 3rd summary table containing details.

        Returns
        -------
        table_1: Table
            Object of Table
        """

        # Column labels
        data = [
            [
                self.label(self.tr("Transect") + "<br/>" + self.tr("ID"), bold=True),
                self.label(
                    self.tr("Width") + "<br/>{}".format(self.parent.units["label_L"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Area") + "<br/>{}".format(self.parent.units["label_A"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Wetted")
                    + "<br/>"
                    + self.tr("Perimeter")
                    + "<br/>{}".format(self.parent.units["label_L"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Hydraulic")
                    + "<br/>"
                    + self.tr("Radius")
                    + "<br/>{}".format(self.parent.units["label_L"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Avg. Boat")
                    + "<br/>"
                    + self.tr("Speed")
                    + "<br/>{}".format(self.parent.units["label_V"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Course Made") + "<br/>" + self.tr("Good (deg)"),
                    bold=True,
                ),
                self.label(
                    self.tr("Q/A") + "<br/>{}".format(self.parent.units["label_V"]),
                    bold=True,
                ),
                self.label(
                    self.tr("Avg. Water") + "<br/>" + self.tr("Direction (deg)"),
                    bold=True,
                ),
            ]
        ]

        meas = self.parent.meas
        trans_prop = meas.compute_measurement_properties(meas)

        for idx in meas.checked_transect_idx:
            filename = idx

            width = "{:.2f}".format(trans_prop["width"][idx] * self.parent.units["L"])
            area = "{:.2f}".format(trans_prop["area"][idx] * self.parent.units["A"])
            wetted_perimeter = "{:.2f}".format(
                trans_prop["wetted_perimeter"][idx] * self.parent.units["L"]
            )
            hydraulic_radius = "{:.2f}".format(
                trans_prop["hydraulic_radius"][idx] * self.parent.units["L"]
            )
            avg_boat_speed = "{:.2f}".format(
                trans_prop["avg_boat_speed"][idx] * self.parent.units["V"]
            )
            avg_boat_course = "{:.2f}".format(trans_prop["avg_boat_course"][idx])
            avg_water_speed = "{:.2f}".format(
                trans_prop["avg_water_speed"][idx] * self.parent.units["V"]
            )
            avg_water_dir = "{:.2f}".format(trans_prop["avg_water_dir"][idx])

            row = [
                filename,
                width,
                area,
                wetted_perimeter,
                hydraulic_radius,
                avg_boat_speed,
                avg_boat_course,
                avg_water_speed,
                avg_water_dir,
            ]
            data.append(row)

        # Create style list
        style_list = [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 1, colors.black),
            ("NOSPLIT", (0, 0), (-1, -1)),
        ]

        # Create and style table
        table_1 = Table(data, colWidths=None, rowHeights=None, repeatRows=1)
        table_style = TableStyle(style_list)
        table_1.setStyle(table_style)

        return table_1

    def label(self, txt, size=9, bold=False, center=True):
        """Use HTML to format labels

        Returns
        -------
        : Paragraph
            Object of Paragraph
        """
        if bold:
            if center:
                return Paragraph(
                    "<para align=center><font size={size}><b>{txt}</b></font></para>".format(
                        size=size, txt=txt
                    ),
                    self.styles["Normal"],
                )
            else:
                return Paragraph(
                    "<para><font size={size}><b>{txt}</b></font></para>".format(
                        size=size, txt=txt
                    ),
                    self.styles["Normal"],
                )

        return Paragraph(
            "<para align=center><font size={size}>{txt}</font></para>".format(
                size=size, txt=txt
            ),
            self.styles["Normal"],
        )

    @staticmethod
    def fig2image(fig, width):
        """Convert figure to a ReportLab Image

        Parameters
        ----------
        fig: Figure
            Object of Figure
        width: float
            Width of figure in inches

        Returns
        -------
        : Image
            Object of Image
        """

        # Save fig to internal memory
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300)
        buf.seek(0)

        # Scale image to specified width
        x, y = fig.get_size_inches()
        ratio = width / x

        return Image(buf, x * ratio * inch, y * ratio * inch)

    def save(self):
        """Build and save pdf file"""

        self.doc.build(
            self.elements,
            onFirstPage=self.header,
            onLaterPages=self.header,
            canvasmaker=PageNumCanvas,
        )

    def create(self):
        """Create pdf documents using flowtables."""

        self.elements.append(self.top_table())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.qa_messages())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.comments())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.file_name_table())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.summary_table_1())
        self.elements.append(self.summary_table_2())
        self.elements.append(self.summary_table_3())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.discharge_plot())
        self.elements.append(Spacer(1, 14))
        self.elements.append(self.extrap_plot())
        for idx in self.parent.meas.checked_transect_idx:
            self.elements.append(Spacer(1, 14))
            self.elements.append(self.contour_plot(idx))
        self.save()


class PageNumCanvas(canvas.Canvas):
    """Creates page x of pages text for header."""

    def __init__(self, *args, **kwargs):
        """Constructor with variable parameters."""

        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self):
        """On a page break add information to list."""

        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add the page number to each page (page x of y)."""

        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Add the page number.

        Parameters
        ----------
        page_count: int
            Total number of pages
        """

        page = "%s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 10)
        width, height = self._pagesize
        self.drawRightString(width - 0.5 * inch, height - 0.5 * inch, page)
