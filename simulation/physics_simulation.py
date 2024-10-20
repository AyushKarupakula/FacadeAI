import numpy as np
from scipy.integrate import odeint

class PhysicsSimulator:
    def __init__(self, mass, spring_constant, damping_coefficient):
        self.mass = mass  # Mass of the façade panel
        self.k = spring_constant  # Spring constant
        self.c = damping_coefficient  # Damping coefficient

    def equation_of_motion(self, state, t, force):
        x, v = state
        dxdt = v
        dvdt = (force - self.k * x - self.c * v) / self.mass
        return [dxdt, dvdt]

    def simulate_panel_motion(self, initial_position, initial_velocity, force, time_span):
        initial_state = [initial_position, initial_velocity]
        t = np.linspace(0, time_span, num=1000)
        solution = odeint(self.equation_of_motion, initial_state, t, args=(force,))
        return t, solution

def check_physical_constraints(panels, max_rotation_speed, max_depth_change_speed):
    constraints_violated = False
    for i in range(1, len(panels)):
        rotation_change = abs(panels[i]['rotation'] - panels[i-1]['rotation'])
        depth_change = abs(panels[i]['depth'] - panels[i-1]['depth'])
        time_step = panels[i]['time'] - panels[i-1]['time']

        if rotation_change / time_step > max_rotation_speed:
            print(f"Warning: Rotation speed limit exceeded between panels {i-1} and {i}")
            constraints_violated = True

        if depth_change / time_step > max_depth_change_speed:
            print(f"Warning: Depth change speed limit exceeded between panels {i-1} and {i}")
            constraints_violated = True

    return not constraints_violated

def run_physics_simulation(panels, wind_force):
    simulator = PhysicsSimulator(mass=10, spring_constant=100, damping_coefficient=5)
    simulated_panels = []

    for panel in panels:
        t, solution = simulator.simulate_panel_motion(
            initial_position=panel['depth'],
            initial_velocity=0,
            force=wind_force,
            time_span=10  # Simulate for 10 seconds
        )
        
        final_position = solution[-1][0]
        final_velocity = solution[-1][1]
        
        simulated_panels.append({
            'time': panel['time'],
            'rotation': panel['rotation'],
            'depth': final_position,
            'velocity': final_velocity
        })

    return simulated_panels

if __name__ == "__main__":
    # Example usage
    panels = [
        {'time': 0, 'rotation': 0, 'depth': 0.1},
        {'time': 1, 'rotation': 15, 'depth': 0.2},
        {'time': 2, 'rotation': 30, 'depth': 0.3},
        {'time': 3, 'rotation': 45, 'depth': 0.4},
    ]

    wind_force = 50  # N

    simulated_panels = run_physics_simulation(panels, wind_force)
    
    if check_physical_constraints(simulated_panels, max_rotation_speed=30, max_depth_change_speed=0.2):
        print("Simulation completed successfully. All constraints satisfied.")
    else:
        print("Simulation completed. Some constraints were violated.")

    for panel in simulated_panels:
        print(f"Time: {panel['time']}, Rotation: {panel['rotation']}, Depth: {panel['depth']:.2f}, Velocity: {panel['velocity']:.2f}")
