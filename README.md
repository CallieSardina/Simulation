# Simulation

## Overview

We are creating a simulation for testing AC, SmallAC, BAC, and SmallBAC algorithm performance over a synchronous, lossy network.
Thus far, I have set up a simulation for sending and receiving messages (via queue), simulating the loss by having a set probability that a message will be dropped.

### Functions 
#### simulation

- Sets the number of nodes that will be in the network
- Sets the probability that a given message will be dropped to emulate a lossy network
- Runs until every node has successfully received every message from all other nodes doing the following:

  - Send messages: add messages from all nodes to the queue (connection channel)
  - Receive messages: get message frm queue, and drop it in accordance with determined probability
  
  
#### makeBoxplot

- Constructs the boxplot based on the simulation data

#### run

- Sets number of trials you wish to run, storing the results in a list
- Passes resulst list to makeBoxplot to construct boxplot given the data

### Notes

- Right now, the messages are just integer values. I will later define a data structure used to represent messages sent across nodes.
  
