from gerrychain import Graph, Partition, Election
from gerrychain.updaters import Tally, cut_edges
from gerrychain import MarkovChain
from gerrychain.constraints import single_flip_contiguous
from gerrychain.proposals import propose_random_flip
from gerrychain.accept import always_accept
from Plotting import boxPlot
from matplotlib import pyplot as plt
import geopandas
import pandas
import maup
import random
from copy import deepcopy
STEPS = 1000000

def mode(l):
    count = {}
    for element in l:
        if element not in count:
            count[element] = 1
        else:
            count[element]+=1
    ret = None
    ret_count = 0
    for unique_element in count:
        if count[unique_element] > ret_count:
            ret = unique_element
            ret_count = count[unique_element]
    return ret

def permuteAssignments(assignment, units, steps):
    perms = [assignment]
    # Get all precincts sitting on a border
    bordering_precincts = {} 
    for index, precinct in units.iterrows():   
        print("GETTING BORDERING PRECINCTS", index)
        # get neighbors 
        neighbors = units[~units.geometry.disjoint(precinct.geometry)].drop(index)
        # Get neighbor assignments
        neighbor_assignments = assignment[[index for (index, row) in neighbors.iterrows()]]
        # If one neighbor has a different assignment, then this precinct is on a border
        if len(set(neighbor_assignments)) > 1:
            # Add this to bordering neighbors with possible re-assignments
            bordering_precincts[index] = [] 
            for a in set(neighbor_assignments):
                if a!=assignment[index]:
                    bordering_precincts[index].append(a)
    i = 0
    while i < steps:
        # Randomly re-assign one of the precints to a neighboring district
        random_precinct = random.choice(list(bordering_precincts.keys())) 
        # Get neighbors of random precinct
        not_contiguous = False
        neighbors = units[~units.geometry.disjoint(units.iloc[random_precinct].geometry)].drop(random_precinct)
        for index, precinct in neighbors.iterrows():
            # For this node, get all disjoint neighbors
            dis = neighbors[neighbors.geometry.disjoint(precinct.geometry)]
            """
            If the current neighbor is the same color as the random precinct and some disjoint neighbor
            """
            for index2, node in dis.iterrows():
                if assignment[index2] == assignment[random_precinct] and assignment[index2] == assignment[index]:
                    not_contiguous = True
                    break
        if not_contiguous:
            print(i, random_precinct)
            print("NEW MAP IS NOT CONTIGUOUS")
            continue
        print(random_precinct)
        # Randomly choose of the possible assignments
        new_assignment = random.choice(bordering_precincts[random_precinct])
        new_assignments = deepcopy(assignment)
        assignment = new_assignments
        new_assignments[random_precinct] = new_assignment
        perms.append(new_assignments)
        # Check if any of the precincts neighbors are different from the current precinct's new assignment
        for index, precinct in neighbors.iterrows():
            if new_assignments[index] != new_assignment:
                # Add this to bordering neighbors with possible re-assignments
                if index not in bordering_precincts:
                    bordering_precincts[index] = [new_assignment] 
                else:
                    if new_assignment not in bordering_precincts[index]:
                        bordering_precincts[index].append(new_assignment)
        i+=1
    return perms





def getChain(json_path,district_plan_path, units_plan_path, election_label,dem_label, rep_label, assignment, steps = 10000 ):
    # Get assignment
    districts = geopandas.read_file(district_plan_path)
    units = geopandas.read_file(units_plan_path)
    # Convert each precinct name to precinct name_county
    for i in range(len(units.index)):
        units.at[i, "NAME"] = units.iloc[i]["NAME"] + "_" + units.iloc[i]["COUNTYFP"]
    units.to_crs(districts.crs, inplace=True)
    initial_assignment = maup.assign(units, districts)
    possible_assignments = permuteAssignments(initial_assignment, units, steps)
    chain = []
    for assignment in possible_assignments: 
        units_copy = units.copy()
        units_copy["DISTRICT"] = assignment
        # Get graph
        graph = Graph.from_json(json_path)
        graph.join(units_copy, columns = ["DISTRICT"], left_index = "NAME", right_index = "NAME")
        election = Election(election_label, {"Dem": dem_label, "Rep": rep_label})
        partition = Partition(
            graph,
            "DISTRICT",
            updaters={
                "cut_edges": cut_edges,
                election_label: election
            }
        )
        chain.append(partition)
    return chain, units

def getChain2(json_path,district_plan_path, units_plan_path, election_label,dem_label, rep_label, assignment, steps = 10000 ):
    # Get assignment
    districts = geopandas.read_file(district_plan_path)
    units = geopandas.read_file(units_plan_path)
    # Convert each precinct name to precinct name_county
    for i in range(len(units.index)):
        units.at[i, "NAME"] = units.iloc[i]["NAME"] + "_" + units.iloc[i]["COUNTYFP"]
    units.to_crs(districts.crs, inplace=True)
    initial_assignment = maup.assign(units, districts)
    units["DISTRICT"] = initial_assignment 
    # Get graph
    graph = Graph.from_json(json_path)
    graph.join(units, columns = ["DISTRICT"], left_index = "NAME", right_index = "NAME")
    election = Election(election_label, {"Dem": dem_label, "Rep": rep_label})
    partition = Partition(
        graph,
        "DISTRICT",
        updaters={
            "cut_edges": cut_edges,
            election_label: election
        }
    )
    return markovChain(partition, steps= steps), units

def markovChain(partition, steps = 1000):
 return MarkovChain(
    proposal=propose_random_flip,
    constraints=[],
    accept=always_accept,
    initial_state=partition,
    total_steps=steps
)

import time
if __name__ == "__main__":
    begin = time.time()
    chain, units = getChain2("../FormattedData/Illinois2016GE.json", "../Shapefiles/il_cong_adopted_2021.zip","../Shapefiles/il_2016.zip",  "PRES16", "G16PREDCLI", "G16PRERTRU", "COUNTYFP", steps = 1)
    end = time.time()
    print("Took {:.3f} seconds to get the chain".format(end-begin))
    print("MAPS GENERATED:", len(chain))
    # Box plot to determine percent democratic vote for each step in the chain
    d_percents = [partition["PRES16"].percents("Dem") for partition in chain]
    data = pandas.DataFrame(d_percents)
    ax = data.boxplot(positions=range(len(data.columns)))
    plt.plot(data.iloc[0], "ro")
    plt.title("Democratic Vote %'s for {} Illinois Districting Plans".format(STEPS))
    plt.xlabel("District #")
    plt.ylabel("Vote %'s")
    plt.savefig("boxplot.png")
    plt.clf()
    # Save images of different maps for gif
    i = 0
    for p in chain:
        if i%10 == 0:
            p.plot(units, cmap="tab20", legend=True)
            plt.savefig("tmp/{}.png".format(i))
            plt.clf()
        i+=1
    
