"use client";

import { useEffect, useState, useRef, useReducer } from "react";
import io, { Socket } from "socket.io-client";
import styles from "./page.module.css";

// ----------------------------------------------------------------- //

const BACKEND_URL = "http://localhost:5001";

// ----------------------------------------------------------------- //
interface TranscriptionSegment {
  transcription: string;
  start_time: number;
  end_time: number;
}

interface TranscriptionSegmentCardProps {
  text: string;
  start: number;
  end: number;
}

// ----------------------------------------------------------------- //

function TranscriptionSegmentCard({ text, start, end }: TranscriptionSegmentCardProps) {
  return (
    <div className={styles.transcriptionSegmentCard}>
      <p className={styles.transcriptionSegmentText}>Text: {text}</p>
      <p className={styles.transcriptionSegmentTime}>
        Start: {start} - End: {end}
      </p>
    </div>
  );
}

// ----------------------------------------------------------------- //

export default function Home() {
  // ----------------------------------------------------------------- //
  // states

  const [messages, setMessages] = useState<{ text: string; timestamp: string; sender: string }[]>(
    []
  );
  const [currentMessage, setCurrentMessage] = useState("");

  // socket + events
  const [socket, setSocket] = useState<Socket | null>(null);
  const [socketId, setSocketId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Added back for real-time transcription
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const [transcriptionSegments, setTranscriptionSegments] = useState<
    TranscriptionSegmentCardProps[]
  >([]);

  // ----------------------------------------------------------------- //
  // Effect to handle socket connection and events

  useEffect(() => {
    console.log("Creating first object to test");

    setTranscriptionSegments([
      {
        text: "This is a test transcription segment.",
        start: 0,
        end: 5,
      },
    ]);

    // ----------------------------------------------------------------- //
    // Initialize socket connection to the streaming namespace
    console.log("Connecting to socket at:", `${BACKEND_URL}/propagate_whisper_events`);
    const socket_url = `${BACKEND_URL}/propagate_whisper_events`;
    const propagateSocket = io(socket_url, {
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ["websocket"],
    });

    // Set up socket event listeners
    propagateSocket.on("confirm_connect", (data) => {
      console.log("Socket connected:", data.sid);
      setSocket(propagateSocket);
      setSocketId(data.sid);
      setConnectionStatus("connected");
      setError(null);
    });

    // status update event
    propagateSocket.on("status_update", (data) => {
      console.log("Status update:", data.status);
      setConnectionStatus(data.status);
      if (data.status === "connection_error") {
        setError("Connection error occurred. Please check the console for details.");
      } else {
        setError(null);
      }
    });

    // segment update event
    propagateSocket.on("segment_update", (data: TranscriptionSegment) => {
      console.log("Segment update received:", data);

      // Update the last segment if it matches the start time, else ignore
      setTranscriptionSegments((prevSegments) => {
        if (prevSegments.length === 0) return prevSegments;
        const lastIndex = prevSegments.length - 1;
        // Update the last segment
        const updatedSegments = [...prevSegments];
        updatedSegments[lastIndex] = {
          text: data.transcription,
          start: data.start_time,
          end: data.end_time,
        };
        return updatedSegments;
      });
    });

    // segment creation event
    propagateSocket.on("segment_creation", (data: TranscriptionSegment) => {
      console.log("Segment creation event received:", data);
      // Add new segment to the list
      setTranscriptionSegments((prevSegments) => [
        ...prevSegments,
        { text: data.transcription, start: data.start_time, end: data.end_time },
      ]);
    });

    // Handle errors
    propagateSocket.on("error", (error) => {
      console.error("Socket error:", error);
      setError(error.message || "An error occurred");
    });

    propagateSocket.on("disconnect", (reason) => {
      console.log("Socket disconnected:", reason);
      setSocket(null);
      setSocketId(null);
      setConnectionStatus("disconnected");
    });

    // Cleanup on component unmount
    return () => {
      if (propagateSocket.connected) {
        propagateSocket.disconnect();
      }
    };
  }, []); // Empty dependency array ensures this runs only once

  const handleSendMessage = () => {
    if (socket && socket.connected && currentMessage.trim() !== "") {
      const newMessage = {
        text: currentMessage,
        timestamp: new Date().toLocaleTimeString(),
        sender: "User",
      };
      socket.emit("send_message", newMessage);
      setMessages((prevMessages) => [...prevMessages, newMessage]);
      setCurrentMessage("");
    }
  };

  // Add this log to see changes to the state
  useEffect(() => {
    console.log("Transcription segments updated:", transcriptionSegments);
  }, [transcriptionSegments]);

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>Text Messaging</h1>

        {connectionStatus === "disconnected" && (
          <p className={styles.statusWarning}>Connecting to server...</p>
        )}
        {connectionStatus === "connection_error" && (
          <p className={styles.statusWarning}>
            Server connection error. Check console for details.
          </p>
        )}
        {error && <p className={styles.statusWarning}>Error: {error}</p>}

        {/* Added back real-time transcription display */}
        {transcriptionSegments && (
          <div className={styles.transcriptionSection}>
            <h2>Real-Time Transcription:</h2>
            <div className={styles.transcriptionText}>
              {transcriptionSegments.map((segment, index) => (
                <TranscriptionSegmentCard
                  key={index} // Include the counter in the key
                  text={segment.text}
                  start={segment.start}
                  end={segment.end}
                />
              ))}
            </div>
          </div>
        )}

        {/* Display for real time speech transcription */}
        <div>
          <h2>Socket ID: {socketId}</h2>
          <p>Connection Status: {connectionStatus}</p>
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
