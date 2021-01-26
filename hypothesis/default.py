r"""Default settings in Hypothesis.

"""

import torch


activation = torch.nn.LeakyReLU
r"""Default activation function in Hypothesis."""


batch_size = 4096
r"""Default batch size."""


dropout = 0.0
r"""Default dropout setting."""


epochs = 1
r"""Default number of data epochs."""


output_transform = "normalize"
r"""Default output transformation for neural networks.

For 1-dimensional outputs, this is equivalent to torch.nn.Sigmoid.
Otherwise, this will reduce to torch.nn.Softmax.
"""


trunk = (256, 256, 256)
r"""Default trunk of large convolution models such as ResNet or DenseNet."""


dependent_delimiter = ','
r"""Split character indicating the dependence between random variables."""


independent_delimiter = '|'
r"""Split character indicating the independene between random variables."""


dataloader_workers = 4
r"""Default number of dataloader workers."""
