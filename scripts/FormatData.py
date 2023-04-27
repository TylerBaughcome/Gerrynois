import pandas
import json
import glob
import geopandas

CONTESTS = ["PRESIDENT AND VICE PRESIDENT", "UNITED STATES SENATOR"]

def jsonify_csv(filename):
    ret = {}
    county_df = pandas.read_csv(filename)
    county_df = pandas.concat([county_df[county_df["ContestName"] == CONTESTS[0]], county_df[county_df["ContestName"] == CONTESTS[1]]])
    county_df = county_df.dropna()
    for _, row in county_df.iterrows():
        if row["PrecinctName"] not in ret:
            ret[row["PrecinctName"]] = {"County": row["JurisName"], "CountyID": row["JurisdictionID"], row["ContestName"] +"_"+ row["PartyName"]: row["VoteCount"]}
        else:
            ret[row["PrecinctName"]][row["ContestName"] + "_"+row["PartyName"]] = row["VoteCount"]
    # Turn ret into a list
    d = []
    for i in ret:
        tmp = ret[i]
        tmp["Precinct"] = i
        d.append(tmp)
    return d

def jsonify_shapefile(path):
    df = geopandas.read_file(path)
    # Assuming each column is a separate VTD from Illinois
    ret = []
    adj = []
    for index, row in df.iterrows():
        d = {"STATEFP": 17, "NAME": row["NAME"] + "_" + row["COUNTYFP"], "COUNTYFP": int(row["COUNTYFP"]), "id": index}
        for column in df.columns:
            if column not in ["COUNTYFP", "geometry", "NAME"]:
                d[column] = row[column]
        ret.append(d)
        # Get neighbors to add to adjacency
        neighbors = df[~df.geometry.disjoint(row.geometry)].drop(index)
        adj.append([{"shared_perim": 1, "id": ind} for ind, _ in neighbors.iterrows()])
        print(index)
    return {"directed": False, "multigraph": False, "graph": [], "nodes": ret, "adjacency": adj}

if __name__ == "__main__":
    ret = jsonify_shapefile("../Shapefiles/il_2016.zip") 
    json.dump(ret, open("../FormattedData/Illinois2016GE.json","w"))
