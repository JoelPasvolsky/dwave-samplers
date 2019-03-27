# Copyright 2019 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test the (private) TabuSearch python interface."""

import unittest

import dimod

import tabu


class TestTabuSearch(unittest.TestCase):
    def test_basic(self):
        qubo = [[2, 1, 1], [1, 2, 1], [1, 1, 2]]
        init = [1, 1, 1]
        tenure = len(init) - 1
        scale = 1
        timeout = 20

        search = tabu.TabuSearch(qubo, init, tenure, scale, timeout)

        solution = list(search.bestSolution())
        energy = search.bestEnergy()

        self.assertEqual(solution, [0, 0, 0])
        self.assertEqual(energy, 0.0)
