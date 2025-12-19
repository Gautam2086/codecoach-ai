# CodeCoach - Voice Interview Prep Agent

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![LiveKit](https://img.shields.io/badge/LiveKit-Voice_AI-00DC82?logo=webrtc&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![Deepgram](https://img.shields.io/badge/Deepgram-STT-13EF93?logo=audio&logoColor=black)
![FAISS](https://img.shields.io/badge/FAISS-RAG-blue)

A voice-based interview preparation assistant built with LiveKit. Talk through algorithms, get practice problems, and have real discussions about optimization strategies.

## Why I Built This

I've been solving DSA problems for years (1200+ on LeetCode) - not just for interviews, but because I genuinely enjoy them. There's something satisfying about finding the optimal solution to a hard problem. It's like solving puzzles.

But here's the thing: when you're stuck on an optimization or want to talk through an approach, you usually have to type it all out in ChatGPT or search through forums. I wanted something more natural - like having a conversation with a senior engineer friend who can discuss time complexity, walk through approaches, and suggest practice problems.

That's CodeCoach. I can literally just say "hey, what's a better way to solve this?" and have a back-and-forth discussion instead of typing everything out.

**Persona**: Supportive senior engineer friend - encouraging, practical, keeps it concise for voice.

## Live Demo

**Try it**: *Coming soon*

**Video Demo**: *Coming soon*

## Architecture

```
┌─────────────────────────────────────────────────┐
│         React Frontend (Vercel)                  │
│  [Start Call] [Live Transcript] [End Call]      │
└─────────────────────────────────────────────────┘
                      │ WebSocket
                      ▼
┌─────────────────────────────────────────────────┐
│            LiveKit Cloud                         │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│      Python Voice Agent (Render)                 │
│  Deepgram(STT) → GPT-4o-mini → ElevenLabs(TTS) │
│                    ↓                             │
│           RAG: FAISS + LangChain                │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Why I chose it |
|-----------|------------|----------------|
| Voice | LiveKit Cloud | Required for real-time audio |
| STT | Deepgram | Fast and accurate transcription |
| LLM | GPT-4o-mini | Quick responses needed for voice |
| TTS | ElevenLabs (OpenAI fallback) | Natural sounding voice |
| RAG | LangChain + FAISS | In-memory, no DB setup needed |
| Embeddings | OpenAI text-embedding-3-small | Fast API calls, no local model to load |
| Frontend | React + TypeScript + Tailwind | Clean, modern stack |

## What it does

- **Voice conversation**: Talk naturally about coding interview topics
- **Live transcript**: See the conversation in real-time as you speak
- **RAG-powered answers**: Retrieves relevant info from CTCI chapter
- **Practice problems**: Say "give me a medium array problem" and it fetches one
- **Observability**: Logs every RAG retrieval with chunk IDs and scores

## Design Decisions

**Why OpenAI embeddings instead of HuggingFace?**  
I actually started with HuggingFace `all-MiniLM-L6-v2` since it's free and runs locally. But I kept hitting issues:
- The model download (~90MB) was blocking the agent startup
- LiveKit's prewarm phase has a timeout, and loading the model took too long
- Tried pre-building the FAISS index separately, but the download kept hanging

Ended up switching to OpenAI `text-embedding-3-small`. It's API-based so there's no model to download - just makes a quick API call. Initialization went from 60+ seconds to about 2 seconds. Small cost trade-off but totally worth it for the UX.

**macOS FAISS fix**  
Ran into a weird crash on macOS - `libomp.dylib already initialized`. Turns out FAISS and some other libs both try to load OpenMP. Fixed it by setting `KMP_DUPLICATE_LIB_OK=TRUE` at the top of the agent. Took a bit of googling to figure that one out.

**Pre-built FAISS index**  
Initially had the FAISS index in `.gitignore`. Realized anyone cloning would have to rebuild it before running. Removed it from gitignore and committed the pre-built index - now it's clone and run.

**Why FAISS over ChromaDB?**  
FAISS loads from a file and runs in-memory. Cloud platforms with ephemeral disks can cause issues with ChromaDB. Simpler is better here.

**Why single CTCI chapter?**  
One chapter with precise retrieval beats the whole book with noisy results.

**Why chunk size 500?**  
Smaller chunks = more precise retrieval. Voice responses should be concise anyway.

**Why observability logging?**  
Good observability matters when debugging AI systems:
```
Query: 'what is the time complexity of hash table lookup'
  #1 chunk=chunk_12 page=5 score=0.823
  #2 chunk=chunk_15 page=6 score=0.756
```

## Setup

The FAISS index is pre-built, so you just need to add your API keys and run.

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your LiveKit, OpenAI, Deepgram keys

# Terminal 1 - token server
python token_server.py

# Terminal 2 - voice agent
python agent.py dev
```

### 2. Frontend

```bash
cd frontend
npm install

# Copy and fill in env
cp .env.example .env

npm run dev
```

### 3. Open the app

Go to `http://localhost:5173` and click "Start Call"

### Environment Variables

Backend `.env`:
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
OPENAI_API_KEY=...
DEEPGRAM_API_KEY=...

# Optional
ELEVENLABS_API_KEY=...
USE_ELEVENLABS=true
ENABLE_RAG=true
```

Frontend `.env`:
```
VITE_LIVEKIT_URL=wss://your-project.livekit.cloud
VITE_TOKEN_SERVER_URL=http://localhost:8080
```

## Project Structure

```
├── backend/
│   ├── agent.py        # Voice agent entry point
│   ├── rag.py          # FAISS + LangChain RAG pipeline
│   ├── tools.py        # get_practice_problems tool
│   ├── prompts.py      # CodeCoach system prompt
│   ├── token_server.py # JWT token endpoint
│   ├── start.sh        # Combined startup script for deployment
│   ├── .env.example    # Environment variables template
│   └── data/           # CTCI PDF + FAISS index
├── frontend/
│   ├── src/App.tsx     # React UI
│   └── .env.example    # Environment variables template
└── README.md
```

## Deployment

Deployed on Render (backend) + Vercel (frontend). Start script: `backend/start.sh`.
