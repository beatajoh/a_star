# interface / mgg toolbox ?


## set it up

### clone the repository

### clone the mgg repository

### virtual environment

### set up the neo4j database

### change a line in the code 

## run the interface
open the terminal, navigate to the interface directory, and run:
````
python main.py

````




## TODO

* Add AO* to the rest of the code.
* Add more node properties and labels to Neo4j (by modifying the upload.py file).
* Add apocriphy function to the and node checks in all_parents_visited(), since we need to do reachability analysis right now before running attack simulations.
* check time complexity.
* Error handleling on user input
* add reachability analysis as an automatic step before some of the attack simulations.
    * or change attack_simulations.all_parents_visited() function to check reachability.



Insert prerequisites
* clone interface and mgg into the same repo
* venv
* set up the neo4j database with specific credentials
* run main.py
* interface/assets and test_graphs