# Google Cloud Hackathon 19

## Overview

A personalized learning platform that acts as a software development tutor. Users create profiles with their interests and educational background, then engage in a guided learning experience:

1. **Assessment**: Chat-based conversation to understand learning goals and current knowledge level
2. **Curriculum Generation**: AI-powered roadmap with structured learning steps tailored to the user's goals
3. **Content & Resources**: Curated links, overviews, and learning materials for each step
4. **Reinforcement**: Auto-generated quizzes to assess understanding and identify knowledge gaps
5. **Adaptive Learning**: Quiz results guide next steps—either revision of weak areas or progression to new material


## Running locally

### Prerequisites
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- A GCP project with the Vertex AI API enabled
- `gcloud` CLI authenticated (`gcloud auth application-default login`)

### Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd Google-Cloud-Hackathon-19

# 2. Copy the env template and fill in your project details
cp .env.example .env

# 3. Install dependencies
uv sync
```

### Start the server

```bash
uv run fastapi dev learning_platform/main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.


## Spec

All feature development starts with a spec. Before writing code, a spec must exist and be approved.

- Specs live in [`specs/`](specs/)
- Each spec follows the template in [`specs/_template.md`](specs/_template.md)
- A spec must include: problem statement, proposed solution, acceptance criteria, and out-of-scope items
