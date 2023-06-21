import json
from py2neo import Graph
import a_star_shortest_path as a_star_shortest_path

def main():

    file="test_graphs/small_graph.json"

    start_node = "A" # id attribute in json file

    target_node = "E"

    # reachability analysis ?

    with open(file, 'r') as readfile:
        atkgraph=json.load(readfile)

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
                    if link==id:
                        parent_list.append(id2)
            n+=1
            atkgraph[i]["parent_list"]=parent_list
    return atkgraph
                    

# function for viewing the shortest path ?


if __name__=='__main__':
     main()
