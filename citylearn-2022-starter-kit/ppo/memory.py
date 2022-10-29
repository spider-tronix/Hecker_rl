# This code will contain all the replay buffer and memory needed to sample trjectory(on-policy/off-policy)
import random
import numpy as np
from collections import namedtuple, deque

Transition_PPO = namedtuple('Transition', ('state', 'next_state', 'action', 'reward', 'done'))
class PPO_Memory(object):
    def __init__(self,capacity):
        """
        Replay buffer for PPO
        INPUT  : state,next_state,action,reward and done
        OUTPUT : batch of off-polocy experience
        """
        self.memory = deque(maxlen=capacity)
        self.capacity = capacity

    def push(self, state, next_state, action, reward, done):
        self.memory.append(Transition_PPO(state, next_state, action, reward, done))

    def sample(self, batch_size):
        transitions = random.sample(self.memory, batch_size)
        batch = Transition_PPO(*zip(*transitions))
        return batch

    def __len__(self):
        return len(self.memory)
    
