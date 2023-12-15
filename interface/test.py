import unittest
import maltoolbox.attackgraph.attackgraph
import maltoolbox.ingestors.neo4j
import maltoolbox.model.model
import maltoolbox.language.specification
import maltoolbox.language.classes_factory
import maltoolbox.attackgraph.attacker
import maltoolbox.attackgraph.query

# Custom files.
import constants
from attack_simulation import AttackSimulation

def add_entry_points_to_attacker(model, entry_point_attack_steps, attacker_index=0):
    for asset_id, attack_steps in entry_point_attack_steps:
                asset = model.get_asset_by_id(asset_id)
                model.attackers[attacker_index].entry_points.append((asset, attack_steps))
    return model

class TestAttackSimulation(unittest.TestCase):

    def setUp(self):
        # Create the language specification and LanguageClassesFactory instance.
        lang_spec = maltoolbox.language.specification.load_language_specification_from_mar(constants.MAR_ARCHIVE)
        lang_classes_factory = maltoolbox.language.classes_factory.LanguageClassesFactory(lang_spec)
        lang_classes_factory.create_classes()

        # Create mal-toolbox Model instance.
        self.model = maltoolbox.model.model.Model("model", lang_spec, lang_classes_factory)
        self.model.load_from_file(constants.MODEL_FILE)

        # Generate mal-toolbox AttackGraph.
        self.attackgraph = maltoolbox.attackgraph.attackgraph.AttackGraph()
        self.attackgraph.generate_graph(lang_spec, self.model)

        # Change nodes with type 'defense' so that is_necessary=False, for testing purposes.
        for node in self.attackgraph.nodes:
            if node.type == 'defense':
                node.is_necessary = False

        # Add the attacker.
        self.model.attackers = []
        attacker_id = 1
        attacker = maltoolbox.model.model.Attacker()
        self.model.add_attacker(attacker, attacker_id)
        self.model.attackers[0].entry_points = []

    def test_shortest_path_on_1_step_or_path(self):
        # Arrange
        target_attack_step = "Credentials:6:attemptCredentialsReuse"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse"]], [8, ["attemptCredentialsReuse"]]]
        actual_cost = 4
        actual_visited_attack_steps = {"Attacker:1:firstSteps", "Credentials:6:attemptCredentialsReuse"}
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]
        
        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, actual_cost)
        self.assertEqual(attack_simulation.visited, actual_visited_attack_steps)

    def test_shortest_path_on_6_step_with_and_in_path(self):
        # Arrange
        target_attack_step = "Application:0:fullAccess"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
        actual_cost = 19
        actual_visited_attack_steps = {"Attacker:1:firstSteps", "Application:0:attemptFullAccessFromSupplyChainCompromise", "Application:0:bypassSupplyChainAuditing", "Application:0:supplyChainAuditingBypassed", "Application:0:fullAccessFromSupplyChainCompromise", "Application:0:fullAccess"}
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]
        
        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, actual_cost)
        self.assertEqual(attack_simulation.visited, actual_visited_attack_steps)

    def test_shortest_path_on_14_step_path(self):
        # Arrange
        target_attack_step = "Credentials:9:propagateOneCredentialCompromised"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
        actual_cost = 79
        actual_visited_attack_steps = {"Attacker:1:firstSteps", "Credentials:6:attemptCredentialsReuse", "Credentials:6:credentialsReuse", "Credentials:6:attemptUse", "Credentials:6:use", "Credentials:6:attemptPropagateOneCredentialCompromised", \
                                        "Credentials:6:propagateOneCredentialCompromised", "User:11:oneCredentialCompromised", "User:11:passwordReuseCompromise", "Credentials:9:attemptCredentialsReuse", "Credentials:9:credentialsReuse", \
                                        "Credentials:9:attemptUse", "Credentials:9:use", "Credentials:9:attemptPropagateOneCredentialCompromised", "Credentials:9:propagateOneCredentialCompromised"}
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]
        
        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, actual_cost)
        self.assertEqual(attack_simulation.visited, actual_visited_attack_steps)

    def test_shortest_path_on_unreachable_attack_step(self):
        # Arrange
        target_attack_step = "Credentials:5:extract"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
        actual_cost = 0
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]
        
        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, actual_cost)
        self.assertNotIn(target_attack_step, attack_simulation.visited)

    def test_shortest_path_on_choice_between_two_paths_to_target(self):
        # Arrange
        target_attack_step = "Application:0:fullAccess"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise", "fullAccess"]], [8, ["attemptCredentialsReuse"]]]
        actual_cost = 1
        actual_visited_attack_steps = {"Attacker:1:firstSteps", "Application:0:fullAccess"}
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]
        
        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.dijkstra()

        # Assert
        self.assertEqual(cost, actual_cost)
        self.assertEqual(attack_simulation.visited, actual_visited_attack_steps)

    def test_random_path_with_infinate_cost_budget_on_reachable_node(self):
        # Arrange
        target_attack_step = "Application:0:bypassSupplyChainAuditing"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]

        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.random_path()

        # Assert
        self.assertGreater(cost, 0)
        self.assertIn(target_attack_step, attack_simulation.visited)

    def test_random_path_with_infinate_cost_budget_on_unreachable_node(self):
        # Arrange
        target_attack_step = "Credentials:8:extract"
        entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse"]], [8, ["attemptCredentialsReuse"]]]
        self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
        self.attackgraph.attach_attackers(self.model)
        attacker = self.attackgraph.attackers[0]

        # Act
        attack_simulation = AttackSimulation(self.attackgraph, attacker) 
        attack_simulation.set_target_node(target_attack_step)
        cost = attack_simulation.random_path()

        # Assert
        self.assertGreater(cost, 0)
        self.assertNotIn(target_attack_step, attack_simulation.visited)
        for horizon_node in attack_simulation.horizon:
                if maltoolbox.attackgraph.query.is_node_traversable_by_attacker(attack_simulation.attackgraph_dictionary[horizon_node], attack_simulation.attacker):
                    self.assertFalse(horizon_node)

    def test_random_path_with_infinate_cost_budget_on_reachable_node_containing_and_step(self):
            # Arrange
            target_attack_step = "Application:0:fullAccessFromSupplyChainCompromise"
            entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
            optimal_cost = 19
            self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
            self.attackgraph.attach_attackers(self.model)
            attacker = self.attackgraph.attackers[0]

            # Act
            attack_simulation = AttackSimulation(self.attackgraph, attacker) 
            attack_simulation.set_target_node(target_attack_step)
            cost = attack_simulation.random_path()

            # Assert
            self.assertGreater(cost, optimal_cost)
            self.assertIn(target_attack_step, attack_simulation.visited)

    def test_random_path_with_restricted_cost_budget_on_reachable_target_node(self):
            # Arrange
            target_attack_step = "Credentials:9:propagateOneCredentialCompromised"
            attacker_cost_budget = 1
            entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
            self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
            self.attackgraph.attach_attackers(self.model)
            attacker = self.attackgraph.attackers[0]

            # Act
            attack_simulation = AttackSimulation(self.attackgraph, attacker) 
            attack_simulation.set_attacker_cost_budget(attacker_cost_budget)
            attack_simulation.set_target_node(target_attack_step)
            cost = attack_simulation.random_path()

            # Assert
            self.assertLessEqual(cost, attacker_cost_budget)
            self.assertNotIn(target_attack_step, attack_simulation.visited)

    def test_random_path_with_cost_budget_and_no_target_node(self):
                # Arrange
                attacker_cost_budget = 10
                entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
                self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
                self.attackgraph.attach_attackers(self.model)
                attacker = self.attackgraph.attackers[0]

                # Act
                attack_simulation = AttackSimulation(self.attackgraph, attacker) 
                attack_simulation.set_attacker_cost_budget(attacker_cost_budget)
                cost = attack_simulation.random_path()

                # Assert
                self.assertLessEqual(cost, attacker_cost_budget)

    def test_random_path_with_no_cost_budget_and_no_target_node(self):
                # Arrange
                entry_point_attack_steps = [[5, ["attemptCredentialsReuse"]], [6, ["attemptCredentialsReuse", "guessCredentials"]], [0, ["softwareProductAbuse", "attemptFullAccessFromSupplyChainCompromise"]], [8, ["attemptCredentialsReuse"]]]
                number_of_traversable_attack_steps = 173    # Value derived from bfs, which includes non-reachable attacksteps.
                self.model = add_entry_points_to_attacker(self.model, entry_point_attack_steps)
                self.attackgraph.attach_attackers(self.model)
                attacker = self.attackgraph.attackers[0]

                # Act
                attack_simulation = AttackSimulation(self.attackgraph, attacker) 
                cost = attack_simulation.random_path()

                # Assert
                self.assertLessEqual(len(attack_simulation.visited), number_of_traversable_attack_steps)
                for horizon_node in attack_simulation.horizon:
                    if maltoolbox.attackgraph.query.is_node_traversable_by_attacker(attack_simulation.attackgraph_dictionary[horizon_node], attack_simulation.attacker):
                        self.assertFalse(horizon_node)

if __name__ == '__main__':
    unittest.main()