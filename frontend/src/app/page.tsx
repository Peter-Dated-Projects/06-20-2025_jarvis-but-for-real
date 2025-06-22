"use client";

import { useEffect, useState } from "react";
import io, { type Socket } from "socket.io-client";
import { MessageCircle, Mic, Wifi, WifiOff, Send } from "lucide-react";
// Remove the CSS module import since you're using regular CSS
// import "./page.module.css"

const BACKEND_URL = "http://localhost:5001";

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

function TranscriptionSegmentCard({
	text,
	start,
	end,
}: TranscriptionSegmentCardProps) {
	return (
		<div className="transcription-card">
			<p className="transcription-text">{text}</p>
			<div className="transcription-time">
				<span>Start: {start}s</span>
				<span>End: {end}s</span>
			</div>
		</div>
	);
}

export default function Home() {
	const [messages, setMessages] = useState<
		{ text: string; timestamp: string; sender: string }[]
	>([]);
	const [currentMessage, setCurrentMessage] = useState("");
	const [socket, setSocket] = useState<Socket | null>(null);
	const [socketId, setSocketId] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [connectionStatus, setConnectionStatus] =
		useState<string>("disconnected");
	const [transcriptionSegments, setTranscriptionSegments] = useState<
		TranscriptionSegmentCardProps[]
	>([]);

	useEffect(() => {
		console.log("Creating first object to test");

		setTranscriptionSegments([
			{
				text: "This is a test transcription segment.",
				start: 0,
				end: 5,
			},
		]);

		console.log(
			"Connecting to socket at:",
			`${BACKEND_URL}/propagate_whisper_events`
		);
		const socket_url = `${BACKEND_URL}/propagate_whisper_events`;
		const propagateSocket = io(socket_url, {
			reconnectionAttempts: 5,
			reconnectionDelay: 1000,
			transports: ["websocket"],
		});

		propagateSocket.on("confirm_connect", (data) => {
			console.log("Socket connected:", data.sid);
			setSocket(propagateSocket);
			setSocketId(data.sid);
			setConnectionStatus("connected");
			setError(null);
		});

		propagateSocket.on("status_update", (data) => {
			console.log("Status update:", data.status);
			setConnectionStatus(data.status);
			if (data.status === "active") {
				// reset the transcription segments when the connection is active
				setTranscriptionSegments([]);
			}

			if (data.status === "connection_error") {
				setError(
					"Connection error occurred. Please check the console for details."
				);
			} else {
				setError(null);
			}
		});

		propagateSocket.on("segment_update", (data: TranscriptionSegment) => {
			console.log("Segment update received:", data);

			setTranscriptionSegments((prevSegments) => {
				if (prevSegments.length === 0)
					return [
						{
							text: data.transcription,
							start: data.start_time,
							end: data.end_time,
						},
					];
				const lastIndex = prevSegments.length - 1;
				const updatedSegments = [...prevSegments];
				updatedSegments[lastIndex] = {
					text: data.transcription,
					start: data.start_time,
					end: data.end_time,
				};
				return updatedSegments;
			});
		});

		propagateSocket.on("segment_creation", (data: TranscriptionSegment) => {
			console.log("Segment creation event received:", data);
			setTranscriptionSegments((prevSegments) => [
				...prevSegments,
				{
					text: data.transcription,
					start: data.start_time,
					end: data.end_time,
				},
			]);
		});

		propagateSocket.on("gemini_response", (data) => {
			console.log("Gemini response received:", data);

			// receive file + play it
			fetch(`${BACKEND_URL}/whispercore/get_audio`)
				.then((response) => {
					if (!response.ok) {
						throw new Error("Network response was not ok");
					}
					return response.blob();
				})
				.then((audioBlob) => {
					const audioUrl = URL.createObjectURL(audioBlob);
					const audio = new Audio(audioUrl);
					audio.play().catch((error) => {
						console.error("Error playing audio:", error);
					});
				})
				.catch((error) => {
					console.error("Error fetching audio:", error);
				});
		});

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

		return () => {
			if (propagateSocket.connected) {
				propagateSocket.disconnect();
			}
		};
	}, []);

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

	useEffect(() => {
		console.log("Transcription segments updated:", transcriptionSegments);
	}, [transcriptionSegments]);

	return (
		<div className="app-container">
			<div className="background-decoration"></div>

			<div className="main-content">
				{/* Header */}
				<div className="header">
					<h1 className="main-title">S.O.N.A.</h1>
					<p className="subtitle">
						Sentiment Operational & Natural Assistant
					</p>
					<p>
						A real-time transcription tool for seamless
						communication and live updates
					</p>
				</div>

				{/* Status Bar */}
				<div className="status-bar">
					<div className="status-content">
						<div className="connection-status">
							{connectionStatus === "active" ||
							connectionStatus === "connected" ? (
								<div className="status-connected">
									<Wifi className="status-icon" />
									<span className="status-text">
										{connectionStatus === "active"
											? "Recording..."
											: "Connected"}
									</span>
								</div>
							) : (
								<div className="status-disconnected">
									<WifiOff className="status-icon" />
									<span className="status-text">
										{connectionStatus === "disconnected"
											? "Connecting..."
											: "Connection Error"}
									</span>
								</div>
							)}
						</div>
						{socketId && (
							<div className="socket-id">
								Socket ID:{" "}
								<span className="socket-id-value">
									{socketId}
								</span>
							</div>
						)}
					</div>
					{error && <div className="error-message">{error}</div>}
				</div>

				<div className="content-grid">
					{/* Transcription Section */}
					<div className="section-card transcription-section">
						<div className="section-header">
							<div className="section-icon transcription-icon">
								<Mic className="icon" />
							</div>
							<h2 className="section-title">
								Live Transcription
							</h2>
						</div>

						<div className="transcription-container">
							{transcriptionSegments.map((segment, index) => (
								<TranscriptionSegmentCard
									key={index}
									text={segment.text}
									start={segment.start}
									end={segment.end}
								/>
							))}
						</div>
					</div>

					{/* Messages Section */}
					<div className="section-card messages-section">
						<div className="section-header">
							<div className="section-icon messages-icon">
								<MessageCircle className="icon" />
							</div>
							<h2 className="section-title">Messages</h2>
						</div>

						{/* Message Input */}
						<div className="message-input-container">
							<input
								type="text"
								value={currentMessage}
								onChange={(e) =>
									setCurrentMessage(e.target.value)
								}
								placeholder="Type your message..."
								className="message-input"
								onKeyPress={(event) => {
									if (event.key === "Enter") {
										handleSendMessage();
									}
								}}
							/>
							<button
								onClick={handleSendMessage}
								disabled={!socket || !socket.connected}
								className="send-button"
							>
								<Send className="send-icon" />
								Send
							</button>
						</div>

						{/* Messages Display */}
						<div className="messages-display">
							{messages.length === 0 ? (
								<div className="no-messages">
									<MessageCircle className="no-messages-icon" />
									<p>
										No messages yet. Start a conversation!
									</p>
								</div>
							) : (
								<div className="messages-list">
									{messages.map((msg, index) => (
										<div
											key={index}
											className={`message-item ${
												index % 2 === 0
													? "message-even"
													: "message-odd"
											}`}
										>
											<div className="message-header">
												<span className="message-sender">
													{msg.sender}
												</span>
												<span className="message-timestamp">
													{msg.timestamp}
												</span>
											</div>
											<p className="message-text">
												{msg.text}
											</p>
										</div>
									))}
								</div>
							)}
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
