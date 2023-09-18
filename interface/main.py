import os
import json
import attack_simulations
from py2neo import Graph, Node, Relationship

import maltoolbox

import sys
sys.path.insert(1, '../../mgg')
import tmp.apocriphy as apocriphy

class Console_colors:
    """
    Constants of colors.
    """
    HEADER = '\033[95m'
    ATTACKER = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

START_COMMANDS = {
    "1": "step-by-step-attack",
    "2": "attack-simulation",
    "3": "reachability-analysis-with-pruning",
    "4": "reachability-analysis",
    "5": "exit"
    }

STEP_BY_STEP_ATTACK_COMMANDS = {
    "1": "horizon",
    "2": "action",
    "3": "exit"
    }

ATTACK_SIMULATION_COMMANDS = {
    "1": "shortest-path-dijkstra",
    "2": "shortest-path-AO-star",
    "3": "random-path",
    "4": "attack-range-BFS",
    "5": "exit"
    }

MAR_ARCHIVE = "assets/org.mal-lang.coreLang-0.3.0.mar"

def upload_json_to_neo4j_database(file, graph):
    """
    Uploads the json file to Neo4j.
    # TODO change this function!

    Arguments:
    file            - json file with the attack graph.
    graph           - connection to the graph database in Neo4j.
    """
    nodes = {}
    graph.delete_all()
    with open(file, 'r') as file:
        data = json.load(file)
    for node in data:
        cost_value = 0
        if node["ttc"] != None:
            cost_value = node["ttc"]["cost"][0]
        # build Node object
        node_obj = Node(
            str(node["horizon"]),
            name = node["id"],
            type = node["type"],
            objclass = node["objclass"],
            objid = node["objid"],
            atkname = node["atkname"],
            is_traversable=node["is_traversable"],
            is_reachable=node["is_reachable"],
            graph_type = "attackgraph",
            cost = cost_value
        )
        graph.create(node_obj)
        nodes[node["id"]] = node_obj
    for node in data:
        links = node["path_links"]
        for link in links:
            if link in nodes.keys():
                from_node = nodes[node["id"]]
                to_node = nodes[link]
                relationship = Relationship(from_node, "Relationship", to_node)
                graph.create(relationship)

def step_by_step_attack_simulation(graph, attacker_node_id, node_dict, file):
    """
    Main function for the step by step attack simulation. 

    Arguments:
    graph                - connection to the graph database in Neo4j.
    attacker_node_id     - the ID of the attacker node.
    node_dic             - a dictionary on the form {node ID: node as dictionary, ...}.
    file                 - name of the file to store the result to.
    """
    print(f"{Console_colors.HEADER}Step by step attack{Console_colors.ENDC}")

    # Add all links to the path_links attribute.
    for key in node_dict.keys():
        node_dict[key]["path_links"] = node_dict[key]["links"]

    # Initialize visited nodes.
    visited = set()

    # Mark the attacker node as visited by adding the node id to visited.
    visited.add(attacker_node_id)

    # Initialize the horizon nodes.
    horizon = set()
    for node in visited:
        horizon = update_horizon(node, horizon, node_dict)

    # Step by step attack simulation.
    while True:
        print_options(STEP_BY_STEP_ATTACK_COMMANDS)
        command = input("Choose: ")

        # View horizon.
        if command == '1':
            print_horizon(horizon, node_dict)

        # Action.
        elif command == '2':
            # Choose next node to visit.       
            node_options = get_horizon_with_commands(horizon)  # TODO print the node type
            print_horizon(horizon, node_dict)
            option = input("Choose a node (id) to attack: ")
            attack_node = node_options[int(option)]

            # Update horizon if the node can be visited.
            if attack_node in horizon and attack_simulations.all_parents_visited(attack_node, visited, node_dict):
                visited.add(attack_node)
                horizon.remove(attack_node)
                horizon = update_horizon(attack_node, horizon, node_dict)

                # Store the path and horizon to file.
                add_nodes_to_json_file(file, visited, node_dict)   
                add_horizon_nodes_to_json_file(file, horizon, node_dict)

                # Upload path.
                upload_json_to_neo4j_database(file, graph)

            else:
                print("The dependency steps for ", attack_node, " has not been visited")
                print("The node was not added to the path")
            # Print horizon nodes.
            print_horizon(horizon, node_dict)

        elif command == '3':
            break

def add_horizon_nodes_to_json_file(file, nodes, node_dict):
    """
    Appends a set of horizon nodes to the json file.
    A node property "horizon" is also added to the nodes.

    Arguments:
    file            - the name of the file to write to.
    nodes           - a set of node ID:s 
    node_dict       - a dictionary on the form {node ID: node as dictionary, ...}.
    """
    # Read attack graph (.json).
    with open(file, 'r', encoding='utf-8') as writefile:
        data = json.load(writefile) 

        # Update "horizon" label.
        for node_id in nodes:
            node = node_dict[node_id]
            node["horizon"] = True
            data.append(node)

    # Write to file.
    with open(file, 'w', encoding='utf-8') as writefile:
        json.dump(data, writefile, indent=4)
    print("The attack horizon is added to the file", file)

def update_horizon(node_id, nodes, node_dict):
    """
    Adds the node ID:s of adjacent nodes to a node to a set.

    Arguments:
    node            - the node ID.
    nodes           - a set of node ID:s.
    node_dict       - a dictionary on the form {node ID: node as dictionary, ...}.
    """
    # Add the horizon nodes.
    for link in node_dict[node_id]['links']:
        nodes.add(link)
    return nodes

def add_nodes_to_json_file(file, nodes, node_dict):
    """
    Writes a set of horizon nodes to the json file.
    A node property "horizon" is also added to the nodes.

    Arguments:
    file            - the name of the file to write to.
    nodes           - a set of node ID:s.
    node_dict       - a dictionary on the form {id: node as dictionary, ...}.
    """
    data = [] 

    # Remove all file contents.
    open(file, 'w').close() 

    # Add non-horizon nodes to file.
    with open(file, 'w', encoding='utf-8') as writefile:
        for node_id in nodes:
            node = node_dict[node_id]
            node["horizon"] = False
            data.append(node)
        # Write to file.
        json.dump(data, writefile, indent=4)
    print("The path is added to the file", file)

def get_horizon_with_commands(nodes):
    """
    Builds a dictionary with an integer as keys and Node ID:s as values.

    Arguments:
    nodes           - a set of node ID:s.

    Return:
    A dictionary on the form {integer: Node ID, ...}.
    """
    dict = {}
    for i, node in enumerate(nodes):
        dict[i+1] = node
    return dict

def print_horizon(horizon, node_dict):
    """
    Prints the node ID:s of a set of nodes together with a number and the node type,
    on the form "(Integer) Node ID type".
    
    Arguments:
    horizon         - a set of node ID:s.
    node_dict       - a dictionary on the form {id: node as dictionary, ...}.
    """
    print(f"{Console_colors.ATTACKER}Attacker Horizon{Console_colors.ENDC}")
    for i, node in enumerate(horizon):
        print("(", i+1, ")", node, node_dict[node]["type"])
    print(f"{Console_colors.ENDC}")

def get_parents_for_and_nodes(attackgraph):
    """
    Adds and builds a "parent_list" property to the attack graph.
    The "parent_list" property is a list with all node ID:s for incoming links.

    Arguments:
    attackgraph           - attack graph in json format.

    Return:
    The attack graph with the "parent_list" property for all nodes.
    """
    n = 0
    id = ""
    id_2 = ""
    for i, node in enumerate(attackgraph):
        id = node["id"]
        parent_list = []
        for node_2 in attackgraph:
            id_2 = node_2["id"]
            for link in node_2["links"]:
                if link == id and node_2["type"] in ["and", "or"]:
                    parent_list.append(id_2)
        n += 1
        attackgraph[i]["parent_list"]=parent_list
    return attackgraph

def attack_simulation(graph, attacker_node_id, node_dict, file):
    """
    Main function for the attack simulations with graph algorithms and reachability analysis. 

    Arguments:
    graph                - connection to the graph database in Neo4j.
    attacker_node_id     - the ID of the attacker node.
    node_dict            - a dictionary on the form {node ID: node as dictionary, ...}.
    file                 - name of the file to store the result to.
    """
    print(f"{Console_colors.HEADER}Attack simulations / Graph algorithms{Console_colors.ENDC}")
   
    while True:
        print_options(ATTACK_SIMULATION_COMMANDS)
        command = input("Choose: ")
        start_node = attacker_node_id 
        path = None

        # Clear 'path_links' attribute.
        for key in node_dict.keys():
            node_dict[key]["path_links"] = []

        if command == '5':
            break
        elif command == '1':
            print("Shortest path Dijkstra")
            target_node = input("Enter target node id: ")
            result = attack_simulations.dijkstra(start_node, target_node, node_dict)
            if result != None:
                total_cost = result[0]
                path = result[1]
                nodes = result[2]
                print("Total cost: ", total_cost)
        elif command == '2':    #TODO
            print("Shortest path AO*")
        elif command == '3':
            print("Random path")
            target_node = input("Enter target node id (press enter to run without target): ")
            attack_budget = input("Enter attack budget (press enter to run without target): ")
            if target_node == "":
                target_node = None
            if attack_budget != "":
                attack_budget = int(attack_budget)
            if attack_budget == "":
                attack_budget = None
            result = attack_simulations.random_path(start_node, node_dict, target_node=target_node, cost_budget=attack_budget)
            if result != None:
                total_cost = result[0]
                path = result[1]
                nodes = result[2]
                print("Total cost: ", total_cost)
        elif command == '4':
            print("BFS with cost budget")
            max_distance = int(input("Enter maximum allowed cost between the source and all nodes: "))
            path = attack_simulations.bfs(start_node, node_dict, max_distance)
            nodes = path.keys()
        if path != None:
            add_nodes_to_json_file(file, nodes, path)
            upload_json_to_neo4j_database(file, graph)
        else: 
            print("No result")

def build_node_dict(attackgraph):
    """
    Builds a dictionary with Node ID:s as keys and the Node dictionaries as values.

    Arguments:
    attackgraph           - attack graph in json format.

    Return:
    A dictionary on the form {Node ID: Node dictionary, ...}.
    """
    dict = {}
    for node in attackgraph:
        node["path_links"] = []
        dict[node["id"]] = node
    return dict

def print_options(args):
    """
    Prints the keys and values of a dictionary.
    
    Arguments:
    args            - a dictionary on the form {integer: string}
    """
    for arg in args:
        command = arg
        description = args[command]
        print(f"{Console_colors.BOLD}", "(", command, ")", end=" ")
        print(f"{Console_colors.BOLD}", description)
    print(f"{Console_colors.ENDC}",end="")

def choose_attackgraph_file(path_to_directory):
    """
    Lets user choose a file withing the directory, and returns the path to that file.
    
    Arguments:
    path_to_directory            - the path to a directory as a string.

    Return:
    The path to the file as a string.
    """
    print("Which attack graph file do you want to load?")
    options = get_files_in_directory(path_to_directory)
    print_options(options)
    command = input("Choose: ")
    file = options[int(command)]
    return os.path.join(path_to_directory, file)


def get_files_in_directory(path_to_directory):
    """
    Builds a dictionary with integers as values and all filenames in the directory as the keys. 

    Arguments:
    path_to_directory            - the path to a directory as a string.

    Return:
    The dictionary containing all filenames in the directory.
    """
    dict = {}
    for i, filename in enumerate(os.listdir(path_to_directory)):
        # Check if the current item is a file.
        if os.path.isfile(os.path.join(path_to_directory, filename)):
            dict[i+1] = filename
    return dict

def reachability_analysis(attackgraph_file, node_id):
    """
    Applies the reachability functions from mgg.apocriphy to the attack graph. 

    Arguments:
    attackgraph_file            - the filename of the attack graph file.
    node id                     - the node ID to attatch the attacker to.

    Return:
    Attack graph with updated 'is_reachable' labels.
    """
    print("Reachability analysis")

    # Load attackgraph from json file
    graph = maltoolbox.attackgraph.attackgraph.load_from_file(attackgraph_file)

    node_ids = [node_id] # TODO fix so that it is possible to attatch multiple attackers
    corelang_file = maltoolbox.language.specification.load_language_specification_from_mar(MAR_ARCHIVE)

    # Reachability analysis from the attacker node
    attackgraph = apocriphy.attach_attacker_and_compute(corelang_file, attackgraph, node_ids)
    return attackgraph



def reachability_analysis_with_pruning(attackgraph_file, file):
    """
    Applies the reachability functions from mgg.apocriphy to the attack graph, and removes the unreachable nodes. 

    Arguments:
    attackgraph_file               - the filename of the attack graph file.
    file                        - the file to store the results to.
    """
    print("Reachability analysis with pruning of unreachable nodes")
    id = input("Attatch the attacker to node id (e.g. Network:8176711980537409:access): ")
    
    # Reachability analysis from the attacker node
    attackgraph = reachability_analysis(attackgraph_file, id)   # TODO fix so that it is possible to attatch multiple attackers

    # Modify the attacker node so that we can prune the untraversable nodes
    attacker = attackgraph[-1]
    attacker.is_reachable = True

    # Prune untraversable nodes
    attackgraph = apocriphy.prune_unreachable(attackgraph)
    
    # Upload graph to Neo4j
    maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, delete=True)

    # Save graph
    attackgraph.save_to_file(file)

    print("The reachable graph is saved to ", file)

def main():

    print(f"{Console_colors.HEADER}Attack Simulation Interface{Console_colors.ENDC}")

    while True:

        # Select attackgraph file (.json).
        directory = "test_graphs/"
        file = choose_attackgraph_file(directory)

        # Files to store result attack graphs.
        step_by_step_results_file = "test_graphs/step_by_step_graph.json"
        attack_simulation_results_file = "test_graphs/attack_simulation_graph.json"
        reachability_analysis_results_file = "test_graphs/reachablility_analysis_graph.json"

        # Create attack graph instance
        # attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()    # TODO

        # Load the attack graph.
        # attackgraph.load_from_file(file)    # TODO
        with open(file, 'r') as readfile:
            attackgraph = json.load(readfile)
        
        # Iterate over attack graph and find all dependency steps.
        # TODO maybe this can be built when the attack graph is generated to save some time, O(n^3)? right now.
        # attackgraph = get_parents_for_and_nodes(attackgraph)
        
        # Build a dictionary 'node_dict' with node id as keys and the entire json node element as the values.
        # Here we add an attribute called "path_links" to the values which can be updated to store the results for the paths from the attack simulations.
        node_dict = build_node_dict(attackgraph)
        
        # Connect to Neo4j graph database.
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))

        attacker_node_id = attackgraph[-1]["id"]   # TODO change this.
        
        while True:
            print_options(START_COMMANDS)
            command = input("Choose: ")

            if command == '1':
                step_by_step_attack_simulation(graph, attacker_node_id, node_dict, step_by_step_results_file)
            
            elif command == '2':
                attack_simulation(graph, attacker_node_id, node_dict, attack_simulation_results_file)
        
            elif command == '3':
                reachability_analysis_with_pruning(file, reachability_analysis_results_file)

            elif command == '4':
                attackgraph = reachability_analysis(file, attacker_node_id)
                
                # Save the graph.
                maltoolbox.attackgraph.attackgraph.save_to_file(attackgraph)
                print("The reachable graph is saved to ", reachability_analysis_results_file)

                # Upload graph to Neo4j.
                maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, delete=True)

            elif command == '5':
                break

if __name__=='__main__':
    main()