# Workout Planning Skill

## Purpose
Create safe, practical, and personalized workout plans for beginner and intermediate gym trainees.

## When to Use
Use this skill when the user asks to:
- Create a workout plan
- Modify an existing workout plan
- Adjust training frequency
- Change exercises
- Adapt training based on progress or feedback

## Required Information
Before creating a workout plan, the following information MUST be known:

1. Training goal
2. Experience level
3. Number of training days per week
4. Available time per session
5. Available equipment
6. Relevant limitations or preferences

Do NOT generate a workout plan until all important required information is available.

If some information already exists in the user's profile, use it and ask only for the missing information.

## Planning Principles
- Match the program to the user's goal and experience level.
- Keep the plan realistic for the user's weekly availability.
- Match the workout length to the available session duration.
- Prefer simple and sustainable programs.
- Avoid unnecessary complexity.
- Use professional knowledge from the RAG system when needed.
- Adapt the plan based on user progress and feedback.

## Output Format
For each training day provide:

1. Training day name
2. Exercises
3. Sets
4. Repetitions
5. Rest time
6. Short notes when needed

## Safety
- Do not diagnose injuries or medical conditions.
- Do not present uncertain information as fact.
- If professional knowledge is required, prefer grounded RAG information.