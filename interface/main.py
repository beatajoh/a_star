from py2neo import Graph
import os
import maltoolbox.attackgraph.attackgraph
import maltoolbox.ingestors.neo4j
import maltoolbox.model.model
import maltoolbox.language.specification
import maltoolbox.language.classes_factory

# Custom files.
from attack_simulation import AttackSimulation
import constants
import help_functions


def main():
    # Connect to Neo4j graph database.
    print("Starting to connect to Neo4j database.")
    neo4j_graph_connection = Graph(uri=constants.URI, user=constants.USERNAME, password=constants.PASSWORD, name=constants.DBNAME)
    #neo4j_graph_connection = Graph(constants.URI, auth=(constants.USERNAME, constants.PASSWORD))
    print("Successful connection to Neo4j database.")

    # Create the language specification and LanguageClassesFactory instance.
    lang_spec = maltoolbox.language.specification.load_language_specification_from_mar(constants.MAR_ARCHIVE)
    lang_classes_factory = maltoolbox.language.classes_factory.LanguageClassesFactory(lang_spec)
    lang_classes_factory.create_classes()

    # Create mal-toolbox Model instance.
    model = maltoolbox.model.model.Model("model", lang_spec, lang_classes_factory)
    model.load_from_file(constants.MODEL_FILE)

    # Generate mal-toolbox AttackGraph.
    attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()
    attackgraph.generate_graph(lang_spec, model)

    # Select one attacker for the simulation.
    # Note: it is possible to add a custom attacker with the model module and thereafter you can run attackgraph.attach_attackers.
    asset = model.get_asset_by_id(0)
    model.attackers[0].entry_points.append((asset, ["attemptFullAccessFromSupplyChainCompromise"]))
    attackgraph.attach_attackers(model)

    attacker = attackgraph.attackers[0]
    attacker_entry_point = attacker.node.id
    print("Attacker entry point (attack step id) is:", attacker_entry_point) 

    # Change nodes with type 'defense' so that is_necessary=False, for testing purposes.
    for node in attackgraph.nodes:
        if node.type == 'defense':
            node.is_necessary = False

    # Upload the attack graph to Neo4j.
    print("Starting uploading the attackgraph to Neo4j.")
    maltoolbox.ingestors.neo4j.ingest_attack_graph(attackgraph, constants.URI, constants.USERNAME, constants.PASSWORD, constants.DBNAME, delete=True)
    print("The attackgraph is uploaded to Neo4j.")

    # Calculate new cost if the output file exists or is empty
    # TODO draw samples from ttc instead.
    if not os.path.exists(constants.COST_FILE) or os.stat(constants.COST_FILE).st_size == 0:
        help_functions.calculate_costs_and_save_as_json(attackgraph.nodes, constants.COST_FILE)
        print(f"Costs saved to {constants.COST_FILE}")
    else:
        print(f"{constants.COST_FILE} already contains data. Skipping calculation.")
   

    # Create AttackSimulation instance.
    attack_simulation = AttackSimulation(attackgraph, attacker) 

    # Display algorithm options.
    attack_options = list(constants.ATTACK_OPTIONS.keys())
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
        # EXAMPLE for the provided model.json.
        # set start node as "Attacker:12:firstSteps".
        # set target_node_id as "Credentials:6:attemptCredentialsReuse".
        # cost should be 4.

        # EXAMPLE for the provided model.json.
        # set start node as "Attacker:12:firstSteps", and compromise "Application:0:attemptFullAccessFromSupplyChainCompromise".
        # set target_node_id as "Application:0:fullAccess".
        # cost should be 9+3+4+2=18.

        # EXAMPLE for the provided model.json.
        # set start node as "Attacker:12:firstSteps", and compromise "Application:0:attemptFullAccessFromSupplyChainCompromise".
        # set target_node_id as "Application:0:attemptApplicationRespondConnectThroughData".
        # cost should be 9+3+4+2+1+3=22.
        
        # EXAMPLE for the provided model.json.
        # set start node as "Attacker:12:firstSteps", and compromise "Application:0:attemptFullAccessFromSupplyChainCompromise".
        # set target_node_id as "Application:0:attemptModify".
        # cost should be 9+3+4+2+1+10=29.

        # EXAMPLE
        # set target_node_id_as "Credentials:9:propagateOneCredentialCompromised".
        # cost should be 79.

        # EXAMPLE
        # set target_node_id as "Credentials:5:extract"
        # This node is not reachable, so it should not be in the result.

        print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
        target_node_id = input("Enter the target node id: ")
        if target_node_id in attack_simulation.attackgraph_dictionary.keys():
            attack_simulation.set_target_node(target_node_id)
            cost = attack_simulation.dijkstra()
            print("The cost for the attacker for traversing the path", cost)
            print("Visited attack steps", attack_simulation.visited)
            attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

    elif user_input == attack_options[2]:
        # Traverse attack graph with random walker algorithm (to get a random path).
        # It is optional to enter a target or attacker cost budget.

        # EXAMPLES
        # It should be able to find Application:0:bypassSupplyChainAuditing without a budget.

        # It shoulde be able to find Application:0:fullAccessFromSupplyChainCompromise, without a budget or a very large budget like 10000. 
        # But this will be more expensive compared to the previous case since we have an 'and' step in the path.
        # if you set the budget to 10, then the target is not found.

        # It should be able to find Application:0:attemptModify without a budget.
        # But this will be more expensive compared to the previous case since we add a couple of 'or' steps.

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
        # Traverse attack graph with breadth first search to retrieve the subgraph within the attacker
        # cost budget.
        print(f"{constants.HEADER_COLOR}{constants.ATTACK_OPTIONS[user_input]}{constants.STANDARD}")
        attacker_cost_budget = input("Enter the attacker cost budget as integer (or press enter): ")
        if attacker_cost_budget != '':
            attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))
        cost = attack_simulation.bfs()
        print("The cost for the attacker for traversing the path", cost)
        attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

    



if __name__=='__main__':
    main()
