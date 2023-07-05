import math
import json
from collections import deque
import heapq
import random

'''
Discovers if the node is an 'and' or 'or' node.
If the node is an 'or' node, the function returns True.
If the node is an 'and' node, the function returns True if all parent nodes has been visited.
'''
def all_parents_visited(node, visited, index):
    if is_and_node(node, index):
        # if all the dependency steps (parents) are visited return true,
        # otherwise return false
        for parent in index[node]["parent_list"]:
            if parent not in visited:
                return False 
    return True
    
def all_neighbors_visited(neighbors, visited): 
    for neighbor in neighbors:
        if neighbor not in visited:
            return False
    return True

'''
Returns true if the node is an and node.
'''
def is_and_node(node, index):
    if index[node]["type"] == 'and':
        return True
    return False

'''
Reconstructs the path found by the Dijkstra function and calculates the total cost for the path.
'''
def reconstruct_path(came_from, current, start_node, costs, index, visited=set()):
    cost = 0
    total_path = []
    if current != start_node:
        total_path = [current]
        # reconstruct the path until the start node is reached
        while current in came_from.keys() and current != start_node:
            old_current = current
            current = came_from[current] # link from current -> old_current
            # condition for 'and' node       
            if len(current)>1:
                for node in current:
                    path, path_cost, _ = reconstruct_path(came_from, node, start_node, costs, index, visited)
                    total_path.insert(0,path)
                    cost += path_cost+costs[old_current]
                    index[path[-1]]["links"].append(old_current)
                break
            else:
                current = current[0]
                # update cost for all nodes once
                if old_current not in visited:
                    cost += costs[old_current]
                    visited.add(old_current)
                total_path.insert(0,current)
                if old_current not in index[current]["links"]:
                    index[current]["links"].append(old_current) 
    return total_path, cost, index


'''
Fills a dictionary.
Returns a dictionary with node ids as keys, with empty list as the values.
'''
def fill_dictionary_with_empty_list(dict):
    for key in dict.keys():
        dict[key] = list()
    return dict

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
Finds the shortest path with Dijkstra algorithm, with added conditions for handling the 'and' nodes.
'''
def dijkstra(atkgraph, start_node, target_node, index):

    node_ids = list(index.keys())

    open_set = []
    heapq.heappush(open_set, (0, start_node))

    visited = set()
    visited.add(start_node)

    came_from = dict.fromkeys(node_ids, '')
    came_from = fill_dictionary_with_empty_list(came_from)

    # g_score is a map with default value of infinity
    g_score = dict.fromkeys(node_ids, 10000)
    g_score[start_node] = 0

    # calculate the h_score for all nodes
    h_score = dict.fromkeys(node_ids, 0)
   
    # for node n, f_score[n] = g_score[n] + h_score(n). f_score[n] represents our current best guess as to
    # how cheap a path could be from start to finish if it goes through n.
    f_score = dict.fromkeys(node_ids, 0)
    f_score[start_node] = h_score[start_node]
    
    costs = get_costs_for_nodes(atkgraph)
    costs_copy = costs.copy()

    current_node = start_node
    while len(open_set) > 0:
        # current_node is the node in open_set having the lowest f_score value
        current_score, current_node = heapq.heappop(open_set)
        visited.add(current_node)

        if current_node == target_node:
            for key in index.keys():    
                index[key]["links"] = []    
            return reconstruct_path(came_from, current_node, start_node, costs_copy, index, set())

        current_neighbors = index[current_node]["links"]
       
        for neighbor in current_neighbors:  
            tentative_g_score = g_score[current_node]+costs[neighbor]
            # try the neighbor node with a lower g_score than the previous node
            if tentative_g_score < g_score[neighbor]:
                # if it is an 'or' node or if the and all parents to the 'and' node has been visited,
                # continue to try this path
                if all_parents_visited(neighbor, visited, index):
                    came_from[neighbor].append(current_node)
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + h_score[neighbor]
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                # if the node is an 'and' node, still update the node cost and keep track of the path
                elif is_and_node(neighbor, index):
                    costs[neighbor]=tentative_g_score
                    came_from[neighbor].append(current_node)
    return "path not found"


''' 
calculate the random path (according to option 1)
'''
def random_path(atkgraph, start_node, target_node, index):
    node_ids = list(index.keys())

    visited = set()  # Store the IDs of visited nodes to avoid revisiting them
    visited.add(start_node)

    stack = [start_node]

    came_from = dict.fromkeys(node_ids, '')
    came_from = fill_dictionary_with_empty_list(came_from)

    costs = get_costs_for_nodes(atkgraph)
    cost = 0

    current_node = start_node
    while current_node != target_node:
        links = index[current_node]['links']
        # all paths has been tried
        if len(stack) == 0: 
            return "Path not found"
        # leaf in graph     
        if len(links) == 0:
            current_node = stack.pop()
            links = index[current_node]['links']
    
        # select a node from the link list
        neighbor = random.choice(links)

        # a node which has not been visited yet was selected
        if neighbor not in visited:
            if all_parents_visited(neighbor, visited, index):
                came_from[neighbor].append(current_node)
                current_node = neighbor
                stack.append(current_node)
                visited.add(neighbor)
                cost+=costs[current_node]
                if is_and_node(neighbor, index):
                    came_from[neighbor] = index[neighbor]["parent_list"]
            elif len(links)>1 and not all_neighbors_visited(links, visited):
                continue
            else:
                # temporarily unreachable 'and' node was found
                current_node = stack.pop()
    
    
    for key in index.keys():    
        index[key]["links"] = [] 
    path = reconstruct_path(came_from, current_node, start_node, costs, index, set())
    

    return path  
   
