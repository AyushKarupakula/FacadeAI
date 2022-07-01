from flask import Flask, render_template, jsonify
from main_controller import MainController
import threading
import time

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

@app.route('/api/current_status')
def get_current_status():
    return jsonify({
        'last_update': time.time(),
        'panel_count': len(controller.facade_data),
        'energy_use': controller.energy_data[-1]['energy_use'] if controller.energy_data else None,
        'temperature': controller.energy_data[-1]['temperature'] if controller.energy_data else None,
        'humidity': controller.energy_data[-1]['humidity'] if controller.energy_data else None,
    })

@app.route('/api/rl_performance')
def get_rl_performance():
    return jsonify({
        'epsilon': controller.agent.epsilon,
        'memory_size': len(controller.agent.memory),
        'last_reward': controller.env.current_energy_use,
        'total_steps': controller.env.step_count
    })

if __name__ == '__main__':
    app.run(debug=True)
