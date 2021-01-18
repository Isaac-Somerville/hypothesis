import dill as pickle
import hypothesis.workflow as w
import logging
import os
import shutil
import tempfile


def execute(context=None, base=None, cleanup=False, directory=None, environment=None):
    # Check if a custom context has been specified
    if context is None:
        context = w.context
    pickle.settings['recurse'] = True  # Handle dependencies
    # Add default Slurm attributes to the nodes
    add_default_attributes(context, base=base)
    # Set the default anaconda environment
    add_default_environment(context, environment=environment)
    # Create the generation directory
    if directory is None:
        directory = tempfile.mkdtemp()
    if not os.path.exists(directory):
        os.makedirs(directory)
    tasks_directory = directory + "/tasks"
    if not os.path.exists(tasks_directory):
        os.makedirs(tasks_directory)
    # Save the task processor
    save_processor(directory)
    # Generate the executables for the processor
    generate_executables(context, directory)
    # Generate the task files
    for node in context.nodes:
        generate_task_file(node, tasks_directory)
    # Generate the submission script
    lines = []
    lines.append("#!/usr/bin/env bash -i")
    lines.append("#")
    lines.append("# Slurm submission script, generated by Hypothesis.")
    lines.append("# github.com/montefiore-ai/hypothesis")
    lines.append("#")
    # Retrieve the tasks in BFS order
    tasks = list(context.bfs())
    task_indices = {}
    for task_index, task in enumerate(tasks):
        task_indices[task] = task_index
        line = "t" + str(task_index) + "=$(sbatch "
        # Check if the task has dependencies
        if len(task.dependencies) > 0:
            flag = "--dependency=afterok"
            for dependency in task.dependencies:
                dependency_index = task_indices[dependency]
                flag += ":$t" + str(dependency_index)
            line += flag + " "
        line += "tasks/" + task_filename(task) + ")"
        lines.append(line)
    # Write the pipeline file
    with open(directory + "/pipeline.bash", "w") as f:
        for line in lines:
            f.write(line + "\n")
    # Cleanup the generated filed
    if cleanup:
        shutil.rmtree(directory)


def save_processor(directory):
    processor = """
import dill as pickle
import sys

pickle.settings['recurse'] = True
with open(sys.argv[1], "rb") as f:
    function = pickle.load(f)
if len(sys.argv) > 2:
    task_index = int(sys.argv[2])
    function(task_index)
else:
    function()
"""
    with open(directory + "/processor.py", "w") as f:
        f.write(processor)


def generate_executables(context, directory):
    for node in context.nodes:
        code = pickle.dumps(node.f)
        with open(directory + "/" + node.name + ".code", "wb") as f:
            f.write(code)


def task_filename(node):
    return node.name


def add_default_environment(context, environment=None):
    if environment is not None:
        for node in context.nodes:
            node["conda"] = environment


def add_default_attributes(context, base=None):
    for node in context.nodes:
        node["--export"] = "ALL"  # Exports all environment variables,
        node["--parsable"] = ""   # Enables convenient reading of task ID.
        node["--requeue"] = ""    # Automatically requeue when something fails.
        if base is not None:
            node["--chdir"] = base


def generate_task_file(node, directory):
    lines = []
    lines.append("#!/usr/bin/env bash")
    lines.append("#")
    lines.append("#")
    lines.append("# Slurm arguments, generated by Hypothesis.")
    lines.append("# github.com/montefiore-ai/hypothesis")
    lines.append("#")
    # Add the node attributes
    for key in node.attributes:
        if key[:2] != "--":  # Skip non SBATCH arguments
            continue
        value = node[key]
        line = "#SBATCH " + key
        if len(value) > 0:
            line += "=" + value
        lines.append(line)
    # Check if the tasks is an array tasks.
    if node.tasks > 1:
        multiarray = True
        lines.append("#SBATCH --array 0-" + str(node.tasks - 1))
    else:
        multiarray = False
    # Check if a custom Anaconda environment has been specified.
    try:
        environment = node["conda"]
        lines.append("eval \"$(conda shell.bash hook)\"")
        lines.append("conda activate " + environment)
    except:
        pass
    # Execute the function
    line = "ipython processor.py " + node.name + ".code"
    if multiarray:
        line += " $SLURM_ARRAY_TASK_ID"
    lines.append(line)
    # Write the task file.
    with open(directory + "/" + task_filename(node), "w") as f:
        for line in lines:
            f.write(line + "\n")
