import help_functions
import constants
import maltoolbox.attackgraph.query
import maltoolbox
import maltoolbox.attackgraph.attackgraph
from py2neo import Graph, Node, Relationship
from collections import deque
import heapq
import random

class AttackSimulation:
    
    def __init__(self, attackgraph_instance, attackgraph_dictionary, attacker):
        """
        Initialize the AttackSimulation instance.

        Parameters:
        - attackgraph_instance: An instance of the AttackGraph class.
        - attackgraph_dictionary: A dictionary representing the attack graph.
        - attacker: An instance of the Attacker class.
        """
        self.attackgraph_instance = attackgraph_instance
        self.attackgraph_dictionary = attackgraph_dictionary
        self.attacker = attacker
        self.path = {key: [] for key in attackgraph_dictionary.keys()}
        self.horizon = set()
        self.visited = set()
        self.start_node = attacker.node.id
        self.target_node = None
        self.attacker_cost_budget = None

    def set_target_node(self, target_node):
        """
        Set the target node for the simulation.

        Parameters:
        - target_node: The ID of the target node.
        """
        self.target_node = target_node

    def set_attacker_cost_budget(self, attacker_cost_budget):
        """
        Set the attacker's cost budget for the simulation.

        Parameters:
        - attacker_cost_budget: The budget representing the cost budget of the attacker.
        """
        self.attacker_cost_budget = attacker_cost_budget

    def print_horizon(self):
        """
        Prints the horizon attack steps and the type in custom format.
        """
        horizon_dict = self.build_horizon_dict()
        print(f"{constants.ATTACKER_COLOR}Attacker Horizon{constants.STANDARD}")
        help_functions.print_dictionary(horizon_dict)

    def add_children_to_horizon(self, node):
        """
        Add the horizon nodes to the set of visited nodes.

        This method iterates over the children of the given node, adding each child's
        ID to the set of visited nodes (self.visited) if it is not already present in the set.

        Parameters:
        - node: The AttackGraphNode whose children are to be added to the horizon.

        """
        for child in node.children:
            if child.id not in self.visited:
                self.horizon.add(child.id)

    def build_horizon_dict(self):
        """
        Build a dictionary with an integer as keys and Node ID:s as values.
        
        Return:
        - dict: A dictionary on the form {ID (string): node (AttackGraphNode)}.
        """
        dict = {}
        for i, node_id in enumerate(self.horizon):
            dict[i+1] = node_id + self.attackgraph_dictionary[node_id].type
        return dict

    def step_by_step_attack_simulation(self, neo4j_graph_connection):
        """
        Traverse the attack graph step by step. 
        
        Parameters:
            - neo4j_graph_connection: The Neo4j Graph instance.

        Returns:
        - cost: The total cost of the explored path.
        """
        # Add all children nodes to the path attribute.
        for node_id in self.attackgraph_dictionary.keys():
            self.path[node_id] = self.attackgraph_dictionary[node_id].children

        # Mark the attacker node as visited by adding the node id to visited.
        attacker_entry_point_id = self.attacker.node.id  # TODO
        self.visited.add(attacker_entry_point_id)

        # Initialize the horizon nodes.
        for node in self.visited:
            self.add_children_to_horizon(self.attackgraph_dictionary[node])
        
        # Begin step by step attack simulation.
        while True:
            help_functions.print_dictionary(constants.STEP_BY_STEP_ATTACK_COMMANDS)
            command = input("Choose: ")

            # View current attacker horizon.
            if command == '1':
                self.print_horizon()

            # Action.   
            elif command == '2':
                # Choose next node to visit.       
                node_options = self.build_horizon_dict()
                self.print_horizon()
                option = input("Choose a node (id) to attack: ")
                attacked_node_id = node_options[int(option)]
                attacked_node = self.attackgraph_dictionary[attacked_node_id]

                # Update horizon if the node can be visited.
                if attacked_node_id in self.horizon and self.check_move(attacked_node):
                    self.visited.add(attacked_node_id)
                    self.horizon.remove(attacked_node_id)
                    self.add_children_to_horizon(attacked_node)
                    
                    # Update the AttackGraphNode status.
                    attacked_node.compromised_by.append(self.attacker)

                    # Upload attacker path and horizon.
                    self.upload_graph_to_neo4j(neo4j_graph_connection, add_horizon=True)
                    print("Attack step was compromised")
                else:
                    print("The required dependency steps for", attacked_node_id, "has not been traversed by the attacker")
                    print("The node was not added to the path")
                # Print horizon nodes.
                self.print_horizon()
            elif command == '3':
                # Return
                return
            
    def check_move(self, node):
        """
        Check if an attack step is traversable.

        This method evaluates the traversability of an attack step, considering both the
        node type ('or' or 'and') and the reachability of the node. For 'or' nodes,
        it returns True. For 'and' nodes, it checks if the node is reachable by the
        attacker and if all dependency steps have been visited, returning True in that
        case. Otherwise, it returns False.

        Parameters:
        - node: The AttackGraphNode instance to be checked for traversability.

        Returns:
        - True if the node is an 'or' node.
        - True if the node is an 'and' node which is reachable and all parent attack steps
        have been visited.
        - False otherwise.

        Notes:
        - The function assumes the existence of the following instance variables:
            - self.visited: A set of visited nodes.
            - self.attacker: The attacker instance.
        """
        if node.type == 'and':
            # Check traversability.
            if not maltoolbox.attackgraph.query.is_node_traversable_by_attacker(node, self.attacker):
                return False
            # Check if all parent steps has been traversed
            for parent in node.parents:
                if parent not in self.visited:
                    return False 
        return True
    
    def upload_graph_to_neo4j(self, neo4j_graph_connection, add_horizon=False):
        """
        Uploads the traversed path and attacker horizon (optional) by the attacker to the Neo4j database.

        Parameters:
        - neo4j_graph_connection: The Neo4j Graph instance.
        - add_horizon: Flag which if True, adds on the horizon to Neo4j.

        Notes:
        - The function assumes the existence of the following instance variables:
            - self.visited: A set of visited nodes.
            - self.self.attackgraph_dictionary: A dictionary representing the attack graph.
        """
        
        nodes = {}
        neo4j_graph_connection.delete_all()

        # Build attack steps for Neo4j from all visited nodes.
        for node_id in self.visited:
            node = self.attackgraph_dictionary[node_id]
            neo4j_node = Node(
                id = node.id,
                type = node.type,
                asset = node.asset,
                name = node.name,
                horizon = False
            )
            neo4j_graph_connection.create(neo4j_node)
            nodes[node.id] = neo4j_node
        
        # Build horizon attack steps for Neo4j if the horizon is not empty.
        if self.horizon and add_horizon:
            for node_id in self.horizon:
                node = self.attackgraph_dictionary[node_id]
                neo4j_node = Node(
                        id = node.id,
                        type = node.type,
                        asset = node.asset,
                        name = node.name,
                        horizon = True
                    )
                neo4j_graph_connection.create(neo4j_node)
                nodes[node.id] = neo4j_node

        # Add edges to the attack graph in Neo4j.
        for id in self.attackgraph_dictionary.keys():
            if id in nodes.keys():
                for link in self.path[id]:
                    if link.id in nodes.keys():
                        from_node = nodes[id]
                        to_node = nodes[link.id]
                        if (from_node['horizon'] == False and to_node['horizon'] == False) or \
                        (from_node['horizon'] == False and to_node['horizon'] == True):
                            relationship = Relationship(from_node, "Relationship", to_node)
                            neo4j_graph_connection.create(relationship)

    def dijkstra(self):
        """
        Find the shortest path between two nodes using Dijkstra's algorithm with added 
        conditions for processing 'and' nodes.
        
        Returns:
        A tuple on the form cost
        - cost: Integer representing the total cost of the path.
        """
        node_ids = list(self.attackgraph_dictionary.keys())
        open_set = []
        heapq.heappush(open_set, (0, self.start_node))
        self.visited.add(self.start_node)
        came_from = dict.fromkeys(node_ids, '')
        came_from = {key: [] for key in came_from.keys()}

        # The g_score is a map with default value of "infinity".
        g_score = dict.fromkeys(node_ids, 10000)
        g_score[self.start_node] = 0

        # TODO calculate the h_score for all nodes if possible.
        h_score = dict.fromkeys(node_ids, 0)
    
        # For node n, f_score[n] = g_score[n] + h_score(n). f_score[n] represents our current best guess as to
        # How cheap a path could be from start to finish if it goes through n.
        f_score = dict.fromkeys(node_ids, 0)
        f_score[self.start_node] = h_score[self.start_node] # TODO calculate the h_score for all nodes if possible.
        
        costs = self.get_costs() # TODO Replace with cost attribute.
        costs_copy = costs.copy()

        current_node = self.start_node
        while len(open_set) > 0:
            # The current_node is the node in open_set having the lowest f_score value.
            current_score, current_node = heapq.heappop(open_set)
            self.visited.add(current_node)

            # Stop condition.
            if current_node == self.target_node:
                self.visited = set()
                return self.reconstruct_path(came_from, current_node, costs_copy)[0]
    
            current_neighbors = self.attackgraph_dictionary[current_node].children # TODO Assuming the horizon is the direct children attack steps.
            for neighbor in current_neighbors:  
                tentative_g_score = g_score[current_node]+costs[neighbor.id]
                # Try the neighbor node with a lower g_score than the previous node.
                if tentative_g_score < g_score[neighbor.id]:
                    # If it is an 'or' node or if the and all parents to the 'and' node has been visited,
                    # continue to try this path.
                    if self.check_move(neighbor):
                        came_from[neighbor.id].append(current_node)
                        g_score[neighbor.id] = tentative_g_score
                        f_score[neighbor.id] = tentative_g_score + h_score[neighbor.id] # TODO calculate the h_score for all nodes
                        if neighbor.id not in open_set:
                            heapq.heappush(open_set, (f_score[neighbor.id], neighbor.id))
                    # If the node is an 'and' node, still update the node cost and keep track of the path.
                    elif neighbor.type == 'and':
                        costs[neighbor.id] = tentative_g_score
                        came_from[neighbor.id].append(current_node)
        return 

    def reconstruct_path(self, came_from, current, costs):
        """
        Reconstructs the backwards attack path from the start node to the given node with recursion.

        This method is used in the context of a Djikstra's algorithm to reconstruct
        the optimal path from the start node to the specified node, considering a set
        of costs associated with each node in the path.

        Parameters:
        - came_from: A dictionary mapping nodes to their predecessors in the optimal path.
        - current: The node for which the path needs to be reconstructed.
        - costs: A dictionary containing the costs associated with each node.

        Returns:
        - cost: The total cost of the reconstructed path.
        - last_node: The last node in the reconstructed path.
        """
        cost = 0
        if current != self.start_node:
            # Reconstruct the path backwards from current until the start node is reached.
            while current in came_from.keys() and current != self.start_node:
                old_current = current
                # Get all parent nodes to current in the path.
                current = came_from[current]
                # Condition for 'and' node.       
                if len(current) > 1:
                    for node in current:
                        path_cost, _, _= self.reconstruct_path(came_from, node, costs)
                        cost += path_cost + costs[old_current]
                        self.path[node].append(self.attackgraph_dictionary[old_current])
                        self.visited.add(old_current)
                    break
                # Condition for 'or' nodes.
                else:
                    current = current[0]
                    if old_current not in self.visited:
                        cost += costs[old_current]
                        self.visited.add(old_current)
                    if old_current not in self.path[current]:
                        self.path[current].append(self.attackgraph_dictionary[old_current])
            self.visited.add(self.start_node)
        print(old_current)
        return cost, old_current

    def get_costs(self):
        """
        # TODO Currently there is no cost attribute, so this function is used instead. 
        Assigns a constant cost for compromising the attack step for all nodes in the graph.

        Return:
        A dictionary containing all attack step ids as keys, and the constant cost as values.
        """
        dict = {}
        for node in self.attackgraph_instance.nodes:
            dict[node.id] = 2
        return dict


    def random_path(self):
        """
        Generate a random attack path in the attack graph, considering attacker cost budget and/or target node.

        This method explores a random path in the attack graph, starting from the start node.
        It uses a random selection strategy among the horizon nodes, respecting the attacker's cost budget
        and searching for a specific target node if provided.

        Returns:
        - cost: The total cost of the random path.
        """
        node_ids = list(self.attackgraph_dictionary.keys())
        self.visited.add(self.start_node)
        came_from = dict.fromkeys(node_ids, '')
        target_found = False
        unreachable_horizon_nodes = set()

        # Initialize the attack horizon
        # TODO Assuming the horizon is the direct children attack steps.
        for node in self.attackgraph_dictionary[self.start_node].children:
            self.horizon.add(node.id)
            came_from[node.id] = self.start_node

        costs = self.get_costs() # TODO Replace with cost attribute.
        cost = 0

        if self.target_node == None and self.attacker_cost_budget == None:
            return cost
        
        while self.horizon and unreachable_horizon_nodes != self.horizon:
            next_node = random.choice(list(self.horizon))
            print(next_node)
            # Attack unvisited node in the horizon.
            if self.check_move(self.attackgraph_dictionary[next_node]):
                if self.attacker_cost_budget != None and cost+costs[next_node] > self.attacker_cost_budget:
                    break
                self.visited.add(next_node)
                self.path[came_from[next_node]].append(self.attackgraph_dictionary[next_node])
                cost += costs[next_node]
                if next_node in unreachable_horizon_nodes:
                    unreachable_horizon_nodes.remove(node)
                # Update the horizon.
                self.horizon.remove(next_node)
                for node in self.attackgraph_dictionary[next_node].children:
                    self.horizon.add(node.id)
                    came_from[node.id] = next_node
                # Check if the target node was selected (if the target node was specified).
                if self.target_node != None and node == self.target_node:
                    target_found = True
                    print("The target,",self.target_node,"was found!")
                    break
            else:
                unreachable_horizon_nodes.add(next_node)
        # Check if the target never was selected in the path
        if self.target_node != None and target_found == False:
            print("The target,", self.target_node, "was not found!")
        return cost

    def bfs(self):
        """
        Perform Breadth-First Search (BFS) on the attack graph from the start node.

        This method explores the attack graph starting from the specified start node,
        considering a cost budget for the attacker. It calculates the total cost of the
        paths within the budget and returns the final cost.

        Returns:
        - cost: The total cost of the paths explored within the attacker's cost budget.
        """
        # Start BFS from the start node with distance 0.
        queue = deque([(self.start_node, 0)])  
        self.visited = set([self.start_node]) 
        costs = self.get_costs() # TODO Replace with cost attribute.
        while queue:
            node, cost = queue.popleft()
            # Explore the horizon of the current node.
            for link in self.attackgraph_dictionary[node].children: # TODO Assuming the horizon is the direct children attack steps.
                cost = cost + costs[link.id]
                if link.id not in self.visited and cost <= self.attacker_cost_budget:
                    self.visited.add(link.id)
                    queue.append((link.id, cost))
                    self.path[node].append(link)
        return cost