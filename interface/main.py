import os
import json
from typing import List
import attack_simulations
from py2neo import Graph, Node, Relationship
import maltoolbox
import reachability
import maltoolbox.attackgraph.attackgraph
import maltoolbox.ingestors.neo4j

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

def upload_graph_to_neo4j(neo4j_graph, path_nodes, attackgraph_dict, horizon_nodes=None):
    """
    Uploads the traversed path and attacker horizon (optional) by the attacker to the Neo4j database.

    Arguments:
    neo4j_graph           - connection to the graph database in Neo4j.
    path_nodes            - a set of attack steps in the path.
    attackgraph_dict      - a dictionary containing the node id:s as keys and corresponding AttackGraphNode as values.
    horizon_nodes         - a set of horizon attack steps.
    """
    
    nodes = {}
    neo4j_graph.delete_all()

    for node_id in path_nodes:
        node = attackgraph_dict[node_id]

        # Build attack steps for Neo4j.
        node_obj = Node(
            id = node.id,
            type = node.type,
            asset = node.asset,
            name = node.name,
            horizon = False,
            #ttc = node.ttc,
            #children = node.children,
            #parents = node.parents,
            #compromised_by = node.compromised_by
        )
        neo4j_graph.create(node_obj)
        nodes[node.id] = node_obj
    
    # Build horizon attack steps for Neo4j.
    if horizon_nodes != None:
        for node_id in horizon_nodes:
            node = attackgraph_dict[node_id]
            node_obj = Node(
                    id = node.id,
                    type = node.type,
                    asset = node.asset,
                    name = node.name,
                    horizon = True,
                    #ttc = node.ttc,
                    #children = node.children,
                    #parents = node.parents,
                    #compromised_by = node.compromised_by
                )
            neo4j_graph.create(node_obj)
            nodes[node.id] = node_obj

    # Add edges to the attack graph in Neo4j.
    for id in attackgraph_dict.keys():
        if id in nodes.keys():
            node = attackgraph_dict[id]
            for child in node.children:
                if child.id in nodes.keys():
                    from_node = nodes[id]
                    to_node = nodes[child.id]
                    if (from_node['horizon'] == False and to_node['horizon'] == False) or \
                       (from_node['horizon'] == False and to_node['horizon'] == True):
                        relationship = Relationship(from_node, "Relationship", to_node)
                        neo4j_graph.create(relationship)

def upload_attacker_to_neo4j(neo4j_graph, attacker, node_id):
    attacker_node = Node(
        name = "Attacker",
        id = attacker.id
    )
    node = neo4j_graph.nodes.match(id=node_id).first()
    relationship = Relationship(attacker_node, "Attack", node)
    neo4j_graph.create(relationship)

def step_by_step_attack_simulation(neo4j_graph, attacker, attackgraph_dict):
    """
    Main function for the step by step attack simulation. 

    Arguments:
    neo4j_graph                - connection to the graph database in Neo4j.
    attacker             - the Attacker instance.
    attackgraph_dict     - the attackgraph as a dictionary with a string node id as key 
                           and AttackGraphNode as value.
    Return:
    list of all AttackGraphNodes.
    """
    print(f"{Console_colors.HEADER}Step by step attack{Console_colors.ENDC}")

    # Add all children nodes to the extra attribute.
    #for node_id in attackgraph_dict.keys():
    #    attackgraph_dict[node_id].extra = attackgraph_dict[node_id].children
    
    # Initialize visited nodes.
    visited = set()

    # Mark the attacker node as visited by adding the node id to visited.
    attacker_entry_point_id = attacker.node.id
    visited.add(attacker_entry_point_id)
    
    # Initialize the horizon nodes.
    horizon = set()
    for node in visited:
        horizon = update_horizon(attackgraph_dict[node], horizon, visited)
    
    # Begin step by step attack simulation.
    while True:

        print_options(STEP_BY_STEP_ATTACK_COMMANDS)
        command = input("Choose: ")

        # View current attacker horizon.
        if command == '1':
            print_horizon(horizon, attackgraph_dict)

        # Action.   
        elif command == '2':
            # Choose next node to visit.       
            node_options = get_horizon_with_commands(horizon)
            print_horizon(horizon, attackgraph_dict)
            option = input("Choose a node (id) to attack: ")
            attacked_node_id = node_options[int(option)]
            attacked_node = attackgraph_dict[attacked_node_id]

            # Update horizon if the node can be visited.
            if attacked_node_id in horizon and attack_simulations.all_parents_visited(attacker, attacked_node, visited):
                visited.add(attacked_node_id)
                horizon.remove(attacked_node_id)
                horizon = update_horizon(attacked_node, horizon, visited)
                
                # Update the AttackGraphNode status.
                attacked_node.compromised_by.append(attacker)

                # Upload attacker path and horizon.
                upload_graph_to_neo4j(neo4j_graph, visited, attackgraph_dict, horizon)
                upload_attacker_to_neo4j(neo4j_graph, attacker, attacked_node_id)
                print("Attack step was compromised")

            else:
                print("The required dependency steps for ", attacked_node_id, "has not been traversed by the attacker")
                print("The node was not added to the path")

            # Print horizon nodes.
            print_horizon(horizon, attackgraph_dict)

        elif command == '3':
            # Return all AttackGraphNodes.
            return list(attackgraph_dict.values())

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
            #node["horizon"] = True
            data.append(node)

    # Write to file.
    with open(file, 'w', encoding='utf-8') as writefile:
        json.dump(data, writefile, indent=4)
    print("The attack horizon is added to the file", file)

def update_horizon(node, horizon, visited):
    """
    Adds the node ID:s of adjacent nodes to a node to a set.

    Arguments:
    node                - the AttackGraphNode node.
    horizon             - a set of horizon node id:s.
    visited             - a set of visited node id:s
    """
    # Add the horizon nodes.
    for child in node.children:
        if child.id not in visited:
            horizon.add(child.id)
    return horizon

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
            #node["horizon"] = False
            data.append(node)
        # Write to file.
        json.dump(data, writefile, indent=4)
    print("The path is added to the file", file)

def get_horizon_with_commands(nodes):
    """
    Builds a dictionary with an integer as keys and Node id:s as values.

    Arguments:
    nodes           - a set of node id:s.

    Return:
    A dictionary on the form {str id: AttackGraphNode}.
    """
    dict = {}
    for i, node_id in enumerate(nodes):
        dict[i+1] = node_id
    return dict

def print_horizon(horizon, attackgraph_dict):
    """
    Prints the node id:s of a set of nodes together with a number and the node type.
    
    Arguments:
    horizon         - a set of horizon node id:s.
    node_dict       - a dictionary on the form {str id: AttackGraphNode}.
    """
    print(f"{Console_colors.ATTACKER}Attacker Horizon{Console_colors.ENDC}")
    for i, node_id in enumerate(horizon):
        print("(", i+1, ")", node_id, attackgraph_dict[node_id].type)
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
            for link in node_2["children"]:
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


def create_lookup_dict(objects: list, attribute_name: str):
    lookup_dict = {}
    for obj in objects:
        attribute_value = getattr(obj, attribute_name, None)
        print(attribute_value)
        if attribute_value is not None:
            lookup_dict[attribute_value] = obj
    return lookup_dict


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
    Applies the reachability functions from reachability.py to the attack graph. 

    Arguments:
    attackgraph_file            - the filename of the attack graph file.
    node id                     - the node ID to attatch the attacker to.

    Return:
    Attack graph with updated 'is_reachable' labels.
    """
    print("Reachability analysis")
    attackgraph = 0

    # Create new AttackGraph instance.
    attackgraph_object = maltoolbox.attackgraph.attackgraph.AttackGraph()

    # Load attackgraph from json file.
    attackgraph_object.load_from_file(attackgraph_file)

    # Build lookup dict with node ids as key, and AttackGraphNodes as values.
    lookup_dict = create_lookup_dict(attackgraph_object.nodes, "id")
   
    #for node in attackgraph_object.nodes:
    print("checkpoint1")
    # Load coreLang language specification
    corelang_file = maltoolbox.language.specification.load_language_specification_from_mar(MAR_ARCHIVE)
    print("checkpoint2")
    # Reachability analysis from the attacker node
    node_ids = [node_id] # TODO fix so that it is possible to attatch multiple attackers
    
    #id = attackgraph_object.get_node_by_id(node_id)
    print("before")
    attackgraph = reachability.attach_attacker_and_compute(attackgraph_object, corelang_file, attackgraph_object.nodes, node_ids)
    print("done")

    return attackgraph


def reachability_analysis_with_pruning(attackgraph_file, file):
    """
    Applies the reachability functions from reachability to the attack graph, and removes the unreachable nodes. 

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
    attackgraph = reachability.prune_unreachable(attackgraph)
    
    # Upload graph to Neo4j
    maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, delete=True)

    # Save graph
    attackgraph.save_to_file(file)

    print("The reachable graph is saved to ", file)

def main():

    # Connect to Neo4j graph database.
    neo4j_connection = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))

    print(f"{Console_colors.HEADER}Attack Simulation Interface{Console_colors.ENDC}")
   
    while True:

        # Select attackgraph file (.json).
        directory = "test_graphs/"
        file = choose_attackgraph_file(directory)

        # Files to store result attack graphs.
        step_by_step_results_file = "test_graphs/step_by_step_graph.json"
        attack_simulation_results_file = "test_graphs/attack_simulation_graph.json"
        reachability_analysis_results_file = "test_graphs/reachablility_analysis_graph.json"

        # Create AttackGraph instance.
        attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()

        # Load the attack graph.
        attackgraph.load_from_file(file)

        # Build a dictionary 'attackgraph_dict' with the node id as keys and the corresponding AttackGraphNode as the values.
        attackgraph_dict = {node.id: node for node in attackgraph.nodes}
      
        # TODO fix this
        attacker = attackgraph.attackers[1]
        print("ATTACKER NODE ID", attacker.node.id)        
        
        while True:
            print_options(START_COMMANDS)
            command = input("Choose: ")

            if command == '1':
                attackgraph.nodes = step_by_step_attack_simulation(neo4j_connection, attacker, attackgraph_dict)
                
                # Save the attack graph.
                attackgraph.save_to_file(step_by_step_results_file)
            '''
            elif command == '2':
                attack_simulation(graph, attacker_node_id, attackgraph_dict, attack_simulation_results_file)
        
            elif command == '3':
                reachability_analysis_with_pruning(file, reachability_analysis_results_file)

            elif command == '4':
                attackgraph = reachability_analysis(file, attacker_node_id)
                print(attackgraph)
                # Save the graph.
                #maltoolbox.attackgraph.attackgraph.save_to_file(attackgraph)
                print("The reachable graph is saved to ", reachability_analysis_results_file)

                # Upload graph to Neo4j.
                #maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, delete=True)

            elif command == '5':
                break'''

if __name__=='__main__':
    main()