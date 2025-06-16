
import { useState } from "react"
import "./App.css"
import { LIVEKIT_APP_URL } from "../config"

const VoiceAgentTrigger = () => {
  const [serverUrl, setServerUrl] = useState(LIVEKIT_APP_URL)
  const [callStatus, setCallStatus] = useState("idle") // idle, dialing, connected, ended
  const [dialInfo, setDialInfo] = useState({
    phone_number: "",
    transfer_to: "",
  })
  const [isLoading, setIsLoading] = useState(false)

  // Generate a unique room name
  const generateRoomName = () => {
    return `outbound-call-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  const triggerOutboundCall = async () => {
    if (!dialInfo.phone_number || !serverUrl) {
      alert("Please provide phone number and server URL")
      return
    }

    try {
      setIsLoading(true)
      setCallStatus("dialing")

      const newRoomName = generateRoomName()

      // Prepare request to FastAPI to dispatch agent
      const requestBody = JSON.stringify({
        room_name: newRoomName,
        agent_name: "outbound-caller",
        phone_number: dialInfo.phone_number,
        transfer_to: dialInfo.transfer_to || "",
      })

      const response = await fetch("http://localhost:8000/dispatch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: requestBody,
        redirect: "follow",
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || "Failed to dispatch agent.")
      }

      console.log("Agent dispatched successfully:", await response.text())
      setCallStatus("connected")
    } catch (error) {
      console.error("Error triggering outbound call:", error)
      setCallStatus("idle")
      alert("Error starting call: " + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const resetCall = () => {
    setCallStatus("idle")
    setDialInfo({
      phone_number: "",
      transfer_to: "",
    })
  }

  return (
    <div className="voice-agent-container">
      <div className="voice-agent-wrapper">
        <h1 className="main-title">Voice Agent Trigger</h1>

        <div className="config-section">
          <h2 className="section-title">Configuration</h2>

          <div className="form-group">
            <label className="form-label">LiveKit Server URL</label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="wss://your-livekit-server.com"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number to Call</label>
            <input
              type="tel"
              value={dialInfo.phone_number}
              onChange={(e) => setDialInfo({ ...dialInfo, phone_number: e.target.value })}
              placeholder="+1234567890"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Transfer To (Optional)</label>
            <input
              type="tel"
              value={dialInfo.transfer_to}
              onChange={(e) => setDialInfo({ ...dialInfo, transfer_to: e.target.value })}
              placeholder="+1234567890"
              className="form-input"
            />
          </div>
        </div>

        <div className="control-section">
          <h2 className="section-title">Call Control</h2>

          <div className="status-control">
            <div className="status-info">
              <p className="status-text">
                Status:
                <span className={`status-badge status-${callStatus}`}>
                  {callStatus.charAt(0).toUpperCase() + callStatus.slice(1)}
                </span>
              </p>
            </div>

            <div className="button-group">
              <button
                onClick={triggerOutboundCall}
                disabled={callStatus !== "idle" || !dialInfo.phone_number || !serverUrl || isLoading}
                className="trigger-button"
              >
                {isLoading ? "Starting..." : "Start Outbound Call"}
              </button>

              {callStatus !== "idle" && (
                <button onClick={resetCall} className="reset-button">
                  Reset
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="instructions-section">
          <h3 className="instructions-title">Setup Instructions:</h3>
          <ol className="instructions-list">
            <li>Set your LiveKit server URL</li>
            <li>Generate and provide a LiveKit token (implement token generation)</li>
            <li>Make sure your Python agent is running and can receive job dispatches</li>
            <li>Configure SIP trunk for outbound calls in your LiveKit server</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default VoiceAgentTrigger
