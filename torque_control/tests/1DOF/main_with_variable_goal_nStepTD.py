from statePredictor import statePredictor
import numpy as np
import torch
from torch.autograd import Variable
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
import time
# from agent import Agent
from agent_nStepTD import Agent
import collections

fidelity = 0.1 #0.1 # seconds per step
trials = 10000
doneThresh = 0.1 #stop trial of theta gets within this distance with low velocity
maxTrialLen = 50
action_scale = 3 #0.01 #3
save_progress = True
n = 3 #number of TD steps to take
discount_factor = 0.9

#init CUDA
if torch.cuda.is_available():
	device = torch.device("cuda:0")
	torch.set_default_tensor_type('torch.cuda.FloatTensor') 
	print("Running on GPU")
else:
	device = torch.device("cpu")
	torch.set_default_tensor_type('torch.FloatTensor')
	print("Running on the CPU")


sp = statePredictor()
sp.dt = fidelity
sp.numPts = 2

#EASY MODE 
sp.numerical_constants[5:] = 0 #disable friction
# sp.numerical_constants[4] = 0 #no gravity

#init arrays for tracking results
count = 0
rewardArr = np.zeros(1)

actor_loss = np.zeros(trials*maxTrialLen)
critic_loss = np.zeros(trials*maxTrialLen)
action_vec = np.zeros(trials*maxTrialLen)
tick = 0

agent = Agent(3,1) #pos, vel, goal_pos

for trial in range(trials):
	print("took ", tick, " ticks")
	print("trial ", trial, " -------------------------------------")
	#get initial states
	goal_pos = torch.randn(1)
	states = torch.randn(2)
	# states = torch.zeros(2)
	next_states = states

	SARS_of_current_trial = collections.deque()

	tick = 0
	done = 0
	while done != 1:

		states = next_states.float()
		states = states.to(device)

		#decide on action given states
		agent.actor.eval()
		with torch.no_grad():
			action = agent.actor(torch.cat((states,goal_pos), dim=0).unsqueeze(0))
		agent.actor.train() #unlocks actor

		# print("states = ",states, " action = ", action.cpu().detach().numpy()[0], " goal = ", goal_pos)
		
		sp.numerical_specified[0] = action.cpu().detach().numpy()[0]*action_scale
		sp.x0 = states

		# next_states = torch.as_tensor(sp.predict()[1])
		next_states = sp.predict()[1]
		next_states = torch.as_tensor(next_states)
		states = torch.as_tensor(states)
		reward = -(abs(states[0] - goal_pos)**2) #- 0.1*abs(states[1]) #test velocity
		reward = torch.as_tensor(reward)

		if tick == maxTrialLen:
			# reward -= 10 #punishment for not finihsing
			done = 1
		if (abs(sp.x0[0] - goal_pos)) < doneThresh and (abs(sp.x0[1]) < 0.1): #actual goal for 1dof -> go to this position and stop
		# if abs(sp.x0[0]) > goal_pos and abs(sp.x0[1]) < 0.1 : #simple goal -> get 2.5 rad away from 0 and stop moving
			done = 1
		done = torch.as_tensor(done)

		e = agent.memory.experience(torch.cat((states,goal_pos), dim=0).cpu().numpy(), action.cpu().numpy(), reward.cpu().numpy(), torch.cat((next_states,goal_pos), dim=0).cpu().numpy(), done.cpu().numpy())
		SARS_of_current_trial.append(e)
		e.append()

		#update rewards of past n trials
		# TODO while tick < n we need to only partially update
		if n > (tick+1):
			for i in range(1,n):
				a[tick-i].reward += a[tick].reward*discount_factor**(i)  


		tick += 1
		actor_loss[count] = agent.aLossOut #straight from critic
		critic_loss[count] = agent.cLossOut	
		count += 1	


	agent.step(SARS_of_current_trial)
		
	print("goal = ", goal_pos, " states = ",states, " action = ", action.cpu().detach().numpy()[0])
	
	rewardArr = np.append(rewardArr, reward.cpu().numpy())

	if trial % 10 == 0:
		if save_progress:
			agent.save_models()
			np.save("actor_loss",actor_loss)
			np.save("critic_loss",critic_loss)
			np.savetxt("rewards", rewardArr)
