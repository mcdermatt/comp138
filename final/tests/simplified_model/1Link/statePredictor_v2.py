import cloudpickle
from numpy import zeros, array, linspace, deg2rad, arange
from scipy.integrate import odeint
import time
import torch

class statePredictor:

	

	# def __init__(self,numerical_constants = numerical_constants, numerical_specified = numerical_specified, args = args, rhs = rhs, x0 = x0):
	def __init__(self):
		
		numerical_constants = array([
				 0.164,  # j1_length [m]
				 0.08,  # j1_com_length [m]
				 1.81,  # j1_mass [kg]
				 0.001,  # NOT USED j1_inertia [kg*m^2]
				 9.81, # acceleration due to gravity [m/s^2]
				 0.1, # static friction coeffs  
				 0.125, #kinetic friction coeffs
				 0.05] #viscous damping coeffs 
				) 
		numerical_specified = zeros(1)
		x0 = torch.zeros(2)
		args = {'constants': numerical_constants,
				'specified': numerical_specified}
		rhs = cloudpickle.load(open("full_EOM_func_COMBINED_FRICTION_MODEL.txt", 'rb'))


		self.numerical_constants = numerical_constants
		self.numerical_specified = numerical_specified
		self.args = args
		self.rhs = rhs
		self.dt = 0.02
		self.numPts = 150
		self.x0 = x0

	# def predict(self):
	# 	numerical_constants = self.numerical_constants
	# 	numerical_specified = self.numerical_specified
	# 	x0 = self.x0
	# 	rhs = self.rhs
	# 	dt = self.dt
	# 	# frames_per_sec = 100
	# 	# final_time = 1
	# 	# t = linspace(0.0, final_time, final_time * frames_per_sec)
	# 	t = linspace(0.0,dt,5)

	# 	#predicted trajectroy given no external forces
	# 	y = odeint(rhs, x0, t, args=(numerical_specified, numerical_constants))

	# 	return(y)

	def predict(self):
		"""IMPORTANT- WE ARE NOT DOING NUMERICAL INTEGRATION HERE: 
			SIMULATING ONLY ONE TIMESTEP 3 SECONDS AWAY WILL BE 100% ACCURATE
				"""
		t = linspace(0.0,self.dt,self.numPts)
		# t = self.dt*arange(self.numPts)
		# print(dt)
		#if x0 is tensor, make it array so it can be read by odeint
		try:
			self.x0 = self.x0.cpu().detach().numpy()
		except:
			pass
		# print(type(self.x0))
		#predicted trajectory given no external forces
		y = odeint(self.rhs, self.x0, t, args=(self.numerical_specified, self.numerical_constants))

		return(y)