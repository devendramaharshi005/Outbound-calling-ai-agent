from __future__ import annotations

import asyncio
import threading
import logging
import json
import os

from dotenv import load_dotenv
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    RunContext,
    get_job_context,
    function_tool,
    cli,
    WorkerOptions,
    RoomInputOptions
)
from livekit.plugins import assemblyai, elevenlabs, google, silero, noise_cancellation

from log_streamer import (
    register_client,
    unregister_client,
    WebSocketLogHandler,
)

# Load environment
load_dotenv(dotenv_path=".env.local")
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

# Logger setup
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)
log_handler = WebSocketLogHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        unregister_client(websocket)

class DispatchRequest(BaseModel):
    room_name: str
    agent_name: str
    phone_number: str
    transfer_to: str

@app.post("/dispatch")
async def create_agent_dispatch(data: DispatchRequest):
    lkapi = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=data.agent_name,
            room=data.room_name,
            metadata=json.dumps({
                "phone_number": data.phone_number,
                "transfer_to": data.transfer_to,
            }),
        )
    )
    dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=data.room_name)
    await lkapi.aclose()
    return {
        "message": "Dispatch created successfully",
        "dispatch": data.room_name
    }

# --- LiveKit Agent ---
class OutboundCaller(Agent):
    def __init__(self, *, name: str, appointment_time: str, dial_info: dict[str, Any]):
        super().__init__(
            instructions=f"""
            You are a scheduling assistant for a dental practice. Your interface is voice.
            Confirm the appointment of {name} on {appointment_time}. Be polite.
            """
        )
        self.participant: rtc.RemoteParticipant | None = None
        self.dial_info = dial_info

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def hangup(self):
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        transfer_to = self.dial_info["transfer_to"]
        logger.info(f"transferring call to {transfer_to}")
        await ctx.session.generate_reply(instructions="Transferring you now.")
        try:
            await get_job_context().api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=get_job_context().room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            await self.hangup()

    @function_tool()
    async def end_call(self, ctx: RunContext):
        logger.info("ending call")
        await self.hangup()

    @function_tool()
    async def look_up_availability(self, ctx: RunContext, date: str):
        logger.info(f"checking availability on {date}")
        await asyncio.sleep(2)
        return {"available_times": ["2pm", "3pm"]}

    @function_tool()
    async def confirm_appointment(self, ctx: RunContext, date: str, time: str):
        logger.info(f"appointment confirmed on {date} at {time}")
        return "Confirmed"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        logger.info("voicemail detected")
        await self.hangup()

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()
    dial_info = json.loads(ctx.job.metadata)
    participant_identity = dial_info["phone_number"]

    agent = OutboundCaller(
        name="Jayden",
        appointment_time="next Tuesday at 3pm",
        dial_info=dial_info,
    )

    session = AgentSession(
        turn_detection="stt",
        stt=assemblyai.STT(
            end_of_turn_confidence_threshold=0.7,
            min_end_of_turn_silence_when_confident=160,
            max_turn_silence=2400,
        ),
        vad=silero.VAD.load(),
        tts=elevenlabs.TTS(
            voice_id="Xb7hH8MSUJpSbSDYk0k2",
            model="eleven_multilingual_v2"
        ),
        llm=google.LLM(model="gemini-2.0-flash-exp", temperature=0.8),
    )

    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVCTelephony(),
            )
        )
    )

    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=participant_identity,
                participant_identity=participant_identity,
                wait_until_answered=True,
            )
        )

        await session_started
        participant = await ctx.wait_for_participant(identity=participant_identity)
        agent.set_participant(participant)
        logger.info(f"participant joined: {participant.identity}")

    except api.TwirpError as e:
        logger.error(f"SIP error: {e.message}")
        ctx.shutdown()

# --- Main ---
import log_streamer

def start_fastapi():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    log_streamer.event_loop = loop  # Set the shared loop for WebSocket logs
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    threading.Thread(target=start_fastapi, daemon=True).start()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller",
        )
    )
