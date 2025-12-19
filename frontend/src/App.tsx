import { useState, useCallback, useEffect, useRef } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
  useRoomContext,
  useLocalParticipant,
} from "@livekit/components-react";
import { RoomEvent, Participant } from "livekit-client";
import type { TranscriptionSegment } from "livekit-client";
import "@livekit/components-styles";

const TOKEN_SERVER = import.meta.env.VITE_TOKEN_SERVER_URL || "http://localhost:8080";

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

type Message = {
  id: string;
  sender: "user" | "agent";
  text: string;
  timestamp: Date;
  isFinal: boolean;
};

// Live transcript component- shows conversation as it happens.
function LiveTranscript({ messages }: { messages: Message[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages come in
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
        <p>Start talking - your conversation will appear here</p>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-2 ${
              msg.sender === "user"
                ? "bg-emerald-600 text-white rounded-br-sm"
                : "bg-slate-700 text-slate-100 rounded-bl-sm"
            } ${!msg.isFinal ? "opacity-70" : ""}`}
          >
            <p className="text-sm leading-relaxed">{msg.text}</p>
            <p className={`text-xs mt-1 ${msg.sender === "user" ? "text-emerald-200" : "text-slate-400"}`}>
              {msg.sender === "user" ? "You" : "CodeCoach"} • {formatTime(msg.timestamp)}
              {!msg.isFinal && " •••"}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

// main voice UI component- visualizer + transcript side by side.
// captures both user & agent speech in real-time.
function VoiceAssistantUI() {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isMuted, setIsMuted] = useState(false);

  // Mic toggle - lets user mute when needed
  const toggleMic = async () => {
    if (!localParticipant) return;
    const newMuted = !isMuted;
    await localParticipant.setMicrophoneEnabled(!newMuted);
    setIsMuted(newMuted);
  };

  // subscribes to transcription events from the room
  useEffect(() => {
    if (!room) return;
    
    const handleTranscription = (
      segments: TranscriptionSegment[],
      participant?: Participant
    ) => {
      // figures out if this is from user or agent
      const isAgent = participant?.identity?.includes("agent") ?? false;
      const sender = isAgent ? "agent" : "user";
      
      segments.forEach((seg) => {
        const segId = `${sender}-${seg.id}`;
        
        setMessages(prev => {
          // updates existing or adds new
          const existingIdx = prev.findIndex(m => m.id === segId);
          
          if (existingIdx >= 0) {
            // updates in place (transcript might be streaming)
            const updated = [...prev];
            updated[existingIdx] = {
              ...updated[existingIdx],
              text: seg.text,
              isFinal: seg.final,
            };
            return updated;
          }
          
          // skips empty segments
          if (!seg.text.trim()) return prev;
          
          // adds new message
          return [...prev, {
            id: segId,
            sender: sender as "user" | "agent",
            text: seg.text,
            timestamp: new Date(),
            isFinal: seg.final,
          }];
        });
      });
    };
    
    room.on(RoomEvent.TranscriptionReceived, handleTranscription);
    return () => {
      room.off(RoomEvent.TranscriptionReceived, handleTranscription);
  };
  }, [room]);
  
  // also grabs from agentTranscriptions hook as backup
  useEffect(() => {
    if (!agentTranscriptions || agentTranscriptions.length === 0) return;
    
    agentTranscriptions.forEach((seg, idx) => {
      const segId = `agent-${seg.id || idx}`;
      
      setMessages(prev => {
        const existingIdx = prev.findIndex(m => m.id === segId);
        if (existingIdx >= 0) {
          const updated = [...prev];
          updated[existingIdx] = {
            ...updated[existingIdx],
            text: seg.text,
            isFinal: seg.final ?? true,
          };
          return updated;
        }
        
        if (!seg.text.trim()) return prev;
        
        return [...prev, {
          id: segId,
          sender: "agent" as const,
          text: seg.text,
          timestamp: new Date(seg.firstReceivedTime || Date.now()),
          isFinal: seg.final ?? true,
        }];
      });
    });
  }, [agentTranscriptions]);
  
  // status indicator colors
  const statusConfig = {
    listening: { bg: "bg-green-500/20", text: "text-green-400", dot: "bg-green-400", label: "Listening..." },
    thinking: { bg: "bg-yellow-500/20", text: "text-yellow-400", dot: "bg-yellow-400", label: "Thinking..." },
    speaking: { bg: "bg-blue-500/20", text: "text-blue-400", dot: "bg-blue-400", label: "Speaking..." },
    connecting: { bg: "bg-slate-500/20", text: "text-slate-400", dot: "bg-slate-400", label: "Connecting..." },
  };
  const status = statusConfig[state as keyof typeof statusConfig] || statusConfig.connecting;
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
        <div>
          <h1 className="text-xl font-bold text-white">CodeCoach</h1>
          <p className="text-slate-400 text-xs">Your interview prep buddy</p>
        </div>
        <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
          <span className={`w-2 h-2 rounded-full mr-2 animate-pulse ${status.dot}`}></span>
          {status.label}
        </span>
      </div>

      <div className="flex justify-center py-4 border-b border-slate-700/50">
        <div className="w-48 h-16">
          <BarVisualizer state={state} barCount={5} trackRef={audioTrack} className="w-full h-full" />
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-slate-800/30">
        <div className="px-4 py-2 border-b border-slate-700/50">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Live Transcript</span>
        </div>
        <LiveTranscript messages={messages} />
      </div>

      <div className="border-t border-slate-700 p-4 flex items-center justify-between">
        <div className="text-xs text-slate-500">
          {messages.length > 0 ? `${messages.length} messages` : "Speak to begin"}
        </div>
        <div className="flex items-center gap-3">
          {/* Mic mute/unmute */}
          <button
            onClick={toggleMic}
            className={`p-2.5 rounded-lg transition-colors ${
              isMuted 
                ? "bg-red-600 hover:bg-red-700 text-white" 
                : "bg-slate-700 hover:bg-slate-600 text-slate-300"
            }`}
            title={isMuted ? "Unmute mic" : "Mute mic"}
          >
            {isMuted ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            )}
          </button>
          <DisconnectButton className="!bg-red-600 hover:!bg-red-700 !text-white !font-semibold !py-2.5 !px-6 !rounded-lg !text-sm transition-colors !shadow-md !opacity-100">
          End Call
        </DisconnectButton>
        </div>
      </div>
    </div>
  );
}


// main app component- handles token fetching & LiveKit connection
function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const livekitUrl = import.meta.env.VITE_LIVEKIT_URL || "";

  const handleConnect = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // generates unique room & identity
      const room = `codecoach-${Date.now()}`;
      const identity = `user-${Math.random().toString(36).slice(2, 8)}`;
      
      const res = await fetch(`${TOKEN_SERVER}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room, identity }),
      });
      
      if (!res.ok) throw new Error(`Token error: ${res.status}`);
      
      const data = await res.json();
      setToken(data.token);
      setIsConnected(true);
    } catch (err) {
      console.error(err);
      setError("Connection failed. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = useCallback(() => {
    setIsConnected(false);
    setToken(null);
  }, []);

  // pre-connection screen- shows welcome message & features
  if (!isConnected || !token) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          <div className="mb-8">
            <div className="w-20 h-20 bg-emerald-500 rounded-2xl mx-auto mb-4 flex items-center justify-center">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">CodeCoach</h1>
            <p className="text-slate-400">AI Interview Prep</p>
          </div>

          <div className="bg-slate-800 rounded-xl p-6 mb-6 text-left">
            <h2 className="text-white font-semibold mb-3">What I can help with:</h2>
            <ul className="space-y-2 text-slate-300 text-sm">
              <li className="flex items-center">
                <span className="text-emerald-400 mr-2">✓</span>
                Arrays & Strings concepts (from Cracking the Coding Interview book)
              </li>
              <li className="flex items-center">
                <span className="text-emerald-400 mr-2">✓</span>
                Practice problems by difficulty
              </li>
              <li className="flex items-center">
                <span className="text-emerald-400 mr-2">✓</span>
                Algorithm walkthroughs
              </li>
            </ul>
            <div className="mt-4 pt-3 border-t border-slate-700">
              <p className="text-slate-400 text-xs">
                💬 Live transcript included - see our convo in real-time
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleConnect}
            disabled={isLoading}
            className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-600 text-white font-semibold py-4 px-6 rounded-xl transition-colors"
          >
            {isLoading ? "Connecting..." : "Start Call"}
          </button>

          <p className="text-slate-500 text-xs mt-4">
            Make sure your microphone is enabled
          </p>
        </div>
      </div>
    );
  }

  // connected - shows voice UI
  return (
    <div className="min-h-screen bg-slate-900">
      <LiveKitRoom
        serverUrl={livekitUrl}
        token={token}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={handleDisconnect}
        onError={(e) => { setError(e.message); handleDisconnect(); }}
        className="h-screen flex flex-col"
      >
        <RoomAudioRenderer />
        <div className="flex-1 max-w-2xl mx-auto w-full">
          <VoiceAssistantUI />
        </div>
      </LiveKitRoom>
    </div>
  );
}

export default App;