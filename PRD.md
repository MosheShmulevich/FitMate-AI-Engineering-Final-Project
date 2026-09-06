# FitMate — Product Requirements Document

## Problem
Beginner and intermediate gym trainees are exposed to conflicting and unreliable fitness information and often struggle to build an effective training plan and progress toward their goals.

## Target Audience
Beginner and intermediate gym trainees.

## Solution
FitMate is an AI fitness agent that accompanies users toward their training goals by creating personalized workout plans, adapting them based on progress, answering professional questions using trusted knowledge, and using tools when actions are required.

## Core MVP Features
1. Create and manage a trainee profile.
2. Generate personalized workout programs.
3. Answer professional fitness questions using RAG.
4. Track progress and adapt recommendations over time.
5. Use AI tools for calculations, data retrieval, and progress updates.

## AI Architecture
- Single AI Agent
- LangGraph
- ChromaDB for professional RAG knowledge
- SQLite for user profiles, progress, and long-term memory
- Workout Planning Skill
- Function Calling / Tools
- Hybrid Search + Reranking
- Evals with Promptfoo
- Streamlit UI

## Agent

### Role
AI Personal Fitness Coach

### Goal
Guide beginner and intermediate trainees toward their fitness goals using personalized training, professional knowledge, progress tracking, and adaptive recommendations.

### Backstory
FitMate is a digital fitness coach designed to support gym trainees throughout their training journey. It uses professional knowledge, user history, specialized skills, and tools to make informed decisions and provide personalized guidance.

## Success Criteria
- The agent correctly decides when to use RAG, Skills, or Tools.
- Professional answers are grounded in the knowledge base.
- User progress persists between sessions.
- At least 5 evaluation scenarios are executed.
- The final system demonstrates measurable improvement after advanced RAG and prompt optimization.

## Out of Scope for MVP
- Voice assistant
- Food image recognition
- Health-app integration
- Multi-Agent architecture
- MCP integration