# INTERFACE / mgg-toolbox

## PURPOSE

This is an interactive interface forrunning attack simulations on the mgg-generated attack graphs.

## INSTALLATION

### Clone the a_star and mgg repository
Clone the repositories by doing:
```sh
git clone https://github.com/gnebbia/mgg
git clone https://github.com/beatajoh/a_star
```
### virtual environment
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

**NOTE:** In order to get reliable results for Dijkstra, Random path, and Step by step attack, make sure to run any of the Reachability analysis options on the attack graph first. Thereafter, go back to the start and load the file called "*reachability_analysis_graph.json*".

The results from the attack simulations are always stored in the same json files, according to this table:

| Function | Result file |
| -------- | ---------- |
| Step by step | test_graphs/step_by_step_graph.json |
| Dijkstra, Random path, BFS | test_graphs/attack_simulation_graph.json |
| Reachability analysis, Reachablilty analysis with pruning of unreachable nodes | test_graphs/reachablility_analysis_graph.json |

## TODO
* Add AO* to the rest of the code.
* Add more node properties and labels to show Neo4j
    * by modifying the upload_json_to_neo4j_database function in main.py.
* Add apocriphy function to the and node checks in all_parents_visited(), since we need to do reachability analysis manually right now before running attack simulations.
* check time complexity.
* Error handling on user input
* If we don't want to have to do reachability analysis manually for Dijkstra, Random path, Step-by-step algorithms:
    * add reachability analysis as an automatic step before some of the attack simulations.
    * or change all_parents_visited (in attack_simulations.py) function to check reachability.
