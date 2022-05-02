import asyncio
import websockets
import json

async def connect_to_server():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        while True:
            # Simulate requesting adjustments every 5 minutes
            await asyncio.sleep(300)
            
            request = json.dumps({"type": "request_adjustments"})
            await websocket.send(request)
            
            response = await websocket.recv()
            adjustments = json.loads(response)
            
            print("Received façade adjustments:")
            print(f"Adjustment 1: {adjustments['data']['adjustment_1']:.2f}")
            print(f"Adjustment 2: {adjustments['data']['adjustment_2']:.2f}")
            print(f"Adjustment 3: {adjustments['data']['adjustment_3']:.2f}")
            
            # Here, you would update the Grasshopper model with these adjustments

if __name__ == "__main__":
    asyncio.run(connect_to_server())
