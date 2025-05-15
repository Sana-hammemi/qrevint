import numpy as np
import copy
import numba

from scipy import integrate

from surfveltools import probconcept as pc
from surfveltools.normdata import NormDataSurfVelTool
from surfveltools.common_functions import compute_power_coefficient
from qrev.Classes.FitData import FitData
from qrev.Classes.SelectFit import SelectFit


# Todo: Add option to update transects and apply custom settings like in SVT.


class SurfaceVelocity(object):
    def __init__(self, measurement=None):
        """Initialize object."""

        # Allowing method selection as an option to add future methods.
        # type can be transect_mean or smba. If smba, then user would need
        # to select the smba to use or the smba with the max velocity would
        # be used....
        # Todo: Think more about the implementation of settings.
        # setting arbitrary 'loaded_filename' due to SVT parent/child calls.
        self.loaded_filename = ""
        self.settings = {"method": "Entropy", "type": "transect_mean"}

        # type can be transect_mean or smba
        self.measurement = measurement

        if measurement is not None:
            self.data = self.parse_data(measurement)
        else:
            self.data = {}

        self.pc_fit = {}

    @staticmethod
    def compute_alpha(extrap, data_summary):
        """Update the Probability concept fit.

        Parameters:
            extrap: Extrap
            data_summary: dict

        Returns:
            results: dict"""

        results = {}

        point_data = data_summary["point_data"]
        uncert = np.zeros(data_summary["point_data"].shape[0])
        use_uncert = False

        try:
            if np.argmax(point_data[:, 1]) == 0.0:
                # presume umax is at surface
                h = 0.0
            else:
                h = (
                    data_summary["meas_total_depth"]
                    - point_data[np.argmax(point_data[:, 1]), 0]
                )

            clean_pnt = point_data[~np.isnan(point_data).any(axis=1)]

            pc_fit = pc.ProbConceptFit()
            pc_fit.populate_velocity_profile_data(
                depths=clean_pnt[:, 0],
                velocities=clean_pnt[:, 1],
                uncertainties=uncert,
                max_velocity=data_summary["meas_max_velocity"],
                max_depth=data_summary["meas_total_depth"],
                h=h,
                use_uncertainty=use_uncert,
            )

            # Compute alpha coef from the PC method model result (Issue #27)
            results["umean_pc"] = (
                1
                / data_summary["meas_total_depth"]
                * integrate.simpson(pc_fit.fit_velocities, pc_fit.fit_depths)
            )
            results["alpha_from_pc"] = results["umean_pc"] / pc_fit.max_velocity

            # alpha equation only good for power law.
            if extrap.top_method == "Power":
                results["alpha_from_extrap"] = 1 / (1 + extrap.exponent)
            else:
                results["alpha_from_extrap"] = np.nan

            # # init objects
            # norm_data = NormDataSurfVelTool()
            # extrap_fit = FitData()
            #
            # norm_data.populate_data(self, point_data)
            # extrap_fit.populate_data(norm_data, top="Power", bot="Power",
            #                          method="optimize"
            #                          )
            # extrap_fit.u_units = np.multiply(norm_data.unit_mean, extrap_fit.u)
            # extrap_fit.z_units = np.multiply(extrap_fit.z,
            #                                  norm_data.unit_depth)
            # results['alpha_coef_from_extrap'] = 1 / (1 + extrap_fit.exponent)
            #
            # # Recompute coef for the upper and lower 95% CI
            # low_coef = compute_power_coefficient(extrap_fit.z_units,
            #                                      extrap_fit.u_units,
            #                                      extrap_fit.exponent_95_ci[0])
            # high_coef = compute_power_coefficient(extrap_fit.z_units,
            #                                       extrap_fit.u_units,
            #                                       extrap_fit.exponent_95_ci[1])
            #
            # extrap_fit.u_lower_95_ci = self.compute_confidence_interval(
            #     low_coef, extrap_fit.z_units, extrap_fit.exponent_95_ci[0]
            # )
            # extrap_fit.u_upper_95_ci = self.compute_confidence_interval(
            #     high_coef, extrap_fit.z_units, extrap_fit.exponent_95_ci[1]
            # )
            #
            # # Compute stderr for alhpa coef
            # results['alpha_coef_from_extrap_stderr'] = self.compute_alpha_std(
            #     extrap_fit.exponent_95_ci[0], extrap_fit.exponent_95_ci[1])
            #
            # # Let QRev select a fit, then give normalized results
            # sel_fit = SelectFit()
            # sel_fit.populate_data(norm_data, fit_method="Automatic")
            # sel_fit.u_units = np.multiply(
            #     norm_data.unit_mean, sel_fit.u
            # )
            # sel_fit.u_auto_units = np.multiply(
            #     sel_fit.u_auto, norm_data.unit_mean
            # )
            # sel_fit.z_units = np.multiply(sel_fit.z, norm_data.unit_depth)
            # sel_fit.z_auto_units = np.multiply(sel_fit.z_auto,
            #                                    norm_data.unit_depth
            #                                    )

            results.update(
                {
                    "pc_fit": pc_fit,
                    # 'norm_data': norm_data,
                    # 'extrap_fit': extrap_fit,
                    # 'sel_fit': sel_fit,
                }
            )

        except:
            # Todo Add an error msg to the dict
            pass

        return results

    def parse_data(self, measurement, bounds="Auto"):
        """Iterate through transects computing the probability concept fit.

        Parameters:
            measurement: Measurement
            bounds: tuple
                bounds for y-axis location in meters referenced to the LEW.
        Returns:
            data_summary: dict
        """

        data_summary = {}
        composite = {
            "velocities_all": [],
            "umag_mps": [],
            "max_velocity": [],
            "max_velocity_index": [],
            "depth_ens": [],
            "meas_depths_all": [],
            "point_data": [],
            "meas_max_velocity": [],
            "meas_total_depth": [],
            "depth_all": [],
            "x": [],
            "yaxis_depth": [],
            "yaxis_vel": [],
        }

        if bounds == "Auto":
            y_axis_max, y_axis_min = self.get_idx_range(measurement)
        else:
            y_axis_max = bounds[0]
            y_axis_min = bounds[1]

        max_rows = 0
        for transect in measurement.transects:
            if transect.checked:
                idx = transect.in_transect_idx
                data = {
                    "Type": "Transect",
                }

                boat_track = transect.boat_vel.compute_boat_track(transect=transect)

                x = boat_track["distance_m"]

                # Shift data to account for edge distance
                if transect.start_edge == "Left":
                    data["x"] = x[idx] + transect.edges.left.distance_m
                else:
                    # reference to LEW
                    data["x"] = x[idx] + transect.edges.right.distance_m
                    data["x"] = np.nanmax(x) - x - (0 - np.nanmin(x))

                # set y-axis idx range
                idx_range = np.where(
                    np.logical_and(data["x"] >= y_axis_min, data["x"] <= y_axis_max)
                )[0]

                # Todo we should also return the location from LEW (Y-Axis)
                # find index of max velocity
                # _, _, _, max_velocity_index = (
                #     self.get_velocity_from_transect(
                #     transect.w_vel.u_processed_mps,
                #     transect.w_vel.v_processed_mps,
                #     transect.w_vel.valid_data,
                #     idx))

                data["yaxis_max"] = y_axis_max
                data["yaxis_min"] = y_axis_min

                # Call a second time using the max velocity index
                (
                    meas_velocities_all,
                    umag_mps,
                    max_vel,
                    max_velocity_index,
                ) = self.get_velocity_from_transect(
                    transect.w_vel.u_processed_mps,
                    transect.w_vel.v_processed_mps,
                    transect.w_vel.valid_data,
                    idx_range,
                )

                if meas_velocities_all.shape[0] > max_rows:
                    max_rows = meas_velocities_all.shape[0]

                data.update(
                    {
                        "velocities_all": meas_velocities_all,
                        "umag_mps": umag_mps,
                        "max_velocity": max_vel,
                        "max_velocity_index": max_velocity_index,
                    }
                )

                data.update(self.get_depth_from_transect(transect, idx_range))

                # all_depth = self.get_depth_from_transect(transect, idx)
                # data['yaxis_depth'] = (data['x'][all_depth['max_depth_idx'][0]])

                (
                    point_data,
                    meas_max_velocity,
                    meas_total_depth,
                    depth_all,
                ) = self.prepare_data(
                    data["depth_ens"], data["meas_depths_all"], data["velocities_all"]
                )

                data.update(
                    {
                        "point_data": point_data,
                        "meas_max_velocity": meas_max_velocity,
                        "meas_total_depth": meas_total_depth,
                        "depth_all": depth_all,
                    }
                )

                data.update({"results": self.compute_alpha(transect.extrap, data)})

                composite["velocities_all"].append(data["velocities_all"])
                composite["umag_mps"].append(data["umag_mps"])
                composite["max_velocity"].append(data["max_velocity"])
                composite["max_velocity_index"].append(data["max_velocity_index"])
                composite["depth_ens"].append(data["depth_ens"])
                composite["meas_depths_all"].append(data["meas_depths_all"])
                data_summary[transect.file_name] = copy.deepcopy(data)

        # combine transect lists to create composite dataset.
        composite["velocities_all"] = self.prep_hstack(composite["velocities_all"])
        composite["umag_mps"] = self.prep_hstack(composite["umag_mps"])
        composite["max_velocity"] = np.concatenate(composite["max_velocity"], axis=0)
        composite["depth_ens"] = np.concatenate(composite["depth_ens"], axis=0)
        composite["meas_depths_all"] = self.prep_hstack(composite["meas_depths_all"])
        composite["yaxis_max"] = y_axis_max
        composite["yaxis_min"] = y_axis_min

        point_data, meas_max_velocity, meas_total_depth, depth_all = self.prepare_data(
            composite["depth_ens"],
            composite["meas_depths_all"],
            composite["velocities_all"],
        )

        composite.update(
            {
                "point_data": point_data,
                "meas_max_velocity": meas_max_velocity,
                "meas_total_depth": meas_total_depth,
                "depth_all": depth_all,
            }
        )

        composite.update({"results": self.compute_alpha(transect.extrap, composite)})

        data_summary["Measurment"] = copy.deepcopy(composite)

        # if len(measurement.mb_tests) > 0:
        #     for test in measurement.mb_tests:
        #         transect = test.transect
        #         idx = transect.in_transect_idx
        #         data = {'Type': test.type}
        #         meas_velocities_all, umag_mps, max_vel, max_velocity_index = (
        #             self.get_velocity_from_transect(
        #                 transect.w_vel.u_processed_mps,
        #                 transect.w_vel.v_processed_mps,
        #                 transect.w_vel.valid_data,
        #                 idx))
        #
        #         data.update({'velocities_all': meas_velocities_all,
        #                      'umag_mps': umag_mps,
        #                      'max_velocity': max_vel,
        #                      'max_velocity_index': max_velocity_index,
        #                      })
        #
        #         # Treat loop tests like a transect using the max index to
        #         # parse data
        #         if data['Type'] == 'Loop':
        #             meas_velocities_all, umag_mps, max_vel, max_velocity_index = (
        #                 self.get_velocity_from_transect(
        #                     transect.w_vel.u_processed_mps,
        #                     transect.w_vel.v_processed_mps,
        #                     transect.w_vel.valid_data,
        #                     idx))
        #
        #             data.update({'velocities_all': meas_velocities_all,
        #                          'umag_mps': umag_mps,
        #                          'max_velocity': max_vel,
        #                          'max_velocity_index': max_velocity_index,
        #                          })
        #
        #         data.update(self.get_depth_from_transect(transect, data[
        #             'max_velocity_index']))
        #
        #         point_data, meas_max_velocity, meas_total_depth, depth_all = (
        #             self.prepare_data(data['depth_ens'],
        #                               data['meas_depths_all'],
        #                               data['velocities_all']))
        #
        #         data.update({'point_data': point_data,
        #                      'meas_max_velocity': meas_max_velocity,
        #                      'meas_total_depth': meas_total_depth,
        #                      'depth_all': depth_all,})
        #
        #         data.update({'results': self.compute_alpha(transect, data)})
        #
        #         data_summary[transect.file_name] = copy.deepcopy(data)

        return data_summary

    def get_idx_range(self, meas):
        """Identify range for y-axis.

        Parameters:
            meas: Measurement
        Returns:
            idx: Array
                range in feet for y-axis"""

        y_axis_vel = []

        for transect in meas.transects:
            if transect.checked:
                idx = transect.in_transect_idx

                # find index of max velocity
                _, _, _, max_velocity_index = self.get_velocity_from_transect(
                    transect.w_vel.u_processed_mps,
                    transect.w_vel.v_processed_mps,
                    transect.w_vel.valid_data,
                    idx,
                )

                boat_track = transect.boat_vel.compute_boat_track(transect=transect)

                x = boat_track["distance_m"]

                # Shift data to account for edge distance
                if transect.start_edge == "Left":
                    x = x[transect.in_transect_idx] + transect.edges.left.distance_m
                else:
                    # reference to LEW
                    x = x[transect.in_transect_idx] + transect.edges.right.distance_m
                    x = np.nanmax(x) - x - (0 - np.nanmin(x))

                y_axis_vel.append(x[max_velocity_index][0])

        y_axis_max = np.nanmax(y_axis_vel)
        y_axis_min = np.nanmin(y_axis_vel)

        return y_axis_max, y_axis_min

    @staticmethod
    def prep_hstack(values):
        """Format values of composite dictionary.

        Parameters:
            values: dict
        Returns:
            new_array: Array"""

        max_len = max(transect.shape[0] for transect in values)
        new_data = [
            np.pad(
                transect,
                (0, max_len - transect.shape[0]),
                "constant",
                constant_values=np.nan,
            )
            for transect in values
        ]

        new_array = np.hstack(new_data)

        return new_array

    @staticmethod
    def get_depth_from_transect(transect, idx):
        """Get the depth from the transect data.

        Parameters:
            transect: TransectData
                object to get the depth from
            idx: array

        Returns:
            data: dict
                keys = depth_ens, meas_depths_all
        """

        depths_selected = getattr(transect.depths, transect.depths.selected)
        cell_depth = np.copy(depths_selected.depth_cell_depth_m[:, idx])

        depth_ens = np.copy(depths_selected.depth_processed_m[idx])
        boolean_arr = cell_depth <= depth_ens
        cell_depth[~boolean_arr] = np.nan

        max_depth_idx = [np.nanargmax(depth_ens, axis=0)]

        meas_depths_all = cell_depth

        # bundle depth data into a dictionary
        data = {
            "depth_ens": depth_ens,
            "meas_depths_all": meas_depths_all,
            "max_depth_idx": max_depth_idx,
        }

        return data

    @staticmethod
    def get_velocity_from_transect(u_processed_mps, v_processed_mps, valid_data, idx):
        """Get velocity data from transect or MB test.

        Parameters:
            u_processed_mps: Array
            v_processed_mps: Array
            valid_data: Array
            idx: array
                transect index to get the velocity from
        Returns:
            meas_velocities_all
            umag_mps
            max_vel
            max_velocity_index
        """

        # Get valid transect water velocities
        u = np.copy(u_processed_mps[:, idx])
        v = np.copy(v_processed_mps[:, idx])
        invalid_data = np.logical_not(valid_data[0, :, idx]).T
        u[invalid_data] = np.nan
        v[invalid_data] = np.nan

        # Compute the velocity magnitude in each ensemble
        umag_mps = np.sqrt(u**2 + v**2)

        # Keep output
        meas_velocities_all = umag_mps
        # compute depth average velocity
        max_vel = np.nanmax(umag_mps, axis=0)
        max_velocity_index = [np.nanargmax(max_vel, axis=0)]

        return meas_velocities_all, umag_mps, max_vel, max_velocity_index

    @staticmethod
    def prepare_data(depth_ens, meas_depths_all, velocities_all):
        """Prepare data for the probability concept fit.

        Parameters:
            depth_ens: Array
            meas_depths_all: Array
            velocities_all: Array
        Returns:
            point_data: Array
            meas_max_velocity: Array
            meas_total_depth: Array
            depth_all: Array
        """

        # Get the ensemble averaged-depth and convert to depth relative the water surface
        meas_avg_depths = np.nanmean(meas_depths_all, axis=1)
        meas_total_depth = np.nanmax(depth_ens, axis=0)
        meas_avg_depths_ws = meas_total_depth - meas_avg_depths

        # Get the ensemble quantiles of velocity
        meas_velocities_25 = np.nanquantile(velocities_all, 0.25, axis=1)
        meas_velocities_50 = np.nanquantile(velocities_all, 0.50, axis=1)
        meas_velocities_75 = np.nanquantile(velocities_all, 0.75, axis=1)
        meas_velocities_avg = np.nanmean(velocities_all, axis=1)

        # Grab only valid data
        condition_1 = np.logical_not(np.isnan(meas_velocities_25))
        condition_2 = np.logical_not(np.isnan(meas_velocities_50))
        condition_3 = np.logical_not(np.isnan(meas_velocities_75))
        condition_4 = np.logical_not(np.isnan(meas_avg_depths))
        condition_5 = meas_avg_depths > 0
        condition_all = np.logical_and.reduce(
            (condition_1, condition_2, condition_3, condition_4, condition_5)
        )

        meas_max_velocity = np.nanmax(meas_velocities_50)
        estimate_velocity_uncertainty = meas_velocities_75 - meas_velocities_25

        data = np.vstack(
            (
                meas_avg_depths_ws[condition_all],
                meas_velocities_avg[condition_all],
            )
        )
        point_data = np.vstack((data, estimate_velocity_uncertainty[condition_all])).T

        depth_all = meas_total_depth - meas_depths_all

        return point_data, meas_max_velocity, meas_total_depth, depth_all

    @staticmethod
    def compute_confidence_interval(coef, z_units, exp):
        """Compute confidence interval

        Parameters:
            coef: float
            z_units: Array
            exp: float
        Returns:
            c_interval: Array
        """

        c_interval = coef * z_units**exp

        return c_interval

    @staticmethod
    def compute_alpha_std(low_exp, high_exp):
        """Compute alpha standard error

        Parameters:
            low_exp: float
            high_exp: float
        Returns:
            std: float
        """

        a_low = 1 / (1 + low_exp)
        a_high = 1 / (1 + high_exp)
        std = np.abs(a_low - a_high)

        return std
