
# Colors.
HEADER_COLOR = '\033[95m'
ATTACKER_COLOR = '\033[91m'
STANDARD = '\033[0m'
BOLD = '\033[1m'

# All walker options.
ATTACK_OPTIONS = {
    "1": "step by step attack",
    "2": "shortest path with dijkstra",
    "3": "random path",
    "4": "breadth first search"
    }

# Used in AttackSimulation.step_by_step_attack_simulation().
STEP_BY_STEP_ATTACK_COMMANDS = {
    "1": "horizon",
    "2": "action",
    "3": "exit"
    }

# Path to the tmp directory.
FILE = "tmp/attackgraph.json"

# File to store result attack graphs.
RESULT_FILE = "result/result_attackgraph.json"

MAR_ARCHIVE = "assets/org.mal-lang.coreLang-0.3.0.mar"

