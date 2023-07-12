import os
import json
import attack_simulations as atksim
import upload as upload_json_to_neo4j
from py2neo import Graph

import sys
sys.path.insert(1, '/Users/beatajohansson/Projects/mgg')
import mgg
import mgg.atkgraph

class console_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

start_commands = {
    "1": "step-by-step-attack",
    "2": "attack-simulation",
    "3": "exit"
    }

step_by_step_attack_commands = {
    "1": "horizon",
    "2": "action",
    "3": "exit"
    }

action_commands = {
    "1": "enter node id"
    }

attack_simulation_commands = {
    "1": "shortest-path-dijkstra",
    "2": "shortest-path-AO-star",
    "3": "random-path",
    "4": "attack-range-BFS",
    "5": "exit"
    }

def step_by_step_attack_simulation(graph, atkgraph, index, file):
    print(f"{console_colors.HEADER}step-by-step-attack{console_colors.ENDC}")

    # add all links to the path_links attribute
    for key in index.keys():
        index[key]["path_links"] = index[key]["links"]
    
    # initialize visited nodes
    visited = set()

    # mark the attacker node as visited by adding the node id to visited
    visited.add(atkgraph[-1]['id'])

    # initialize the horizon
    horizon = set()
    for node in visited:
        horizon = update_horizon(node, horizon, index)
       
    while True:
        print_options(step_by_step_attack_commands)

        command = input("choose: ")

        if command == '1':
            print_horizon(horizon, index)
        elif command == '2':
            # choose next node name to visit       
            node_options = get_horizon_w_commands(horizon)  # TODO print the node type
            print_options(node_options)
            option = input("choose node to attack: ")
            attack_node = node_options[int(option)]

            # update horizon
            if attack_node in horizon and atksim.all_parents_visited(attack_node, visited, index):
                visited.add(attack_node)
                horizon.remove(attack_node)
                horizon = update_horizon(attack_node, horizon, index)
                # store the path and horizon to file
                add_nodes_to_json_file(file, visited, index)   
                add_horizon_nodes_to_json_file(file, horizon, index)
                upload_json_to_neo4j.upload_json_to_neo4j_database(file, graph)
            else:
                print("could not attack this node because all dependency steps has not been visited")
            print_horizon(horizon, index)
        elif command == '3':
            break

def add_horizon_nodes_to_json_file(file, horizon, index):
    with open(file, 'r', encoding='utf-8') as writefile:
        data = json.load(writefile) 
        for node_id in horizon:
            node = index[node_id]
            node["horizon"] = True
            data.append(node)
    with open(file, 'w', encoding='utf-8') as writefile:
        json.dump(data, writefile, indent=4)
    print("The attack horizon is added to the file", file)

def update_horizon(node, horizon, index):
    for link in index[node]['links']:
        horizon.add(link)
    return horizon

def add_nodes_to_json_file(file, visited, index):
    data = [] 
    open(file, 'w').close() # remove all file contents
    with open(file, 'w', encoding='utf-8') as writefile:
        for node_id in visited:
            node = index[node_id]
            node["horizon"] = False
            data.append(node)
        json.dump(data, writefile, indent=4)
    print("The path is added to the file", file)


def get_horizon_w_commands(horizon):
    dict = {}
    for i, node in enumerate(horizon):
        dict[i+1] = node
    return dict

def print_horizon(horizon, index):
    print(f"{console_colors.FAIL}Attacker Horizon{console_colors.ENDC}")
    for i, node in enumerate(horizon):
        print(f"{console_colors.BOLD}", "(", i+1, ")", node, index[node]["type"])
    print(f"{console_colors.ENDC}")


def get_parents_for_and_nodes(atkgraph):
    n = 0
    id = ""
    id2 = ""
    for i, node in enumerate(atkgraph):
        id = node["id"]
        parent_list = []
        for node2 in atkgraph:
            id2 = node2["id"]
            for link in node2["links"]:
                if link == id and node2["type"] in ["and", "or"]:
                    parent_list.append(id2)
        n+=1
        atkgraph[i]["parent_list"]=parent_list
    return atkgraph


def attack_simulation(graph, atkgraph, index, file):
    print(f"{console_colors.HEADER}Attack-Simulation{console_colors.ENDC}")
   
    while True:
        print_options(attack_simulation_commands)
        command = input("choose: ")
        start_node = atkgraph[-1]['id'] # TODO change this
        path = None

        # clear path_links attribute
        for key in index.keys():
            index[key]["path_links"] = []

        if command == '5':
            break
        elif command == '1':
            print("shortest path dijkstra")
            target_node = input("enter target node id: ")
            result = atksim.dijkstra(start_node, target_node, index)
            if result != None:
                total_cost = result[0]
                path = result[1]
                print("cost: ", total_cost)
        elif command == '2':    #TODO add to the rest
            print("shortest path AO star")
            #target_node = input("enter target node id: ")
            #path, cost = atksim.ao_star(atkgraph, target_node, index)
            #print("cost: ", cost)
            target_node = "Application:7219598629313512:networkConnect"
            path, cost = atksim.ao_star(atkgraph, target_node, index)    
        elif command == '3':
            print("random path")
            target_node = input("enter target node id (press enter to run without target): ")
            attack_budget = input("enter attack budget (press enter to run without target): ")
            if target_node == "":
                target_node = None
            if attack_budget != "":
                attack_budget = int(attack_budget)
            if attack_budget == "":
                attack_budget = None
            result = atksim.random_path(start_node, index, target_node=target_node, cost_budget=attack_budget)
            if result != None:
                total_cost = result[0]
                path = result[1]
                print("cost: ", total_cost)
        elif command == '4': # TODO for this subgraph to be correct we should also do a reachability analysis before... and check the dependency steps for the and nodes
            print("attack range BFS")
            max_distance = int(input("enter maximum distance (cost): "))
            path = atksim.bfs(start_node, index, max_distance)
        
        if path != None:
            add_nodes_to_json_file(file, path.keys(), path)
            upload_json_to_neo4j.upload_json_to_neo4j_database(file, graph)
        else: 
            print("no result")
        


def index_nodes_by_id(atkgraph):
    dict = {}
    for node in atkgraph:
        node["path_links"] = []
        dict[node["id"]] = node
    return dict

def print_options(args):
        for arg in args:
            command = arg
            description = args[command]
            print(f"{console_colors.BOLD}", "(", command, ")", end=" ")
            print(f"{console_colors.BOLD}", description)
        print(f"{console_colors.ENDC}",end="")

def choose_atkgraph_file(directory):
    print("which attack graph file do you want to load?")
    options = get_files_in_directory(directory)
    print_options(options)
    command = input("choose: ")
    file = options[int(command)]
    return os.path.join(directory, file)


def get_files_in_directory(directory):
    dict = {}
    for i, filename in enumerate(os.listdir(directory)):
        # Check if the current item is a file
        if os.path.isfile(os.path.join(directory, filename)):
            dict[i+1] = filename
    return dict


def main():
    print(f"{console_colors.HEADER}Attack Simulation Interface{console_colors.ENDC}")
    
    # attack graph file (.json)
    directory = "../test_graphs/"
    file = choose_atkgraph_file(directory)
    store_results_file = "../test_graphs/temp.json"

    # load the attack graph
    with open(file, 'r') as readfile:
        atkgraph = json.load(readfile)
    
    # TODO make a list of AtkgraphNodes using mgg node.py
        
    # TODO reachability analysis here with mgg functions

    # iterate over attack graph and find all dependency steps
    # TODO maybe this can be built when the attack graph is generated to save some time, O(n^3) right now
    atkgraph = get_parents_for_and_nodes(atkgraph)
    
    # build a dictionary with node id as keys and the entire json node element as the values
    # we add an attribute called "path_links" which can be updated to store the results for the path
    index = index_nodes_by_id(atkgraph)

    # connect to Neo4j graph database
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))

    while True:
        print_options(start_commands)
        command = input("choose: ")
        if command == '1':
            step_by_step_attack_simulation(graph, atkgraph, index, store_results_file)
        elif command == '2':
            attack_simulation(graph, atkgraph, index, store_results_file)
        elif command == '3':
            break

if __name__=='__main__':
    main()