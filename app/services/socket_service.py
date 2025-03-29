"""
A320 Wing Simulation Socket Service
-----------------------------------
Socket.IO service for communicating between the client and server for the A320 wing simulation.
"""

from flask_socketio import emit
from app import socketio
from app.services.a320_aerodynamics import A320WingAerodynamics

# Create a simulation instance
simulation = A320WingAerodynamics()

@socketio.on('connect', namespace='/simulation')
def simulation_connect():
    """Client connected - send initial simulation data"""
    print('Simulation client connected')
    emit('simulation_data', simulation.get_simulation_data())

@socketio.on('disconnect', namespace='/simulation')
def simulation_disconnect():
    """Client disconnected"""
    print('Simulation client disconnected')

@socketio.on('update_settings', namespace='/simulation')
def handle_settings_update(settings):
    """Handle control settings updates from client"""
    print(f'Received settings update: {settings}')
    
    # Update simulation with new settings
    data = simulation.update_settings(settings)
    
    # Broadcast updated simulation data to client
    emit('simulation_data', data)

@socketio.on('start_simulation', namespace='/simulation')
def start_simulation():
    """Start the simulation"""
    print('Starting simulation')
    emit('simulation_status', {'running': True})

@socketio.on('stop_simulation', namespace='/simulation')
def stop_simulation():
    """Stop the simulation"""
    print('Stopping simulation')
    emit('simulation_status', {'running': False})

@socketio.on('reset_simulation', namespace='/simulation')
def reset_simulation():
    """Reset the simulation to default settings"""
    print('Resetting simulation')
    # Create new simulation instance with default settings
    global simulation
    simulation = A320WingAerodynamics()
    emit('simulation_data', simulation.get_simulation_data())
    emit('simulation_status', {'running': True})