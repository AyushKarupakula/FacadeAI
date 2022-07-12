import time
import threading
from data_acquisition.fetch_data import fetch_weather_data, load_config
from ai_control_system.facade_env import FacadeEnv
from ai_control_system.dqn_agent import DQNAgent
from models.components.facade_controller import FacadeController
from revit_integration.revit_integration import RevitIntegration
from visualization.visualization import FacadeVisualizer
import pandas as pd
import numpy as np

class MainController:
    def __init__(self):
        self.config = load_config()
        self.facade_controller = FacadeController()
        self.revit_integration = None  # Will be initialized with a Revit document
        self.visualizer = FacadeVisualizer()
        self.facade_data = []
        self.energy_data = []
        self.comfort_data = []
        
        # Initialize RL environment and agent
        self.env = FacadeEnv()
        self.agent = DQNAgent(state_size=self.env.observation_space.shape[0],
                              action_size=self.env.action_space.shape[0])
        self.agent.action_space = self.env.action_space  # Set the action space for the agent

    def run_simulation_cycle(self):
        state = self.env.reset()
        state = np.reshape(state, [1, self.env.observation_space.shape[0]])
        
        for time_step in range(self.env.max_steps):
            # Get action from DQN agent
            action = self.agent.act(state)
            
            # Take action in environment
            next_state, reward, done, _ = self.env.step(action)
            next_state = np.reshape(next_state, [1, self.env.observation_space.shape[0]])
            
            # Remember the previous state, action, reward, and done
            self.agent.remember(state, action, reward, next_state, done)
            
            # Make next_state the new current state for the next frame.
            state = next_state
            
            # Store facade, energy, and comfort data
            self.store_facade_data(self.env.current_state, action)
            self.store_energy_data(self.env.current_energy_use)
            self.store_comfort_data(self.env.current_comfort_score)
            
            if done:
                break
        
        # Train the agent with experiences in memory
        if len(self.agent.memory) > 32:
            self.agent.replay(32)

    def store_facade_data(self, state, action):
        self.facade_data.append({
            'time': time.time(),
            'temperature': state[0],
            'humidity': state[1],
            'wind_speed': state[2],
            'wind_direction': state[3],
            'cloudiness': state[4],
            'weather_condition': state[5],
            'panel_count': int(10 + action[0] * 10),
            'rotation': action[1] * 90,
            'depth': 0.1 + action[2] * 0.4
        })

    def store_energy_data(self, energy_use):
        self.energy_data.append({
            'time': time.time(),
            'energy_use': energy_use,
            'temperature': self.facade_data[-1]['temperature'],
            'humidity': self.facade_data[-1]['humidity']
        })

    def store_comfort_data(self, comfort_score):
        self.comfort_data.append({
            'time': time.time(),
            'comfort_score': comfort_score
        })

    def update_visualizations(self):
        facade_df = pd.DataFrame(self.facade_data)
        energy_df = pd.DataFrame(self.energy_data)
        comfort_df = pd.DataFrame(self.comfort_data)
        
        facade_df.to_csv('visualization/facade_data.csv', index=False)
        energy_df.to_csv('visualization/energy_data.csv', index=False)
        comfort_df.to_csv('visualization/comfort_data.csv', index=False)
        
        self.visualizer.load_facade_data('visualization/facade_data.csv')
        self.visualizer.load_energy_data('visualization/energy_data.csv')
        self.visualizer.load_comfort_data('visualization/comfort_data.csv')
        
        self.visualizer.plot_facade_behavior()
        self.visualizer.plot_energy_performance()
        self.visualizer.plot_comfort_performance()
        self.visualizer.create_heatmap()
        self.visualizer.create_interactive_3d_plot()
        self.visualizer.create_animated_facade()

    def run(self):
        while True:
            self.run_simulation_cycle()
            self.update_visualizations()
            time.sleep(3600)  # Run every hour

def main():
    controller = MainController()
    
    # Initialize Revit integration
    # In a real scenario, you'd need to run this within Revit
    class MockDocument:
        def __init__(self):
            self.Application = None
            self.Create = None
            self.FreeformElement = None
    
    mock_doc = MockDocument()
    controller.revit_integration = RevitIntegration(mock_doc)
    controller.env.revit_integration = controller.revit_integration
    
    # Run the main control loop in a separate thread
    control_thread = threading.Thread(target=controller.run)
    control_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()
