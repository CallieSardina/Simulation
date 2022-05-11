import math
from re import S
import matplotlib.pyplot as plt
import Message
import Node
import numpy as np
import queue
import random
import yaml

with open("./tests.yaml", 'r') as file:
    settings = yaml.full_load(file)

    numTrials = settings['numTrials']
    numNodes = settings['numNodes']
    numFaultyNodes = settings['numFaultyNodes']
    crashProbability = settings['crashProbability']
    randomSeed = settings['randomSeed']

    random.seed(randomSeed)

    channel = [] 

    # "network channel"
    def setChannel():
        channel.clear()
        for i in range(numNodes * numNodes):
            channel.append(queue.Queue(0))

    # returns True if message should be dropped
    def drop(dropProbability):
        return random.random() < dropProbability

    # returns True if node should crash this round
    def crash(crashProbability):
        return random.random() < crashProbability

    # creates nodes according to initializations for SmallAC
    def initializeSmallAC(n):
        nodes = []
        for i in range(n):
            x_i = random.random()
            nodes.append(Node.Node(i, x_i, x_i, x_i, 0, np.zeros(n)))
        for node in nodes:
            node.R[node.i] = 1
        return nodes

    # initialized the matrix of individual communication link probabilities for in- and out-gtroups
    def initialize2DArray(inGroup, outGroup, n):
        matrix = [[] for i in range(n)]
        for i in range(100):
            for j in range(100):
                if(i <= 33 and j <= 33):
                    matrix[i].append(inGroup)
                else:
                    if(33 < i <= 66 and 33 < j <= 66):
                        matrix[i].append(inGroup)
                    else:
                        if(66 < i <= 99 and 66 < j <= 99):
                            matrix[i].append(inGroup)
                        else:
                            matrix[i].append(outGroup)
        return matrix

    # calculate p_end according to Equation 2
    def calcPEnd(e):
        return math.log(e, 0.5)

    # broadcast message from node (adding it to queue)
    def broadcast(node, crashedNodes, probabilityMatrix, n):
        if(node not in crashedNodes):
            message = Message.Message(node.i, node.v, node.p)
            for offset in range(n):
                index = (node.i * n) + offset
                channel[index].put((message, probabilityMatrix[node.i][offset]))
        else:
            message = Message.Message(node.i, node.v, -1)
            for offset in range(n):
                index = (node.i * n) + offset
                channel[index].put((message, probabilityMatrix[node.i][offset]))

    # reset metod for SmallAC
    def reset(node, n):
        node.R[node.i] = 1
        for j in range(n):
            if(not(j == node.i)):
                node.R[j] = 0
        node.v_min = node.v
        node.v_max = node.v

    # store method for SmallAC
    def store(v_j, node):
        if(v_j < node.v):
            node.v_min = v_j
        else:
            if(v_j > node.v_max):
                node.v_max = v_j

    # Algorithm SamllAC 
    def smallAC(node, M, n, f, p_end):
        for m_j in M:
            #jump to future phase
            if(m_j.p > node.p):
                node.v = m_j.v
                node.p = m_j.p
                reset(node, n)
            else:
                if(m_j.p == node.p and node.R[m_j.i] == 0):
                    node.R[m_j.i] = 1
                    store(m_j.v, node)
                    # go to next phase
                    magR = 0
                    for r in range(len(node.R)):
                        if(node.R[r] == 1):
                            magR += 1
                    if(magR >= n - f):
                        node.v= 0.5 * (node.v_min + node.v_max)
                        node.p += 1
                        reset(node, n)
                    if(node.p == p_end):
                        return 1

    def runVaryingProbabilities(nodes, crashedNodes, round, rounds, p_end, n, f):
        for node in nodes:
            if(node not in crashedNodes):
                messages = []
                for q in range(node.i, (n - 1) * n + node.i + 1, n):
                    messageTuple = channel[q].get()
                    message = messageTuple[0]
                    if(not(drop(messageTuple[1]))):
                        messages.append(message)
                    out = smallAC(node, messages, n, f, p_end)
                    if(out == 1):
                        if(rounds[node.i] == -1):
                            rounds[node.i] = round

    def runConstantProbabilities(dropProbability, nodes, crashedNodes, round, rounds, p_end, n, f):
        for node in nodes: 
            if(node not in crashedNodes):
                messages = []
                for q in range(node.i, (n - 1) * n + node.i + 1, n):
                    message = channel[q].get()[0]
                    if(not(drop(dropProbability))):
                        messages.append(message)
                out = smallAC(node, messages, n, f, p_end)
                if(out == 1):
                    if(rounds[node.i] == -1):
                        rounds[node.i] = round

    # simulation structure
    def simulation(n, dropProbability, f):
        setChannel()

        # initialize simulation settings
        complete = False
        round = 1
        nodes = initializeSmallAC(n)
        probabilityMatrix = initialize2DArray(0.1, 0.5, n)
        epsilon = 0.001
        p_end = int(calcPEnd(epsilon)) + 1

        # for output data - the rounds it took node i to reach p_end is stores in rounds[i]
        rounds = [-1 for i in range(n)]
        
        # decide which nodes will crash and in what/ some round
        # f nodes will crash, as specified by function call
        nodesToCrash = random.sample(nodes, f)
        crashedNodes = []


        # loop to send/ receive messages from every node 
        while(not(complete)):
            # broadcast <i, v_i, p_i> to all
            for node in nodesToCrash:
                if(node not in crashedNodes and crash(crashProbability)):
                    crashedNodes.append(node)

            for node in nodes:
                broadcast(node, crashedNodes, probabilityMatrix, n)

            if(dropProbability == -1):
                runVaryingProbabilities(nodes, crashedNodes, round, rounds, p_end, n, f)
            else:
                runConstantProbabilities(dropProbability, nodes, crashedNodes, round, rounds, p_end, n, f)     

            for i in range(n):
                if(rounds[i] == -1 and nodes[i] not in crashedNodes):
                    complete = False
                    break
                else:
                    complete = True
            if(complete):
                if(checkEAgreement(nodes, crashedNodes, epsilon)):
                    #print("Epsilon-agreement is satisfied.")
                    return rounds
            else:
                round += 1      

    # logic to check that epsilon-agreement is satisfied 
    # -- all fault-free nodes outputs are within epsilon of each other
    def checkEAgreement(nodes, crashedNodes, epsilon):
        eAgree = False
        for node_i in nodes:
            if(not(node_i in crashedNodes)):
                for node_j in nodes:
                    if(not(node_j in crashedNodes)):
                        if(not(abs(node_i.v - node_j.v) <= epsilon)):
                            eAgree = False
                            break
                        else:
                            eAgree = True
        return eAgree

    def getNumCrashes(outputs):
        crashedCount = 0
        for i in range(len(outputs)):
            if(outputs[i] == -1):
                crashedCount +=1
        print("NODES CRASHED: ", crashedCount)
         
    # FOR TESTING -- run simulation 
    # any outputs equal to -1 represent crashed nodes  
    #outputs = simulation(100, -1, 10)
    #for i in range(len(outputs)):
    #    print("Node ", i, "made it to p_end at round: ", outputs[i])
    #getNumCrashes(outputs)

    # constructs box plot, given number of trials and results, for task1
    def makeBoxplot_smallAC(resultsDict):
        fig = plt.figure()
        plt.rcParams['figure.figsize'] = (3, 2)
        ax = fig.add_subplot(111)
        boxplotData = resultsDict.values()
        ax.boxplot(boxplotData)
        ax.set_ylim(bottom = 0)
        ax.set_xticklabels(resultsDict.keys())
        ax.set_xlabel("Message Loss Rate")
        ax.set_ylabel("Number of Rounds")
        filename = "smallAC-test" + str(numNodes) + "-" + str(numFaultyNodes) + "-" + str(crashProbability) + ".pdf"
        plt.savefig(filename,bbox_inches='tight',pad_inches = 0)
        plt.show()

    # runs simulation and creates boxplot
    # runs each loss rate (10%, 20%, 30%, 40%, 50%, 60%) 10 times, outputing result data to task1.txt
    def run_task_smallAC():
        resultsDict = {}
        final_round10 = []
        final_round20 = []
        final_round30 = []
        final_round40 = []
        final_round50 = []
        final_round60 = []
        final_round_1050= []
        for i in range(numTrials):
            sim10 = simulation(numNodes, 0.1, numFaultyNodes)
            final_round10.append(max(sim10))
            getNumCrashes(sim10)
            sim20 = simulation(numNodes, 0.2, numFaultyNodes)
            final_round20.append(max(sim20))
            getNumCrashes(sim20)
            sim30 = simulation(numNodes, 0.3, numFaultyNodes)
            final_round30.append(max(sim30))
            getNumCrashes(sim30)
            sim40 = simulation(numNodes, 0.4, numFaultyNodes)
            final_round40.append(max(sim40))
            getNumCrashes(sim40)
            sim50 = simulation(numNodes, 0.5, numFaultyNodes)
            final_round50.append(max(sim50))
            getNumCrashes(sim50)
            sim60 = simulation(numNodes, 0.6, numFaultyNodes)
            final_round60.append(max(sim60))
            getNumCrashes(sim60)
            sim1050 = simulation(numNodes, -1, numFaultyNodes)
            final_round_1050.append(max(sim1050))
            getNumCrashes(sim60)
        resultsDict.update({0.1 : final_round10})
        resultsDict.update({0.2 : final_round20})
        resultsDict.update({0.3 : final_round30})
        resultsDict.update({0.4 : final_round40})
        resultsDict.update({0.5 : final_round50})
        resultsDict.update({0.6 : final_round60})
        resultsDict.update({"0.1, 0.5" : final_round_1050})

        filename = "smallAC-test" + str(numNodes) + "-" + str(numFaultyNodes) + "-" + str(crashProbability) + ".txt"
        file = open(filename, "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_smallAC(resultsDict)

    run_task_smallAC()
