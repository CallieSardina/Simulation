import math
import matplotlib.pyplot as plt
import Message
import Node
import numpy as np
import queue
import random

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
def receive(node, messages, dropProbability, n):
    received = []
    for message in messages:
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
    return -1



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
    crashProbability  = 0.3

    # loop to send/ receive messages from every node 
    while(not(complete)):
        # broadcast <i, v_i, p_i> to all
        for i in range(n):
            if(not(nodes[i] in nodesToCrash and crash(crashProbability))):
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
            if(not(nodes[i] in nodesToCrash and crash(crashProbability))):
                M[i] = receive(nodes[i], messages, dropProbability, n)

        # logic for running SmallAC
        for i in range(n):
            if(not(nodes[i] in nodesToCrash and crash(crashProbability))):
                out = smallAC(nodes[i], M[i], n, f, p_end)
                if(out == 1):
                    if(rounds[i] == -1):
                        rounds[i] = round 

        for i in range(n):
            if(rounds[i] == -1 and not(nodes[i] in nodesToCrash)):
                complete = False
                break
            else:
                complete = True
        if(complete):
            if(checkEAgreement(nodes, nodesToCrash, epsilon)):
                print("Epsilon-agreement is satisfied.")
            return rounds
        else:
            round += 1      

# logic to check that epsilon-agreement is satisfied 
# -- all fault-free nodes outputs are within epsilon of each other
def checkEAgreement(nodes, nodesToCrash, epsilon):
    eAgree = False
    for node_i in nodes:
        if(not(node_i in nodesToCrash)):
            for node_j in nodes:
                if(not(node_j in nodesToCrash)):
                    if(not(abs(node_i.v - node_j.v) <= epsilon)):
                        eAgree = False
                        break
                    else:
                        eAgree = True
    return eAgree
           
# run simulation 
# any outputs equal to -1 represent crashed nodes  
outputs = simulation(10, 0.3, 2)
for i in range(len(outputs)):
    print("Node ", i, "made it to p_end at round: ", outputs[i])




