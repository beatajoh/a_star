
HEADER_COLOR = '\033[95m'
ATTACKER_COLOR = '\033[91m'
STANDARD = '\033[0m'
BOLD = '\033[1m'


START_COMMANDS = {
    "1": "step by step attack",
    "2": "shortest path with dijkstra",
    "3": "random path",
    #"3": "reachability-analysis-with-pruning",
    #"4": "reachability-analysis",
    "5": "exit"
    }

STEP_BY_STEP_ATTACK_COMMANDS = {
    "1": "horizon",
    "2": "action",
    "3": "exit"
    }

ATTACK_SIMULATION_COMMANDS = {
    "1": "shortest-path-dijkstra",
    "2": "shortest-path-AO-star",
    "3": "random-path",
    "4": "attack-range-BFS",
    "5": "exit"
    }

MAR_ARCHIVE = "assets/org.mal-lang.coreLang-0.3.0.mar"

# path tho the tmp directory
FILE = "tmp/attackgraph.json"

# Files to store result attack graphs.
step_by_step_results_file = "test_graphs/step_by_step_graph.json"
attack_simulation_results_file = "test_graphs/attack_simulation_graph.json"
reachability_analysis_results_file = "test_graphs/reachablility_analysis_graph.json"
