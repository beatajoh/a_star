from py2neo import Graph
import maltoolbox.attackgraph.attackgraph
import maltoolbox.ingestors.neo4j

# Custom files.
from attack_simulation import AttackSimulation
import constants
import help_functions


def main():
    # Connect to Neo4j graph database.
    neo4j_graph_connection = Graph(constants.URI, auth=(constants.USERNAME, constants.PASSWORD))
    print("Connected to Neo4j database.")

    # Create mal-toolbox AttackGraph instance.
    attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()

    # File of the attack graph model.
    file = constants.FILE

    # Load the attack graph.
    attackgraph.load_from_file(file)

    # Upload the attack graph to Neo4j.
    print("Starting uploading the attackgraph to Neo4j.")
    maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, constants.URI, constants.USERNAME, constants.PASSWORD, constants.DBNAME, delete=True)
    print("The attackgraph is uploaded to Neo4j.")
    
    # TODO Select one attacker.
    attacker = attackgraph.attackers[0]
    print("Attacker entry point (attack step id) is:", attacker.node.id, end="\n\n") 

    # Create AttackSimulation instance.
    attack_simulation = AttackSimulation(attackgraph, attacker)    
    attack_options = list(constants.ATTACK_OPTIONS.keys())

    while True:
        # Display algorithm options.
        print(f"{constants.HEADER_COLOR}Choose any of the options below. If you want to exit, press any key.{constants.STANDARD}")
        help_functions.print_dictionary(constants.ATTACK_OPTIONS) 
        user_input = input(f"Which simulation? {attack_options}:")

        if user_input == attack_options[0]:
            # Traverse attack graph step by step.
            print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
            attack_simulation.step_by_step_attack_simulation(neo4j_graph_connection)
            attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=True)

        elif user_input == attack_options[1]:
            # Traverse attack graph with Dijkstra's algorithm, to get the shortest path.
            # EXAMPLE: set target_node_id as "Application:4:attemptApplicationRespondConnectThroughData"
            print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
            target_node_id = input("Enter the target node id: ")
            if target_node_id in attack_simulation.attackgraph_dictionary.keys():
                attack_simulation.set_target_node(target_node_id)
                cost = attack_simulation.dijkstra()
                print("The cost for the attacker for traversing the path", cost)
                print("print!", attack_simulation.visited)
                attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

        elif user_input == attack_options[2]:
            # Traverse attack graph with random walker algorithm (to get a random path).
            # It is optional to enter a target or attacker cost budget.
            print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
            target_node_id = input("Enter the target node id (or press enter): ")
            if target_node_id in attack_simulation.attackgraph_dictionary.keys():
                attack_simulation.set_target_node(target_node_id)
            attacker_cost_budget = input("Enter the attacker cost budget as integer (or press enter): ")
            if attacker_cost_budget != '':
                attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))
            cost = attack_simulation.random_path()
            print("The cost for the attacker for traversing the path", cost)
            attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

        elif user_input == attack_options[3]:
            # Traverse attack graph with breadth first search to retrieve all "traversable" steps within the attacker
            # cost budget.
            print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
            attacker_cost_budget = input("Enter the attacker cost budget as integer (or press enter): ")
            if attacker_cost_budget != '':
                attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))
            cost = attack_simulation.bfs()
            print("The cost for the attacker for traversing the path", cost)
            attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

        else: 
            break
    #except:
    #    print("try again")

if __name__=='__main__':
    main()