
import json
from collections import deque
import heapq

def all_parents_visited(atkgraph, neighbor, open_set, parent_nodes, visited, f_score):
    #print(neighbor)
    #print(parent_nodes)
    if neighbor in parent_nodes:
        print("AND NODE!!!",neighbor)
        for parents in parent_nodes[neighbor]:
            if visited[parents] == 0:
                print("FALSE AND", neighbor)
                return False 
    return True

def is_and_node(neighbor, parent_nodes):
    if neighbor in parent_nodes:
       return True
    return False

def reconstruct_path(came_from, current, start_node):
    if current != start_node:
        total_path = [current]
        while current in came_from.keys():
            current = came_from[current]
            if current == '':
                break
            if len(current)>1:
                for node in current:
                    path = reconstruct_path(came_from, node, start_node)
                    total_path.insert(0,path)
            else:
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
        #print(node)
        if not node['ttc']==None: # for the attacker node, the ttc is None
            dict[node['id']]=node['ttc']['cost'][0]
    return dict

def a_star(atkgraph):

    start_node = "A" # id attribute in json file
    print(start_node)
    target_node = "E"

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

    costs = get_costs_for_nodes(atkgraph)
    neighbor_nodes = get_neighbor_nodes(atkgraph)
    parent_nodes = get_parent_nodes_for_and_nodes(atkgraph)

    current_node = start_node

    while len(open_set) > 0:
        print("OPEN SET        ",open_set)
        # current_node = the node in openSet having the lowest f_score value
        current_score, current_node = heapq.heappop(open_set)
        visited[current_node]=1
        print(visited)

        if current_node == target_node:
            print("Finished")
            #print(visited)
            #print(came_from)
            print(f_score)
            print(came_from)
            return reconstruct_path(came_from, current_node, start_node)

        current_neighbors = neighbor_nodes[current_node]
        #print(current_neighbors)
        for neighbor in current_neighbors:
            #print("CURRENT NODE: ", neighbor,"F COST:  ", f_score[current_node])
            
            tentative_g_score = g_score[current_node]+costs[neighbor] # d(current, neighbor)
            
            #print("NEIGHBOR NODE: ", neighbor,"G COST:", costs[neighbor])
            #print("NEIGHBOR NODE: ", neighbor,"NEW G COST:", tentative_g_score)
            #print("NEIGHBOR NODE: ", neighbor,"(OLD) NEIGHBOR G COST:", g_score[neighbor])


            if tentative_g_score < g_score[neighbor]:
                # True if neighbor node can be visited  
                if all_parents_visited(atkgraph, neighbor, open_set, parent_nodes, visited, f_score):
                    # might need logic here before for equal shortest paths with same cost?
                    came_from[neighbor] += current_node
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + 0 # h(neighbor) = 0
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                elif is_and_node(neighbor, parent_nodes):
                    costs[neighbor]=tentative_g_score   # even if we can't continue to the and node, still update the node cost
                    came_from[neighbor]+=current_node
                    print(came_from)
             
                    
    print("shortest path found?")

    return False # Open set is empty but goal was never reached
   