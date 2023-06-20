import json
from py2neo import Graph
import a_star_shortest_path as a_star_shortest_path

def main():
    file="test_graphs/small_graph.json"
    with open(file, 'r') as readfile:
        atkgraph = json.load(readfile)

    atkgraph=get_parents_for_and_nodes(atkgraph)

   
    with open('atkgraph.json', 'w', encoding='utf-8') as writefile:
        json.dump(atkgraph, writefile, indent=4)
    
    path=a_star_shortest_path.a_star(atkgraph)

    print("\n\n", path, "\n\n\n")
    
    
'''
Go through the attack graph .json file and get all parents to and nodes and add new "parent_list" attribute to the file.
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
                    

def convert_model_to_mgg(uri="bolt://localhost:7687", 
            username="neo4j",
            password="mgg12345!",
            dbname="neo4j",
            delete=False
    ) -> dict:
        print("hello")
        g = Graph(uri=uri, user=username, password=password, name=dbname) 

        # Get all relationships
        results = g.run('MATCH paths=(source {name: "Attacker:6417249322885591:firstSteps"})-[*]->(target {name: "Application:7219598629313512:networkAccess"}) return paths'
    ).data()
        print(results)

        objects = {}
        associations = []

        for row in results:
            rel1 = list(row['r1'].types())[0]
            rel2 = list(row['r2'].types())[0]
            nodea = dict(row['a'])
            nodeb = dict(row['b'])
            objects[nodea['scad_id']] = {your_key: nodea[your_key] for your_key in ['name','metaconcept','eid']}
            objects[nodeb['scad_id']] = {your_key: nodeb[your_key] for your_key in ['name','metaconcept','eid']}
            add_elem = True
            for assoc in associations:
                if set([nodea['scad_id'],nodeb['scad_id'],rel1,rel2]) == set(assoc.values()):
                    add_elem = False
            if add_elem:
                associations.append({'id1': nodea['scad_id'], 'id2': nodeb['scad_id'], 'type1': rel1, 'type2': rel2})


        newmodel = {'metadata': {'scadVersion': '1.0.0', 'langVersion': '0.3.0', 'langID': 'org.mal-lang.coreLang', 'malVersion': '0.1.0-SNAPSHOT', 'info': 'Created with securiCAD Professional 1.6'}, 'objects': objects, 'associations': associations}
        print("\n\nEXIT\n\n")
        return newmodel

if __name__=='__main__':
     main()
