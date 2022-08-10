from flask import Flask, render_template, jsonify
from main_controller import MainController
import threading
import time
import numpy as np

app = Flask(__name__)

controller = MainController()

# Start the main control loop in a separate thread
control_thread = threading.Thread(target=controller.run)
control_thread.daemon = True
control_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/facade_data')
def get_facade_data():
    return jsonify(controller.facade_data)

@app.route('/api/energy_data')
def get_energy_data():
    return jsonify(controller.energy_data)

@app.route('/api/comfort_data')
def get_comfort_data():
    return jsonify(controller.comfort_data)

@app.route('/api/current_status')
def get_current_status():
    return jsonify({
        'last_update': time.time(),
        'panel_count': len(controller.facade_data),
        'energy_use': controller.energy_data[-1]['energy_use'] if controller.energy_data else None,
        'temperature': controller.energy_data[-1]['temperature'] if controller.energy_data else None,
        'humidity': controller.energy_data[-1]['humidity'] if controller.energy_data else None,
        'comfort_score': controller.comfort_data[-1]['comfort_score'] if controller.comfort_data else None,
    })

@app.route('/api/rl_performance')
def get_rl_performance():
    # Get the latest action from the PPO agent
    state = controller.env.current_state
    if state is not None:
        action = controller.agent.get_action(state)
    else:
        action = np.zeros(controller.agent.action_size)

    return jsonify({
        'learning_rate': controller.agent.learning_rate,
        'gamma': controller.agent.gamma,
        'epsilon': controller.agent.epsilon,
        'value_coef': controller.agent.value_coef,
        'entropy_coef': controller.agent.entropy_coef,
        'last_total_loss': controller.last_total_loss if hasattr(controller, 'last_total_loss') else None,
        'total_steps': controller.env.step_count,
        'latest_action': action.tolist()
    })

if __name__ == '__main__':
    app.run(debug=True)
