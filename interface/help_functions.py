from typing import List
import json
import random

# Custom files.
import constants

def print_dictionary(dict):
    """
    Prints the keys and values of a dictionary in custom format.
    
    Arguments:
    dict           - a dictionary
    """
    for command in dict:
        description = dict[command]
        print(f"{constants.BOLD}", "(", command, ")", end=" ")
        if type(description) == list:
            description_str = ""
            for elem in description:
                description_str += elem + " "
            description = description_str
        print(f"{constants.BOLD}", description)
    print(f"{constants.STANDARD}",end="")


def calculate_costs_and_save_as_json(node_list, output_file):
    """
    Calculates the cost randomly and maps the attack step id to the cost.
    This information is then saved on file.
    
    Arguments:
    node_list       - a list of attack steps.
    output_file     - file name.
    """
    costs_dict = {}

    for node in node_list:
        node_id = node.id
        node_asset = node.asset

        if node_id is not None and node_asset != "Attacker":
            cost = random.randint(1, 10)
            costs_dict[node_id] = cost

    with open(output_file, 'w') as file:
        json.dump(costs_dict, file)

def load_costs_from_file():
    """
    Load cost from file.
    
    Return:
    costs_dict      - dictionary
    """
    try:
        with open(constants.COST_FILE, 'r') as file:
            costs_dict = json.load(file)
        return costs_dict
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle file not found or invalid JSON
        return {}
