from collections import deque
import heapq
import random
import re


def all_parents_visited(node_id, visited, index):
    """
    Checks if the dependency steps for a node are completed.
    This includes also checking the reachability of the node.

    Arguments:
    node_id              - node ID.
    index                - a dictionary representing the attack graph.

    Return:
    True if the node is an 'or' node.
    True if the node is an 'and' node which is reachable and all dependency steps has been visited.
    Otherwise False.
    """
    if is_and_node(node_id, index):
        # check reachability
        if not is_reachable(node_id, index):
            return False
        # check if all dependency steps has been visited
        for parents in index[node_id]["parent_list"]:
            if parents not in visited:
                return False 
    return True

def is_reachable(node_id, index):
    """
    Returns the nodes is_reachable value.

    Arguments:
    node_id              - node ID.
    index                - a dictionary representing the attack graph.

    Return:
    True or False according to the is_reachable property.
    """
    return index[node_id]["is_reachable"]

def is_and_node(node_id, index):
    """
    Checks if node is an 'and' node.

    Arguments:
    node_id              - node ID.
    index                - a dictionary representing the attack graph.

    Return:
    True if the node is an 'and' node, otherwise False.
    """
    if index[node_id]["type"] == "and":
       return True
    return False

def reconstruct_path(came_from, current, start_node, costs, index, visited=set()):
    """
    Reconstructs the path found by the Dijksta algorithm and calculates the total cost for the path.

    Arguments:
    came_from            - a dictionary representing the path on the form {Node ID: [Node ID, ...]}. The nodes in the values has links to the corresponding node in the key.
    current              - current node id for a node in the path. At the start this is the target node ID.
    start_node           - node ID for the start node
    costs                - a dictionary representing the costs for all nodes on the form {Node ID: cost, ...}.
    index                - a dictionary representing the attack graph.
    visited              - set of visited nodes.


    Return:
    A tuple on the form (cost, index, visited, _)
    cost                 - integer representing the total cost of the path-.
    index                - a dictionary representing the attack graph. The "path_links" property contains the paths.
    visited              - a set of nodes in the path.
    """
    cost = 0
    if current != start_node:
        # reconstruct the path until the start node is reached
        while current in came_from.keys() and current != start_node:
            old_current = current
            # link from current -> old_current
            current = came_from[current]
            # condition for 'and' node       
            if len(current)>1:
                for node in current:
                    path_cost, _, _, _ = reconstruct_path(came_from, node, start_node, costs, index, visited)
                    cost += path_cost+costs[old_current]
                    index[old_current]["path_links"].append(old_current)
                break
            else:
                current = current[0]
                if old_current not in visited:
                    cost += costs[old_current]
                    visited.add(old_current)
                if old_current not in index[current]["path_links"]:
                    index[current]["path_links"].append(old_current) 
        visited.add(start_node)
    return cost, index, visited, old_current
    
def fill_dictionary_with_empty_list(dict):
    """
    Fills a dictionary with empty lists as the values

    Arguments:
    dict            - dictionary with keys.

    Return:
    A dictionary with the same keys and empty lists as the values.
    """
    for key in dict.keys():
        dict[key] = list()
    return dict

def get_costs(index):
    """
    Gets the cost for all nodes in the graph.

    Arguments:
    index           - dictionary representing the attack graph.

    Return:
    A dictionary containing all node IDs as keys, and the costs as values.
    """
    dict = {}
    for key in index.keys():
        node = index[key]
        if not node['ttc'] == None: # for the attacker node, the ttc is None
            dict[key]=node['ttc']['cost'][0]
    return dict


def bfs(source, index, max_distance):
    """
    Breadth First Search with changed stop condition.
    Gets a subgraph with nodes which is at a lower or equal distance/cost than a max distance value.

    Arguments:
    source               - node ID.
    index                - a dictionary representing the attack graph.
    max_distance         - integer representing the max distance/cost

    Return:
    A set of nodes included in the subgraph
    """
    nodes = {}
    queue = deque([(source, 0)])  # Start BFS from the start node with distance 0
    visited = set([source])  # Keep track of visited nodes
    # Perform Breadth-First Search (BFS) from the start node
    while queue:
        node, distance = queue.popleft()
        if distance > max_distance:
            break
        # reset the "path_links" attribute
        index[node]["path_links"] = index[node]["links"]
        # Assign the distance from the source for each node
        nodes[node] = index[node]  
        # Explore the neighbors of the current node
        for link in index[node]["links"]:
            if link not in visited:
                visited.add(link)
                queue.append((link, distance + index[link]['ttc']['cost'][0]))
    return nodes

def dijkstra(start_node, target_node, index):
    """
    Finds the shortest path between two nodes with Dijkstra's algorithm, with added conditions for processing the 'and' nodes.

    Arguments:
    start_node           - Node ID of the start node (this is often the attacker node id).
    target_node          - Node ID of the target node.
    index                - a dictionary on the form {node ID: node as dictionary, ...}, representing the attack graph.

    Return:
    A tuple on the form (cost, index, visited, _)
    cost                 - integer representing the total cost of the path-.
    index                - a dictionary representing the attack graph. The "path_links" property contains the paths.
    visited              - a set of nodes in the path.
    """
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

    # TODO calculate the h_score for all nodes
    h_score = dict.fromkeys(node_ids, 0)
   
    # for node n, f_score[n] = g_score[n] + h_score(n). f_score[n] represents our current best guess as to
    # how cheap a path could be from start to finish if it goes through n.
    f_score = dict.fromkeys(node_ids, 0)
    f_score[start_node] = h_score[start_node] # TODO calculate the h_score for all nodes
    
    costs = get_costs(index)
    costs_copy = costs.copy()

    current_node = start_node
    while len(open_set) > 0:
        # current_node is the node in open_set having the lowest f_score value
        current_score, current_node = heapq.heappop(open_set)
        visited.add(current_node)

        if current_node == target_node:
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
                    f_score[neighbor] = tentative_g_score + h_score[neighbor] # TODO calculate the h_score for all nodes
                    if neighbor not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                # if the node is an 'and' node, still update the node cost and keep track of the path
                elif is_and_node(neighbor, index):
                    costs[neighbor]=tentative_g_score
                    came_from[neighbor].append(current_node)
    return 

def random_path(start_node, index, target_node=None, cost_budget=None):
    """
    Get a random path in the attack graph. 
    It is possible to search for a target_node and/or use a cost_budget.

    Arguments:
    start_node           - Node ID of the start node (this is often the attacker node id).
    index                - a dictionary on the form {node ID: node as dictionary, ...}, representing the attack graph.
    target_node          - Node ID of the target node.
    cost_budget          - integer representing the attacker cost budget.

    Return:
    A tuple on the form (cost, index, visited).
    cost                 - integer representing the total cost of the path.
    index                - a dictionary representing the attack graph. The "path_links" property contains the paths.
    visited              - a set of nodes in the path.
    """
    node_ids = list(index.keys())
    visited = set()  
    visited.add(start_node)
    came_from = dict.fromkeys(node_ids, '')
    horizon = set()
    target_found = False
    unreachable_horizon_nodes = set()
    # initialize the attack horizon
    for node_id in index[start_node]["links"]:
        horizon.add(node_id)
        came_from[node_id] = start_node
    costs = get_costs(index)
    cost = 0
    if target_node == None and cost_budget == None:
        return cost, index, visited
    while len(horizon) > 0 and unreachable_horizon_nodes != horizon:
        node = random.choice(list(horizon))
        # attack unvisited node
        if all_parents_visited(node, visited, index):
            if cost_budget != None and cost+costs[node] > cost_budget:
                break
            visited.add(node)
            index[came_from[node]]["path_links"].append(node) 
            cost += costs[node]
            if node in unreachable_horizon_nodes:
                unreachable_horizon_nodes.remove(node)
            # update the horizon
            horizon.remove(node)
            for node_id in index[node]['links']:
                horizon.add(node_id)
                came_from[node_id] = node
            # check if the target was selected
            if target_node != None and node == target_node:
                target_found = True
                print("the target,", target_node,"was found!")
                break
        else:
            unreachable_horizon_nodes.add(node)
    # check if the target never was selected in the path
    if target_node != None and target_found == False:
        print("the target,", target_node, "was not found!")
    return cost, index, visited

# all AO* functions are below here:

def ao_star(atkgraph, start_node, index):
    """
    AO* main function.
    TODO connect this to the rest of the code?
    """
    H = get_heuristics_for_nodes(index, start_node)
    weight = get_costs(index)
    and_nodes = get_and_nodes(atkgraph)
    adjacency_list = get_adjacency_list(atkgraph, and_nodes)
    print(adjacency_list)
    Updated_cost = update_cost(H, adjacency_list, weight)
    shortest_path_str = shortest_path_ao_star(start_node, Updated_cost, H)
    print(shortest_path_str)
    total_cost = calculate_shortest_path_cost(shortest_path_str, weight, H)
    return shortest_path_str, total_cost

def calculate_shortest_path_cost(shortest_path_str, cost, heuristics):
    """
    AO* function.
    """
    nodes = re.findall(r'\b\w+\b', shortest_path_str)
    total_cost = 0
    visited = set()
    for i, node in enumerate(nodes):
        if node == 'OR':
            if nodes.count(nodes[i-1]) > 1:
                visited.add(nodes[i-1])
                del nodes[i+1]
            elif nodes.count(nodes[i+1]) > 1:
                visited.add(nodes[i+1])
                del nodes[i-1]
            continue
        if node not in ['AND', 'OR'] and node not in visited:
            visited.add(node)
    # Calculate the total cost for visited nodes
    for node in visited:
        total_cost += cost[node] + heuristics[node]
    return total_cost

def shortest_path_ao_star(Start, Updated_cost, H):
    """
    AO* function.
    """
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

def update_cost(H, Conditions, weight):
    """
    AO* function.
    """
    Main_nodes = list(Conditions.keys())
    Main_nodes.reverse()
    least_cost= {}
    for key in Main_nodes:
        condition = Conditions[key]
        print(key,':', Conditions[key],'>>>', Cost(H, condition, weight))
        c = Cost(H, condition, weight)
        least_cost[key] = Cost(H, condition, weight)
    return least_cost

def get_and_nodes(atkgraph):
    """
    AO* function.
    """
    list = set()
    for node in atkgraph:
        if node['type'] == 'and':
            list.add(node['id'])
    return list  

def get_adjacency_list(atkgraph, and_nodes):
    """
    AO* function
    """
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
    return dict 

def Cost(H, condition, weight):
    """
    AO* function.
    """
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

def get_heuristics_for_nodes(index, target_node):
    """
    AO* function.
    Breadth-First Search (BFS), starting from the target node.
    """
    heuristics = {}
    i=0
    # Perform Breadth-First Search (BFS) from the target node
    queue = deque([(target_node, 0)])  # Start BFS from the target node with distance 0
    visited = set([target_node])  # Keep track of visited nodes
    while queue:
        i+=1
        node, distance = queue.popleft()
        heuristics[node] = distance  # Assign the distance as the heuristic value
        # Explore the neighbors of the current node
        parent_list = index[node]["parent_list"]
        for parent in parent_list:
            if parent not in visited:
                visited.add(parent)
                queue.append((parent, distance + 1))  # Increment the distance by 1 for each neighbor
    print("graph",i)
    return heuristics