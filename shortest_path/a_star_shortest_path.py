import math
import json
from collections import deque
import heapq

'''
Discovers if the node is an 'and' or 'or' node.
If the node is an 'or' node, the function returns True.
If the node is an 'and' node, the function returns True if all parent nodes has been visited.
'''
def all_parents_visited(atkgraph, node, open_set, parent_nodes, visited):
    print("="*100)
    print("node:" + node)
    print("parent_nodes: ", parent_nodes)
    print("="*100)
    if is_and_node(node, parent_nodes):
        print("AND NODE!!!",node)
        for parents in parent_nodes[node]:
            if parents not in visited:
                print(parent_nodes)
                print("FALSE AND", node)
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
Reconstructs the path found by the a_star function and calculates the total cost for the path.
'''
def reconstruct_path(came_from, current, start_node, costs, visited=set()):
    print(current)
    cost = 0
    if current != start_node:
        total_path = [current]
        while current in came_from.keys():
            old_current = current
            current = came_from[current]        
            if len(current)>1:
                for node in current:
                    path, costt = reconstruct_path(came_from, node, start_node, costs, visited)
                    total_path.insert(0,path)
                    cost+=costt+costs[old_current]
                    print(path," ? ", costt, "  ?  ")
            else:
                total_path.insert(0,current)
                if old_current not in visited:
                    cost+=costs[old_current]
                    visited.add(old_current)
                if current == start_node:
                    break
    return total_path, cost

'''
Fills a dictionary.
Returns a dictionary with node ids as keys, and score as values.
'''
def fill_dictionary(atkgraph, score):
    scores = {}
    for node in atkgraph:
        scores[node['id']] = score
    return scores

'''
Gets the neighbor nodes, aka the outgoing links to nodes, for all nodes in the attack graph.
Returns a dictionary with node ids as keys, and score as values.
'''
def get_neighbor_nodes(atkgraph): 
    dict = {}
    for node in atkgraph:
        dict[node['id']] = node['links']
    return dict

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
Gets the cost for all attack steps in the graph.
Returns a dictionary with node ids as keys, and the parent_list as values.
'''
def get_costs_for_nodes(atkgraph):
    dict = {}
    for node in atkgraph:
        print(node)
        if not node['ttc']==None: # for the attacker node, the ttc is None
            dict[node['id']]=node['ttc']['cost'][0]
    return dict

'''
calculate the heuristic for all node a_star
'''
def calculate_heuristic(node, target, atkgraph):
    if 'ttc' in node and 'cost' in node['ttc']:
        path_cost = 0
        current_node = node
        while current_node['id'] != target['id'] and len(current_node['links'])>0:
            path_cost += sum(current_node['ttc']['cost'])
            next_node_id = current_node['links'][0]  # assuming there is only one outgoing link
            next_node = next(n for n in atkgraph if n['id'] == next_node_id)
            current_node = next_node

        path_cost += sum(current_node['ttc']['cost'])

        return path_cost
    
'''
Finds the shortest path with A* algorithm, with added conditions for handling the 'and' nodes.
'''
def a_star(atkgraph, start_node, target_node):

    open_set = []
    heapq.heappush(open_set, (0, start_node))

    visited = set()
    visited.add(start_node)

    came_from = fill_dictionary(atkgraph, "")

    g_score = fill_dictionary(atkgraph, 10000) # map with default value of Infinity
    g_score[start_node] = 0

    h_score = fill_dictionary(atkgraph, 0)

    # for node n, f_score[n] := g_score[n] + h(n). f_score[n] represents our current best guess as to
    # how cheap a path could be from start to finish if it goes through n.
    f_score = fill_dictionary(atkgraph, 0) # map with default value of Infinity
    f_score[start_node] = h_score[start_node]

    for node in atkgraph:
        if node['id'] == start_node:
            h_score[node['id']] = calculate_heuristic(node, node, atkgraph)  
        else:
            h_score[node['id']] = calculate_heuristic(node, atkgraph[-1], atkgraph)
    
    print("-"*100)
    print(h_score)
    print("-"*100)

    costs = get_costs_for_nodes(atkgraph)
    costs_copy = get_costs_for_nodes(atkgraph)
    neighbor_nodes = get_neighbor_nodes(atkgraph)
    parent_nodes = get_parent_nodes_for_and_nodes(atkgraph)

    current_node = start_node

    while len(open_set) > 0:
        print(g_score["C"])
        print("OPEN SET        ",open_set)
        # current_node is the node in open_set having the lowest f_score value
        current_score, current_node = heapq.heappop(open_set)
        visited.add(current_node)

        if current_node == target_node:
            print("Finished")
            print(visited)
            print(came_from)
            print(current_node)
            print(current_score)
            print("COSTS: ", costs_copy)
            return reconstruct_path(came_from, current_node, start_node, costs_copy)

        current_neighbors = neighbor_nodes[current_node]
        print(current_neighbors)
        found_a_path=False
        if len(current_neighbors)>1:
            print("HALFAJFOEAÅ")
        for neighbor in current_neighbors:            
            tentative_g_score = g_score[current_node]+costs[neighbor]
            # try the neighbor node with a lower g_score than the previous node
            if tentative_g_score < g_score[neighbor]:
                # if it is an 'or' node or if the and all parents to the 'and' node has been visited,
                # continue to try this path
                print(found_a_path)
                if all_parents_visited(atkgraph, neighbor, open_set, parent_nodes, visited):
                    came_from[neighbor] += current_node
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + h_score[neighbor]
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (g_score[neighbor], neighbor))
                # if the node is an 'and' node, still update the node cost and keep track of the path
                elif is_and_node(neighbor, parent_nodes):
                    #costs[neighbor]=tentative_g_score
                    costs[neighbor]=tentative_g_score
                    came_from[neighbor]+=current_node
                    print("YEEES ADDING ",tentative_g_score)
                    
    # return false if the open set is empty but goal was never reached
    return False 
   