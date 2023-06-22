import json
from py2neo import Graph
import a_star_shortest_path as a_star_shortest_path

def main():

    file = "test_graphs/temp-scad.json"

    # start_node and target_node are the id attribute in the .json file
    start_node = "Attacker:6417249322885591:firstSteps"

    #target_node = "Application:7219598629313512:fullAccessAfterSoftProdVulnerability" # False
    #target_node = "SoftwareVulnerability:892728578927324:attemptAbuse" # cost = 24
    #target_node = "Application:2213271547579497:denyFromConnectionRule" # cost = 21
    target_node = "Application:7219598629313512:denyFromConnectionRule" # cost = 23

    #target_node = "Network:8176711980537409:successfulAccess" # cost = 4

    # tests for: test_graphs/real_graph.json

    #start_node = "Attacker:6417249322885591:firstSteps"

    # uncomment any of these lines:
    #target_node = "Network:8176711980537409:eavesdrop" # cost = 24
    #target_node = "Network:8176711980537409:accessNetworkData" # cost = 21
    #target_node = "Network:8176711980537409:eavesdrop" # cost = 27+4+7 (and)
    #target_node = "Application:2213271547579497:networkRequestConnect" # cost = 27
    #target_node = "Network:8176711980537409:successfulAccess" # cost = 17
    #target_node = "Network:8176711980537409:access" # cost = 7

    with open(file, 'r') as readfile:
        atkgraph=json.load(readfile)

    # reachability analysis here ?

    # Get all parent nodes for 'and' nodes in the graph
    atkgraph = get_parents_for_and_nodes(atkgraph)

    # write the attack graph to atkgraph.json in test_graphs directory
    with open('test_graphs/atkgraph.json', 'w', encoding='utf-8') as writefile:
        json.dump(atkgraph, writefile, indent=4)

    # calculate the shortest path
    path=a_star_shortest_path.a_star(atkgraph, start_node, target_node)

    print("\n\n", path, "\n\n\n")
    
    
'''
Traverse the attack graph .json file and get all parents to 'and' nodes and add new 'parent_list' attribute to the file.
parent_list is an array of attack step ids.
'''
def get_parents_for_and_nodes(atkgraph):
    n=0
    id=""
    id2=""
    for i, node in enumerate(atkgraph):
        id=node["id"]
        parent_list=[]
        if node["type"]=="and":
            for node2 in atkgraph:
                id2=node2["id"]
                for link in node2["links"]:
                    print(node2["type"] in ["and", "or"])
                    if link==id and node2["type"] in ["and", "or"]:
                        parent_list.append(id2)
            n+=1
            atkgraph[i]["parent_list"]=parent_list
    return atkgraph
                    

# function for viewing the shortest path ?


if __name__=='__main__':
     main()
