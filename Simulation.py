import matplotlib.pyplot as plt
import numpy as np
import queue
import random

queue = queue.Queue(0)

# retruns True if message should be dropped
def drop(dropProbability):
    return random.random() < dropProbability

# simulation structure
def simulation(dropProbability):
    # num nodes
    n = 100 

    # initialize simulation settings
    complete = False
    round = 1
    nodeList = [[] for i in range(n)]
    
    # loop to send/ receive messages from every node
    while(not(complete)):
        # message would be the message from the node, for now it is an int value
        message = 1
        for node in range(n):
            # send message
            queue.put(message)
            message += 1
        for i in range(n):
            # receive message
            received = queue.get()
            for j in range(n):
                # for each node, drop message with certain probability
                if(not(drop(dropProbability))):
                    if(received not in nodeList[j]):
                        nodeList[j].append(received)   

        # update loop condition, wchecking if all nodes have received all messages
        for i in range(n):
            if(len(nodeList[i]) != n):
                complete = False
                break
            else:
                complete = True
        if(complete):
            return round
        else:
            round += 1  

# constructs box plot, given number of trials and results
def makeBoxplot(resultsDict):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    boxplotData = resultsDict.values()
    ax.boxplot(boxplotData)
    ax.set_xticklabels(resultsDict.keys())
    ax.set_xlabel("Message Loss Rate")
    ax.set_ylabel("Number of Rounds")
    plt.show()

# runs simulation and creates boxpot
def run():
    trials = 500
    resultsDict = {}
    results1 = []
    results2 = []
    results3 = []
    for i in range(trials):
        results1.append(simulation(0.1))
        results2.append(simulation(0.2))
        results3.append(simulation(0.3))
    resultsDict.update({0.1 : results1})
    resultsDict.update({0.2 : results2})
    resultsDict.update({0.3 : results3})
    makeBoxplot(resultsDict)

# run program
run()




