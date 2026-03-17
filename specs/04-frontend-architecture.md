# Spec: Frontend Architecture

## Design Decisions

| # | Decision |
|---|---|
| 1 | **Dedicated API endpoints** — each page feature gets its own endpoint instead of routing everything through `/api/chat`. |
| 2 | **Free navigation** — users can visit any page at any time; content is driven by user choice. |
| 3 | **Code lab** — interactive sandbox with language selector and server-side execution via sandboxed subprocess (5s timeout, resource limits). |
| 4 | **Dashboard** — real progress from localStorage, zero-state for new users. |
| 5 | **localStorage only** — no backend database for now. All keys prefixed `eduai.`. |
| 6 | **Auth deferred** — cookie-based UUID identity. |
| 7 | **Full agent quiz integration** — agent generates questions AND evaluates answers server-side. |

## Tech Stack

- **Runtime**: Python 3.11+, uv
- **AI/Agent**: Google ADK, gemini-2.5-flash
- **Server**: FastAPI + Jinja2
- **Frontend**: Vanilla JS + Tailwind CSS
- **State**: localStorage (client-side)

## localStorage Schema

```
eduai.sessionContext     → { name, experience_level, learning_goal, key_prior_knowledge[], confirmed_focus }
eduai.assessmentComplete → true | false
eduai.curriculum         → { steps: [{ order, title, overview, resources[] }] }
eduai.currentStep        → number (index of current step, default 0)
eduai.stepsCompleted     → number[] (indices of passed steps)
eduai.quizResult         → { stepIndex, score, total, passed, answers[], timestamp }
eduai.quizHistory        → [ { stepIndex, score, total, passed, timestamp } ]
eduai.progress           → { lessonsCompleted, totalLessons, quizzesPassed, quizzesFailed }
eduai.codeLanguage       → string (last selected language)
```

## API Endpoints

### Existing

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat` | SSE streaming chat with root agent |
| POST | `/api/new-profile` | Clear session + cookie |
| POST | `/api/reset-progression` | Reset session |

### Planned

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/curriculum/generate` | Generate learning path from user context |
| POST | `/api/resources` | Get resources for a specific step |
| POST | `/api/quiz/generate` | Generate 3 MCQs for a step |
| POST | `/api/quiz/evaluate` | Evaluate quiz answers |
| POST | `/api/code/execute` | Execute user code in sandbox |

## Code Execution Security

- Allowlisted languages: Python, JavaScript, TypeScript
- 5-second timeout, `subprocess.run(shell=False)`
- Max 10,000 chars input, 50KB stdout/stderr
- No dangerous imports (`os`, `subprocess`, `sys`, `shutil`, `socket`)
- Isolated temp directory per execution, cleaned after
- Resource limits via `ulimit`

## Future Work

- Authentication (Firebase Auth / OAuth2)
- Persistent state (database-backed progress)
- Quiz attempt history and spaced repetition
- Docker-based code execution sandbox
- Mobile app
