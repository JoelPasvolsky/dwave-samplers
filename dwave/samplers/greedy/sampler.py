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

"""A dimod sampler that uses the steepest gradient descent."""

from numbers import Integral
from time import perf_counter_ns
from typing import Optional

from dimod.core.initialized import InitialStateGenerator

import dimod
import numpy as np

from dwave.samplers.greedy.descent import steepest_gradient_descent

__all__ = ["SteepestDescentSolver", "SteepestDescentSampler"]


class SteepestDescentSolver(dimod.Sampler, dimod.Initialized):
    """Steepest descent sampler for binary quadratic models.

    `Steepest descent <https://en.wikipedia.org/wiki/Gradient_descent>`_  is the
    discrete analogue of gradient descent, but the best move is computed using a
    local minimization rather rather than computing a gradient. The dimension along
    which to descend is determined, at each step, by the variable flip that causes
    the greatest reduction in energy.

    Solves convex problems to optimality.

    Number of downhill runs (samples produced) is determined by ``num_reads``,
    number of ``initial_states``, or a combination of the two, depending on
    the ``initial_states_generator``.

    For a given input model's graph :math:`G = (V, E)`, :math:`V` being a set of
    graph vertices and :math:`E` a set of edges, runtime complexity of the
    underlying C++ implementation is :math:`O(|E|)` for initialization phase
    and :math:`O(|V|)` per downhill step.

    In the ``large_sparse_opt`` mode, runtime complexity on sparse graphs is
    :math:`O(|V|*log|V|)` for initialization and :math:`O(max\_degree * log|V|)`
    per downhill step.

    Aliased as :class:`~greedy.sampler.SteepestDescentSampler`.

    .. note::
        Ocean SDK versions earlier than 8.0 supported also a 
        ``SteepestDescentSampler`` under the ``greedy`` namespace in a 
        ``dwave-greedy`` package. If your code uses that obsoleted class, 
        upgrade lines such as

        >>> from greedy import SteepestDescentSampler   # doctest: +SKIP

        to

        >>> from dwave.samplers import SteepestDescentSampler   # doctest: +SKIP

        or

        >>> from dwave.samplers.greedy import SteepestDescentSampler   # doctest: +SKIP

    Examples:
        Solve a simple Ising problem.

        >>> from dwave.samplers import SteepestDescentSampler
        ...
        >>> sampler = SteepestDescentSampler()
        >>> samples = sampler.sample_ising({0: 2, 1: 2}, {(0, 1): -1})
        ...
        >>> print(samples)      # doctest: +SKIP
           0  1 energy num_oc. num_st.
        0 -1 -1   -5.0       1       2
        ['SPIN', 1 rows, 1 samples, 2 variables]

        Post-processes samples generated by another sampler (simulated annealing
        in this example):

        >>> from dwave.samplers import SteepestDescentSampler, SimulatedAnnealingSampler
        >>> import dimod
        ...
        >>> bqm = dimod.generators.ran_r(5, 3)
        >>> samples = SimulatedAnnealingSampler().sample(bqm)
        >>> postprocessed = SteepestDescentSampler().sample(bqm, initial_states=samples)

        For additional examples, see :meth:`.sample`.
    """

    parameters = None
    """Keyword arguments accepted by the sampling methods.

    Examples:

        >>> from dwave.samplers import SteepestDescentSampler
        >>> sampler = SteepestDescentSampler()
        >>> sampler.parameters.keys()
        dict_keys(['num_reads', 'initial_states', 'initial_states_generator', 'seed', 'large_sparse_opt'])

    """

    properties = None
    """Values for parameters accepted by the sampling methods.

    Examples:

        >>> from dwave.samplers import SteepestDescentSampler
        >>> sampler = SteepestDescentSampler()
        >>> sampler.properties.keys()
        dict_keys(['initial_states_generators', 'large_sparse_opt_values'])

    """

    def __init__(self):
        # create a copy (isolate from subclass)
        self.parameters = {
            'num_reads': [],
            'initial_states': [],
            'initial_states_generator': ['initial_states_generators'],
            'seed': [],
            'large_sparse_opt': ['large_sparse_opt_values'],
        }
        self.properties = {
            'initial_states_generators': ('none', 'tile', 'random'),
            'large_sparse_opt_values': (True, False),
        }

    def sample(self, bqm: dimod.BinaryQuadraticModel,
               num_reads: Optional[int] = None,
               initial_states: Optional[dimod.typing.SamplesLike] = None,
               initial_states_generator: InitialStateGenerator = "random",
               seed: Optional[int] = None,
               large_sparse_opt: bool = False, **kwargs) -> dimod.SampleSet:
        """Find minima of a binary quadratic model.

        Starts from ``initial_states``, and converges to local minima using
        discrete steepest-descent method.

        Args:
            bqm: Binary quadratic model to be sampled.

            num_reads:
                Number of reads. Each read is generated by one run of the steepest
                descent algorithm. If ``num_reads`` is not explicitly given, it is
                selected to match the number of initial states given. If initial states
                are not provided, only one read is performed.

            initial_states:
                One or more samples, each defining an initial state for all the
                problem variables. Initial states are given one per read, but
                if fewer than ``num_reads`` initial states are defined, additional
                values are generated as specified by ``initial_states_generator``.
                See :func:`~dimod.as_samples` for a description of "samples-like".

            initial_states_generator:
                Defines the expansion of ``initial_states`` if fewer than
                ``num_reads`` are specified:

                * "none":
                    If the number of initial states specified is smaller than
                    ``num_reads``, raises ``ValueError``.

                * "tile":
                    Reuses the specified initial states if fewer than ``num_reads``
                    or truncates if greater.

                * "random":
                    Expands the specified initial states with randomly generated
                    states if fewer than ``num_reads`` or truncates if greater.

            seed:
                32-bit unsigned integer seed to use for the PRNG. Specifying a
                particular seed with a constant set of parameters produces
                identical results. If not provided, a random seed is chosen.

            large_sparse_opt:
                Use optimizations for large and sparse problems (search tree for
                next descent variable instead of linear array).

        Returns:
            A `dimod.SampleSet` for the binary quadratic model.

            The `info` field of the sample set contains three categories of timing information:
            preprocessing, sampling, and postprocessing time. All timings are reported in units of
            nanoseconds. Preprocessing time is the total time spent converting the BQM variable type
            (if required) and parsing input arguments. Sampling time is the total time the algorithm
            spent in sampling states of the binary quadratic model. Postprocessing time is the total
            time spent reverting variable type and creating a `dimod.SampleSet`.

        Note:
            Number of descents (single variable flips) taken to reach the local
            minimum for each sample is stored in a data vector called ``num_steps``.

        Examples:
            This example samples a simple two-variable Ising model.

            >>> import dimod
            >>> bqm = dimod.BQM.from_ising({'a': -1}, {'ab': 1})
            ...
            >>> from dwave.samplers import SteepestDescentSampler
            >>> sampler = SteepestDescentSampler()
            ...
            >>> sampleset = sampler.sample(bqm)
            >>> print(sampleset)      # doctest: +SKIP
               a  b energy num_oc. num_st.
            0 +1 -1   -2.0       1       0
            ['SPIN', 1 rows, 1 samples, 2 variables]

            Run steepest descent one million times (takes ~150ms on an average
            laptop), converging to local minima, each time starting from a
            random state:

            >>> bqm = dimod.BQM.from_ising({}, {'ab': 1})
            >>> sampler = SteepestDescentSampler()
            ...
            >>> samples = sampler.sample(bqm, num_reads=10**6)
            >>> print(samples.aggregate())      # doctest: +SKIP
               a  b energy num_oc. num_st.
            0 -1 +1   -1.0  500115       1
            1 +1 -1   -1.0  499885       1
            ['SPIN', 2 rows, 1000000 samples, 2 variables]

            Use a combination of one fixed initial state and two randomly
            generated ones to sample from a simple convex Ising problem with
            global minimum at ``(-1,-1)``:

            >>> bqm = dimod.BQM.from_ising({'x': 2, 'y': 2}, {'xy': -1})
            >>> sampler = SteepestDescentSampler()
            ...
            >>> samples = sampler.sample(bqm, initial_states=([1, 1], 'xy'), num_reads=3)
            >>> print(samples)      # doctest: +SKIP
               x  y energy num_oc. num_st.
            0 -1 -1   -5.0       1       2
            1 -1 -1   -5.0       1       1
            2 -1 -1   -5.0       1       2
            ['SPIN', 3 rows, 3 samples, 2 variables]

            Notice it required 2 variable flips (``num_steps`` field in the last
            column) to reach the minimum state, ``(-1, -1)``, from the initial
            state, ``(1, 1)``.
        """
        timestamp_preprocess = perf_counter_ns()
        # get the original vartype so we can return consistently
        original_vartype = bqm.vartype

        # convert to spin
        if bqm.vartype is not dimod.SPIN:
            bqm = bqm.change_vartype(dimod.SPIN, inplace=False)

        # validate seed
        if not (seed is None or isinstance(seed, Integral)):
            raise TypeError("'seed' should be None or a positive 32-bit integer")
        if isinstance(seed, Integral) and not 0 <= seed <= 2**32 - 1:
            raise ValueError("'seed' should be an integer between 0 and 2**32 - 1 inclusive")

        # parse initial_states et al
        parsed_initial_states = self.parse_initial_states(
            bqm,
            num_reads=num_reads,
            initial_states=initial_states,
            initial_states_generator=initial_states_generator,
            seed=seed)

        num_reads = parsed_initial_states.num_reads
        initial_states = parsed_initial_states.initial_states

        # get linear/quadratic data
        linear, (coupler_starts, coupler_ends, coupler_weights), offset = \
            bqm.to_numpy_vectors(variable_order=initial_states.variables)

        # we need initial states as contiguous numpy array
        initial_states_array = \
            np.ascontiguousarray(initial_states.record.sample, dtype=np.int8)

        timestamp_sample = perf_counter_ns()

        # run the steepest descent
        samples, energies, num_steps = steepest_gradient_descent(
            num_reads,
            linear, coupler_starts, coupler_ends, coupler_weights,
            initial_states_array, large_sparse_opt)

        timestamp_postprocess = perf_counter_ns()

        # resulting sampleset
        result = dimod.SampleSet.from_samples(
            (samples, initial_states.variables),
            energy=energies + offset,
            vartype=dimod.SPIN,
            num_steps=num_steps,
        )

        result.change_vartype(original_vartype, inplace=True)

        # Developer note: the specific keys of the timing dict are chosen to be consistent with
        #                 other samplers' timing dict.
        result.info.update(dict(timing=dict(
            preprocessing_ns=timestamp_sample - timestamp_preprocess,
            sampling_ns=timestamp_postprocess - timestamp_sample,
            # Update timing info last to capture the full postprocessing time
            postprocessing_ns=perf_counter_ns() - timestamp_postprocess,
        )))

        return result


SteepestDescentSampler = SteepestDescentSolver
