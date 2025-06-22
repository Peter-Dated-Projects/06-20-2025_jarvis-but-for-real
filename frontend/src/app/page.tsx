"use client";

import { useEffect, useState, useRef } from "react";
import io, { Socket } from "socket.io-client";
import styles from "./page.module.css";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001";

interface TranscriptionSegment {
  text: string;
  start: number;
  end: number;
}

function TranscriptionSegmentCard({ text, start, end }: TranscriptionSegment) {
  return (
    <div className={styles.transcriptionSegmentCard}>
      <p className={styles.transcriptionSegmentText}>{text}</p>
      <p className={styles.transcriptionSegmentTime}>
        {start} - {end}
      </p>
    </div>
  );
}

export default function Home() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<{ text: string; timestamp: string; sender: string }[]>(
    []
  );
  const [currentMessage, setCurrentMessage] = useState("");
  const [socketId, setSocketId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const [error, setError] = useState<string | null>(null);

  // Added back for real-time transcription
  const [isRealTimeSTT, setIsRealTimeSTT] = useState(false);
  const [transcriptionSegments, setTranscriptionSegments] = useState<TranscriptionSegment[]>([]);

  useEffect(() => {
    console.log("Creating first object to test");
    setTranscriptionSegments([
      {
        text: "This is a test transcription segment.",
        start: 0,
        end: 5,
      },
      {
        text: "ADL WAHDLWAH",
        start: 5,
        end: 23,
      },
    ]);

    // Initialize socket connection to the streaming namespace
    const newSocket = io(BACKEND_URL + "/streaming", {
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ["websocket"],
    });

    // Set up socket event listeners
    newSocket.on("connect", (data) => {
      console.log("Socket connected:", data.sid);
      setSocket(newSocket);
      setSocketId(data.sid);
      setConnectionStatus("connected");
      setError(null);
    });

    // handles real time stt enable signal
    newSocket.on("real_time_stt_enable", (data) => {
      console.log("Real-time STT enabled");
      setIsRealTimeSTT(true);
    });

    // handles real time stt disable signal
    newSocket.on("real_time_stt_disable", (data) => {
      console.log("Real-time STT disabled");
      setIsRealTimeSTT(false);
      setTranscriptionSegments([]); // Clear transcription segments when disabled
    });

    // handles Real time stt message updates
    newSocket.on("real_time_stt_segment_update", (data) => {
      if (data.segment) {
        // check length of array
        const length = transcriptionSegments.length;

        if (length == 0) {
          // error
          console.error("Received empty segment data");
          return;
        }

        // update the last item
        const lastSegment = transcriptionSegments[length - 1];
        lastSegment.text = data.segment.text;
        lastSegment.start = data.segment.start;
        lastSegment.end = data.segment.end;

        // update the state
        setTranscriptionSegments((prev) => {
          const updatedSegments = [...prev];
          updatedSegments[length - 1] = lastSegment;
          return updatedSegments;
        });
      }
    });

    // handles real time stt new messages
    newSocket.on("real_time_stt_new_message", (data) => {
      if (data.message) {
        // Add the new message to the transcription segments
        const newSegment: TranscriptionSegment = {
          text: data.message.text,
          start: data.message.start,
          end: data.message.end,
        };
        setTranscriptionSegments((prev) => [...prev, newSegment]);

        // Update real-time transcription display
        setIsRealTimeSTT(true);
      }
    });

    // Handle errors
    newSocket.on("error", (error) => {
      console.error("Socket error:", error);
      setError(error.message || "An error occurred");
    });

    newSocket.on("disconnect", (reason) => {
      console.log("Socket disconnected:", reason);
      setSocket(null);
      setSocketId(null);
      setConnectionStatus("disconnected");
    });

    // Cleanup on component unmount
    return () => {
      if (newSocket.connected) {
        newSocket.disconnect();
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
            <h2>Real-time Transcription:</h2>
            <p className={styles.transcriptionText}>
              {transcriptionSegments.map((segment) => (
                <TranscriptionSegmentCard
                  key={segment.start}
                  start={segment.start}
                  end={segment.end}
                  text={segment.text}
                />
              ))}
            </p>
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
