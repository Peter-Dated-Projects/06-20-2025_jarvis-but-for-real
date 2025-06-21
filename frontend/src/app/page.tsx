"use client";

import { useEffect, useState, useRef } from "react";
import io, { Socket } from "socket.io-client";
import styles from "./page.module.css";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001";
const AVAILABLE_MODELS: string[] = ["small", "medium"];

export default function Home() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [realTimeTranscription, setRealTimeTranscription] = useState("");
  const [messages, setMessages] = useState<{ text: string; timestamp: string; sender: string }[]>(
    []
  );
  const [currentMessage, setCurrentMessage] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [socketId, setSocketId] = useState<string | null>(null);

  const [activeModel, setActiveModel] = useState<string>(AVAILABLE_MODELS[0] || "small"); // Default to the first available model

  useEffect(() => {
    // Initialize socket connection
    const newSocket = io(BACKEND_URL + "/streaming", {
      // Changed to connect to the root namespace
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ["websocket"],
    });

    newSocket.on("connect", () => {
      console.log("Socket connected:", newSocket.id);
      setSocket(newSocket);
      setSocketId(newSocket.id); // Store the socket ID

      // setup the configuration for real-time transcription
      newSocket.emit("configuration", {
        sid: newSocket.id, // Include session ID for backend routing
        target_model_path: activeModel, // Specify the model to use
      });
    });

    // Add handler for real-time transcription events
    newSocket.on("real_time_stt_response", (data) => {
      console.log("Received real-time transcription:", data);

      // Check if we have a new transcription segment
      if (data.new_segment && data.segment_transcript) {
        setRealTimeTranscription(data.segment_transcript);
        console.log("Updated transcription:", data.segment_transcript);
      } else if (data.message) {
        // This is just an acknowledgment message
        console.log("STT processing message:", data.message);
      }
    });

    newSocket.on("error", (error) => {
      console.error("Socket error:", error);
    });

    newSocket.on("disconnect", (reason) => {
      console.log("Socket disconnected:", reason);
      setSocket(null);
      setSocketId(null);
      if (isRecording) {
        // stopRecording(); // Consider if recording should stop automatically
      }
    });

    // Cleanup on component unmount
    return () => {
      if (newSocket.connected) {
        newSocket.disconnect();
      }
    };
  }, []); // Empty dependency array ensures this runs only once

  const startRecording = async () => {
    if (!socket || !socket.connected) {
      alert("Socket not connected. Please wait.");
      return;
    }
    if (isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "audio/webm" }); // Using webm as it's widely supported
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          // Send audio data in chunks
          const data = {
            sid: socket.id, // Include session ID for backend routing if needed
            audio_data: event.data,
            real_time: true,
            audio_format: "webm", // Matches the mimeType
            channels: 1, // Assuming mono audio
            sample_rate:
              mediaRecorderRef.current?.stream.getAudioTracks()[0].getSettings().sampleRate ||
              48000,
          };
          socket.emit("real_time_stt_request", data);

          console.log("Audio Chunk Data: ", data);
          console.log("Audio chunk sent, size:", event.data.size);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        console.log("Recording stopped, final blob size:", audioBlob.size);
        stream.getTracks().forEach((track) => track.stop());
        if (socket && socket.connected) {
          socket.emit("stop_recording", { sid: socket.id });
        }
      };

      mediaRecorderRef.current.start(500); // Send data every half second
      setIsRecording(true);
      setRealTimeTranscription(""); // Clear previous transcription
      console.log("Recording started");
    } catch (error) {
      console.error("Error starting recording:", error);
      alert("Could not start recording. Please ensure microphone access is allowed.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log("Recording stopped by user");
    }
  };

  const handleSendMessage = () => {
    if (socket && socket.connected && currentMessage.trim() !== "") {
      const newMessage = {
        text: currentMessage,
        timestamp: new Date().toLocaleTimeString(),
        sender: "User", // Or use socket.id for a unique sender ID
      };
      socket.emit("send_message", newMessage); // Emit to the default namespace
      setMessages((prevMessages) => [...prevMessages, newMessage]); // Optimistically update UI
      setCurrentMessage("");
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>Real-time Audio Transcription & Messaging</h1>

        <div className={styles.controls}>
          <button
            onClick={startRecording}
            disabled={isRecording || !socket || !socket.connected}
            className={styles.button}
          >
            Start Recording
          </button>
          <button
            onClick={stopRecording}
            disabled={!isRecording || !socket || !socket.connected}
            className={styles.button}
          >
            Stop Recording
          </button>
        </div>

        {isRecording && <p className={styles.status}>Recording...</p>}
        {!socket && <p className={styles.statusWarning}>Connecting to server...</p>}
        {socket && !socket.connected && (
          <p className={styles.statusWarning}>Server disconnected. Attempting to reconnect...</p>
        )}

        <div className={styles.transcriptionSection}>
          <h2>Real-time Transcription:</h2>
          <p className={styles.transcriptionText}>
            {realTimeTranscription || "Waiting for audio..."}
          </p>
        </div>

        <div className={styles.messageSection}>
          <h2>Messages</h2>
          <div className={styles.messageInput}>
            <input
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Type your message"
              className={styles.input}
              onKeyPress={(event) => {
                if (event.key === "Enter") {
                  handleSendMessage();
                }
              }}
            />
            <button
              onClick={handleSendMessage}
              className={styles.button}
              disabled={!socket || !socket.connected}
            >
              Send
            </button>
          </div>
          <table className={styles.messageTable}>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Sender</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((msg, index) => (
                <tr key={index}>
                  <td>{msg.timestamp}</td>
                  <td>{msg.sender}</td>
                  <td>{msg.text}</td>
                </tr>
              ))}
              {messages.length === 0 && (
                <tr>
                  <td colSpan={3}>No messages yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
