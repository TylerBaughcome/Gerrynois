import geopandas
from matplotlib import pyplot as plt
import maup
from gerrychain import Graph, Partition, Election
from gerrychain.updaters import Tally, cut_edges
from gerrychain import MarkovChain
from gerrychain.constraints import single_flip_contiguous
from gerrychain.proposals import propose_random_flip
from gerrychain.accept import always_accept

def political_distribution_illinois(excluded_districts = []):

    districts = geopandas.read_file("../Shapefiles/il_cong_adopted_2021.zip")
    units = geopandas.read_file("../Shapefiles/il_2016.zip")
    units.to_crs(districts.crs, inplace=True)
    assignment = maup.assign(units, districts)
    units["DISTRICT"] = assignment
    units = units[~units["DISTRICT"].isin(excluded_districts)]
    dem = units["G16PREDCLI"].sum()
    rep = units["G16PRERTRU"].sum()
    other = units["G16PRELJOH"].sum() + units["G16PREGSTE"].sum() + units["G16PREOWRI"].sum()
    total = dem+rep + other
    return {"dem": dem/total, "rep": rep/total, "other": other/total}

if __name__ == "__main__":
    print(political_distribution_illinois())