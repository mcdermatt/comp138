from __future__ import print_function, division
from sympy import symbols, simplify, trigsimp, Abs, Heaviside, Function, DiracDelta, Dummy, lambdify, Eq, E
from sympy.physics.mechanics import dynamicsymbols, ReferenceFrame, Point, inertia, RigidBody, KanesMethod
from sympy.physics.vector import init_vprinting, vlatex
from IPython.display import Image
from sympy.printing.pretty.pretty import pretty_print
from numpy import deg2rad, rad2deg, array, zeros, linspace, e
from scipy.integrate import odeint
from pydy.codegen.ode_function_generators import generate_ode_function
import matplotlib.pyplot as plt
from pydy.viz.shapes import Cylinder, Sphere
import pydy.viz
from pydy.viz.visualization_frame import VisualizationFrame
from pydy.viz.scene import Scene
import cloudpickle
from sympy import integrate
import os
import inspect
from scipy.integrate import solve_ivp
from sympy.functions.elementary.complexes import sign

#this file is used to generate a serialized function that can be used to estimate
# next states given current states

init_vprinting(use_latex='mathjax', pretty_print=True)

#Kinematics ------------------------------
#init reference frames, assume base attached to floor
inertial_frame = ReferenceFrame('I')
j0_frame = ReferenceFrame('J0')
j1_frame = ReferenceFrame('J1')

#declare dynamic symbols for the three joints
theta0, theta1 = dynamicsymbols('theta0, theta1')

#orient frames
j0_frame.orient(inertial_frame,'Axis',(theta0, inertial_frame.y))
j1_frame.orient(j0_frame,'Axis',(theta1, j0_frame.z))


#TODO figure out better name for joint points
#init joints
joint0 = Point('j0')
j0_length = symbols('l_j0')
joint1 = Point('j1')
joint1.set_pos(joint0, j0_length*j0_frame.y)
j1_length = symbols('l_j1')

#COM locations
j0_com_length, j1_com_length, j2_com_length = symbols('d_j0, d_j1, d_j2')
j0_mass_center = Point('j0_o')
j0_mass_center.set_pos(joint0, j0_com_length * j0_frame.y)
j1_mass_center = Point('j1_o')
j1_mass_center.set_pos(joint1, j1_com_length * j1_frame.y)

#kinematic differential equations
#init var for generalized speeds (aka angular velocities)
omega0, omega1 = dynamicsymbols('omega0, omega1')
kinematical_differential_equations = [omega0 - theta0.diff(),
                                    omega1 - theta1.diff()]

j0_frame.set_ang_vel(inertial_frame,omega0*j0_frame.y)
j1_frame.set_ang_vel(j0_frame,omega1*j0_frame.z)

#set base link fixed to ground plane
joint0.set_vel(inertial_frame,0)
#get linear velocities of each point
j0_mass_center.v2pt_theory(joint0, inertial_frame, j0_frame)
joint1.v2pt_theory(joint0, inertial_frame, j0_frame)
j1_mass_center.v2pt_theory(joint1, inertial_frame, j1_frame)

print("finished Kinematics")

#Inertia---------------------------------------------------------------
j0_mass, j1_mass = symbols('m_j0, m_j1')
j0_inertia, j1_inertia = symbols('I_j0, I_j1')

#inertia values taken from CAD model (same as simscape multibody) [kg*m^2]
#<joint>.inertia(frame, ixx, iyy, izz, ixy = _, iyz= _, izx = _)
j0_inertia_dyadic = inertia(j0_frame, 0.012, 0.01, 0.0114, ixy = 0.00007, iyz = -0.00002, izx = -0.0002)
j0_central_inertia = (j0_inertia_dyadic, j0_mass_center)

j1_inertia_dyadic = inertia(j1_frame, 0.016, 0.008, 0.0125, ixy = 0.0016, iyz = -0.0012, izx = 0.0011)
j1_central_inertia = (j1_inertia_dyadic, j1_mass_center)

#fully define rigid bodies
link0 = RigidBody('Link 0', j0_mass_center, j0_frame, j0_mass, j0_central_inertia)
link1 = RigidBody('Link 1', j1_mass_center, j1_frame, j1_mass, j1_central_inertia)

print("finished Inertia")

#Kinetics---------------------------------------------------------------
g = symbols('g')

#exert forces at a point
j0_grav_force = (j0_mass_center, -j0_mass * g * inertial_frame.y)
# j0_grav_force = (j0_mass_center, 0*inertial_frame.y) #perp to dir of grav
j1_grav_force = (j1_mass_center, -j1_mass * g * inertial_frame.y)
# j1_grav_force = (j1_mass_center, 0*inertial_frame.y)

#joint torques
j0_torque, j1_torque, j2_torque = dynamicsymbols('T_j0, T_j1, T_j2')
# l0_torque = (j0_frame, j0_torque * inertial_frame.y + j1_torque * inertial_frame.y)
l0_torque = (j0_frame, j0_torque * j0_frame.y + j1_torque * j0_frame.y) #debug
l1_torque = (j1_frame, j1_torque * j1_frame.z)

print("finished Kinetics")

#FRICTION---------------------------------------------------------------

j0_fs, j1_fs, j0_fk, j1_fk, j0_damp, j1_damp,= symbols('j0_fs, j1_fs, j0_fk, j1_fk, j0_damp, j1_damp')
j2_f = symbols('j2_f', cls = Function)

#Abs and sign function do not work with both symbolic and numerical integration
# sign(omega) = (-1 + (2/(1+(e**(-10000*(omega))))))
# diracDelata(omega) = (1 - (1/(1+(100*e**(-10000*(omega1**2))))))
#j0_friction = 

j0_friction = (j0_frame, -((1/(1+(100*e**(-10000*(omega0**2)))))*(-1 + (2/(1+(e**(-10000*(omega0))))))*j0_fk + (1 - (1/(1+(100*e**(-10000*(omega0**2))))))*(-1 + (2/(1+(e**(-10000*(omega0))))))*j0_fs + (omega0 * j0_damp)) * j0_frame.y)
j1_friction = (j1_frame, -((1/(1+(100*e**(-10000*(omega1**2)))))*(-1 + (2/(1+(e**(-10000*(omega1))))))*j1_fk + (1 - (1/(1+(100*e**(-10000*(omega1**2))))))*(-1 + (2/(1+(e**(-10000*(omega1))))))*j1_fs + (omega1 * j1_damp)) * j1_frame.z) 


print(j0_friction)

#Equations of Motion----------------------------------------------------
coordinates = [theta0, theta1]
speeds = [omega0, omega1]

kane = KanesMethod(inertial_frame, coordinates, speeds, kinematical_differential_equations)
# print(kane.kindiffdict()) #shows what variabels are related through differentiation

loads = [j0_grav_force, 
		 j1_grav_force, 
		 j0_friction,
		 j1_friction,
		 l0_torque,
		 l1_torque]
bodies = [link0, link1]

#fr + frstar = 0
#M(q,t)u˙=f(q,q˙,u,t)
fr, frstar = kane.kanes_equations(bodies,loads)
print("finished KanesMethod")

mass_matrix = kane.mass_matrix_full
print("finished mass_matrix")
#pretty_print(mass_matrix)
#forcing_vector = trigsimp(kane.forcing_full)
forcing_vector = kane.forcing_full
# pretty_print(forcing_vector)
# print(forcing_vector)
print("finished forcing_vector")

print("finished Equations of Motion")

#Simulation -----------------------------------------------------------
constants = [j0_length,
			 j0_com_length,
			 j0_mass,
			 j0_inertia,
			 j1_length,
			 j1_com_length,
			 j1_mass,
			 j1_inertia,
			 g,
			 j0_fs,
			 j1_fs,
			 j0_fk,
			 j1_fk,
			 j0_damp,
			 j1_damp]
specified = [j0_torque, j1_torque]

#CHECK OUT DIFFERENT GENERATOR CLASSES- MIGHT BE ABLE TO GET ONE TO WORK WITH DiracDelta
right_hand_side = generate_ode_function(forcing_vector, coordinates,
                                        speeds, constants,
                                        mass_matrix=mass_matrix,
                                        specifieds=specified)
                                        # generator='theano')

EOM_file = "full_EOM_func_COMBINED_FRICTION_MODEL.txt"
cloudpickle.dump(right_hand_side,open(EOM_file, 'wb'))

print("generated right_hand_side")

#right_hand_side is a FUNCTION
#initial values for system
x0 = zeros(4)
#initial pos
# x0[0] = deg2rad(30)
x0[1] = deg2rad(30)

#initial vel
# x0[3] = deg2rad(180)
# x0[4] = deg2rad(-90)
#x0[5] = 0

numerical_constants = array([0.05,  # j0_length [m]
                             0.01,  # j0_com_length [m]
                             4.20,  # ( ͡° ͜ʖ ͡°)  j0_mass [kg] 
                             0.001,  # NOT USED j0_inertia [kg*m^2]
                             0.164,  # j1_length [m]
                             0.08,  # j1_com_length [m]
                             1.81,  # j1_mass [kg]
                             0.001,  # NOT USED j1_inertia [kg*m^2]
                             9.81, # acceleration due to gravity [m/s^2]
                             0.1, # static friction coeffs #OK
                             0.1,							#OK  
                             0.125, #kinetic friction coeffs  #OK
                             0.125, 							#OK
                             0.025, #viscous damping coeffs 	#OK
                             0.025], 							#OK
                            ) 

#set joint torques to zero for first simulation
numerical_specified = zeros(2)
args = {'constants': numerical_constants,
        'specified': numerical_specified}
frames_per_sec = 60
final_time = 3
t = linspace(0.0, final_time, final_time * frames_per_sec)
#create variable to store trajectories of states as func of time
y = odeint(right_hand_side, x0, t, args=(numerical_specified, numerical_constants))

#visualization ----------------------------------------------------------------
#draw spheres at each joint
j0_shape = Sphere(color='black',radius = 0.025)
j1_shape = Sphere(color='black',radius = 0.025)

#create VisualizationFrame - attaches a shape to a reference frame and a point
j0_viz_frame = VisualizationFrame(inertial_frame, joint0, j0_shape)
j1_viz_frame = VisualizationFrame(inertial_frame, joint1, j1_shape)

#make cylindrical links to connect joints
j0_center = Point('j0_c')
j1_center = Point('j1_c')
j0_center.set_pos(joint0, j0_length / 2 * j0_frame.y)
j1_center.set_pos(joint1, j1_length / 2 * j1_frame.y)

constants_dict = dict(zip(constants, numerical_constants))

l0_shape = Cylinder(radius=0.01, length=constants_dict[j0_length], color = 'blue')
l0_viz_frame = VisualizationFrame('Link 0', j0_frame, j0_center, l0_shape)

l1_shape = Cylinder(radius=0.01, length=constants_dict[j1_length], color = 'blue')
l1_viz_frame = VisualizationFrame('Link 1', j1_frame, j1_center, l1_shape)

scene = Scene(inertial_frame,joint0)
#make list of frames we want in scene
scene.visualization_frames = [j0_viz_frame,
							  j1_viz_frame,
							  l0_viz_frame,
							  l1_viz_frame]
scene.states_symbols = coordinates + speeds
scene.constants = constants_dict
scene.states_trajectories = y
scene.display()