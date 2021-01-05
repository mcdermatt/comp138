import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim
import collections
import random

device = torch.device("cuda:0")
# device = torch.device("cpu")

class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, action_size, buffer_size, batch_size):
        """Initialize a ReplayBuffer object.
        Params
        ======
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
        """
        # print(device)
        self.action_size = action_size
        self.memory = collections.deque(maxlen=buffer_size)  # internal memory (deque)
        self.batch_size = batch_size
        self.experience = collections.namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
    
    def add(self, e):
        """Add a new set of experiences to memory."""

        #e = (state, action, reward, next_state,next_next_state,.... done)
        # self.memory.append(e) #was this

        #need to add together now since we are getting data in chunks
        self.memory += e
    
    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(np.vstack([e.state for e in experiences if e is not None])).float().to(device)
        actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).float().to(device)
        rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
        next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(device)
        dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)

        return states, actions, rewards, next_states, dones

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)