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

    random.seed(randomSeed)

    # "network channel"
    queue = queue.Queue(0)

    # returns True if message should be dropped
    def drop(dropProbability):
        return random.random() < dropProbability

    # returns True if node should crash this round
    def crash(crashProbability):
        return random.random() < crashProbability

    # calculate p_end according to Equation 2
    def calcPEnd(e):
        return math.log(e, 0.5)

    # when x is in phase p, x will broadcast  its state from phase 0 to phase p 
    # in every round of phase p 
    def broadcast(messageSet):
        queue.put(messageSet)

    # for every message in the queue, node i will receive the message, 
    # or drop it according to the specified probability
    # the receiver node will only take what it needs, for the purpose of simulation
    def receive(node, messages, dropProbability):
        received = []
        for messageSet in messages:
            if(not(drop(dropProbability))):
                for message in messageSet:
                    if(node.p == message.p):
                        received.append(message)
        return received

    # creates nodes according to initialozations for Algorithm AC
    def initializeAC(n, p_end):
        nodes = []
        for i in range(n):
            x_i = random.random()
            nodes.append(NodeAC.NodeAC(i, x_i, 0, [[] for i in range(p_end + 1)]))
        return nodes

    # Algorithm AC
    def algAC(node, p_end, M, n, f):
        #print("RUNNING AC ON NODE: ", node.i)
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
        print("node: ", node.i, "LEN R: ", len(node.R[node.p]))
        #for m in node.R[node.p]:
        #    print("node.R[node.p]: ", m.i, m.p)
        if(len(node.R[node.p]) >= n - f):
            states = []
            for state in node.R[node.p]:
                states.append(state.v)
            node.p += 1
            print("NODE ", node.i, "UPDATED PHASE TO: ", node.p)
            node.v = 0.5 * (max(states) + min(states))
        if(node.p == p_end):
            return 1
        #return -1
        

    # simulation structure
    def simulation(n, dropProbability, f):

        # initialize simulation settings
        complete = False
        round = 1
        epsilon = 0.001
        p_end = int(calcPEnd(epsilon)) + 1
        nodes = initializeAC(n, p_end)

        # for output data - the rounds it took node i to reach p_end is stores in rounds[i]
        rounds = [-1 for i in range(n)]
        
        # decide which nodes will crash and in what/ some round
        # f nodes will crash, as specified by function call
        nodesToCrash = random.sample(nodes, f)
        #crashProbability  = 0.01
        crashedNodes = []

        # loop to send/ receive messages from every node 
        while(not(complete)):
        #for i in range(5):
            print("")
            # broadcast <i, v_i, p_i> to all
            for node in nodesToCrash:
                if node not in crashedNodes and crash(crashProbability):
                    crashedNodes.append(node)

            for node in nodes:
                messageSet = []
                if(node not in crashedNodes):
                    if(node.p == 0):
                        messageSet.append(Message.Message(node.i, node.v, node.p))
                        #for m in messageSet:
                        #    print("NODE ", node.i, "SEDNING MESSAGE ", m.p)
                        broadcast(messageSet)
                    else:
                        for i in range(0, node.p + 1):
                            messageSet.append(Message.Message(node.i, node.v, i))
                        #for m in messageSet:
                        #    print("NODE ", node.i, "SEDNING MESSAGE ", m.p)
                        broadcast(messageSet)
                #else:
                #    messageSet.append(Message.Message(node.i, 0, -1))
                #    broadcast(messageSet)

            # M <-- messages received in round r
            messages = [None for i in range(queue.qsize())]
            for i in range(queue.qsize()):
                messages[i] = queue.get()
            M = [[] for i in range(n)]
            for node in nodes:
                if(node not in crashedNodes):
                    M[node.i] = receive(node, messages, dropProbability)
                #print("RECEIVEING AT  NODE: ", node.i)
                #for m in M[node.i]:
                #    print("M[i]: ", m.i, m.p)                

            # logic for running Algorithm AC
            for node in nodes:
                if(node not in crashedNodes and rounds[node.i] == -1):
                    out = algAC(node, p_end, M[node.i], n, f)
                    if(out == 1):
                        if(rounds[node.i] == -1):
                            rounds[node.i] = round

            for i in range(n):
                if(rounds[i] == -1 and not(nodes[i] in nodesToCrash)):
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

    # run simulation 
    # any outputs equal to -1 represent crashed nodes  
    outputs = simulation(100, 0.6, 49)
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

        file = open("algACSimulation_test.txt", "w")
        file.write(str(resultsDict))
        file.close()

        makeBoxplot_algAC(resultsDict)

    #run_task_algAC()



