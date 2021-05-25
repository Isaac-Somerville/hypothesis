r"""Simulation pipeline example.

A demo workflow to created batched simulations for a train
and test dataset. Followed up by a merge operation.

As you'll notice, executing this workflow for the 2nd time
is significantly shorter! This is because Hypothesis determines
what part of the computational graph need to be computed to
ensure that the specified constraints are met.

No more recomputation and rescheduling on HPC systems!
"""

import argparse
import glob
import hypothesis as h
import hypothesis.workflow as w
import logging
import numpy as np
import os

from hypothesis.workflow import shell


parser = argparse.ArgumentParser()
parser.add_argument("--batch-size", type=int, default=10000, help="Simulation batch-size (default: 10000).")
parser.add_argument("--train", type=int, default=1000000, help="Total number of simulations for training (default: 1000000).")
parser.add_argument("--test", type=int, default=100000, help="Total number of simulations for testing (default: 100000).")
parser.add_argument("--local", action="store_true", help="Execute the workflow locally (default: false).")
parser.add_argument("--slurm", action="store_true", help="Execute the workflow on Slurm (default: false).")
parser.add_argument("--debug", action="store_true", help="Useless flag (default: false).")
arguments, _ = parser.parse_known_args()

num_train_blocks = arguments.train // arguments.batch_size
num_test_blocks = arguments.test // arguments.batch_size

if arguments.debug:
    print("Hello world!")

@w.root
@w.postcondition(w.exists("data/train/simulations.npy"))
@w.postcondition(w.exists("data/test/simulations.npy"))
def main():
    logging.info("Executing root node.")
    # Create the necessary directories
    train_dir = "data/train"
    test_dir = "data/test"
    if not os.path.exists(train_dir):
        os.makedirs(train_dir)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)


@w.dependency(main)
@w.tasks(num_train_blocks)
def simulate_train(task_index):
    logging.info("Simulating training block " + str(task_index))
    suffix = str(task_index).zfill(5)
    output_file = "data/train/block-" + suffix + ".npy"
    if not os.path.exists(output_file):
        simulated_data = np.random.random((arguments.batch_size, 5))
        np.save(output_file, simulated_data)
    assert os.path.exists(output_file)


@w.dependency(simulate_train)
@w.postcondition(w.exists("data/train/simulations.npy"))
def merge_train():
    logging.info("Merging training data")
    shell("hypothesis merge --extension numpy --dimension 0 --in-memory --files 'data/train/block-*.npy' --sort --out data/train/simulations.npy")
    shell("rm -rf data/train/block-*.npy")
    assert os.path.exists("data/train/simulations.npy")


@w.dependency(main)
@w.tasks(num_train_blocks)
def simulate_test(task_index):
    logging.info("Simulating testing block " + str(task_index))
    suffix = str(task_index).zfill(5)
    output_file = "data/test/block-" + suffix + ".npy"
    if not os.path.exists(output_file):
        simulated_data = np.random.random((arguments.batch_size, 5))
        np.save(output_file, simulated_data)
    assert os.path.exists(output_file)


@w.dependency(simulate_test)
@w.postcondition(w.exists("data/test/simulations.npy"))
def merge_test():
    logging.info("Merging testing data")
    shell("hypothesis merge --extension numpy --dimension 0 --in-memory --files 'data/test/block-*.npy' --sort --out data/test/simulations.npy")
    shell("rm -rf data/test/block-*.npy")
    assert os.path.exists("data/test/simulations.npy")


if __name__ == "__main__":
    # Check if an executor has been requested through the arguments.
    if arguments.local:
        w.local.execute()
    elif arguments.slurm:
        w.slurm.execute()