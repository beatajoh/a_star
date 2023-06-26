import random


'''
Gets the cost for all attack steps in the graph.
Returns a dictionary with node ids as keys, and the parent_list as values.
'''
def get_costs_for_nodes(atkgraph):
    dict = {}
    for node in atkgraph:
        if not node['ttc'] == None: # for the attacker node, the ttc is None
            dict[node['id']]=node['ttc']['cost'][0]
    return dict

'''
Reconstructs the path found by the a_star function and calculates the total cost for the path.
'''
def reconstruct_path(came_from, current, start_node, costs, visited=set()):
    cost = 0
    total_path=[]
    if current != start_node:
        total_path = [current]
        # reconstruct the path until the start node is reached
        while current in came_from.keys() and current != start_node:
            old_current = current
            current = came_from[current] 
            # special condition for 'and' node       
            if len(current)>1:
                for node in current:
                    path, costt = reconstruct_path(came_from, node, start_node, costs, visited)
                    total_path.insert(0,path)
                    cost += costt+costs[old_current]
            else:
                current = current[0]
                # update cost for all nodes once
                if old_current not in visited:
                    cost += costs[old_current]
                    visited.add(old_current)
                total_path.insert(0,current)
    return total_path, cost


'''
Discovers if the node is an 'and' or 'or' node.
If the node is an 'or' node, the function returns True.
If the node is an 'and' node, the function returns True if all parent nodes has been visited.
'''
def all_parents_visited(node, parent_nodes, visited):
    if is_and_node(node, parent_nodes):
        print("FOUND AND NODE")
        # if all the dependency steps (parents) are visited return true,
        # otherwise return false
        for parents in parent_nodes[node]:
            if parents not in visited:
                print("FALSE AND NODE")
                return False 
    return True

'''
Returns true if the node is an and node.
'''
def is_and_node(node, parent_nodes):
    if node in parent_nodes:
       return True
    return False

'''
Gets the parent nodes, aka the incoming links to nodes, for all nodes in the attack graph.
Returns a dictionary with node ids as keys, and the parent_list as values.
'''
def get_parent_nodes_for_and_nodes(atkgraph): 
    dict = {}
    for node in atkgraph:
        if node['type'] == 'and':
            dict[node['id']] = node['parent_list']
    return dict


'''
Gets the neighbor nodes, aka the outgoing links to nodes, for all nodes in the attack graph.
Returns a dictionary with node ids as keys, and score as values.
'''
def get_neighbor_nodes(atkgraph): 
    dict = {}
    for node in atkgraph:
        dict[node['id']] = node['links']
    return dict


def all_neighbors_visited(neighbors, node, visited): 
    for neighbor in neighbors[node]:
        if neighbor not in visited:
            return False
    return True
'''
Fills a dictionary.
Returns a dictionary with node ids as keys, with empty list as the values.
'''
def fill_dictionary_with_empty_list(atkgraph):
    dict = {}
    for node in atkgraph:
        dict[node['id']] = list()
    return dict

''' 
calculate the random path (according to option 1)
'''
def random_path(atkgraph, start_node, target_node):
    print("hej")

    visited = set()  # Store the IDs of visited nodes to avoid revisiting them

    parent_nodes = get_parent_nodes_for_and_nodes(atkgraph)
    current_node = start_node
    visited.add(current_node)
    stack = [current_node]
    neighbor_nodes = get_neighbor_nodes(atkgraph)  # Get the linked nodes of the current node

    came_from = fill_dictionary_with_empty_list(atkgraph)

    costs = get_costs_for_nodes(atkgraph)
    #neighbor_nodes[current_node][0]
    while current_node != target_node:
        print("STACK: ", stack)
        print("CURRENT NODE: ", current_node)
        visited.add(current_node)

  
        # select a neighbor node which hasn't been visited yet
        if len(stack) == 0: 
            break
        if len(neighbor_nodes[current_node]) == 0: 
            print("Reached a leaf, so we need to continue from another place")
            current_node = stack.pop()
            print("POPPED FROM STACK: ",current_node)
            print("THE NEIGHBORS ",neighbor_nodes[current_node])
                    
        neighbor = random.choice(neighbor_nodes[current_node])
        print("CHOICE:   ", neighbor)

        if neighbor not in visited:
            print("WHATINTHE")
            if all_parents_visited(neighbor, parent_nodes, visited):
                print("YES ADD THIS NODE TO THE PATH")
                visited.add(neighbor)
                came_from[neighbor].append(current_node)
                stack.append(current_node)
                current_node = neighbor
            else: 
                print("found and node, so start from another place")
                current_node = stack.pop()
                continue
        elif neighbor in visited: # if we selected a node which has been visited
            print("HALLLOOOOOOOOO GO BAAAAAACK")
            # if we have tried all paths forward, move backwards again
            if all_neighbors_visited(neighbor_nodes, current_node, visited):
                current_node = stack.pop()
    
    path = reconstruct_path(came_from, current_node, start_node, costs)

    return path