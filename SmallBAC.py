import math
import matplotlib.pyplot as plt
import Message
import NodeSmallBAC
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

    random.seed(randomSeed)

    # "network channel"
    queue = queue.Queue(0)

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
            nodes.append(NodeSmallBAC.NodeSmallBAC(i, x_i, 0, np.zeros(n), [], []))
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
    def receive(node, messages, dropProbability, n):
        received = []
        for message in messages:
            if(not(drop(dropProbability))):
                received.append(message)
        return received

    # reset metod for SmallBAC
    def reset(node, n):
        for j in range(n):
            if(not(j == node.i)):
                node.R[j] = 0
        node.R_low = []
        node.R_high = []

    # store method for SmallBAC
    def store(v_j, node, f):
        if(len(node.R_low) <= f + 1):
            node.R_low.append(v_j)
        else:
            if(v_j < max(node.R_low)):
                maxVal = max(node.R_low)
                index = node.R_low.index(maxVal)
                node.R_low[index] = v_j
        if(len(node.R_high) <= f + 1):
            node.R_high.append(v_j)
        else:
            if(v_j > min(node.R_high)):
                minVal = min(node.R_low)
                index = node.R_low.index(minVal)
                node.R_high[index] = v_j


    # Algorithm SamllBAC 
    def smallBAC(node, M, n, f, p_end):
        #print("RUNNING SMALL_BAC ON NODE ", node.i)
        for m_j in M:
            if(m_j.p >= node.p and node.R[m_j.i] == 0):
                node.R[m_j.i] = 1
                store(m_j.v, node, f)
            magR = 0
            for r in range(len(node.R)):
                if(node.R[r] == 1):
                    magR += 1
            if(magR >= n - f):
                node.v= 0.5 * (max(node.R_low) + min(node.R_high))
                node.p += 1
                reset(node, n)
        if(node.p == p_end):
            return 1
        #return -1

    # simulation structure
    def simulation(n, dropProbability, f):

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
        #for i in range(5):
            # broadcast <i, v_i, p_i> to all
            for node in nodesToCrash:
                if node not in crashedNodes and crash(crashProbability):
                    crashedNodes.append(node)

            for i in range(n):
                if(nodes[i] not in crashedNodes):
                    message = Message.Message(nodes[i].i, nodes[i].v, nodes[i].p)
                    #print("NODE: ", nodes[i].i, "SENDING MESSAGE: ", message.i, message.p)
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
                    M[i] = receive(nodes[i], messages, dropProbability, n)
                #for m in M[nodes[i].i]:
                #    print("NODE ", nodes[i].i, "RECEIVED MESSAGE ", m.i, m.p)

            # logic for running SmallAC
            for i in range(n):
                if(nodes[i] not in crashedNodes):
                    out = smallBAC(nodes[i], M[i], n, f, p_end)
                    if(out == 1):
                        if(rounds[i] == -1):
                            #print("ROUND: ", round)
                            rounds[i] = round 

            for i in range(n):
                if(rounds[i] == -1 and nodes[i] not in crashedNodes):
                    complete = False
                    break
                else:
                    complete = True
            if(complete):
                if(checkEAgreement(nodes, crashedNodes, epsilon)):
                    print("Epsilon-agreement is satisfied.")
                    for node in nodes:
                        print("NODE: ", node.i, "STATE: ", node.v)
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
            
    # run simulation -- for quick testing
    # any outputs equal to -1 represent crashed nodes  
    #outputs = simulation(100, 0.4, 10)
    #for i in range(len(outputs)):
    #    print("Node ", i, "made it to p_end at round: ", outputs[i])

    # returns the number of nodes crashed 
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
        plt.savefig('smallBAC-test.pdf', bbox_inches='tight',pad_inches = 0)
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
        resultsDict.update({0.1 : final_round10})
        resultsDict.update({0.2 : final_round20})
        resultsDict.update({0.3 : final_round30})
        resultsDict.update({0.4 : final_round40})
        resultsDict.update({0.5 : final_round50})
        resultsDict.update({0.6 : final_round60})

        file = open("smallBACSimulation_test.txt", "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_smallAC(resultsDict)

    run_task_smallAC()

