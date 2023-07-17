import os
import json
import attack_simulations as atksim
from py2neo import Graph, Node, Relationship
import sys
sys.path.insert(1, '../../mgg')
import mgg
import mgg.atkgraph
import tmp.apocriphy as apocriphy
import mgg.securicad
import mgg.ingestor.neo4j

class console_colors:
    """
    Constants of colors.
    """
    HEADER = '\033[95m'
    ATTACKER = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

start_commands = {
    "1": "step-by-step-attack",
    "2": "attack-simulation",
    "3": "reachability-analysis-with-pruning",
    "4": "reachability-analysis",
    "5": "exit"
    }

step_by_step_attack_commands = {
    "1": "horizon",
    "2": "action",
    "3": "exit"
    }

attack_simulation_commands = {
    "1": "shortest-path-dijkstra",
    "2": "shortest-path-AO-star",
    "3": "random-path",
    "4": "attack-range-BFS",
    "5": "exit"
    }

def upload_json_to_neo4j_database(file, graph):
    """
    Uploads the json file to Neo4j.

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
    print(f"{console_colors.HEADER}Step by step attack{console_colors.ENDC}")

    # add all links to the path_links attribute
    for key in node_dict.keys():
        node_dict[key]["path_links"] = node_dict[key]["links"]
    # initialize visited nodes
    visited = set()
    # mark the attacker node as visited by adding the node id to visited
    visited.add(attacker_node_id)
    # initialize the horizon
    horizon = set()
    for node in visited:
        horizon = update_horizon(node, horizon, node_dict)
    while True:
        print_options(step_by_step_attack_commands)
        command = input("Choose: ")
        if command == '1':
            print_horizon(horizon, node_dict)
        elif command == '2':
            # choose next node name to visit       
            node_options = get_horizon_w_commands(horizon)  # TODO print the node type
            print_horizon(horizon, node_dict)
            option = input("Choose a node (id) to attack: ")
            attack_node = node_options[int(option)]
            # update horizon
            if attack_node in horizon and atksim.all_parents_visited(attack_node, visited, node_dict):
                visited.add(attack_node)
                horizon.remove(attack_node)
                horizon = update_horizon(attack_node, horizon, node_dict)
                # store the path and horizon to file
                add_nodes_to_json_file(file, visited, node_dict)   
                add_horizon_nodes_to_json_file(file, horizon, node_dict)
                upload_json_to_neo4j_database(file, graph)
            else:
                print("The dependency steps for ", attack_node, " has not been visited")
                print("The node was not added to the path")
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
    with open(file, 'r', encoding='utf-8') as writefile:
        data = json.load(writefile) 
        for node_id in nodes:
            node = node_dict[node_id]
            node["horizon"] = True
            data.append(node)
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
    open(file, 'w').close() # remove all file contents
    with open(file, 'w', encoding='utf-8') as writefile:
        for node_id in nodes:
            node = node_dict[node_id]
            node["horizon"] = False
            data.append(node)
        json.dump(data, writefile, indent=4)
    print("The path is added to the file", file)


def get_horizon_w_commands(nodes):
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
    print(f"{console_colors.ATTACKER}Attacker Horizon{console_colors.ENDC}")
    for i, node in enumerate(horizon):
        print("(", i+1, ")", node, node_dict[node]["type"])
    print(f"{console_colors.ENDC}")


def get_parents_for_and_nodes(atkgraph):
    """
    Adds and builds a "parent_list" property to the attack graph.
    The "parent_list" property is a list with all node ID:s for incoming links.

    Arguments:
    atkgraph           - attack graph in json format.

    Return:
    The attack graph with the "parent_list" property for all nodes.
    """
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


def attack_simulation(graph, attacker_node_id, node_dict, file):
    """
    Main function for the attack simulations with graph algorithms and reachability analysis. 

    Arguments:
    graph                - connection to the graph database in Neo4j.
    attacker_node_id     - the ID of the attacker node.
    node_dict            - a dictionary on the form {node ID: node as dictionary, ...}.
    file                 - name of the file to store the result to.
    """
    print(f"{console_colors.HEADER}Attack simulations / Graph algorithms{console_colors.ENDC}")
   
    while True:
        print_options(attack_simulation_commands)
        command = input("Choose: ")
        start_node = attacker_node_id 
        path = None

        # clear path_links attribute
        for key in node_dict.keys():
            node_dict[key]["path_links"] = []

        if command == '5':
            break
        elif command == '1':
            print("Shortest path Dijkstra")
            target_node = input("Enter target node id: ")
            result = atksim.dijkstra(start_node, target_node, node_dict)
            if result != None:
                total_cost = result[0]
                path = result[1]
                nodes = result[2]
                print("Total cost: ", total_cost)
        elif command == '2':    #TODO add to the rest
            print("Shortest path AO*")
            '''
            target_node = input("enter target node id: ")
            path, cost = atksim.ao_star(atkgraph, target_node, node_dict)
            '''
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
            result = atksim.random_path(start_node, node_dict, target_node=target_node, cost_budget=attack_budget)
            if result != None:
                total_cost = result[0]
                path = result[1]
                nodes = result[2]
                print("Total cost: ", total_cost)
        elif command == '4':
            print("BFS with cost budget")
            max_distance = int(input("Enter maximum allowed cost between the source and all nodes: "))
            path = atksim.bfs(start_node, node_dict, max_distance)
            nodes = path.keys()
        if path != None:
            add_nodes_to_json_file(file, nodes, path)
            upload_json_to_neo4j_database(file, graph)
        else: 
            print("No result")

def build_node_dict(atkgraph):
    """
    Builds a dictionary with Node ID:s as keys and the Node dictionaries as values.

    Arguments:
    atkgraph           - attack graph in json format.

    Return:
    A dictionary on the form {Node ID: Node dictionary, ...}.
    """
    dict = {}
    for node in atkgraph:
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
        print(f"{console_colors.BOLD}", "(", command, ")", end=" ")
        print(f"{console_colors.BOLD}", description)
    print(f"{console_colors.ENDC}",end="")

def choose_atkgraph_file(path_to_directory):
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
        # Check if the current item is a file
        if os.path.isfile(os.path.join(path_to_directory, filename)):
            dict[i+1] = filename
    return dict

def reachability_analysis(atkgraph_file, node_id):
    """
    Applies the reachability functions from mgg.apocriphy to the attack graph. 

    Arguments:
    atkgraph_file               - the filename of the attack graph file.
    node id                     - the node ID to attatch the attacker to.
    """
    print("Reachability analysis")
    graph = mgg.atkgraph.load_atkgraph(atkgraph_file)
    # TODO fix so that it is possible to attatch multiple attackers
    node_ids = [node_id] 
    corelang_filename ="assets/org.mal-lang.coreLang-0.3.0.mar"
    corelang_file = mgg.securicad.load_language_specification(corelang_filename)
    # compute reachability from the attacker node
    graph = apocriphy.attach_attacker_and_compute(corelang_file, graph, node_ids)
    return graph



def reachability_analysis_with_pruning(atkgraph_file, file):
    """
    Applies the reachability functions from mgg.apocriphy to the attack graph, and removes the unreachable nodes. 

    Arguments:
    atkgraph_file               - the filename of the attack graph file.
    file                        - the file to store the results to.
    """
    print("Reachability analysis with pruning of unreachable nodes")
    # TODO fix so that it is possible to attatch multiple attackers
    id = input("Attatch the attacker to node id (e.g. Network:8176711980537409:access): ")
    graph = reachability_analysis(atkgraph_file, id)
    # modify the attacker node so that we can prune the untraversable nodes
    attacker = graph[-1]
    attacker.is_reachable = True
    # prune untraversable nodes
    graph = apocriphy.prune_unreachable(graph)
    # upload graph to Neo4j
    mgg.ingestor.neo4j.ingest(graph, delete=True)
    # save graph
    mgg.atkgraph.save_atkgraph(graph, file)
    print("The reachable graph is saved to ", file)

def main():
    print(f"{console_colors.HEADER}Attack Simulation Interface{console_colors.ENDC}")
    while True:
        # attack graph file (.json)
        directory = "test_graphs/"
        file = choose_atkgraph_file(directory)

        # files to store result attack graphs
        step_by_step_results_file = "test_graphs/step_by_step_graph.json"
        attack_simulation_results_file = "test_graphs/attack_simulation_graph.json"
        reachability_analysis_results_file = "test_graphs/reachablility_analysis_graph.json"

        # load the attack graph
        with open(file, 'r') as readfile:
            atkgraph = json.load(readfile)
        
        # iterate over attack graph and find all dependency steps
        # TODO maybe this can be built when the attack graph is generated to save some time, O(n^3)? right now
        atkgraph = get_parents_for_and_nodes(atkgraph)
        
        # build a dictionary with node id as keys and the entire json node element as the values
        # we add an attribute called "path_links" to the nodes which can be updated to store the results for the paths from the attack simulations
        node_dict = build_node_dict(atkgraph)
        
        # connect to Neo4j graph database
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))

        attacker_node_id = atkgraph[-1]["id"]   # TODO change this ?

        while True:
            print_options(start_commands)
            command = input("Choose: ")
            if command == '1':
                step_by_step_attack_simulation(graph, attacker_node_id, node_dict, step_by_step_results_file)
            elif command == '2':
                attack_simulation(graph, attacker_node_id, node_dict, attack_simulation_results_file)
            elif command == '3':
                reachability_analysis_with_pruning(file, reachability_analysis_results_file)
            elif command == '4':
                atkgraph = reachability_analysis(file, attacker_node_id)
                # save graph
                mgg.atkgraph.save_atkgraph(atkgraph, reachability_analysis_results_file)
                print("The reachable graph is saved to ", reachability_analysis_results_file)
                # upload graph to Neo4j
                mgg.ingestor.neo4j.ingest(atkgraph, delete=True)
            elif command == '5':
                break

if __name__=='__main__':
    main()