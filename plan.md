# Project Plan — Frontend Rewrite

> **Goal**: Replace the hardcoded mockup frontend with a fully dynamic,
> agent-connected UI where every page is driven by real user interaction
> and agent output. All state persists in localStorage.

---

## Design Decisions (confirmed)

| # | Decision |
|---|---|
| 1 | **Multiple dedicated API endpoints** — each page feature gets its own endpoint (`/api/curriculum`, `/api/quiz/generate`, `/api/quiz/evaluate`, `/api/resources`, `/api/code/execute`) instead of routing everything through `/api/chat`. |
| 2 | **Free navigation** — users can visit any page at any time, but content is driven by user choice (e.g. user picks quiz topic, picks which step to view resources for). |
| 3 | **Code lab** — interactive sandbox with language selector buttons, an example pane, and a secure terminal where users can write and run code. Server-side execution via a sandboxed subprocess with strict timeouts and resource limits. |
| 4 | **Dashboard** — shows real progress for the current user. Starts at zero. All progress stored in localStorage and survives page navigation/refresh. |
| 5 | **Resources** — pulled dynamically from the curriculum agent based on the user's chosen topic/step. |
| 6 | **localStorage only** — no backend database for now. |
| 7 | **Auth deferred** — keep cookie-based UUID identity. |
| 8 | **Full agent quiz integration** — agent generates questions AND evaluates answers. No client-side answer checking. |

---

## Tech Stack

- **Runtime**: Python 3.11+
- **Package Manager**: uv
- **AI/Agent Framework**: Google ADK (Agent Development Kit)
- **Model**: gemini-2.5-flash
- **Server**: FastAPI + Jinja2 templates
- **Frontend**: Vanilla JS + Tailwind CSS (no framework)
- **State**: localStorage (client-side)
- **Code Execution**: Server-side sandboxed subprocess (Python, JS, etc.)

---

## Current State (what exists)

### Backend (✅ solid, needs new endpoints)
- Root agent orchestrates 3 sub-agents (assessment, curriculum, quiz)
- All agents produce structured JSON
- Single `/api/chat` SSE endpoint works end-to-end
- Session management via in-memory dict + cookie
- 163 tests passing

### Frontend (❌ mostly hardcoded mockups)

| Page | File | Status | Problem |
|---|---|---|---|
| Chat | `chat.html` | ✅ Working | Only page connected to agent. Sticker buttons have hardcoded messages. |
| Profile | `profile.html` | ⚠️ Partial | Reads localStorage but shows hardcoded fallback content. |
| Dashboard | `dashboard.html` | ❌ Hardcoded | 100% mock data (streak, level, 4/16 lessons, "AI Engineering for Frontend Devs"). |
| Roadmap | `roadmap.html` | ❌ Hardcoded | 6 static nodes (Python Foundations, LLM Architecture, etc.). Ignores curriculum agent. |
| Resources | `resources.html` | ❌ Hardcoded | Static "Mastering RAG Concepts" with 3 fixed external links. |
| Code | `code.html` | ❌ Hardcoded | Static exercise "Prompt Template Refactor". No real execution. |
| Quiz | `quiz.html` | ❌ Hardcoded | 3 fixed questions with client-side evaluation. Ignores quiz agent. |
| Quiz Results | `quiz_results.html` | ⚠️ Partial | Reads localStorage quiz result, but quiz data was hardcoded upstream. |

---

## localStorage Schema

All keys prefixed with `eduai.` to avoid collisions.

```
eduai.sessionContext     → { name, experience_level, learning_goal, key_prior_knowledge[], confirmed_focus }
eduai.assessmentComplete → true | false
eduai.curriculum         → { steps: [{ order, title, overview, resources[] }] }
eduai.currentStep        → number (index of step user is currently on, default 0)
eduai.stepsCompleted     → number[] (indices of steps that have been passed)
eduai.quizResult         → { stepIndex, score, total, passed, answers[], timestamp }
eduai.quizHistory        → [ { stepIndex, score, total, passed, timestamp } ]
eduai.progress           → { lessonsCompleted, totalLessons, quizzesPassed, quizzesFailed }
eduai.codeLanguage       → string (last selected language in code lab)
```

---

## New API Endpoints

### Existing (keep as-is)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat` | SSE streaming chat with root agent |
| POST | `/api/new-profile` | Clear session + cookie |
| POST | `/api/reset-progression` | Reset session |

### New endpoints to add

| Method | Path | Request Body | Response | Purpose |
|---|---|---|---|---|
| POST | `/api/curriculum/generate` | `{ user_context: object }` | JSON `{ steps: [...] }` | Ask curriculum agent to generate learning path from user context |
| POST | `/api/resources` | `{ topic: string, step_title: string }` | JSON `{ resources: [...] }` | Ask curriculum agent for resources on a specific topic/step |
| POST | `/api/quiz/generate` | `{ step_title: string, step_overview: string }` | JSON `{ questions: [...] }` | Ask quiz agent to generate 3 MCQs for a step |
| POST | `/api/quiz/evaluate` | `{ questions: [...], answers: number[] }` | JSON `{ score, total, passed, revision_hint?, feedback }` | Ask quiz agent to evaluate answers |
| POST | `/api/code/execute` | `{ language: string, code: string }` | JSON `{ stdout, stderr, exit_code, timed_out }` | Execute user code in a sandboxed subprocess |

---

## Phased Implementation

### Phase 1 — New API Endpoints (backend)

Add 5 new endpoints to `src/app.py`. Each endpoint talks to the
appropriate agent tool directly (not through chat).

#### 1a. `/api/curriculum/generate`
- Accept `user_context` JSON from the request body
- Build a prompt: "Generate a curriculum for this user: {user_context}"
- Call the agent with `curriculum_agent` tool via `adk_app.async_stream_query`
- Parse the structured JSON from the agent response
- Return the `{ steps: [...] }` JSON

#### 1b. `/api/resources`
- Accept `{ topic, step_title }` from request body
- Build a prompt: "Suggest 3-5 learning resources for: {step_title} on the topic {topic}"
- Call the agent to get curated resources
- Return `{ resources: [...] }` JSON

#### 1c. `/api/quiz/generate`
- Accept `{ step_title, step_overview }` from request body
- Build a prompt: "Generate a quiz for this learning step: {step_title} — {step_overview}"
- Call agent with quiz tool
- Parse and return `{ questions: [...] }` JSON

#### 1d. `/api/quiz/evaluate`
- Accept `{ questions, answers }` from request body
- Build a prompt with the questions, correct answers, and user answers
- Call agent with quiz tool in evaluation mode
- Return `{ score, total, passed, revision_hint?, feedback }` JSON

#### 1e. `/api/code/execute`
- Accept `{ language, code }` from request body
- Validate language is in allowlist: `["python", "javascript", "typescript"]`
- Validate code length (max 10,000 chars)
- Execute in a sandboxed subprocess with:
  - 5-second timeout
  - No network access (if possible)
  - Restricted imports (no os, subprocess, sys for user code)
  - Captured stdout/stderr
- Return `{ stdout, stderr, exit_code, timed_out }`
- **Security**: sanitize input, prevent command injection, use subprocess with
  `shell=False`, resource limits via `ulimit` or similar

#### 1f. Tests
- Add tests for all 5 new endpoints in `tests/test_app.py`
- Mock agent calls to avoid hitting the model in tests
- Test error handling (invalid input, agent failure, timeout)

---

### Phase 2 — Dashboard Rewrite (`dashboard.html`)

**Current**: 100% hardcoded mock data
**Target**: Real progress from localStorage, zero-state for new users

#### Changes:
1. **Remove all hardcoded data**: streak, level, lesson count, quest title
2. **On page load** (`DOMContentLoaded`):
   - Read `eduai.progress` from localStorage
   - Read `eduai.sessionContext` for user name and learning goal
   - Read `eduai.curriculum` for total lessons count
   - Read `eduai.stepsCompleted` for completed count
3. **Zero state** (no assessment done):
   - Show "Welcome! Start your learning journey" hero
   - "Start Assessment" button → `/chat`
   - Progress: 0/0, no streak, no level
4. **Active state** (assessment done, curriculum exists):
   - Show user's name: "Welcome back, {name}!"
   - Learning goal as quest title
   - Progress bar: `stepsCompleted.length / curriculum.steps.length`
   - Lessons completed: `{n} of {total} steps completed`
   - Next step: title of first incomplete step
   - "Continue Learning" → `/resources?step={nextStepIndex}`
5. **Completed state** (all steps passed):
   - Celebration message
   - "Start a new learning path" button → `/chat` (triggers new assessment)
6. **Keep**: theme toggle, sidebar navigation, responsive layout, whimsical styling

---

### Phase 3 — Chat Improvements (`chat.html`)

**Current**: Working SSE chat, but sticker buttons have hardcoded user personas
**Target**: Dynamic sticker buttons, better state handling

#### Changes:
1. **Replace hardcoded sticker messages** with generic prompts:
   - "Start my learning assessment"
   - "Generate a curriculum for me"
   - "Quiz me on my current topic"
2. **After assessment completes** (state received with `assessment_complete`):
   - Auto-trigger curriculum generation via `/api/curriculum/generate`
   - Store result in `eduai.curriculum`
   - Show "Curriculum created! Visit the Roadmap to see your learning path."
3. **Status badge** in header:
   - Read assessment state from localStorage
   - Show "Assessment Pending" / "Assessment Complete" / "Learning in Progress"
4. **Keep**: SSE streaming, theme toggle, file attachment, sidebar nav

---

### Phase 4 — Roadmap Rewrite (`roadmap.html`)

**Current**: 6 hardcoded nodes (Python Foundations, LLM Architecture, etc.)
**Target**: Dynamic nodes from curriculum agent output

#### Changes:
1. **Remove all 6 hardcoded nodes**
2. **On page load**:
   - Read `eduai.curriculum` from localStorage
   - Read `eduai.stepsCompleted` from localStorage
   - If no curriculum: show empty state "Complete your assessment in chat to generate a roadmap"
3. **Render curriculum steps dynamically**:
   - Each step becomes a timeline node
   - Status derived from `stepsCompleted` array:
     - `completed` → green checkmark
     - `current` (first incomplete) → "In Progress" badge
     - `locked` → grayed out (but still clickable since navigation is free)
   - Title: `step.title`
   - Description: `step.overview`
4. **Click a step** → navigate to `/resources?step={index}`
5. **Progress sidebar**:
   - Skills acquired: `stepsCompleted.length / curriculum.steps.length`
   - Dynamic percentage bar
6. **"Resume Learning" button** → `/resources?step={firstIncompleteIndex}`
7. **Keep**: timeline connector, whimsical node icons, theme toggle, responsive layout

---

### Phase 5 — Resources Rewrite (`resources.html`)

**Current**: Hardcoded "Mastering RAG Concepts" with 3 static links
**Target**: Dynamic resources pulled from agent for selected step

#### Changes:
1. **Remove all hardcoded module content**
2. **Read URL param**: `?step={index}` to know which step to show
3. **On page load**:
   - Read `eduai.curriculum` from localStorage
   - Get the step at the given index
   - If step has resources already (from curriculum JSON): display them
   - If not, or if user wants more: call `/api/resources` endpoint
   - Show loading spinner while fetching
4. **Render dynamically**:
   - Module title: `Step {order}: {step.title}`
   - Overview: `step.overview`
   - Resource cards: from `step.resources[]`
     - Title, URL (opens in new tab), description
     - Resource type icon (article, video, documentation)
5. **"Test my Knowledge" button** → `/quiz?step={index}`
6. **"Get More Resources" button** → calls `/api/resources` with step info
7. **Step selector dropdown or tabs** at top so user can switch between steps
   without going back to roadmap
8. **Keep**: bottom navigation, theme toggle, responsive grid

---

### Phase 6 — Quiz Rewrite (`quiz.html`)

**Current**: 3 hardcoded questions with client-side answer checking
**Target**: Agent-generated questions, agent-evaluated answers

#### Changes:
1. **Remove all hardcoded questions** (`defaultQuestions` array)
2. **Read URL param**: `?step={index}` to know which step to quiz on
3. **On page load**:
   - Read `eduai.curriculum` from localStorage for step context
   - If no step param: show a step selector (user picks topic)
   - Call `POST /api/quiz/generate` with `{ step_title, step_overview }`
   - Show loading state: "Generating questions..."
   - Render questions when received
4. **Question rendering**:
   - Same UI structure (radio buttons, progress bar)
   - Questions come from agent, not hardcoded
   - Do NOT store `correct_index` on client — answers are evaluated server-side
5. **On submit all answers**:
   - Call `POST /api/quiz/evaluate` with questions and selected answer indices
   - Show loading: "Evaluating your answers..."
   - Receive `{ score, total, passed, revision_hint, feedback }`
   - Store result in `eduai.quizResult`
   - If passed: add step index to `eduai.stepsCompleted`, update `eduai.progress`
   - Redirect to `/quiz-results`
6. **Keep**: radio button styling, progress bar, whimsical icons, theme toggle

---

### Phase 7 — Quiz Results Update (`quiz_results.html`)

**Current**: Reads localStorage quiz result (partially dynamic)
**Target**: Show agent feedback, revision hints on fail

#### Changes:
1. **Read `eduai.quizResult`** from localStorage (already does this)
2. **Add revision hint display**:
   - If `passed === false` and `revision_hint` exists: show it in a
     highlighted card below the score
   - "The agent suggests: {revision_hint}"
3. **Add agent feedback**:
   - Display the `feedback` string from the evaluation response
4. **Update action buttons**:
   - Pass: "Continue to Next Step" → `/resources?step={nextStepIndex}`
   - Fail: "Review Resources" → `/resources?step={currentStepIndex}`
   - Fail: "Retry Quiz" → `/quiz?step={currentStepIndex}`
5. **Keep**: celebration animation, answer review cards, share/print, theme toggle

---

### Phase 8 — Profile/Context Update (`profile.html`)

**Current**: Reads localStorage but has lots of hardcoded fallback content
**Target**: Clean dynamic display of user context + progress summary

#### Changes:
1. **Replace hardcoded fallback text** with cleaner empty states
2. **On page load**:
   - Read `eduai.sessionContext`, `eduai.curriculum`, `eduai.stepsCompleted`
   - If no context: show "No assessment yet" with "Start Assessment" → `/chat`
3. **Display real data**:
   - Name from `sessionContext.name`
   - Level badge from `sessionContext.experience_level`
   - Learning goal from `sessionContext.learning_goal`
   - Prior knowledge tags from `sessionContext.key_prior_knowledge`
   - Focus from `sessionContext.confirmed_focus`
4. **Progress summary card**:
   - Steps completed / total from curriculum
   - Quizzes passed / failed from `eduai.progress`
5. **Keep**: "Refine Learning Goals" → `/chat`, share button, theme toggle,
   "Start From Beginning" (calls `/api/new-profile` + clears localStorage)

---

### Phase 9 — Code Lab Rewrite (`code.html`)

**Current**: Static exercise with fake "Run" that echoes text
**Target**: Interactive sandbox with language selection and real execution

#### Changes:
1. **Remove hardcoded exercise** ("Prompt Template Refactor")
2. **Language selector** (button group at top):
   - Python, JavaScript, TypeScript buttons
   - Store selection in `eduai.codeLanguage`
   - Each language loads an example starter snippet
3. **Example pane** (left sidebar or toggle):
   - Show a beginner-friendly example for the selected language
   - Related to the user's learning goal if curriculum exists
   - "Try this example" button copies it to the editor
4. **Code editor** (main area):
   - Textarea with monospace font (keep existing)
   - Syntax-aware placeholder per language
5. **"Run Code" button** (real execution):
   - `POST /api/code/execute` with `{ language, code }`
   - Show loading spinner
   - Display stdout/stderr in output pane
   - Show exit code and "timed out" warning if applicable
6. **Output pane** (bottom or right):
   - Clear separation: stdout (green text), stderr (red text)
   - "Clear Output" button
7. **"Ask Tutor" button** → navigates to `/chat` with code context
   (pre-fill message with code snippet)
8. **Security note in UI**: "Code runs in a sandboxed environment with a 5-second timeout."
9. **Keep**: theme toggle, responsive layout, back navigation

---

### Phase 10 — Shared UI Cleanup

#### Changes:
1. **Sidebar consistency**: ensure all pages use the same sidebar component
   with the same navigation links and active-state highlighting
2. **Navigation links audit**: verify all sidebar/bottom-nav links point to
   correct routes on every page
3. **Active page indicator**: highlight current page in sidebar on every page
4. **Theme toggle**: already present on all pages — verify consistency
5. **Mobile navigation**: ensure bottom nav bar is consistent across all pages
6. **Loading states**: add a shared loading spinner pattern used by all pages
   that call APIs
7. **Error states**: add a shared error display pattern ("Something went wrong.
   Try again." with retry button)
8. **Empty states**: each page should have a clear empty-state message when
   required data is missing

---

### Phase 11 — Integration Testing

1. **End-to-end flow test**:
   - Start fresh (no localStorage)
   - Visit `/` → redirected to `/chat`
   - Complete assessment → curriculum auto-generated
   - Visit `/roadmap` → see dynamic steps
   - Click a step → go to `/resources?step=0`
   - See resources for step 0
   - Click "Test my Knowledge" → `/quiz?step=0`
   - Answer questions → agent evaluates
   - View results → step marked complete
   - Return to roadmap → step 0 shows completed
   - Visit `/code` → select language, run code

2. **Update existing tests** in `tests/test_app.py`:
   - Add tests for all 5 new endpoints
   - Mock agent responses
   - Test edge cases (no curriculum exists, invalid step index, code timeout)

3. **Cross-page state tests**:
   - Verify localStorage schema is consistent across all pages
   - Verify no page crashes when localStorage is empty
   - Verify no page crashes when localStorage has partial data

---

## File Change Summary

| File | Action | Scope |
|---|---|---|
| `src/app.py` | **Edit** | Add 5 new API endpoints |
| `src/templates/dashboard.html` | **Rewrite** | Replace all hardcoded data with localStorage-driven dynamic content |
| `src/templates/chat.html` | **Edit** | Replace sticker messages, add auto-curriculum trigger |
| `src/templates/roadmap.html` | **Rewrite** | Replace 6 hardcoded nodes with dynamic rendering from `eduai.curriculum` |
| `src/templates/resources.html` | **Rewrite** | Replace static module with dynamic step resources from API |
| `src/templates/code.html` | **Rewrite** | Add language selector, real code execution via `/api/code/execute` |
| `src/templates/quiz.html` | **Rewrite** | Replace hardcoded questions with agent-generated ones via `/api/quiz/generate` |
| `src/templates/quiz_results.html` | **Edit** | Add revision hint display, agent feedback |
| `src/templates/profile.html` | **Edit** | Clean up fallback states, add progress summary |
| `tests/test_app.py` | **Edit** | Add tests for new endpoints |

---

## Security Considerations

### Code Execution Sandbox (`/api/code/execute`)
- **Allowlisted languages only**: Python, JavaScript, TypeScript
- **Timeout**: Hard 5-second limit via subprocess timeout
- **No shell**: `subprocess.run(shell=False)` with explicit interpreter path
- **Code length limit**: Max 10,000 characters
- **No network**: Code cannot make outbound requests (enforced via subprocess env)
- **No dangerous imports**: For Python, wrap in a restricted environment that
  blocks `os`, `subprocess`, `sys`, `shutil`, `socket`, `importlib`
- **Temp directory**: Each execution runs in an isolated temp directory, cleaned after
- **Resource limits**: Memory limit via `ulimit` if on Linux/macOS
- **stdout/stderr capture**: Limited to 50KB each to prevent memory abuse
- **Input validation**: Reject null bytes, non-UTF8 content

### General
- All user input sanitized before rendering (use `escapeHtml()`)
- No `innerHTML` with unsanitized content
- CORS not needed (same-origin)
- Cookie: `httponly=True, samesite=lax` (already set)

---

## Future Work (deferred)
- [ ] **Authentication & accounts** — Firebase Auth / OAuth2
- [ ] **Persistent state** — Database-backed user progress
- [ ] **Real-time collaboration** — Share learning paths
- [ ] **Quiz attempt history** — Track all attempts, not just latest
- [ ] **Spaced repetition** — Schedule review quizzes
- [ ] **Code execution: Docker** — Move sandbox to container for better isolation
- [ ] **Mobile app** — React Native or Flutter wrapper
