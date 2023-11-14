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
        self.target_node = target_node

    def set_attacker_cost_budget(self, attacker_cost_budget):
        self.attacker_cost_budget = attacker_cost_budget

    def print_horizon(self):
        """
        TODO docs
        Prints the node id:s of a set of nodes together with a number and the node type.
        
        Arguments:
        horizon         - a set of horizon node id:s.
        node_dict       - a dictionary on the form {str id: AttackGraphNode}.
        """
        print(f"{constants.ATTACKER_COLOR}Attacker Horizon{constants.STANDARD}")
        for i, node_id in enumerate(self.horizon):
            print("(", i+1, ")", node_id, self.attackgraph_dictionary[node_id].type)
        print(f"{constants.STANDARD}")

    def add_children_to_horizon(self, node):
        """
        TODO docs
        Adds the node ID:s of adjacent nodes to a node to a set.

        Arguments:
        node                - the AttackGraphNode node.
        horizon             - a set of horizon node id:s.
        visited             - a set of visited node id:s
        """
        # Add the horizon nodes.
        for child in node.children:
            if child.id not in self.visited:
                self.horizon.add(child.id)

    def get_horizon_with_commands(self):
        """
        TODO docs
        Builds a dictionary with an integer as keys and Node id:s as values.

        Arguments:
        nodes           - a set of node id:s.

        Return:
        A dictionary on the form {str id: AttackGraphNode}.
        """
        dict = {}
        for i, node_id in enumerate(self.horizon):
            dict[i+1] = node_id
        return dict

    def step_by_step_attack_simulation(self, neo4j_graph_connection):
        """
        TODO docs
        Main function for the step by step attack simulation. 

        Arguments:
        neo4j_graph          - connection to the graph database in Neo4j.
        attacker             - the Attacker instance.
        attackgraph_dictionary     - the attackgraph as a dictionary with a string node id as key 
                            and AttackGraphNode as value.
        Return:
        A List of all AttackGraphNodes.
        """
        print(f"{constants.HEADER_COLOR}Step by step attack{constants.STANDARD}")

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
            help_functions.print_options(constants.STEP_BY_STEP_ATTACK_COMMANDS)
            command = input("Choose: ")

            # View current attacker horizon.
            if command == '1':
                self.print_horizon()

            # Action.   
            elif command == '2':
                # Choose next node to visit.       
                node_options = self.get_horizon_with_commands()
                self.print_horizon()
                option = input("Choose a node (id) to attack: ")
                attacked_node_id = node_options[int(option)]
                attacked_node = self.attackgraph_dictionary[attacked_node_id]

                # Update horizon if the node can be visited.
                if attacked_node_id in self.horizon and self.check_dependency_steps(attacked_node):
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
            
    def check_dependency_steps(self, node):
        """
        Checks if the dependency steps for a node are completed.
        This includes also checking the reachability of the node.

        Arguments:
        node_id              - node ID.
        attackgraph_dict     - a dictionary representing the attack graph.

        Return:
        True if the node is an 'or' node.
        True if the node is an 'and' node which is reachable and all dependency steps has been visited.
        Otherwise False.
        
        """
        if node.type == 'and':
            # check reachability
            if not maltoolbox.attackgraph.query.is_node_traversable_by_attacker(node, self.attacker):
                return False
            # check if all dependency steps has been traversed
            for parent in node.parents:
                if parent not in self.visited:
                    return False 
        return True
    
    def upload_graph_to_neo4j(self, neo4j_graph_connection, add_horizon=False):
        """
        Uploads the traversed path and attacker horizon (optional) by the attacker to the Neo4j database.

        Arguments:
        neo4j_graph           - connection to the graph database in Neo4j.
        path_nodes            - a set of attack steps in the path.
        attackgraph_dict      - a dictionary containing the node id:s as keys and corresponding AttackGraphNode as values.
        horizon_nodes         - a set of horizon attack steps.
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
        TODO docs
        Finds the shortest path between two nodes with Dijkstra's algorithm, with added conditions for processing the 'and' nodes.

        Arguments:
        start_node           - node id of the start node (this is often the attacker node id).
        target_node          - node id of the target node.
        node_dict            - a dictionary on the form {str node id: AttackGraphNode}, representing the attack graph.

        Return:
        A tuple on the form (cost, node_dict, visited, _)
        cost                 - integer representing the total cost of the path.
        node_dict            - a dictionary representing the attack graph. The "path_links" property contains the paths.
        visited              - a set of nodes in the path.
        """

        node_ids = list(self.attackgraph_dictionary.keys())

        open_set = []
        heapq.heappush(open_set, (0, self.start_node))

        #visited = set()
        print("start_node", type(self.start_node))
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
        f_score[self.start_node] = h_score[self.start_node] # TODO calculate the h_score for all nodes.
        
        costs = self.get_costs()
        costs_copy = costs.copy()

        current_node = self.start_node
        while len(open_set) > 0:
            # The current_node is the node in open_set having the lowest f_score value.
            current_score, current_node = heapq.heappop(open_set)
            self.visited.add(current_node)

            if current_node == self.target_node:
                print("DONE")
                print(came_from)
                self.visited = set()
                return self.reconstruct_path(came_from, current_node, costs_copy)

            current_neighbors = self.attackgraph_dictionary[current_node].children
        
            for neighbor in current_neighbors:  
                tentative_g_score = g_score[current_node]+costs[neighbor.id]
                # Try the neighbor node with a lower g_score than the previous node.
                if tentative_g_score < g_score[neighbor.id]:
                    # If it is an 'or' node or if the and all parents to the 'and' node has been visited,
                    # continue to try this path.
                    if self.check_dependency_steps(neighbor):
                    #all_parents_visited(attacker, neighbor, visited):
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
        TODO
        Reconstructs the path found by the Dijksta algorithm and calculates the total cost for the path.

        Arguments:
        came_from            - a dictionary representing the path on the form {Node ID: [Node ID, ...]}. The nodes in the values has links to the corresponding node in the key.
        current              - current node id for a node in the path. At the start this is the target node ID.
        start_node           - node ID for the start node
        costs                - a dictionary representing the costs for all nodes on the form {Node ID: cost, ...}.
        node_dict            - a dictionary representing the attack graph.
        visited              - set of visited nodes.


        Return:
        A tuple on the form (cost, node_dict, visited, _)
        cost                 - integer representing the total cost of the path-.
        node_dict            - a dictionary representing the attack graph. The "path_links" property contains the paths.
        visited              - a set of nodes in the path.
        """
        cost = 0
        if current != self.start_node:
            # Reconstruct the path backwards until the start node is reached.
            while current in came_from.keys() and current != self.start_node:
                old_current = current
                # Get all links betweem current to old_current.
                current = came_from[current]
                # Condition for 'and' node       
                if len(current) > 1:
                    for node in current:
                        path_cost, _, _= self.reconstruct_path(came_from, node, costs)
                        cost += path_cost + costs[old_current]
                        #TODO node_dict[node]["path_links"].append(old_current)
                        #TODO self.attackgraph_dictionary[node].extra.append(old_current)
                        self.path[node].append(self.attackgraph_dictionary[old_current])
                        self.visited.add(old_current)
                    break
                # Condition for 'or' nodes.
                else:
                    current = current[0]
                    if old_current not in self.visited:
                        cost += costs[old_current]
                        self.visited.add(old_current)
                    #TODO if old_current not in self.attackgraph_dictionary[current].extra:
                    if old_current not in self.path[current]:
                        self.path[current].append(self.attackgraph_dictionary[old_current])
                        # TODO self.attackgraph_dictionary[current].extra.append(self.attackgraph_dictionary[old_current]) 
            self.visited.add(self.start_node)
        return cost, old_current

    def get_costs(self):
        """
        TODO docs and fix
        Gets the cost for all nodes in the graph.

        Arguments:
        node_dict       - dictionary representing the attack graph.

        Return:
        A dictionary containing all node ids as keys, and the costs as values.
        """
        dict = {}
        for node in self.attackgraph_instance.nodes:
            dict[node.id] = 2
        return dict


    def random_path(self):
        """
        TODO
        Get a random path in the attack graph. 
        It is possible to search for a target_node and/or use a cost_budget.

        Arguments:
        start_node           - Node ID of the start node (this is often the attacker node id).
        node_dict            - a dictionary on the form {node ID: node as dictionary, ...}, representing the attack graph.
        target_node          - Node ID of the target node.
        cost_budget          - integer representing the attacker cost budget.

        Return:
        A tuple on the form (cost, node_dict, visited).
        cost                 - integer representing the total cost of the path.
        node_dic             - a dictionary representing the attack graph. The "path_links" property contains the paths.
        visited              - a set of nodes in the path.
        """
        node_ids = list(self.attackgraph_dictionary.keys())
        # prepare the AttackGraphNode.extra attribute so we can store the path there.
        #for id in node_ids:
        #    self.attackgraph_dictionary[id].extra = []

        self.visited.add(self.start_node)

        came_from = dict.fromkeys(node_ids, '')

        target_found = False

        unreachable_horizon_nodes = set()

        # initialize the attack horizon
        for node in self.attackgraph_dictionary[self.start_node].children:
            self.horizon.add(node.id)
            came_from[node.id] = self.start_node

        costs = self.get_costs()
        cost = 0

        if self.target_node == None and self.attacker_cost_budget == None:
            return cost
       
        while self.horizon and unreachable_horizon_nodes != self.horizon:
            next_node = random.choice(list(self.horizon))
            print(next_node)
            # attack unvisited node
            if self.check_dependency_steps(self.attackgraph_dictionary[next_node]):
                if self.attacker_cost_budget != None and cost+costs[next_node] > self.attacker_cost_budget:
                    break
                self.visited.add(next_node)
                self.path[came_from[next_node]].append(self.attackgraph_dictionary[next_node])
                cost += costs[next_node]
                if next_node in unreachable_horizon_nodes:
                    unreachable_horizon_nodes.remove(node)

                # update the horizon
                self.horizon.remove(next_node)
                for node in self.attackgraph_dictionary[next_node].children:
                    self.horizon.add(node.id)
                    came_from[node.id] = next_node
                # check if the target was selected
                if self.target_node != None and node == self.target_node:
                    target_found = True
                    print("The target,", self.target_node,"was found!")
                    break
            else:
                unreachable_horizon_nodes.add(next_node)
        print("whoops 2")
        # check if the target never was selected in the path
        if self.target_node != None and target_found == False:
            print("The target,", self.target_node, "was not found!")
        return cost

    def bfs(self):
        """
        TODO
        Breadth First Search with changed stop condition.
        Gets a subgraph with nodes which is at a lower or equal distance/cost than a max distance value.

        Arguments:
        source               - node ID.
        node_dict            - a dictionary representing the attack graph.
        max_distance         - integer representing the max distance/cost

        Return:
        A set of nodes included in the subgraph
        """
        queue = deque([(self.start_node, 0)])  # Start BFS from the start node with distance 0
        self.visited = set([self.start_node])  # Keep track of visited nodes
        # Perform Breadth-First Search (BFS) from the start node
        costs = self.get_costs()
        while queue:
            node, cost = queue.popleft()
            # Explore the neighbors of the current node
            for link in self.attackgraph_dictionary[node].children:
                cost = cost + costs[link.id]
                if link.id not in self.visited and cost <= self.attacker_cost_budget:
                    self.visited.add(link.id)
                    queue.append((link.id, cost))
                    self.path[node].append(link)
        return cost