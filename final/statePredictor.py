import cloudpickle
from numpy import zeros, array, linspace, deg2rad
from scipy.integrate import odeint
import time

class statePredictor():

	numerical_constants = array([0.05,  # j0_length [m]
			 0.01,  # j0_com_length [m]
			 4.20,  # ( ͡° ͜ʖ ͡°)  j0_mass [kg] 
			 0.001,  # NOT USED j0_inertia [kg*m^2]
			 0.164,  # j1_length [m]
			 0.08,  # j1_com_length [m]
			 1.81,  # j1_mass [kg]
			 0.001,  # NOT USED j1_inertia [kg*m^2]
			 0.158,  # j2_com_length [m]
			 2.259,  # j2_mass [kg]
			 0.001,  # NOT USED j2_inertia [kg*m^2]
			 9.81, # acceleration due to gravity [m/s^2]
			 1, # static friction coeffs
			 1,
			 1,  
			 0.5, #kinetic friction coeffs
			 0.5,
			 0.5,
			 0.025, #viscous damping coeffs
			 0.025,
			 0.025], 
			) 
	numerical_specified = zeros(3)
	x0 = zeros(6)
	args = {'constants': numerical_constants,
				'specified': numerical_specified}
	rhs = cloudpickle.load(open("full_EOM_func_COMBINED_FRICTION_MODEL.txt", 'rb'))

	# def __init__(self, g = 0.81):
	# 	self.rhs = rhs
	# 	self.numerical_constants = numerical_constants
	# 	self.numerical_specified = numerical_specified
	# 	self.x0 = x0
	# 	self.args = args

	def predict(self, numerical_constants = numerical_constants, numerical_specified = numerical_specified, x0 = x0, rhs = rhs, dt=1):
		# frames_per_sec = 100
		# final_time = 1
		# t = linspace(0.0, final_time, final_time * frames_per_sec)
		t = linspace(0.0,dt,2)

		#predicted trajectroy given no external forces
		y = odeint(rhs, x0, t, args=(numerical_specified, numerical_constants))

		return(y)