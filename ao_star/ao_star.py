import json
from collections import deque
import re

# Cost to find the AND and OR path
def Cost(H, condition, weight):
    cost = {}
    if 'AND' in condition:
        AND_nodes = condition['AND']
        Path_A = ' AND '.join(AND_nodes)
        PathA = sum(H[node]+weight[node] for node in AND_nodes)
        cost[Path_A] = PathA

    if 'OR' in condition:
        OR_nodes = condition['OR']
        if OR_nodes:
            Path_B =' OR '.join(OR_nodes)
            PathB = min(H[node]+weight[node] for node in OR_nodes)
            cost[Path_B] = PathB

    return cost


# Update the cost
def update_cost(H, Conditions, weight):
    Main_nodes = list(Conditions.keys())
    Main_nodes.reverse()
    least_cost= {}
    for key in Main_nodes:
        condition = Conditions[key]
        print(key,':', Conditions[key],'>>>', Cost(H, condition, weight))
        least_cost[key] = Cost(H, condition, weight)
    return least_cost

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
Traverse the attack graph .json file and get all parents to 'and' nodes and add new 'parent_list' attribute to the file.
parent_list is an array of attack step ids.
'''
def get_parents_for_and_nodes(atkgraph):
    n=0
    id=""
    id2=""
    for i, node in enumerate(atkgraph):
        id=node["id"]
        parent_list=[]
        if node["type"]=="and":
            for node2 in atkgraph:
                id2=node2["id"]
                for link in node2["links"]:
                    if link==id and node2["type"] in ["and", "or"]:
                        parent_list.append(id2)
            n+=1
            atkgraph[i]["parent_list"]=parent_list
        else:
            for node2 in atkgraph:
                id2=node2["id"]
                for link in node2["links"]:
                    if link==id and node2["type"] in ["and", "or"]:
                        parent_list.append(id2)
            n+=1
            atkgraph[i]["parent_list"]=parent_list
    return atkgraph

def get_and_nodes(atkgraph):
    list = set()
    for node in atkgraph:
        if node['type'] == 'and':
            list.add(node['id'])
    return list    

def get_adjacency_list(atkgraph, and_nodes):
    dict = {}
    or_and = ''
    for node in atkgraph:
        adjacent = {}
        if node['id'] in and_nodes:
            or_and = 'AND'
        else: 
            or_and = 'OR'
        adjacent[or_and] = []
        for parent in node['parent_list']:
            adjacent[or_and].append(parent)
        dict[node['id']] = adjacent
    # print("the result", dict)
    return dict 

'''
Performing a graph traversal algorithm, 
breadth-first search (BFS), starting from the target node.
'''
def get_heuristics_for_nodes(atkgraph, target_node):
    heuristics = {}
    
    # Perform Breadth-First Search (BFS) from the target node
    queue = deque([(target_node, 0)])  # Start BFS from the target node with distance 0
    visited = set([target_node])  # Keep track of visited nodes

    while queue:
        node, distance = queue.popleft()
        heuristics[node] = distance  # Assign the distance as the heuristic value
        # Explore the neighbors of the current node
        for other_node in atkgraph:
            if other_node['id'] == node:
                parent_list = other_node['parent_list']
                break    
        for parent in parent_list:
            if parent not in visited:
                visited.add(parent)
                queue.append((parent, distance + 1))  # Increment the distance by 1 for each neighbor
    
    return heuristics


def shortest_path_ao_star(Start, Updated_cost, H):
    Path = Start
    if Start in Updated_cost.keys():
        values = Updated_cost[Start].values()
        if values:
            Min_cost = min(values)
            key = list(Updated_cost[Start].keys())
            Index = list(Updated_cost[Start].values()).index(Min_cost)
            Next = key[Index].split()
            if len(Next) == 1:
                Start = Next[0]
                path = shortest_path_ao_star(Start, Updated_cost, H)
                Path += '<--' + path
            else:
                if "AND" in Next:
                    Path += '<--(' + key[Index] + ') ['
                    for i in range(len(Next)):
                        if Next[i] == "AND":
                            continue
                        Start = Next[i]
                        path = shortest_path_ao_star(Start, Updated_cost, H)
                        Path += path
                        if i < len(Next) - 1:
                            Path += ' + '
                    Path += ']'
                else:
                    Path += '<--(' + key[Index] + ') '
                    Start = Next[0]
                    path = shortest_path_ao_star(Start, Updated_cost, H)
                    Path += path

    return Path

def calculate_shortest_path_cost(shortest_path_str, cost, heuristics):
    nodes = re.findall(r'\b\w+\b', shortest_path_str)
    total_cost = 0
    visited = set()

    for node in nodes:
        if node not in ['AND', 'OR'] and node not in visited:
            total_cost += cost[node] + heuristics[node]
            visited.add(node)

    return total_cost


# H = {'H': 0, 'E': 1, 'C': 2, 'F': 2, 'B': 3, 'D': 3, 'A': 4, 'G': 4}


# with open("atkgraph.json", 'r') as readfile:
#     atkgraph=json.load(readfile)
with open("../test_graphs/small_graph_2.json", 'r') as readfile:
    atkgraph=json.load(readfile)

atkgraph = get_parents_for_and_nodes(atkgraph)


# with open("atkgraph.json", 'w', encoding='utf-8') as writefile:
#     json.dump(atkgraph, writefile, indent=4)
with open("../test_graphs/small_graph_2.json", 'w', encoding='utf-8') as writefile:
    json.dump(atkgraph, writefile, indent=4)

target_node = 'H'  
H = get_heuristics_for_nodes(atkgraph, target_node)
print('Heuristics: ',H)
weight = get_costs_for_nodes(atkgraph)
print("="*150)
print('Cost: ', weight)
and_nodes = get_and_nodes(atkgraph)

adjacency_list = get_adjacency_list(atkgraph, and_nodes)
print("-"*150)
print('Adjacency list: ', adjacency_list)
print("="*150)
Updated_cost = update_cost(H, adjacency_list, weight)
print("-"*150)
print('Updated costs: ', Updated_cost)
print("*"*150)
shortest_path_str = shortest_path_ao_star(target_node, Updated_cost, H)
print('Shortest Path:\n', shortest_path_str)

total_cost = calculate_shortest_path_cost(shortest_path_str, weight, H)
print('Total Cost:', total_cost)

