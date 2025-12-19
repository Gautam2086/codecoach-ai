"""
CodeCoach - Voice-based interview prep agent.
Uses LiveKit Agents SDK with Deepgram STT, OpenAI LLM & ElevenLabs TTS.

Docs: https://docs.livekit.io/agents/start/voice-ai/
"""

import asyncio
import logging
import os

# Fix for macOS OpenMP conflict with FAISS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import deepgram, openai, elevenlabs, silero

from prompts import SYSTEM_PROMPT
from rag import get_rag_pipeline
from tools import get_practice_problems

load_dotenv()

# ElevenLabs plugin expects ELEVEN_API_KEY env var
# https://github.com/elevenlabs/cli
if os.getenv("ELEVENLABS_API_KEY") and not os.getenv("ELEVEN_API_KEY"):
    os.environ["ELEVEN_API_KEY"] = os.getenv("ELEVENLABS_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codecoach")

_rag = None     # Singleton RAG pipeline


class CodeCoachAgent(Agent):
    # Custom agent that injects RAG context on each user turn.
    
    def __init__(self, *, rag=None, **kwargs):
        super().__init__(**kwargs)
        self._rag = rag
    
    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        # Injecting relevant CTCI context before LLM generates response
        await super().on_user_turn_completed(turn_ctx, new_message)
        
        if not self._rag or not self._rag.is_initialized:
            return
        
        query = (new_message.text_content or "").strip()
        if not query:
            return
        
        # Running retrieval in thread pool (FAISS is sync)
        try:
            context = await asyncio.to_thread(self._rag.get_context_for_llm, query)
        except Exception as e:
            logger.error(f"RAG error: {e}")
            return
        
        if context:
            turn_ctx.add_message(role="developer", content=context)


def prewarm(proc: JobProcess):
    # Loading RAG here so it's ready before any calls come in
    global _rag
    use_rag = os.getenv("ENABLE_RAG", "false").lower() == "true"
    
    if use_rag:
        try:
            logger.info("Loading RAG pipeline...")
            _rag = get_rag_pipeline()
            logger.info("RAG ready")
        except Exception as e:
            logger.error(f"RAG init failed: {e}")
            _rag = None
    
    logger.info("Agent ready")


async def entrypoint(ctx: JobContext):
    logger.info(f"Joining room: {ctx.room.name}")
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    # Waiting for participant to join the room
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant: {participant.identity}")
    
    # TTS setup: ElevenLabs or OpenAI fallback
    use_eleven = os.getenv("USE_ELEVENLABS", "false").lower() == "true"
    if use_eleven and os.getenv("ELEVEN_API_KEY"):
        logger.info("TTS: ElevenLabs")
        tts = elevenlabs.TTS(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
            model="eleven_monolingual_v1",
        )
    else:
        logger.info("TTS: OpenAI")
        tts = openai.TTS(voice="alloy")
    
    # Creating agent with tool support
    agent = CodeCoachAgent(
        instructions=SYSTEM_PROMPT,
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=tts,
        vad=silero.VAD.load(),
        tools=[get_practice_problems],
        rag=_rag,
    )
    
    # Starting the agent session
    session = AgentSession()
    await session.start(room=ctx.room, agent=agent)
    
    logger.info("Agent started")
    
    # Greeting the participant
    await session.say(
        "Hey! I'm CodeCoach, your interview prep buddy. "
        "Ask me about arrays, strings, hash tables, or say 'give me a problem' to practice. "
        "What would you like to work on?"
    )
    
    # Keeping the agent alive until the participant disconnects
    done = asyncio.Event()
    ctx.room.on("disconnected")(lambda: done.set())
    await done.wait()
    
    logger.info("Session ended")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
