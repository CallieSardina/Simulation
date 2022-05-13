import initialize2DArray
import math
import matplotlib.pyplot as plt
import Message
import NodeAC
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
    strategy = settings['strategy']
    inGroup = settings['inGroup']
    outGroup = settings['outGroup']

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

    # calculate p_end according to Equation 2
    def calcPEnd(e):
        return math.log(e, 0.5)

    # broadcasts message from node i to all nodes j
    # used in strategy 1 and strategy 2
    def broadcast(node, probabilityMatrix, n):
        messageSet = []
        if(node.p == 0):
            messageSet.append(Message.Message(node.i, node.v, node.p))
        else:
            for i in range(0, node.p + 1):
                messageSet.append(Message.Message(node.i, node.v, i))
        for offset in range(n):
            index = (node.i * n) + offset
            channel[index].put((messageSet, probabilityMatrix[node.i][offset]))

    # broadcasts message from node i to all nodes j, with byzantine behavior according to strategy 1
    def broadcast1_byzantine(node, probabilityMatrix, n):
        messageSet = []
        if(node.p == 0):
            messageSet.append(Message.Message(node.i, random.random(), node.p))
        else:
            v = random.random()
            for i in range(0, node.p + 1):
                messageSet.append(Message.Message(node.i, v, i))
        for offset in range(n):
            index = (node.i * n) + offset
            channel[index].put((messageSet, probabilityMatrix[node.i][offset]))


    # creates nodes according to initialozations for Algorithm BAC
    def initializeBAC(n):
        nodes = []
        for i in range(n):
            x_i = random.random()
            nodes.append(NodeAC.NodeAC(i, x_i, 0, [[] for i in range(n + 1)]))
        return nodes


    # Algorithm BAC
    def algBAC(node, p_end, M, n, f):
        for m in M: 
            if(m.p == node.p):
                if(len(node.R[node.p]) > 0):
                    contains = False
                    for message in node.R[node.p]:
                        if(message.i == m.i and message.p == m.p):
                            contains = True
                    if(not(contains)):
                        node.R[node.p].append(m)
                else:
                    node.R[node.p].append(m)
            if(len(node.R[node.p]) >= n - f):
                states = []
                for state in node.R[node.p]:
                    states.append(state.v)
                node.p += 1
                ascending = sorted(states)
                descending = sorted(states, reverse = True)
                node.v = 0.5 * (ascending[f + 1] + descending[f + 1])
            if(node.p == p_end):
                return 1

    # receives messages at each node, and runs AlgBAC
    # part of byzantine stretegy 1
    def simulation_byzantine1(nodes, crashedNodes, probabilityMatrix, round, rounds, p_end, n, f):
        for node in nodes:
            if node not in crashedNodes:
                broadcast(node, probabilityMatrix, n)
            else:
                broadcast1_byzantine(node, probabilityMatrix, n)
        messages = [[] for i in range(n)]
        for node in nodes:
            for q in range(node.i, (n - 1) * n + node.i + 1, n):
                messageTuple = channel[q].get()
                messageSet = messageTuple[0]
                if(round % 2 == 1):
                    if(not(drop(messageTuple[1]))):
                        for message in messageSet:
                            if(message.p == -1):
                                break
                            messages[node.i].append(message)
                else:
                    for message in messageSet:
                        if(message.p == -1):
                            break
                        messages[node.i].append(message)

        for node in nodes: 
            if(node not in crashedNodes):
                out = algBAC(node, p_end, messages[node.i], n, f)
                if(out == 1):
                    if(rounds[node.i] == -1):
                        rounds[node.i] = round 

    # receives messages at each node, and runs AlgBAC
    # at each node, if it is 
    # part of byzantine stretegy 2
    def simulation_byzantine2(nodes, crashedNodes, probabilityMatrix, round, rounds, p_end, n, f):
        for node in nodes:
            broadcast(node, probabilityMatrix, n)
        messages = [[] for i in range(n)]
        for node in nodes:
            for q in range(node.i, (n - 1) * n + node.i + 1, n):
                messageTuple = channel[q].get()
                messageSet = messageTuple[0]
                for message in messageSet:
                    if(message.i == node.i and nodes[node.i] in crashedNodes):
                        if(node.v > message.v):
                            message.v = 1
                        if(node.v < message.v):
                            message.v = 0
                if(round % 2 == 1):
                    if(not(drop(messageTuple[1]))):
                        for message in messageSet:
                            if(message.p == -1):
                                break
                            messages[node.i].append(message)
                else:
                    for message in messageSet:
                        if(message.p == -1):
                            break
                        messages[node.i].append(message)                    
        for node in nodes:
            if(node not in crashedNodes):
                out = algBAC(node, p_end, messages[node.i], n, f)
                if(out == 1):
                    if(rounds[node.i] == -1):
                        rounds[node.i] = round

    # simulation structure
    def simulation(n, f, strategy, inGroup, outGroup, percent_in):
        setChannel()

        # initialize simulation settings
        complete = False
        round = 1
        epsilon = 0.001
        p_end = int(calcPEnd(epsilon)) + 1
        nodes = initializeBAC(n)
        probabilityMatrix = initialize2DArray.initialize2DArray_2groups(inGroup, outGroup, n, percent_in)

        # for output data - the rounds it took node i to reach p_end is stores in rounds[i]
        rounds = [-1 for i in range(n)]
        
        # decide which nodes will crash and in what/ some round
        # f nodes will crash, as specified by function call
        nodesToCrash = random.sample(nodes, f)
        crashedNodes = []

        # loop to send/ receive messages from every node 
        while(not(complete)):
            setChannel()
            for node in nodesToCrash:
                if node not in crashedNodes and crash(crashProbability):
                    crashedNodes.append(node)

            if(strategy == 1):
                simulation_byzantine1(nodes, crashedNodes, probabilityMatrix, round, rounds, p_end, n, f)
            else:
                simulation_byzantine2(nodes, crashedNodes, probabilityMatrix, round, rounds, p_end, n, f)

            for i in range(n):
                if(rounds[i] == -1 and not(nodes[i] in crashedNodes)):
                    complete = False
                    break
                else:
                    complete = True
            if(complete):
                if(checkEAgreement(nodes, crashedNodes, epsilon)):
                    #print("Epsilon-agreement is satisfied.")
                    return rounds
                else:
                    print("ERROR: Epsilon-agreement is not satisfied")
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

    # FOR TESTING PURPOSES -- run simulation 
    # any outputs equal to -1 represent crashed nodes  
    #outputs = simulation(60, 0.4, 11, 2)
    #for i in range(len(outputs)):
    #    print("Node ", i, "made it to p_end at round: ", outputs[i])

    # constructs box plot, given number of trials and results, for task1
    def makeBoxplot_algAC(resultsDict):
        fig = plt.figure()
        plt.rcParams['figure.figsize'] = (3, 2)
        ax = fig.add_subplot(111)
        boxplotData = resultsDict.values()
        ax.boxplot(boxplotData)
        ax.set_ylim(bottom = 0)
        ax.set_xticklabels(resultsDict.keys())
        ax.set_xlabel("Message Loss Rate")
        ax.set_ylabel("Number of Rounds")
        filename = "algBAC-test-inout-" + str(numNodes) + "-" + str(numFaultyNodes) + "-" + str(crashProbability) + "-" + str(strategy) + ".pdf"
        plt.savefig(filename, bbox_inches='tight',pad_inches = 0)
        plt.show()

    # runs simulation and creates boxplot
    # runs each loss rate (10%, 20%, 30%, 40%, 50%, 60%) 10 times, outputing result data to task1.txt
    def run_task_algBAC():
        resultsDict = {}
        final_round10 = []
        final_round20 = []
        final_round30 = []
        final_round40 = []
        final_round50 = []
        #final_round60 = []
        #final_round_1050 = []
        for i in range(numTrials):
            sim10 = simulation(numNodes, numFaultyNodes, strategy, inGroup, outGroup, 0.95)
            final_round10.append(max(sim10))
            getNumCrashes(sim10)
            sim20 = simulation(numNodes, numFaultyNodes, strategy, inGroup, outGroup, 0.9)
            final_round20.append(max(sim20))
            getNumCrashes(sim20)
            sim30 = simulation(numNodes, numFaultyNodes, strategy, inGroup, outGroup, 0.85)
            final_round30.append(max(sim30))
            getNumCrashes(sim30)
            sim40 = simulation(numNodes, numFaultyNodes, strategy, inGroup, outGroup, 0.8)
            final_round40.append(max(sim40))
            getNumCrashes(sim40)
            sim50 = simulation(numNodes, numFaultyNodes, strategy, inGroup, outGroup, 0.75)
            final_round50.append(max(sim50))
            getNumCrashes(sim50)
            #sim60 = simulation(numNodes, 0.6, numFaultyNodes, strategy)
            #final_round60.append(max(sim60))
            #getNumCrashes(sim60)
            #sim1050 = simulation(numNodes, -1, numFaultyNodes, strategy)
            #final_round_1050.append(max(sim1050))
        resultsDict.update({"95&5" : final_round10})
        resultsDict.update({"90&10" : final_round20})
        resultsDict.update({"85&15" : final_round30})
        resultsDict.update({"80&20" : final_round40})
        resultsDict.update({"75&25": final_round50})
        #resultsDict.update({0.6 : final_round60})
        #resultsDict.update({"0.1, 0.5" : final_round_1050})

        filename = "AlgBAC-test-inout-" + str(numNodes) + "-" + str(numFaultyNodes) + "-" + str(crashProbability) + "-" + str(strategy) + ".txt"
        file = open(filename, "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_algAC(resultsDict)

    run_task_algBAC()



