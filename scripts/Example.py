from gerrychain import Graph, Partition, Election
from gerrychain.updaters import Tally, cut_edges
from matplotlib import pyplot as plt
import pandas
from gerrychain import MarkovChain
from gerrychain.constraints import single_flip_contiguous
from gerrychain.proposals import propose_random_flip
from gerrychain.accept import always_accept


graph = Graph.from_json("../FormattedData/PA_VTDs.json")

election = Election("PRES16", {"Dem": "T16PRESD", "Rep": "T16PRESR"})

initial_partition = Partition(
    graph,
    assignment="CD_2011",
    updaters={
        "cut_edges": cut_edges,
        "population": Tally("TOTPOP", alias="population"),
        "PRES16": election
    }
)

chain = MarkovChain(
    proposal=propose_random_flip,
    constraints=[single_flip_contiguous],
    accept=always_accept,
    initial_state=initial_partition,
    total_steps=100000
)


d_percents = [sorted(partition["PRES16"].percents("Dem")) for partition in chain]
plt.title("% Democratic Vote For 100,000 Districting Maps")
plt.ylabel("% Democratic Vote")
plt.xlabel("District #")
data = pandas.DataFrame(d_percents) 
ax = data.boxplot(positions=range(len(data.columns)))
plt.plot(data.iloc[0], "ro")
plt.show()


