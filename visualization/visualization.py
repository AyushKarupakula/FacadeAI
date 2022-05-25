import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px

class FacadeVisualizer:
    def __init__(self):
        self.facade_data = None
        self.energy_data = None

    def load_facade_data(self, file_path):
        self.facade_data = pd.read_csv(file_path)

    def load_energy_data(self, file_path):
        self.energy_data = pd.read_csv(file_path)

    def plot_facade_behavior(self):
        if self.facade_data is None:
            print("No facade data loaded. Please load data first.")
            return

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        x = self.facade_data['panel_id']
        y = self.facade_data['time']
        z_rotation = self.facade_data['rotation']
        z_depth = self.facade_data['depth']

        ax.scatter(x, y, z_rotation, c='r', marker='o', label='Rotation')
        ax.scatter(x, y, z_depth, c='b', marker='^', label='Depth')

        ax.set_xlabel('Panel ID')
        ax.set_ylabel('Time')
        ax.set_zlabel('Value')
        ax.legend()

        plt.title('Facade Behavior Over Time')
        plt.show()

    def plot_energy_performance(self):
        if self.energy_data is None:
            print("No energy data loaded. Please load data first.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        ax1.plot(self.energy_data['time'], self.energy_data['energy_use'], label='Energy Use')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Energy Use (kWh)')
        ax1.legend()

        ax2.plot(self.energy_data['time'], self.energy_data['temperature'], label='Temperature')
        ax2.plot(self.energy_data['time'], self.energy_data['humidity'], label='Humidity')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Value')
        ax2.legend()

        plt.tight_layout()
        plt.show()

    def create_heatmap(self):
        if self.facade_data is None or self.energy_data is None:
            print("Both facade and energy data must be loaded. Please load data first.")
            return

        merged_data = pd.merge(self.facade_data, self.energy_data, on='time')
        pivot_data = merged_data.pivot('panel_id', 'time', 'energy_use')

        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_data, cmap='YlOrRd', annot=False)
        plt.title('Energy Use Heatmap by Panel and Time')
        plt.xlabel('Time')
        plt.ylabel('Panel ID')
        plt.show()

    def create_interactive_3d_plot(self):
        if self.facade_data is None:
            print("No facade data loaded. Please load data first.")
            return

        fig = go.Figure(data=[go.Scatter3d(
            x=self.facade_data['panel_id'],
            y=self.facade_data['time'],
            z=self.facade_data['rotation'],
            mode='markers',
            marker=dict(
                size=5,
                color=self.facade_data['depth'],
                colorscale='Viridis',
                opacity=0.8
            ),
            text=self.facade_data['energy_use'],
            hoverinfo='text'
        )])

        fig.update_layout(
            title='Interactive 3D Facade Behavior',
            scene=dict(
                xaxis_title='Panel ID',
                yaxis_title='Time',
                zaxis_title='Rotation'
            ),
            width=800,
            height=700,
        )

        fig.show()

    def create_animated_facade(self):
        if self.facade_data is None:
            print("No facade data loaded. Please load data first.")
            return

        fig = px.scatter(self.facade_data, x='panel_id', y='rotation', animation_frame='time',
                         animation_group='panel_id', size='depth', color='energy_use',
                         hover_name='panel_id', size_max=55, range_y=[0, 90])

        fig.update_layout(title='Animated Facade Behavior Over Time')
        fig.show()

if __name__ == "__main__":
    visualizer = FacadeVisualizer()
    
    # Load sample data (you would replace these with your actual data files)
    visualizer.load_facade_data('sample_facade_data.csv')
    visualizer.load_energy_data('sample_energy_data.csv')
    
    # Generate visualizations
    visualizer.plot_facade_behavior()
    visualizer.plot_energy_performance()
    visualizer.create_heatmap()
    visualizer.create_interactive_3d_plot()
    visualizer.create_animated_facade()
