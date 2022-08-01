import time
import threading
from data_acquisition.fetch_data import fetch_weather_data, load_config
from ai_control_system.facade_env import FacadeEnv
from ai_control_system.ppo_agent import PPOAgent
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
        self.agent = PPOAgent(state_size=self.env.observation_space.shape[0],
                              action_size=self.env.action_space.shape[0])

    def run_simulation_cycle(self):
        state = self.env.reset()
        total_reward = 0
        states, actions, rewards, next_states, dones = [], [], [], [], []
        
        for time_step in range(self.env.max_steps):
            action = self.agent.get_action(state)
            next_state, reward, done, _ = self.env.step(action)
            
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)
            
            total_reward += reward
            state = next_state
            
            # Store facade, energy, and comfort data
            self.store_facade_data(self.env.current_state, action)
            self.store_energy_data(self.env.current_energy_use)
            self.store_comfort_data(self.env.current_comfort_score)
            
            if done:
                break
        
        # Train the PPO agent
        loss = self.agent.train(states, actions, rewards, next_states, dones)
        
        print(f"Episode finished. Total reward: {total_reward}, Loss: {loss}")

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
