import json
import attack_simulations as atksim
import upload as upload_json_to_neo4j
import node as node
from py2neo import Graph, Node, Relationship


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

# 
action_commands = {
    "1": "enter node id"
    }

attack_simulation_commands = {
    "1": "shortest-path-dijkstra",
    "2": "random-path",
    "3": "attack-range"
    }

def update_horizon(node, horizon, index):
    for link in index[node]['links']:
        horizon.add(link)
    return horizon


def step_by_step_attack_simulation(graph, atkgraph, index):
    print(f"{console_colors.HEADER}step-by-step-attack{console_colors.ENDC}")
    
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
            print_horizon(horizon)
        elif command == '2':
            # choose next node name to visit       
            dict = print_horizon_w_commands(horizon)
            print_options(dict)
            option = input("choose node to attack: ")
            attack_node = dict[int(option)]

            # update horizon
            if attack_node in horizon:
                visited.add(attack_node)
                horizon.remove(attack_node)
                horizon = update_horizon(attack_node, horizon, index)
                print_horizon(horizon)

            # store the path and horizon to file
            file = 'temp.json' 
            add_nodes_to_json_file(file, visited, index)   # add the horizon in different color
            add_horizon_nodes_to_json_file(file, horizon, index)
            upload_json_to_neo4j.upload_json_to_neo4j_database(file, graph)

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

def add_nodes_to_json_file(file, visited, index):
    data = [] 
    with open(file, 'w', encoding='utf-8') as writefile:
        writefile.truncate()    # remove all file contents
        for node_id in visited:
            node = index[node_id]
            node["horizon"] = False
            data.append(node)
        json.dump(data, writefile, indent=4)


def print_horizon_w_commands(horizon):
    dict = {}
    for i, node in enumerate(horizon):
        dict[i] = node
    return dict

def print_horizon(horizon):
    print(f"{console_colors.FAIL}Attacker Horizon{console_colors.ENDC}")
    for node in horizon:
        print(" "*12, node)


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
    return atkgraph


def attack_simulation(graph, atkgraph, index):
    print(f"{console_colors.HEADER}Attack-Simulation{console_colors.ENDC}")

    # iterate over attack graph and find all dependency steps
    # maybe this can be built when the attack graph is generated to save some time ?
    atkgraph = get_parents_for_and_nodes(atkgraph)

    while True:
        print_options(attack_simulation_commands)

        command = input("choose: ")
        start_node = atkgraph[-1]['id']

        if command == '1':
            print("DIJKSTRA")
            target_node = input("enter target node id: ")
            path = atksim.dijkstra(atkgraph, start_node, target_node)
            print("PATH:  ", path[0])   # TODO path[0] for paths with 'and' nodes is not yet implemented
            print("COST:  ", path[1])
        elif command == '2':
            print("RANDOM PATH")
            start_node = atkgraph[-1]['id']
            target_node = input("enter target node id: ")
            path = atksim.random_path(atkgraph, start_node, target_node)
            print("PATH:  ", path)
        elif command == '3':
            break

        '''
        # store the path and horizon to file
        file = 'temp.json'
        add_nodes_to_json_file(file, path[0], index)  # also add attacker horizon here?
        upload_json_to_neo4j.upload_json_to_neo4j_database(file, graph)
        '''
           

def index_nodes_by_id(atkgraph):
    dict = {}
    for node in atkgraph:
        dict[node["id"]] = node
    return dict

def print_options(args):
        for arg in args:
            command = arg
            description = args[command]
            print(f"{console_colors.BOLD}", "(", command, ")", end=" ")
            print(f"{console_colors.BOLD}", description)
        print(f"{console_colors.ENDC}",end="")

def main():
    print(f"{console_colors.HEADER}Attack Simulation Interface{console_colors.ENDC}")

    # attack graph file (.json)
    file = "../test_graphs/real_graph.json"
    #file = "../test_graphs/small_graph_2.json"

    # load the attack graph
    with open(file, 'r') as readfile:
        atkgraph = json.load(readfile)
    
    # build a dictionary with node id as keys and the entire json node element as the values
    index = index_nodes_by_id(atkgraph)

    # connect to Neo4j graph database
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))

    while True:
        
        print_options(start_commands)
    
        command = input("choose: ")

        if command == '1':
            step_by_step_attack_simulation(graph, atkgraph, index)
        elif command == '2':
            attack_simulation(graph, atkgraph, index)
        elif command == '3':
            break

if __name__=='__main__':
    main()