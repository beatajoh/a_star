from typing import List
import constants
import maltoolbox
import maltoolbox.attackgraph.attackgraph

def print_dictionary(dict):
    """
    Prints the keys and values of a dictionary in custom format.
    
    Arguments:
    dict           - a dictionary
    """
    for command in dict:
        description = dict[command]
        print(f"{constants.BOLD}", "(", command, ")", end=" ")
        print(f"{constants.BOLD}", description)
    print(f"{constants.STANDARD}",end="")

