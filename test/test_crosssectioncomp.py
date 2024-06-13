import unittest
import os
import numpy as np

from qrev import Measurement
from qrev import CrossSectionComp

test_dir = os.path.join(os.getcwd(), 'data')


class TestCrossSectionComp(unittest.TestCase):

    def test_mean_xs_no_gps(self):
        expected_dir = os.path.join(test_dir, 'results',
                                    'mean_xs_without_gps.csv')
        expected_data = np.genfromtxt(expected_dir, delimiter=',')
        meas_file = os.path.join(test_dir, 'trdi_no_gps',
                                 '02292010_20201216',
                                 '02292010_20201216.mmt')

        meas = Measurement(in_file=meas_file, source='TRDI')
        xs = CrossSectionComp(meas.transects)
        mean_xs = xs.cross_section[(len(xs.cross_section)-1)]

        self.assertIsNone(np.testing.assert_array_equal(
            expected_data, mean_xs))

    def test_mean_xs_with_gps(self):
        expected_dir = os.path.join(test_dir, 'results',
                                    'mean_xs_with_gps.csv')
        expected_data = np.genfromtxt(expected_dir, delimiter=',')
        meas_file = os.path.join(test_dir, 'trdi_with_gps',
                                 'CB0_20200901',
                                 'CB0_20200901.mmt')

        meas = Measurement(in_file=meas_file, source='TRDI')
        xs = CrossSectionComp(meas.transects)
        mean_xs = xs.cross_section[(len(xs.cross_section)-1)]

        self.assertIsNone(np.testing.assert_array_almost_equal(
            expected_data, mean_xs, decimal=5))


if __name__ == '__main__':
    unittest.main()
