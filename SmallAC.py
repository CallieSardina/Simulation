import math
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

    # "network channel"
    queue = queue.Queue(0)

    def initializeDropProb(num10, num20, num30, num40, num50, num60):
        num10 = num10
        num20 = num20
        num30 = num30
        num40 = num40
        num50 = num50
        num60 = num60

        dropProbabilities = {}
        count = 0
        for i in range (num10):
            dropProbabilities.update({i : 0.1})
        count += num10
        for i in range (count, count + num20):
            dropProbabilities.update({i : 0.2})
        count += num20
        for i in range (count, count + num30):
            dropProbabilities.update({i : 0.3})
        count += num30
        for i in range (count, count + num40):
            dropProbabilities.update({i : 0.4})
        count += num40
        for i in range (count, count + num50):
            dropProbabilities.update({i : 0.5})
        count += num50
        for i in range (count, count + num60):
            dropProbabilities.update({i : 0.6})
        return dropProbabilities

    dropProbabilities0 = initializeDropProb(17, 17, 17, 17, 16, 16)
    dropProbabilities1 = initializeDropProb(100, 0, 0, 0, 0, 0)
    dropProbabilities2 = initializeDropProb(0, 100, 0, 0, 0, 0)
    dropProbabilities3 = initializeDropProb(0, 0, 100, 0, 0, 0)
    dropProbabilities4 = initializeDropProb(0, 0, 0, 100, 0, 0)
    dropProbabilities5 = initializeDropProb(0, 0, 0, 0, 100, 0)
    dropProbabilities6 = initializeDropProb(0, 0, 0, 0, 0, 100)
    
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

    # calculate p_end according to Equation 2
    def calcPEnd(e):
        return math.log(e, 0.5)

    # broadcast message from node (adding it to queue)
    def broadcast(message):
        queue.put(message)

    # for every message in the queue, node i will receive the message, 
    # or drop it according to the specified probability
    def receive(messages, dropProbabilities):
        received = []
        for message in messages:
            dropProbability = dropProbabilities.get(message.i)
            if(not(drop(dropProbability))):
                received.append(message)
        return received

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

    # simulation structure
    def simulation(n, dropProbabilities, f):

        # initialize simulation settings
        complete = False
        round = 1
        nodes = initializeSmallAC(n)
        epsilon = 0.001
        p_end = int(calcPEnd(epsilon)) + 1

        # for output data - the rounds it took node i to reach p_end is stores in rounds[i]
        rounds = [-1 for i in range(n)]
        
        # decide which nodes will crash and in what/ some round
        # f nodes will crash, as specified by function call
        nodesToCrash = random.sample(nodes, f)
        #crashProbability  = 0.1
        crashedNodes = []

        # loop to send/ receive messages from every node 
        while(not(complete)):
            # broadcast <i, v_i, p_i> to all
            for node in nodesToCrash:
                if node not in crashedNodes and crash(crashProbability):
                    crashedNodes.append(node)

            for i in range(n):
                if(nodes[i] not in crashedNodes):
                    message = Message.Message(nodes[i].i, nodes[i].v, nodes[i].p)
                    broadcast(message)
                else:
                    message = Message.Message(nodes[i].i, 0, -1)
                    broadcast(message)

            # M <-- messages received in round r
            messages = [None for i in range(n)]
            for i in range(n):
                messages[i] = queue.get()
            M = [[] for i in range(n)]
            for i in range(n):
                if(nodes[i] not in crashedNodes):
                    M[i] = receive(messages, dropProbabilities)

            # logic for running SmallAC
            for i in range(n):
                if(nodes[i] not in crashedNodes):
                    out = smallAC(nodes[i], M[i], n, f, p_end)
                    if(out == 1):
                        if(rounds[i] == -1):
                            rounds[i] = round 

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
            
    # FOR TESTING -- run simulation 
    # any outputs equal to -1 represent crashed nodes  
    #outputs = simulation(100, dropProbabilities, 49)
    #for i in range(len(outputs)):
    #    print("Node ", i, "made it to p_end at round: ", outputs[i])

    def getNumCrashes(outputs):
        crashedCount = 0
        for i in range(len(outputs)):
            if(outputs[i] == -1):
                crashedCount +=1
        print("NODES CRASHED: ", crashedCount)

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
        final_round_varying = []
        for i in range(numTrials):
            sim10 = simulation(numNodes, dropProbabilities1, numFaultyNodes)
            final_round10.append(max(sim10))
            getNumCrashes(sim10)
            sim20 = simulation(numNodes, dropProbabilities2, numFaultyNodes)
            final_round20.append(max(sim20))
            getNumCrashes(sim20)
            sim30 = simulation(numNodes, dropProbabilities3, numFaultyNodes)
            final_round30.append(max(sim30))
            getNumCrashes(sim30)
            sim40 = simulation(numNodes, dropProbabilities4, numFaultyNodes)
            final_round40.append(max(sim40))
            getNumCrashes(sim40)
            sim50 = simulation(numNodes, dropProbabilities5, numFaultyNodes)
            final_round50.append(max(sim50))
            getNumCrashes(sim50)
            sim60 = simulation(numNodes, dropProbabilities6, numFaultyNodes)
            final_round60.append(max(sim60))
            getNumCrashes(sim60)
            simVarying = simulation(numNodes, dropProbabilities0, numFaultyNodes)
            final_round_varying.append(max(simVarying))
            getNumCrashes(simVarying)
        resultsDict.update({0.1 : final_round10})
        resultsDict.update({0.2 : final_round20})
        resultsDict.update({0.3 : final_round30})
        resultsDict.update({0.4 : final_round40})
        resultsDict.update({0.5 : final_round50})
        resultsDict.update({0.6 : final_round60})
        resultsDict.update({"Varying" : final_round_varying})

        filename = "smallAC-test" + str(numNodes) + "-" + str(numFaultyNodes) + "-" + str(crashProbability) + ".txt"
        file = open(filename, "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_smallAC(resultsDict)

    run_task_smallAC()

