from collections import deque
import json

class Node:
    def __str__(self):
        return f"Node: {self.node_id}, g_cost = {self.g_cost}, h_cost = {self.h_cost}, f_cost = {self.f_cost}, type = {self.type}, parents = {[node.node_id for node in self.parents]}, links = {self.links}, parent_list = {self.parent_list}, actual_cost = {self.actual_cost}"

    def __init__(self, node_id, parent=None):
        self.node_id = node_id
        self.g_cost = float('inf')  # Cost from the start node to this node
        self.h_cost = float('inf')  # Heuristic cost (estimated cost) from this node to the goal
        self.f_cost = float('inf')  # Total cost: f_cost = g_cost + h_cost
        self.type = None
        self.parents = [parent] if parent else []
        self.links = []
        self.parent_list = []
        self.actual_cost = float('inf')

def create_node_dict(atkgraph, heuristics):
    node_dict = {}
    for node_data in atkgraph:
        node_id = node_data["id"]
        node = Node(node_id)
        node.h_cost = heuristics.get(node_id, float('inf'))
        node.links = node_data.get("links", [])
        node.type = node_data.get("type", None)
        node.parent_list = node_data.get("parent_list", [])
        ttc_data = node_data.get("ttc", {})
        node.actual_cost = ttc_data.get("cost", [])[0]
        if node.type == "defense":
            if node_data["defense_status"] and "value" in node_data["defense_status"] and node_data["defense_status"]["value"] == "1.0":
                node.g_cost = float('inf')
            else:
                node.g_cost = float(0)
        if node.type == "exists" or node.type == "notExists":
            node.g_cost = float(0)
        node_dict[node_id] = node

    return node_dict

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

def get_node_by_id(node_id, atkgraph):
    for node in atkgraph:
        if node["id"] == node_id:
            return node
    return None

def get_list_node_by_id(node_id, node_list):
    for node in node_list:
        if node.node_id == node_id:
            return node
    return None

def get_heuristics_for_nodes(atkgraph, target_node):
    heuristics = {}
    queue = deque([(target_node, 0)])  # Start BFS from the target node with distance 0
    visited = set([target_node])  # Keep track of visited nodes

    while queue:
        node, distance = queue.popleft()
        heuristics[node] = distance  # Assign the distance as the heuristic value
        for other_node in atkgraph:
            if other_node['id'] == node:
                parent_list = other_node['parent_list']
                break    
        for parent in parent_list:
            if parent not in visited:
                visited.add(parent)
                queue.append((parent, distance + 1))  # Increment the distance by 1 for each neighbor
    
    return heuristics

def calculate_and_cost(current_node, neighbor_node, node_dict):
    # Calculate the cost of an AND node by considering the maximum g_cost of its child nodes
    cost = neighbor_node.actual_cost
    # print("************AND_NODE***********")
    for parent_node_id in neighbor_node.parent_list:
        # print(f'For AND node {neighbor_node.node_id} check parent node id {parent_node_id}')
        cost += node_dict[parent_node_id].g_cost
        
    return cost

def calculate_or_cost(current_node, neighbor_node, node_dict):
    # Calculate the cost of an OR node by considering the minimum g_cost of its child nodes
    return current_node.g_cost + neighbor_node.actual_cost


def a_star_search(start_node_id, goal_node_id, atkgraph):
    heuristics = get_heuristics_for_nodes(atkgraph, goal_node_id)
    node_dict = create_node_dict(atkgraph, heuristics)
    start_node = node_dict[start_node_id]
    start_node.g_cost = 0
    goal_node = node_dict[goal_node_id]
    # print(f'start_node: {start_node}')
    # print(f'goal_node: {goal_node}')
    open_list = [start_node]
    closed_list = []

    while open_list:
        open_list.sort(key=lambda node: (node.f_cost))  # Sort open_list by heuristic value and g Cost
        current_node = open_list.pop(0)  # Select the node with the lowest heuristic

        closed_list.append(current_node)
        # print("-"*100)
        # print(f'current_node.node_id : {current_node.node_id}')
        # print(f'goal_node.node_id: {goal_node.node_id}')

        if current_node.node_id == goal_node.node_id:
            path = []
            current_nodes = [current_node]
            total_cost = current_node.f_cost
            while current_nodes:
                node = current_nodes.pop()
                if node in path:
                    continue
                path.append(node)
                for parent_node in node.parents:
                    current_nodes.append(parent_node)
                # print(f'CURRENT PATH {[node.node_id for node in path]}')

            # Print the costs of every node on the path
            # print("Heuristics of nodes on the path:")
            for node_id in path:
                node_cost = heuristics[node_id] if node_id in heuristics else -1
                # print(f"{node_id}, cost = {node_cost}")

            return path, total_cost

        for neighbor_node_id in current_node.links:
            # print(f'neighbor_node_id: {neighbor_node_id}')
            neighbor_node = node_dict[neighbor_node_id]
            node_type = neighbor_node.type

            # Calculate the new tentative g_cost for this neighbor
            if node_type == "and":
                tentative_g_cost = calculate_and_cost(current_node, neighbor_node, node_dict)
            else:
                tentative_g_cost = calculate_or_cost(current_node, neighbor_node, node_dict)

            # Check if the neighbor node is already in the open list
            in_open_list = False
            for node in open_list:
                if node.node_id == neighbor_node.node_id:
                    in_open_list = True
                    break

            # print(f'Comparing new tenatitve G cost {tentative_g_cost} to old cost of {neighbor_node.g_cost}')
            if tentative_g_cost < neighbor_node.g_cost:
                neighbor_node.g_cost = tentative_g_cost
                neighbor_node.f_cost = neighbor_node.g_cost + neighbor_node.h_cost
                if neighbor_node.type == "and":
                    for parent_node_id in neighbor_node.parent_list:
                        neighbor_node.parents.append(node_dict[parent_node_id])
                else:
                    neighbor_node.parents = [current_node]
                if not in_open_list:
                    # Add the neighbor to the open list
                    open_list.append(neighbor_node)
        # print("-"*100)
        # for node in open_list:
            # print(f'{node.node_id}: G:{node.g_cost} H:{node.h_cost} F:{node.f_cost} A:{node.actual_cost}')
    
    return None, None

with open("/home/kali/Documents/tyr_mal_infrastructure/mgg-project/interface/test_graphs/MODIFIED_network_connect_authenticate_attack_graph.json", 'r') as readfile:
    atkgraph=json.load(readfile)

atkgraph = get_parents_for_and_nodes(atkgraph)

with open("/home/kali/Documents/tyr_mal_infrastructure/mgg-project/interface/test_graphs/MODIFIED_network_connect_authenticate_attack_graph.json", 'w', encoding='utf-8') as writefile:
    json.dump(atkgraph, writefile, indent=4)

start_node_id = "Attacker:-8931970777742292796:firstSteps"
goal_node_id = "Application:8326449865063550222:fullAccess"
shortest_path, total_cost = a_star_search(start_node_id, goal_node_id, atkgraph)

# print("-"*100)
if shortest_path:
    print(f"Shortest path: {[node.node_id for node in shortest_path]}")
    print("Total cost to end node:", total_cost)
else:
    print("No path found.")