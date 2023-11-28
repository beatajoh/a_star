import unittest
import maltoolbox.attackgraph.attackgraph
from py2neo import Graph
import maltoolbox.ingestors.neo4j

# Custom files.
import constants
from attack_simulation import AttackSimulation


class TestAttackSimulation(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestAttackSimulation, self).__init__(*args, **kwargs)

        # Connect to Neo4j graph database.
        print("Connect to Neo4j graph database.")
        self.graph = Graph(constants.URI, auth=(constants.USERNAME, constants.PASSWORD))

        # Create new mal-toolbox AttackGraph instance.
        self.attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()
        
        # Load the attack graph.
        print("Load attackgraph.")
        self.attackgraph.load_from_file(constants.TEST_FILE)

        # Set up attackers.
        self.attacker_1 = self.attackgraph.attackers[0]
        self.attacker_2 = self.attackgraph.attackers[1]

        print(self.attackgraph.nodes[0].is_necessary and False)

        # Test 1
        """
        MATCH path = (sourceNode {full_name: 'Attacker:12:firstSteps'})-[*]->(targetNode {full_name: 'User:11:oneCredentialCompromised'}) RETURN path
        """
        self.target_1 = "User:11:oneCredentialCompromised"

        # Test 2
        self.start_node_2 = ""
        self.target_2 = ""

        # Test 3
        self.target_3 = "Credentials:5:attemptExtractFromReplica"

        # Test 4 
        """
        MATCH path = (n {full_name: "Credentials:8:credentialTheft"})-[*..4]->(m) RETURN path
        """
        self.start_node_4 = "Credentials:8:credentialTheft"
        self.target_4 = "Credentials:8:propagateOneCredentialCompromised"
        self.shortest_path_4 = [
            "Credentials:8:attemptUse",
            "Credentials:8:use",
            "Credentials:8:attemptPropagateOneCredentialCompromised",
            self.target_4
        ]

    def set_up(self):
        # Upload the attack graph to Neo4j.
        print("Starting uploading the attackgraph to Neo4j.")
        maltoolbox.ingestors.neo4j.ingest_attack_graph(self.attackgraph, constants.URI, constants.USERNAME, constants.PASSWORD, constants.DBNAME, delete=True)
        print("The attackgraph is uploaded to Neo4j.")

         # Create new mal-toolbox AttackGraph instance.
        self.attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()

        # Load the attack graph.
        print("Load attackgraph.")
        self.attackgraph.load_from_file(constants.TEST_FILE)

        # Set up attackers.
        self.attacker_1 = self.attackgraph.attackers[0]
        self.attacker_2 = self.attackgraph.attackers[1]

    '''
    def test_dijkstra_empty_instance(self):
        # Arrange
        attack_simulation = AttackSimulation(None, self.attacker_1)
        attack_simulation.set_target_node(self.target_1)

        # Act
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, 0)
    '''
    
    def test_dijkstra_with_empty_target(self):
        print(self.attacker_1.node.id)
        # Arrange
        attack_simulation = AttackSimulation(self.attackgraph, self.attacker_1)

        # Act 
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, None)

    def test_dijkstra_with_unreachable_target(self):
        print(self.attacker_1.node.id)

        # Arrange
        attack_simulation = AttackSimulation(self.attackgraph, self.attacker_1)
        attack_simulation.set_target_node(self.target_1)

        # Act 
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, None)

    def test_dijkstra_with_disconnected_unreachable_target(self):
        print(self.attacker_1.node.id)

        # Arrange
        attack_simulation = AttackSimulation(self.attackgraph, self.attacker_1)
        attack_simulation.set_target_node(self.target_3)

        # Act 
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, None)
   
    def test_dijkstra_with_reachable_target(self):
        # Arrange
        attack_simulation = AttackSimulation(self.attackgraph, self.attacker_1)
            
        for node in self.attackgraph.nodes:
            if node.id == "Credentials:8:notPhishable" or node.id == "Credentials:8:attemptCredentialTheft" :
                self.attacker_1.reached_attack_steps.append(node)
            if node.id == self.attacker_1.node.id:
                first_steps_node = node
            if node.id == self.start_node_4:
                start_node = node
        first_steps_node.children.append(start_node)
        attack_simulation.set_target_node(self.target_4)

        correct_cost = 0
        costs = attack_simulation.get_costs()
        for node in self.shortest_path_4:
            correct_cost += costs[node]

        # Act 
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, correct_cost)

    def test_dijkstra_with_reachable_target_long_path(self):
        pass

'''
    def test_dijkstra_on_shortest_path(self):
        # Arrange
        attack_simulation = AttackSimulation(self.attackgraph, self.attacker_1)
        attack_simulation.set_target_node(self.target_1)

        cypher_query = (
            f"MATCH path = (sourceNode:Label {{id: '{self.attacker_1.node.id}'}})-[*]->(targetNode:Label {{id: '{self.target_1}'}}) "
            "WITH COLLECT(path) AS allPaths "
            "UNWIND allPaths AS uniquePath "
            "RETURN DISTINCT uniquePath"
        )

        # Execute the query
        result = self.graph.run(cypher_query)

        # Process the result, e.g., print each path
        for record in result:
            path = record["uniquePath"]
            print(path)

        # Act
        cost = attack_simulation.dijkstra()
        print(cost)
        # Assert
        self.assertEqual(0, 0)'''
    
    #def test_dijkstra_on_path(self):

    #def test_dijkstra_on_path_with_and_nodes(self):

    #def test_dijkstra_on_wrong_type_of_target(self):

    #def test_dijkstra_unreachable_target(self):

    #def test_random(self):

    # def test_bfs(self):

if __name__ == '__main__':
    unittest.main()


'''
class TestBFS(unittest.TestCase):
    def setUp(self):
        # Set up your test graph as a JSON file
        # For simplicity, let's assume a simple directed graph
        # with nodes having 'cost' attributes
        self.graph_file = constants.TEST_FILE

        # Create mal-toolbox AttackGraph instance.
        self.attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()
    
        # Load the attack graph.
        self.attackgraph.load_from_file(self.graph_file)
        

    def test_case1(self):
        # Test BFS with stop condition based on accumulated cost
        graph_data = json.load(open(self.graph_file))

        start_node =
        n = 10  # Example stop condition threshold

        # Create AttackSimulation instance.
        attack_simulation = AttackSimulation(attackgraph, attacker)
        attack_simulation.set_attacker_cost_budget(int(attacker_cost_budget))

        # result = bfs_search(graph_data, start_node, n)

        # Perform assertions based on your expectations
        # For example, check if the result contains the expected nodes
        expected_result = [1, 2, 3, 4]
        self.assertEqual(result, expected_result)

    def tearDown(self):
        # Clean up, delete the temporary graph file
        import os
        os.remove(self.graph_file)

class TestDijkstra(unittest.TestCase):
    def setUp(self):
        # Set up your test graph as a JSON file
        # For simplicity, let's assume a simple directed graph
        # with nodes having 'cost' attributes
        self.graph_file = constants.TEST_FILE

        with open(self.graph_file, 'r') as f:
            json.load(f)

    def test_bfs(self):
        # Test BFS with stop condition based on accumulated cost
        graph_data = json.load(open(self.graph_file))

        start_node = 1
        n = 10  # Example stop condition threshold

        result = bfs_search(graph_data, start_node, n)

        # Perform assertions based on your expectations
        # For example, check if the result contains the expected nodes
        expected_result = [1, 2, 3, 4]
        self.assertEqual(result, expected_result)
'''
