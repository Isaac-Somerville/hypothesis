r"""Simulator definition of the tractable benchmark.

"""

import torch
import numpy as np

from hypothesis.simulation import BaseSimulator
from torch.distributions.multivariate_normal import MultivariateNormal as Normal


class TractableBenchmarkSimulator(BaseSimulator):
    r"""Simulation model associated with the tractable benchmark.

    Marginalizes over the rho and mu parameter. The dimensionality of the
    problem is therefore reduces to 2 compared to `hypothesis.benchmark.tractable`.
    """

    def __init__(self, mu=[0.7, -2.9]):
        super(TractableBenchmarkSimulator, self).__init__()
        self._mu = mu
        self._p = torch.distributions.uniform.Uniform(-3.0, 3.0)

    @torch.no_grad()
    def _generate(self, input):
        success = False

        while not success:
            try:
               if self._mu is None:
                   mean = torch.tensor([self._p.sample().item(), self._p.sample().item()]).float()
               else:
                   mean = torch.tensor(self._mu).float()
               scale = 1.0
               s_1 = input[0] ** 2
               s_2 = input[1] ** 2
               rho = self._p.sample().tanh()
               covariance = torch.tensor([
                   [scale * s_1 ** 2, scale * rho * s_1 * s_2],
                   [scale * rho * s_1 * s_2, scale * s_2 ** 2]])
               normal = Normal(mean, covariance)
               x_out = normal.sample((4,)).view(1, -1)
               success = True
            except ValueError:
                pass

        return x_out

    @torch.no_grad()
    def forward(self, inputs, **kwargs):
        samples = []

        inputs = inputs.view(-1, 2)
        for input in inputs:
            x_out = self._generate(input)
            samples.append(x_out)

        return torch.cat(samples, dim=0)