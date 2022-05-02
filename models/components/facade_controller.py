import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import ghpythonlib.components as ghcomp
import websocket
import json
import threading
import time

class FacadeController:
    def __init__(self):
        self.ws = None
        self.adjustments = {
            "adjustment_1": 0.0,
            "adjustment_2": 0.0,
            "adjustment_3": 0.0
        }
        self.connect_to_server()

    def connect_to_server(self):
        def on_message(ws, message):
            data = json.loads(message)
            if data['type'] == 'facade_adjustments':
                self.adjustments = data['data']
                print("Received new adjustments:", self.adjustments)

        def on_error(ws, error):
            print("Error:", error)

        def on_close(ws):
            print("Connection closed")

        def on_open(ws):
            print("Connection opened")
            self.request_adjustments()

        self.ws = websocket.WebSocketApp("ws://localhost:8765",
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close,
                                         on_open=on_open)

        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def request_adjustments(self):
        self.ws.send(json.dumps({"type": "request_adjustments"}))

    def update_facade(self, base_surface):
        # This is a simplified example of how we might update the façade
        # In a real scenario, this would be much more complex and tailored to your specific design

        # Adjustment 1: Control the number of panels
        panel_count = int(10 + self.adjustments["adjustment_1"] * 10)  # Range: 10-20 panels
        
        # Adjustment 2: Control the rotation of panels
        rotation_angle = self.adjustments["adjustment_2"] * 90  # Range: 0-90 degrees
        
        # Adjustment 3: Control the depth of panels
        panel_depth = 0.1 + self.adjustments["adjustment_3"] * 0.4  # Range: 0.1-0.5 meters

        # Create panels
        panels = []
        u_step = 1.0 / panel_count
        for i in range(panel_count):
            u = i * u_step
            panel_surface = rs.ExtrudeSurface(base_surface, rs.VectorScale(rs.SurfaceNormal(base_surface, [u, 0.5]), panel_depth))
            panel_surface = rs.RotateObject(panel_surface, rs.SurfaceDomain(base_surface, 0), rotation_angle)
            panels.append(panel_surface)

        return panels

# This function will be called by Grasshopper
def update_facade_model(base_surface):
    global facade_controller
    if 'facade_controller' not in globals():
        facade_controller = FacadeController()
    
    # Request new adjustments every 5 minutes
    if int(time.time()) % 300 == 0:
        facade_controller.request_adjustments()
    
    return facade_controller.update_facade(base_surface)

# For testing outside of Grasshopper
if __name__ == "__main__":
    # Simulate a base surface
    base_surface = rs.AddPlaneSurface(rs.WorldXYPlane(), 10, 5)
    
    # Update facade
    panels = update_facade_model(base_surface)
    
    print(f"Created {len(panels)} panels")
