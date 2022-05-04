import math
import matplotlib.pyplot as plt
import Message
import NodeAC
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

# calculate p_end according to Equation 2
def calcPEnd(e):
    return math.log(e, 0.5)

# when x is in phase p, x will broadcast  its state from phase 0 to phase p 
# in every round of phase p 
def broadcast(message):
    queue.put(message)

# for every message in the queue, node i will receive the message, 
# or drop it according to the specified probability
# the receiver node will only take what it needs, for the purpose of simulation
def receive(node, messages, dropProbability, n):
    received = []
    for message in messages:
        if(not(drop(dropProbability)) and (node.p == message.p)):
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
    for i in range(len(M)): 
        if(M[i].p >= node.p):
            node.R[node.p].append(M[i].v)
    if(len(node.R[node.p]) >= n - f):
        states = []
        for state in node.R[node.p]:
            states.append(state)
        node.p += 1
        node.v = 0.5 * (max(states) + min(states))
        node.R[node.p].append(node.v)
    if(node.p == p_end):
        return 1
    return -1
    

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
    crashProbability  = 0.3

    # loop to send/ receive messages from every node 
    while(not(complete)):
        # broadcast <i, v_i, p_i> to all
        for node in nodes:
            if(not(node in nodesToCrash and crash(crashProbability))):
                if(node.p == 0):
                    message = Message.Message(node.i, node.v, node.p)
                    broadcast(message)
                else:
                    for i in range(0, node.p + 1):
                        message = Message.Message(node.i, node.v, i)
                        broadcast(message)
            else:
                message = Message.Message(node.i, 0, -1)
                broadcast(message)

        # M <-- messages received in round r
        messages = [None for i in range(queue.qsize())]
        for i in range(queue.qsize()):
            messages[i] = queue.get()
        M = [[] for i in range(n)]
        for node in nodes:
            if(not(node in nodesToCrash and crash(crashProbability))):
                M[node.i] = receive(node, messages, dropProbability, n)

        # logic for running Algorithm AC
        for node in nodes:
            if(not(node in nodesToCrash and crash(crashProbability)) and rounds[node.i] == -1):
                out = algAC(node, p_end, M[node.i], n, f)
                if(out == 1):
                    if(rounds[node.i == -1]):
                        rounds[node.i] = round

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
outputs = simulation(9, 0.2, 3)
for i in range(len(outputs)):
    print("Node ", i, "made it to p_end at round: ", outputs[i])




