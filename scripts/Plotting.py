import matplotlib.pyplot as plt

def boxPlot(df):
    ax = df.boxplot(positions=range(len(df.columns)))
    plt.plot(df.iloc[0], "ro")
    plt.show()