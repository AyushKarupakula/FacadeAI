import gym
from gym import spaces
import numpy as np
from data_acquisition.fetch_data import fetch_weather_data, load_config
from revit_integration.revit_integration import RevitIntegration

class FacadeEnv(gym.Env):
    def __init__(self):
        super(FacadeEnv, self).__init__()
        
        self.config = load_config()
        self.revit_integration = None  # Will be set by MainController
        
        # Define action and observation space
        self.action_space = spaces.Box(low=0, high=1, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32)
        
        self.current_state = None
        self.current_energy_use = None
        self.step_count = 0
        self.max_steps = 24  # 24 hours in a day

    def reset(self):
        self.step_count = 0
        self.current_state = self._get_observation()
        return self.current_state

    def step(self, action):
        self.step_count += 1
        
        # Apply the action (façade adjustments)
        self._apply_action(action)
        
        # Get the new state
        new_state = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode is done
        done = self.step_count >= self.max_steps
        
        self.current_state = new_state
        
        return new_state, reward, done, {}

    def _get_observation(self):
        weather_data = fetch_weather_data(self.config['openweathermap_api_key'], self.config['city'])
        return np.array([
            weather_data['main']['temp'],
            weather_data['main']['humidity'],
            weather_data['wind']['speed'],
            weather_data['wind']['deg'],
            weather_data['clouds']['all'],
            self._get_weather_condition_encoding(weather_data['weather'][0]['main'])
        ], dtype=np.float32)

    def _get_weather_condition_encoding(self, condition):
        weather_mapping = {'Clear': 0, 'Clouds': 1, 'Rain': 2, 'Snow': 3}
        return weather_mapping.get(condition, 0)

    def _apply_action(self, action):
        # Convert action to façade adjustments
        panel_count = int(10 + action[0] * 10)  # Range: 10-20 panels
        rotation_angle = action[1] * 90  # Range: 0-90 degrees
        panel_depth = 0.1 + action[2] * 0.4  # Range: 0.1-0.5 meters
        
        # Update façade in Revit
        facade_geometry = self._create_facade_geometry(panel_count, rotation_angle, panel_depth)
        self.revit_integration.import_facade_model(facade_geometry)

    def _create_facade_geometry(self, panel_count, rotation_angle, panel_depth):
        # This is a placeholder for creating façade geometry
        # In a real implementation, you would create actual Revit geometry here
        return [{'panel_id': i, 'rotation': rotation_angle, 'depth': panel_depth} for i in range(panel_count)]

    def _calculate_reward(self):
        # Run energy simulation
        energy_model = self.revit_integration.setup_energy_model()
        simulation_results = self.revit_integration.run_energy_simulation(energy_model)
        self.revit_integration.analyze_results(simulation_results)
        
        new_energy_use = simulation_results['annual_energy_use']
        
        if self.current_energy_use is None:
            reward = 0
        else:
            # Reward is the negative change in energy use (we want to minimize energy use)
            reward = self.current_energy_use - new_energy_use
        
        self.current_energy_use = new_energy_use
        
        return reward
