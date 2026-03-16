# Project Plan — Personalized Learning Platform

## Tech Stack
- **Runtime**: Python 3.11+
- **Package Manager**: uv
- **AI/Agent Framework**: Google ADK (Agent Development Kit)
- **Model**: gemini-3-flash-preview
- **Deployment**: Vertex AI Agent Engine (via `adk deploy agent_engine`)
- **Local Dev**: `adk web` (ADK built-in web UI)

## Architecture

### Agent Topology
Root agent (`learning_tutor`) orchestrates 3 sub-agents:

| Agent | Responsibility |
|---|---|
| **Assessment Agent** | Drives the 3–5 turn onboarding chat to clarify the user's goal, surface prior knowledge, and produce a structured user context object |
| **Curriculum Agent** | Takes the user context and generates a 4–6 step structured curriculum with resources |
| **Quiz Agent** | Generates 3 MCQ questions per step, evaluates answers, and produces revision hints on failure |

### Tools
| Tool | Description |
|---|---|
| **Web Fetcher** | Fetches and extracts content from webpages relevant to the user's learning topic, used by the Curriculum Agent to provide curated resources |

### Project Structure
```
src/
  learning_agent/
    __init__.py
    agent.py                # Root agent + sub-agents (assessment, curriculum, quiz)
    agent_engine_app.py     # Vertex AI Agent Engine deployment wrapper
    requirements.txt        # Vertex deploy dependencies
    tools/
      __init__.py
      web_fetcher.py        # Webpage content extraction tool
pyproject.toml              # uv project config + dependencies
specs/                      # Feature specifications
```

## Implementation Phases

### Phase 1 — Spec 01: User Profile & Assessment
- Root agent greets and collects profile info
- Assessment sub-agent with 3–5 turn conversation
- User context extraction as structured JSON

### Phase 2 — Spec 02: Curriculum Generation & Content
- Curriculum sub-agent with structured JSON output
- Web Fetcher tool for resource verification
- Step-by-step learning path generation

### Phase 3 — Spec 03: Quiz & Adaptive Progression
- Quiz sub-agent with MCQ generation
- Answer evaluation and pass/fail logic (2/3 threshold)
- Revision hint generation on failure
- Step progression on pass

## Future Work
- [ ] **Authentication & accounts** — Firebase Auth / OAuth2
- [ ] **Persistent state** — Database-backed user progress across sessions
- [ ] **Profile editing/deletion**
- [ ] **Multiple concurrent learning goals**
- [ ] **Quiz attempt history tracking**
- [ ] **Spaced repetition scheduling**
- [ ] **Mobile-responsive frontend**
