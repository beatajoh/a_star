import os
import json
from typing import List
from attack_simulation import AttackSimulation
from py2neo import Graph, Node, Relationship
import maltoolbox
import reachability
import maltoolbox.attackgraph.attackgraph
import maltoolbox.ingestors.neo4j
import constants


def main():

    # Connect to Neo4j graph database.
    neo4j_graph_connection = Graph("bolt://localhost:7687", auth=("neo4j", "mgg12345!"))
    
    # Create AttackGraph instance.
    attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()

    file = constants.FILE

    # Load the attack graph from tmp directory.
    attackgraph.load_from_file(file)

    # Build a dictionary 'attackgraph_dicttionary' with the node id as keys and the corresponding AttackGraphNode as the values.
    attackgraph_dictionary = {node.id: node for node in attackgraph.nodes}
    
    # TODO select one attacker.
    attacker = attackgraph.attackers[1]
    print("ATTACKER ENTRY POINT ID", attacker.node.id) 

    # Create AttackSimulation instance.
    attack_simulation = AttackSimulation(attackgraph, attackgraph_dictionary, attacker)
    
    #try:
    user_input = int(input("which simulation? (1/2/3/4):"))
    if user_input == 1:
        # Traverse attack graph step by step.
        attack_simulation.step_by_step_attack_simulation(neo4j_graph_connection)
        attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=True)
    elif user_input == 2:
        # Traverse attack graph with Dijkstra's algorithm (to get shortest path).
        # EXAMPLE: target_node_id = "Application:4:attemptApplicationRespondConnectThroughData"
        target_node_id = input("Enter the target node id: ")
        if target_node_id in attack_simulation.attackgraph_dictionary.keys():
            attack_simulation.set_target_node(target_node_id)
            cost, _ = attack_simulation.dijkstra()
            print("The cost for the attacker for traversing the path", cost)
            attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)
    elif user_input == 3:
        target_node_id = input("Enter the target node id (or press enter): ")
        if target_node_id in attack_simulation.attackgraph_dictionary.keys():
            attack_simulation.set_target_node(target_node_id)
        attacker_cost_budget = input("Enter the attacker cost budget as integer (or press enter): ")
        if attacker_cost_budget != '':
            attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))
        cost = attack_simulation.random_path()
        print("The cost for the attacker for traversing the path", cost)
        attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)
    elif user_input == 4:
        attacker_cost_budget = input("Enter the attacker cost budget as integer (or press enter): ")
        if attacker_cost_budget != '':
            attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))
        cost = attack_simulation.bfs()
        print("The cost for the attacker for traversing the path", cost)
        attack_simulation.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=False)

    #except:
    #    print("try again")

if __name__=='__main__':
    main()