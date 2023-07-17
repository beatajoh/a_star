# INTERFACE FOR ATTACK SIMULATIONS

## PURPOSE

This is an interactive interface for running attack simulations on the mgg-generated attack graphs.

## INSTALLATION

### Clone the a_star and mgg repository
Clone the repositories by doing:
```sh
git clone https://github.com/gnebbia/mgg
git clone https://github.com/beatajoh/a_star
```
### Virtual environment
Set up a virtual environment by doing:
```sh
python -m venv env
source env/bin/activate
cd mgg
pip install -r requirements.txt
```
**NOTE:** You need a python version >= 3.9, the latest the better.

### Set up the Neo4j database
we need an open Neo4j instance running with a database
with the following credentials:

- username: neo4j
- password: mgg12345!
- dbname:   neo4j

Note that the Neo4J project name and the DBMS name used within
the project are irrelevant, the most important thing is that
the password matches as the username and specific database
name are set to default values.

## USAGE
open the terminal, navigate to the interface directory, and run:
````
python main.py
````
this flowchart shows the workflow of the interface:
![interface flowchart](assets/interface_flowchart.png)

### What does the attack simulations do?
* **Step by step attack** - Choose a attack path from the attacker node by manually choosing which nodes to move forward to.
* **Shortest path Dijkstra** - Get the shortest path from the attacker node to a target attack step.
* **Random path** - Get a random path of attack steps. It is possible to search for a target attack step and adding a cost budget for the attacker.
* **BFS** - Get a subgraph where all nodes are within a specific distance from the attacker node.
* **Reachability analysis (with pruning)** - Get a subgraph where the label is_reachable is updated (unreachable nodes can be removed).

**NOTE:** In order to get reliable results for Dijkstra, Random path, and Step by step attack, make sure to run any of the Reachability analysis options on the attack graph first. Thereafter, go back to the start and load the file called "*reachability_analysis_graph.json*".

The results from the attack simulations are always stored in the same json files, according to this table:

| Function | Result file |
| -------- | ---------- |
| Step by step | test_graphs/step_by_step_graph.json |
| Dijkstra, Random path, BFS | test_graphs/attack_simulation_graph.json |
| Reachability analysis, Reachablilty analysis with pruning of unreachable nodes | test_graphs/reachablility_analysis_graph.json |

### Example to get started
1. Activate venv.
2. Go to mgg and build an attack graph file (.json) with mgg.
3. Move the json file to the directory interface > test_graphs.
4. Run the interface with ````python main.py````.
5. Now you can choose the *step-by-step* attack option, or any of the graph algorithms if you choose *attack simulations*.
6. For example: load the test_graphs/real_graph.json, choose **(2) Attack simulations**, choose **(1) shortest-path-dijkstra**, and enter the target node id as: Network:8176711980537409:attemptReverseReach
7. The result path should contain these attack steps:
    * Network:8176711980537409:attemptReverseReach, cost = 6
    * Network:8176711980537409:successfulAccess, cost = 10
    * Network:8176711980537409:access, cost = 7
    * Attacker:6417249322885591:firstSteps

    Therefore, the total cost should be 23.

## TODO
* Add AO* to the rest of the code.
* Add more node properties and labels to show Neo4j
    * by modifying the upload_json_to_neo4j_database() function in main.py.
* show all result paths together with the attack graph and asset graph in Neo4j (because right now the paths are displayed separately)
* Error handling on user input.
* If we don't want to have to do reachability analysis manually for Dijkstra, Random path, Step-by-step algorithms:
    * add reachability analysis as an automatic step before some of the attack simulations.
    * or change all_parents_visited() (in attack_simulations.py) function to check reachability with the apocriphy function is_node_reachable().
* The object class (objclass) of attack steps is not checked by the graph algorithms and step-by step attack simulation. This means that e.g. UnknownSoftwareVulnerability attack steps are included in the resulting paths.
* If a simulation is not successful, maybe if a target attack step is not reached, do not upload to Neo4j.
* Make it possible to add multiple attackers/change the point of access for the attacker. Currently we assume that the attacker node is added to the end of the attack graph file.
