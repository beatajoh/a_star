import json

with open("tmp/atkgraph.json", 'r') as f:
    atkgraph = json.load(f)

target_node_id = "Application:7219598629313512:reverseReach"
atknode_index = -1  # Initialize the current node index
visited_nodes = []  # Store the indices of visited nodes during traversal
visited_paths = set()  # Store the IDs of visited nodes to avoid revisiting them
dead_end_count = 0  # Track the number of consecutive dead ends

while target_node_id not in visited_paths:
    link_nodes = atkgraph[atknode_index]['links']  # Get the linked nodes of the current node

    if not link_nodes:
        print("Reached a dead end. Backtracking...")
        dead_end_count += 1
        if dead_end_count >= 2:
            atknode_index = visited_nodes.pop()  # Go back two steps if consecutive dead ends
            dead_end_count = 0
        continue

    for link_node in link_nodes:
        if link_node not in visited_paths:
            dead_end_count = 0
            for i, node in enumerate(atkgraph):
                if node['id'] == link_node:
                    print(node['id'])  # Print the ID of the current node
                    visited_nodes.append(atknode_index)  # Store the current node index
                    visited_paths.add(link_node)  # Add the current node to visited paths
                    atknode_index = i  # Update the current node index to the linked node index
                    break
            break
    else:
        print("Reached a dead end. Backtracking...")
        if visited_nodes:
            atknode_index = visited_nodes.pop()  # Go back one step if a dead end
            dead_end_count = 0
