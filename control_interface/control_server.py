import asyncio
import websockets
import json
from ai_control_system.inference import get_facade_adjustments
from data_acquisition.fetch_data import fetch_weather_data, load_config

class FacadeControlServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.config = load_config()

    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"New client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_adjustments(self, websocket, adjustments):
        message = json.dumps({
            "type": "facade_adjustments",
            "data": {
                "adjustment_1": float(adjustments[0]),
                "adjustment_2": float(adjustments[1]),
                "adjustment_3": float(adjustments[2])
            }
        })
        await websocket.send(message)

    async def handle_client(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'request_adjustments':
                    weather_data = fetch_weather_data(self.config['openweathermap_api_key'], self.config['city'])
                    adjustments = get_facade_adjustments(weather_data)
                    await self.send_adjustments(websocket, adjustments)
        finally:
            await self.unregister(websocket)

    async def run(self):
        server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"Façade Control Server running on ws://{self.host}:{self.port}")
        await server.wait_closed()

if __name__ == "__main__":
    server = FacadeControlServer()
    asyncio.run(server.run())
