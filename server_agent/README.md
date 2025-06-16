<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# Outbound Calling Agent with LiveKit + FastAPI

This project implements a LiveKit-powered voice agent for outbound calls. The agent confirms appointments, transfers calls to a human, and handles answering machines. It supports:

*  **SIP-based outbound calls (via twilio outbound trunk)**
*  **Google Gemini LLM**
*  **AssemblyAI STT (speech-to-text)**
*  **ElevenLabs TTS (text-to-speech)**
*  **WebSocket-based real-time logging**
*  **FastAPI endpoint to trigger agent dispatch**

---

##  Requirements and dependencies

###  Python 
* using python version 3.10+

###  Python Dependencies

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

##  Environment Setup

Create a `.env.local` file (or rename `.env.example`) and define the following variables:

```env
LIVEKIT_URL=https://your-livekit-server-url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

SIP_OUTBOUND_TRUNK_ID=sip_trunk_id_from_livekit

ASSEMBLYAI_API_KEY=your_assembly_ai_key
GOOGLE_API_KEY=your_google_api_key
ELEVENLABS_API_KEY=your_eleven_labs_key
```

---

## 🚀 Running the Application

The server runs:

* A FastAPI backend with WebSocket log streaming (`/ws/logs`)
* The LiveKit Agent via `cli.run_app`

### Start the Fast API Server and Livekit agent together

```bash
python app.py dev
```

This will:

* Start the FastAPI server on port `8000`
* Start the LiveKit agent named `outbound-caller`
* Serve logs to connected WebSocket clients

---

##  Agent Features

The agent (`OutboundCaller`) can:

* Confirm appointments (`confirm_appointment`)
* Look up availability (`look_up_availability`)
* End the call (`end_call`)
* Transfer to a human (`transfer_call`)
* Hang up if answering machine is detected (`detected_answering_machine`)

---

##  Dispatching Calls

###  Using CLI

```bash
lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --metadata '{"phone_number": "+911234567890", "transfer_to": "+919876543210"}'
```

###  Using FastAPI

POST request to `http://localhost:8000/dispatch` with:

```json
{
  "room_name": "outbound-room-01",
  "agent_name": "outbound-caller",
  "phone_number": "+911234567890",
  "transfer_to": "+919876543210"
}
```

Response:

```json
{
  "message": "Dispatch created successfully",
  "dispatch": "outbound-room-01"
}
```

---

##  Viewing Logs in Real Time (in-progress)

Connect a WebSocket client (frontend or tool) to:

```
ws://localhost:8000/ws/logs
```

Logs are broadcast to all connected WebSocket clients using the custom `WebSocketLogHandler`.

---

## 📁 Project Structure

```
├── agent.py                # Agent logic and behavior
├── app.py               # FastAPI + WebSocket + Dispatch API
├── log_streamer.py         # WebSocket log broadcasting
├── .env.local              # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # You're here!
```

---

##  Notes on Services

| Service       | Role             | Config Key           |
| ------------- | ---------------- | -------------------- |
| LiveKit       | SIP/room backend | `LIVEKIT_*`          |
| AssemblyAI    | STT              | `ASSEMBLYAI_API_KEY` |
| ElevenLabs    | TTS              | `ELEVENLABS_API_KEY` |
| Google Gemini | LLM              | `GOOGLE_API_KEY`     |

---

# ✅ TODO (Enhancements)

* Add frontend to view live logs and trigger calls (currently able to trigger calls only.)
* Store call transcripts to disk or database (Engress for recording)
* Implement user authentication for FastAPI/WebSocket (using livekit authtoken creation)
* implementation of react SDK.


--------------------------------------------

#### Below is the template readme for sample agent for dental clinic appointment.




## Python Outbound Call Agent

<p>
  <a href="https://docs.livekit.io/agents/overview/">LiveKit Agents Docs</a>
  •
  <a href="https://livekit.io/cloud">LiveKit Cloud</a>
  •
  <a href="https://blog.livekit.io/">Blog</a>
</p>

This example demonstrates an full workflow of an AI agent that makes outbound calls. It uses LiveKit SIP and Python [Agents Framework](https://github.com/livekit/agents).

It can use a pipeline of STT, LLM, and TTS models, or a realtime speech-to-speech model. (such as ones from OpenAI and Gemini).

This example builds on concepts from the [Outbound Calls](https://docs.livekit.io/agents/start/telephony/#outbound-calls) section of the docs. Ensure that a SIP outbound trunk is configured before proceeding.

## Features

This example demonstrates the following features:

- Making outbound calls
- Detecting voicemail
- Looking up availability via function calling
- Transferring to a human operator
- Detecting intent to end the call
- Uses Krisp background voice cancellation to handle noisy environments

## Dev Setup

Clone the repository and install dependencies to a virtual environment:

```shell
git clone https://github.com/livekit-examples/outbound-caller-python.git
cd outbound-caller-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agent.py download-files
```

Set up the environment by copying `.env.example` to `.env.local` and filling in the required values:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `SIP_OUTBOUND_TRUNK_ID`
- `DEEPGRAM_API_KEY` - optional, only needed when using pipelined models
- `CARTESIA_API_KEY` - optional, only needed when using pipelined models

Run the agent:

```shell
python3 agent.py dev
```

Now, your worker is running, and waiting for dispatches in order to make outbound calls.

### Making a call

You can dispatch an agent to make a call by using the `lk` CLI:

```shell
lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --metadata '{"phone_number": "+1234567890", "transfer_to": "+9876543210}'
```
