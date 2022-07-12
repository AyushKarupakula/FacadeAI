import gym
from gym import spaces
import numpy as np
from data_acquisition.fetch_data import fetch_weather_data, load_config
from revit_integration.revit_integration import RevitIntegration
from simulation.physics_simulation import PhysicsSimulator, run_physics_simulation, check_physical_constraints

class FacadeEnv(gym.Env):
    def __init__(self):
        super(FacadeEnv, self).__init__()
        
        self.config = load_config()
        self.revit_integration = None  # Will be set by MainController
        self.physics_simulator = PhysicsSimulator(mass=10, spring_constant=100, damping_coefficient=5)
        
        # Define action and observation space
        self.action_space = spaces.Box(low=0, high=1, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32)
        
        self.current_state = None
        self.current_energy_use = None
        self.current_comfort_score = None
        self.step_count = 0
        self.max_steps = 24  # 24 hours in a day

    def reset(self):
        self.step_count = 0
        self.current_state = self._get_observation()
        self.current_energy_use = None
        self.current_comfort_score = None
        return self.current_state

    def step(self, action):
        self.step_count += 1
        
        # Apply the action (façade adjustments)
        facade_state = self._apply_action(action)
        
        # Run physics simulation
        wind_force = self._calculate_wind_force()
        simulated_panels = run_physics_simulation(facade_state, wind_force)
        
        # Check physical constraints
        if not check_physical_constraints(simulated_panels, max_rotation_speed=30, max_depth_change_speed=0.2):
            # If constraints are violated, penalize the agent
            reward = -1000
            new_state = self.current_state
        else:
            # Get the new state and calculate reward
            new_state = self._get_observation(simulated_panels)
            reward = self._calculate_reward(new_state)
        
        # Check if episode is done
        done = self.step_count >= self.max_steps
        
        self.current_state = new_state
        
        return new_state, reward, done, {}

    def _get_observation(self, simulated_panels=None):
        weather_data = fetch_weather_data(self.config['openweathermap_api_key'], self.config['city'])
        
        weather_obs = np.array([
            weather_data['main']['temp'],
            weather_data['main']['humidity'],
            weather_data['wind']['speed'],
            weather_data['wind']['deg'],
            weather_data['clouds']['all'],
            self._get_weather_condition_encoding(weather_data['weather'][0]['main'])
        ], dtype=np.float32)
        
        if simulated_panels:
            facade_obs = np.array([
                np.mean([panel['rotation'] for panel in simulated_panels]),
                np.mean([panel['depth'] for panel in simulated_panels]),
                len(simulated_panels)
            ], dtype=np.float32)
        else:
            facade_obs = np.zeros(3, dtype=np.float32)
        
        return np.concatenate([weather_obs, facade_obs])

    def _get_weather_condition_encoding(self, condition):
        weather_mapping = {'Clear': 0, 'Clouds': 1, 'Rain': 2, 'Snow': 3}
        return weather_mapping.get(condition, 0)

    def _apply_action(self, action):
        # Convert action to façade adjustments
        panel_count = int(10 + action[0] * 10)  # Range: 10-20 panels
        rotation_angle = action[1] * 90  # Range: 0-90 degrees
        panel_depth = 0.1 + action[2] * 0.4  # Range: 0.1-0.5 meters
        
        facade_state = [
            {'time': self.step_count, 'rotation': rotation_angle, 'depth': panel_depth}
            for _ in range(panel_count)
        ]
        
        return facade_state

    def _calculate_wind_force(self):
        weather_data = fetch_weather_data(self.config['openweathermap_api_key'], self.config['city'])
        wind_speed = weather_data['wind']['speed']
        return 0.5 * 1.225 * (wind_speed ** 2)  # Simple wind force calculation

    def _calculate_reward(self, state):
        # Run energy simulation
        facade_geometry = self._create_facade_geometry(state)
        self.revit_integration.import_facade_model(facade_geometry)
        energy_model = self.revit_integration.setup_energy_model()
        simulation_results = self.revit_integration.run_energy_simulation(energy_model)
        self.revit_integration.analyze_results(simulation_results)
        
        new_energy_use = simulation_results['annual_energy_use']
        new_comfort_score = self._calculate_comfort_score(state, simulation_results)
        
        if self.current_energy_use is None or self.current_comfort_score is None:
            energy_reward = 0
            comfort_reward = 0
        else:
            # Energy reward is the negative change in energy use (we want to minimize energy use)
            energy_reward = self.current_energy_use - new_energy_use
            
            # Comfort reward is the positive change in comfort score (we want to maximize comfort)
            comfort_reward = new_comfort_score - self.current_comfort_score
        
        self.current_energy_use = new_energy_use
        self.current_comfort_score = new_comfort_score
        
        # Combine energy and comfort rewards (you can adjust the weights)
        total_reward = 0.7 * energy_reward + 0.3 * comfort_reward
        
        return total_reward

    def _calculate_comfort_score(self, state, simulation_results):
        # This is a simplified comfort score calculation
        # In a real implementation, you would use more sophisticated thermal comfort models
        
        indoor_temp = simulation_results.get('indoor_temperature', 22)  # Assume 22°C if not provided
        indoor_humidity = simulation_results.get('indoor_humidity', 50)  # Assume 50% if not provided
        
        # Ideal comfort ranges
        ideal_temp_range = (20, 26)
        ideal_humidity_range = (30, 60)
        
        # Calculate temperature comfort (0 to 1)
        if ideal_temp_range[0] <= indoor_temp <= ideal_temp_range[1]:
            temp_comfort = 1
        else:
            temp_comfort = 1 - min(abs(indoor_temp - ideal_temp_range[0]), abs(indoor_temp - ideal_temp_range[1])) / 10
        
        # Calculate humidity comfort (0 to 1)
        if ideal_humidity_range[0] <= indoor_humidity <= ideal_humidity_range[1]:
            humidity_comfort = 1
        else:
            humidity_comfort = 1 - min(abs(indoor_humidity - ideal_humidity_range[0]), abs(indoor_humidity - ideal_humidity_range[1])) / 50
        
        # Combine temperature and humidity comfort (you can adjust the weights)
        comfort_score = 0.6 * temp_comfort + 0.4 * humidity_comfort
        
        return comfort_score

    def _create_facade_geometry(self, state):
        # Extract facade parameters from state
        rotation = state[6]
        depth = state[7]
        panel_count = int(state[8])
        
        # This is a placeholder for creating façade geometry
        # In a real implementation, you would create actual Revit geometry here
        return [{'panel_id': i, 'rotation': rotation, 'depth': depth} for i in range(panel_count)]
