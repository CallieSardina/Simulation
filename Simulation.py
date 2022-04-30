import matplotlib.pyplot as plt
import numpy as np
import queue
import random

queue = queue.Queue(0)

# retruns True if message should be dropped
def drop(dropProbability):
    return random.random() < dropProbability

# simulation structure
def simulation(n, dropProbability):

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

# constructs box plot, given number of trials and results, for task1
def makeBoxplot_task1(resultsDict):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    boxplotData = resultsDict.values()
    ax.boxplot(boxplotData)
    ax.set_xticklabels(resultsDict.keys())
    ax.set_xlabel("Message Loss Rate")
    ax.set_ylabel("Number of Rounds")
    plt.show()

# constructs box plot for task2
def makeBoxplot_task2(resultsDict):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    boxplotData = resultsDict.values()
    ax.boxplot(boxplotData)
    ax.set_xticklabels(resultsDict.keys())
    ax.set_xlabel("Number of Nodes")
    ax.set_ylabel("Message Loss Rate")
    plt.show()

# runs simulation and creates boxplot
# runs each loss rate (10%, 20%, 30%, 40%, 50%, 60%) 10 times, outputing result data to task1.txt
def run_task1():
    trials = 50
    resultsDict = {}
    results1 = []
    results2 = []
    results3 = []
    results4 = []
    results5 = []
    results6 = []
    for i in range(trials):
        results1.append(simulation(100, 0.1))
        results2.append(simulation(100, 0.2))
        results3.append(simulation(100, 0.3))
        results4.append(simulation(100, 0.4))
        results5.append(simulation(100, 0.5))
        results6.append(simulation(100, 0.6))
    resultsDict.update({0.1 : results1})
    resultsDict.update({0.2 : results2})
    resultsDict.update({0.3 : results3})
    resultsDict.update({0.4 : results4})
    resultsDict.update({0.5 : results5})
    resultsDict.update({0.6 : results6})

    file = open("task1_new.txt", "w")
    file.write(str(resultsDict))
    file.close()

    makeBoxplot_task1(resultsDict)

# runs simulation and creates boxplot
# runs at loss rate 10% for 10 times when n = 50, 100, 150, 200, 250 and outputs result data to task2.txt
def run_task2():
    trials = 10
    resultsDict = {}
    results1 = []
    results2 = []
    results3 = []
    results4 = []
    results5 = []
    for i in range(trials):
        results1.append(simulation(50, .1))
        results2.append(simulation(100, .1))
        results3.append(simulation(150, .1))
        results4.append(simulation(200, .1))
        results5.append(simulation(250, .1))
    resultsDict.update({50 : results1})
    resultsDict.update({100 : results2})
    resultsDict.update({150 : results3})
    resultsDict.update({200 : results4})
    resultsDict.update({250 : results5})

    file = open("task2_new.txt", "w")
    file.write(str(resultsDict))
    file.close()

    makeBoxplot_task2(resultsDict)

# run program
run_task1()
run_task2()




