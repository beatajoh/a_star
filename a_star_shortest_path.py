import math
import json
from collections import deque
import heapq

def all_parents_visited(atkgraph, neighbor, open_set, parent_nodes, visited):
    print("="*100)
    print("neighbor:" + neighbor)
    print("parent_nodes: ", parent_nodes)
    print("="*100)
    if neighbor in parent_nodes:
        print("AND NODE!!!",neighbor)
        for parents in parent_nodes[neighbor]:
            if visited[parents] == 0:
                print("FALSE AND", neighbor)
                return False 
    return True
    
def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from.keys():
        current = came_from[current]
        print("CURRENT",current)
        total_path.insert(0,current)
    return total_path

def fill_dictionary(atkgraph, score):
    scores = {}
    for node in atkgraph:
        scores[node['id']] = score
    return scores

def get_neighbor_nodes(atkgraph): 
    dict = {}
    for node in atkgraph:
        dict[node['id']] = node['links']
    return dict

def get_parent_nodes_for_and_nodes(atkgraph): 
    dict = {}
    for node in atkgraph:
        if node['type'] == 'and':
            dict[node['id']] = node['parent_list']
    return dict

def get_costs_for_nodes(atkgraph):
    dict = {}
    for node in atkgraph:
        print(node)
        if not node['ttc']==None: # for the attacker node, the ttc is None
            dict[node['id']]=node['ttc']['cost'][0]
    return dict

def calculate_heuristic(node, target, atkgraph):
    if 'ttc' in node and 'cost' in node['ttc']:
        path_cost = 0
        current_node = node
        while current_node['id'] != target['id']:
            path_cost += sum(current_node['ttc']['cost'])
            next_node_id = current_node['links'][0]  # assuming there is only one outgoing link
            next_node = next(n for n in atkgraph if n['id'] == next_node_id)
            current_node = next_node

        path_cost += sum(current_node['ttc']['cost'])

        return path_cost


# def calculate_heuristic(node, target, atkgraph):
#     if 'ttc' in node and 'cost' in node['ttc']:
#         path_cost = 0
#         current_node = node
#         first_node_visited = False

#         while current_node['id'] != target['id']:
#             if first_node_visited:
#                 path_cost += sum(current_node['ttc']['cost'])
#             else:
#                 first_node_visited = True
#             next_node_id = current_node['links'][0]  # assuming there is only one outgoing link
#             next_node = next(n for n in atkgraph if n['id'] == next_node_id)
#             current_node = next_node

#         path_cost += sum(current_node['ttc']['cost'])

#         return path_cost

def a_star(atkgraph):

    start_node = "A" # id attribute in json file

    target_node = "H"

    open_set = []
    heapq.heappush(open_set, (0, start_node))

    visited = fill_dictionary(atkgraph,0)
    visited[start_node]=1
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
    neighbor_nodes = get_neighbor_nodes(atkgraph)
    parent_nodes = get_parent_nodes_for_and_nodes(atkgraph)

    current_node = start_node

    while len(open_set) > 0:
        print("OPEN SET        ",open_set)
        # current_node = the node in openSet having the lowest f_score value
        current_score, current_node = heapq.heappop(open_set)
        visited[current_node]=1

        if current_node == target_node:
            print("Finished")
            print(visited)
            print(came_from)
            return reconstruct_path(came_from, current_node)

        current_neighbors = neighbor_nodes[current_node]
        print(current_neighbors)
        for neighbor in current_neighbors:
            print(neighbor)
            
            tentative_g_score = g_score[current_node]+costs[neighbor] # d(current, neighbor)

            if tentative_g_score < g_score[neighbor]:
                if all_parents_visited(atkgraph, neighbor, open_set, parent_nodes, visited):
                    came_from[neighbor] = current_node
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + h_score[neighbor]
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (g_score[neighbor], neighbor))
                    
    print("shortest path found ?")

    return False # Open set is empty but goal was never reached
   