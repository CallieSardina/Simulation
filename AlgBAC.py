import math
import matplotlib.pyplot as plt
import Message
import NodeAC
import numpy as np
import queue
import random
import yaml

with open("/Users/calliesardina/TestAC/Simulation/tests.yaml", 'r') as file:
    settings = yaml.full_load(file)

    numTrials = settings['numTrials']
    numNodes = settings['numNodes']
    numFaultyNodes = settings['numFaultyNodes']
    crashProbability = settings['crashProbability']
    randomSeed = settings['randomSeed']
    strategy = settings['strategy']

    random.seed(randomSeed)

    # "network channel"
    channel = []
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
    def broadcast(node, n):
        message = Message.Message(node.i, node.v, node.p)
        for offset in range(n):
            index = (node.i * n) + offset
            channel[index].put(message)

    # broadcasts message from node i to all nodes j, with byzantine behavior according to strategy 1
    def broadcast1_byzantine(node, n):
        # Byzantine stradegy 1
        message = Message.Message(node.i, random.random(), node.p)
        for offset in range(n):
            index = (node.i * n) + offset
            channel[index].put(message)
    
    # broadcasts message from node i to all nodes j, with state equal to -2
    # when this is received, it signifies that this node is subject to byzantine behavior (strategy 2) 
    def broadcast2_byzantine(node, n):
        # for use in Byzantine stradegy 2
        message = Message.Message(node.i, -2, node.p)
        for offset in range(n):
            index = (node.i * n) + offset
            channel[index].put(message)

    # creates nodes according to initialozations for Algorithm BAC
    def initializeBAC(n, p_end):
        nodes = []
        for i in range(n):
            x_i = random.random()
            nodes.append(NodeAC.NodeAC(i, x_i, 0, [[] for i in range(p_end + 1)]))
        return nodes

    # Algorithm BAC
    def algBAC(node, p_end, M, n, f):
        for m in M: 
            if(m.p >= node.p):
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
            for state in node.R[node.p ]:
                states.append(state.v)
            node.p += 1
            ascending = sorted(states)
            descending = sorted(states, reverse = True)
            node.v = 0.5 * (ascending[f + 1] + descending[f + 1])
        if(node.p == p_end):
            return 1
        
    # receives messages at each node, and runs AlgBAC
    # part of byzantine stretegy 1
    def simulation_byzantine1(nodes, crashedNodes, dropProbability, round, rounds, p_end, n, f):
        for node in nodes:
            if node not in crashedNodes:
                broadcast(node, n)
            else:
                broadcast1_byzantine(node, n)
        for i in range(n):
            if(nodes[i] not in crashedNodes):
                messages = []
                for q in range(nodes[i].i, (n - 1) * n + nodes[i].i + 1, n):
                    message = channel[q].get()
                    if(not(drop(dropProbability))):
                        if(message.p == -1):
                            break
                        messages.append(message)
                out = algBAC(nodes[i], p_end, messages, n, f)
                if(out == 1):
                    if(rounds[i] == -1):
                        rounds[i] = round 

    # receives messages at each node, and runs AlgBAC
    # at each node, if it is 
    # part of byzantine stretegy 2
    def simulation_byzantine2(nodes, crashedNodes, dropProbability, round, rounds, p_end, n, f):
        for node in nodes:
            if node not in crashedNodes:
                broadcast(node, n)
            else:
                broadcast2_byzantine(node, n)
        for node in nodes:
            if node not in crashedNodes:
                messages = []
                for q in range(node.i, (n - 1) * n + node.i + 1, n):
                    message = channel[q].get()
                    if(message.v == -2):
                        if(node.p > message.p):
                            message.v = 1
                        if(node.p < message.p):
                            message.v = 0
                    if(not(drop(dropProbability))):
                        if(message.p == -1):
                            break
                        messages.append(message)
                out = algBAC(node, p_end, messages, n, f)
                if(out == 1):
                    if(rounds[node.i] == -1):
                        rounds[node.i] = round

    # simulation structure
    def simulation(n, dropProbability, f, strategy):

        # initialize simulation settings
        complete = False
        round = 1
        epsilon = 0.001
        p_end = int(calcPEnd(epsilon)) + 1
        nodes = initializeBAC(n, p_end)

        # for output data - the rounds it took node i to reach p_end is stores in rounds[i]
        rounds = [-1 for i in range(n)]
        
        # decide which nodes will crash and in what/ some round
        # f nodes will crash, as specified by function call
        nodesToCrash = random.sample(nodes, f)
        crashedNodes = []

        # loop to send/ receive messages from every node 
        while(not(complete)):

            for node in nodesToCrash:
                if node not in crashedNodes and crash(crashProbability):
                    crashedNodes.append(node)

            if(strategy == 1):
                simulation_byzantine1(nodes, crashedNodes, dropProbability, round, rounds, p_end, n, f)
            else:
                simulation_byzantine2(nodes, crashedNodes, dropProbability, round, rounds, p_end, n, f)

            for i in range(n):
                if(rounds[i] == -1 and not(nodes[i] in nodesToCrash)):
                    complete = False
                    break
                else:
                    complete = True
            if(complete):
                if(checkEAgreement(nodes, crashedNodes, epsilon)):
                    print("Epsilon-agreement is satisfied.")
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

    # run simulation 
    # any outputs equal to -1 represent crashed nodes  
    outputs = simulation(100, 0.1, 10, 2)
    for i in range(len(outputs)):
        print("Node ", i, "made it to p_end at round: ", outputs[i])
    #getNumCrashes(outputs)
    #final_round = max(outputs)
    #print("FINAL ROUND: ", final_round)


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
        plt.savefig('algAC-test.pdf', bbox_inches='tight',pad_inches = 0)
        plt.show()

    # runs simulation and creates boxplot
    # runs each loss rate (10%, 20%, 30%, 40%, 50%, 60%) 10 times, outputing result data to task1.txt
    def run_task_algAC():
        resultsDict = {}
        final_round10 = []
        final_round20 = []
        final_round30 = []
        final_round40 = []
        final_round50 = []
        final_round60 = []
        for i in range(numTrials):
            sim10 = simulation(numNodes, 0.1, numFaultyNodes, strategy)
            final_round10.append(max(sim10))
            getNumCrashes(sim10)
            sim20 = simulation(numNodes, 0.2, numFaultyNodes, strategy)
            final_round20.append(max(sim20))
            getNumCrashes(sim20)
            sim30 = simulation(numNodes, 0.3, numFaultyNodes, strategy)
            final_round30.append(max(sim30))
            getNumCrashes(sim30)
            sim40 = simulation(numNodes, 0.4, numFaultyNodes, strategy)
            final_round40.append(max(sim40))
            getNumCrashes(sim40)
            sim50 = simulation(numNodes, 0.5, numFaultyNodes, strategy)
            final_round50.append(max(sim50))
            getNumCrashes(sim50)
            sim60 = simulation(numNodes, 0.6, numFaultyNodes, strategy)
            final_round60.append(max(sim60))
            getNumCrashes(sim60)
        resultsDict.update({0.1 : final_round10})
        resultsDict.update({0.2 : final_round20})
        resultsDict.update({0.3 : final_round30})
        resultsDict.update({0.4 : final_round40})
        resultsDict.update({0.5 : final_round50})
        resultsDict.update({0.6 : final_round60})

        file = open("algACSimulation_test.txt", "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_algAC(resultsDict)

    #run_task_algAC()



