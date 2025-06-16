from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from livekit import api
import os
import json
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from log_streamer import register_client, unregister_client

app = FastAPI()
# load environment variables, this is optional, only used for local development
load_dotenv(dotenv_path=".env.local")


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register_client(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        unregister_client(websocket)


class DispatchRequest(BaseModel):
    room_name: str
    agent_name: str
    phone_number: str
    transfer_to : str


@app.post("/dispatch")
async def create_agent_dispatch(data: DispatchRequest):
    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=data.agent_name, room=data.room_name,metadata = json.dumps({
        "phone_number": data.phone_number,
        "transfer_to": data.transfer_to
    })
        )
    )
    print("created dispatch", dispatch)

    dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=data.room_name)
    print(f"there are {len(dispatches)} dispatches in {data.room_name}")
    await lkapi.aclose()

    
    return {
        "message": "Dispatch created successfully",
        "dispatch": data.room_name
    }