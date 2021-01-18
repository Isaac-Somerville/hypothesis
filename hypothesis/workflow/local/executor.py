def execute(context):
    # Prune the computational graph
    context.prune()
    # Determine the order of execution
    execution_order = {}
    bfs_order = list(context.bfs())
    current_priority = 0
    for priority, node in enumerate(bfs_order):
        execution_order[node] = priority
    program = [None] * len(context.nodes)
    for k in execution_order:
        program[execution_order[k]] = k
    # Execute the computational graph
    for instruction in range(len(program)):
        program[instruction].f()