
# This file is part of MSMTools.
#
# Copyright (c) 2015, 2014 Computational Molecular Biology Group, Freie Universitaet Berlin (GER)
#
# MSMTools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

r"""Unit test for the fingerprint module

.. moduleauthor:: B.Trendelkamp-Schroer <benjamin DOT trendelkamp-schroer AT fu-berlin DOT de>

"""
from __future__ import absolute_import

import unittest

import numpy as np
from msmtools.util.numeric import assert_allclose

from .decomposition import rdl_decomposition, timescales

from .committor_test import BirthDeathChain

from .fingerprints import fingerprint_correlation, fingerprint_relaxation, fingerprint
from .fingerprints import correlation_decomp, correlation_matvec, correlation
from .fingerprints import relaxation_decomp, relaxation_matvec, relaxation
from six.moves import range


class TestFingerprint(unittest.TestCase):
    def setUp(self):
        self.k = 4

        p = np.zeros(10)
        q = np.zeros(10)
        p[0:-1] = 0.5
        q[1:] = 0.5
        p[4] = 0.01
        q[6] = 0.1

        self.bdc = BirthDeathChain(q, p)

        self.mu = self.bdc.stationary_distribution()
        self.T = self.bdc.transition_matrix_sparse()
        R, D, L = rdl_decomposition(self.T, k=self.k)
        self.L = L
        self.R = R
        self.ts = timescales(self.T, k=self.k)
        self.times = np.array([1, 5, 10, 20])

        ev = np.diagonal(D)
        self.ev_t = ev[np.newaxis, :] ** self.times[:, np.newaxis]

        self.tau = 7.5

        """Observables"""
        obs1 = np.zeros(10)
        obs1[0] = 1
        obs1[1] = 1
        obs2 = np.zeros(10)
        obs2[8] = 1
        obs2[9] = 1

        self.obs1 = obs1
        self.obs2 = obs2

        """Initial vector for relaxation"""
        w0 = np.zeros(10)
        w0[0:4] = 0.25
        self.p0 = w0

    def test_fingerprint_correlation(self):
        """Autocorrelation"""

        """k=4, tau=1"""
        k = self.k
        acorr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs1)
        tsn, acorr_ampn = fingerprint_correlation(self.T, self.obs1, k=k)
        assert_allclose(tsn, self.ts)
        assert_allclose(acorr_ampn, acorr_amp)

        """k=4, tau=7.5"""
        tau = self.tau
        tsn, acorr_ampn = fingerprint_correlation(self.T, self.obs1, k=k, tau=tau)
        assert_allclose(tsn, tau * self.ts)
        assert_allclose(acorr_ampn, acorr_amp)

        """Cross-correlation"""

        """k=4, tau=1"""
        k = self.k
        corr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs2)
        tsn, corr_ampn = fingerprint_correlation(self.T, self.obs1, obs2=self.obs2, k=k)
        assert_allclose(tsn, self.ts)
        assert_allclose(corr_ampn, corr_amp)

        """k=4, tau=7.5"""
        tau = self.tau
        tsn, corr_ampn = fingerprint_correlation(self.T, self.obs1, obs2=self.obs2, k=k, tau=tau)
        assert_allclose(tsn, tau * self.ts)
        assert_allclose(corr_ampn, corr_amp)

    def test_fingerprint_relaxation(self):
        one_vec = np.ones(self.T.shape[0])

        relax_amp = np.dot(self.p0, self.R) * np.dot(self.L, self.obs1)
        tsn, relax_ampn = fingerprint_relaxation(self.T, self.p0, self.obs1, k=self.k)
        assert_allclose(tsn, self.ts)
        assert_allclose(relax_ampn, relax_amp)

    def test_fingerprint(self):
        k = self.k
        amp = np.dot(self.p0 * self.obs1, self.R) * np.dot(self.L, self.obs2)
        tsn, ampn = fingerprint(self.T, self.obs1, obs2=self.obs2, p0=self.p0, k=k)
        assert_allclose(tsn, self.ts)
        assert_allclose(ampn, amp)

    ################################################################################


# Correlation
################################################################################

class TestCorrelation(unittest.TestCase):
    def setUp(self):
        self.k = 4

        p = np.zeros(10)
        q = np.zeros(10)
        p[0:-1] = 0.5
        q[1:] = 0.5
        p[4] = 0.01
        q[6] = 0.1

        self.bdc = BirthDeathChain(q, p)

        self.mu = self.bdc.stationary_distribution()
        self.T = self.bdc.transition_matrix_sparse()
        R, D, L = rdl_decomposition(self.T, k=self.k)
        self.L = L
        self.R = R
        self.ts = timescales(self.T, k=self.k)
        self.times = np.array([1, 5, 10, 20, 100])

        ev = np.diagonal(D)
        self.ev_t = ev[np.newaxis, :] ** self.times[:, np.newaxis]

        obs1 = np.zeros(10)
        obs1[0] = 1
        obs1[1] = 1
        obs2 = np.zeros(10)
        obs2[8] = 1
        obs2[9] = 1

        self.obs1 = obs1
        self.obs2 = obs2
        self.one_vec = np.ones(10)

    def test_correlation_decomp(self):
        """Auto-correlation"""

        acorr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs1)
        acorr = np.dot(self.ev_t, acorr_amp)
        acorrn = correlation_decomp(self.T, self.obs1, k=self.k, times=self.times)
        assert_allclose(acorrn, acorr)

        """Cross-correlation"""

        """k=None"""
        corr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs2)
        corr = np.dot(self.ev_t, corr_amp)
        corrn = correlation_decomp(self.T, self.obs1, obs2=self.obs2, k=self.k, times=self.times)
        assert_allclose(corrn, corr)

    def test_correlation_matvec(self):
        """Auto-correlation"""
        times = self.times
        P = self.T.toarray()
        acorr = np.zeros(len(times))
        for i in range(len(times)):
            P_t = np.linalg.matrix_power(P, times[i])
            acorr[i] = np.dot(self.mu * self.obs1, np.dot(P_t, self.obs1))
        acorrn = correlation_matvec(self.T, self.obs1, times=self.times)
        assert_allclose(acorrn, acorr)

        """Cross-correlation"""
        corr = np.zeros(len(times))
        for i in range(len(times)):
            P_t = np.linalg.matrix_power(P, times[i])
            corr[i] = np.dot(self.mu * self.obs1, np.dot(P_t, self.obs2))
        corrn = correlation_matvec(self.T, self.obs1, obs2=self.obs2, times=self.times)
        assert_allclose(corrn, corr)

    def test_correlation(self):
        """Auto-correlation"""
        acorr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs1)
        acorr = np.dot(self.ev_t, acorr_amp)
        acorrn = correlation(self.T, self.obs1, k=self.k, times=self.times)
        assert_allclose(acorrn, acorr)

        """Cross-correlation"""
        corr_amp = np.dot(self.mu * self.obs1, self.R) * np.dot(self.L, self.obs2)
        corr = np.dot(self.ev_t, corr_amp)
        corrn = correlation(self.T, self.obs1, obs2=self.obs2, k=self.k, times=self.times)
        assert_allclose(corrn, corr)


################################################################################
# Relaxation
################################################################################

class TestRelaxation(unittest.TestCase):
    def setUp(self):
        self.k = 4

        p = np.zeros(10)
        q = np.zeros(10)
        p[0:-1] = 0.5
        q[1:] = 0.5
        p[4] = 0.01
        q[6] = 0.1

        self.bdc = BirthDeathChain(q, p)

        self.mu = self.bdc.stationary_distribution()
        self.T = self.bdc.transition_matrix_sparse()

        """Test matrix-vector product against spectral decomposition"""
        R, D, L = rdl_decomposition(self.T, k=self.k)
        self.L = L
        self.R = R
        self.ts = timescales(self.T, k=self.k)
        self.times = np.array([1, 5, 10, 20, 100])

        ev = np.diagonal(D)
        self.ev_t = ev[np.newaxis, :] ** self.times[:, np.newaxis]

        """Observable"""
        obs1 = np.zeros(10)
        obs1[0] = 1
        obs1[1] = 1
        self.obs = obs1

        """Initial distribution"""
        w0 = np.zeros(10)
        w0[0:4] = 0.25
        self.p0 = w0

    def test_relaxation_decomp(self):
        """k=None"""
        relax_amp = np.dot(self.p0, self.R) * np.dot(self.L, self.obs)
        relax = np.dot(self.ev_t, relax_amp)
        relaxn = relaxation_decomp(self.T, self.p0, self.obs, k=self.k, times=self.times)
        assert_allclose(relaxn, relax)

    def test_relaxation_matvec(self):
        times = self.times
        P = self.T.toarray()
        relax = np.zeros(len(times))
        for i in range(len(times)):
            P_t = np.linalg.matrix_power(P, times[i])
            relax[i] = np.dot(self.p0, np.dot(P_t, self.obs))
        relaxn = relaxation_matvec(self.T, self.p0, self.obs, times=self.times)
        assert_allclose(relaxn, relax)

    def test_relaxation(self):
        relax_amp = np.dot(self.p0, self.R) * np.dot(self.L, self.obs)
        relax = np.dot(self.ev_t, relax_amp)
        relaxn = relaxation(self.T, self.p0, self.obs, k=self.k, times=self.times)
        assert_allclose(relaxn, relax)


if __name__ == "__main__":
    unittest.main()