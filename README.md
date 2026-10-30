# Mini Agent Lab

A small, observable tool-calling agent for learning agent loops, runtime harnesses, and evaluations.

The agent sends tool definitions to DeepSeek, executes requested tools, returns their results, and prints each round of the conversation. Its initial task is to diagnose an intentionally broken calculator example.

## Structure

```text
mmagent.py                    # Agent loop, API client, and readable trace output
tools.py                      # Tool implementations and their schemas
examples/buggy_calculator/    # Intentionally failing task for the agent
tests/                        # Tests for the agent and its tools
```

## Setup

Python 3.9 or newer is required. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Add your DeepSeek API key to `.env`, or set the `DEEPSEEK_API_KEY` environment variable. The environment variable takes precedence. The `.env` file is ignored by Git.

## Run the agent

```bash
python mmagent.py
```

Each round shows the messages sent to the model, its response, tool calls and IDs, and tool results. This makes live API calls and incurs provider usage charges.

The tools operate inside `examples/buggy_calculator/`. The example test is meant to fail: `average` uses floor division. The agent diagnoses the issue and cannot edit files with its current tools.

## Run the project tests

```bash
python -m pytest -q
```

Project tests are separate from the intentionally failing example. To see the example failure directly:

```bash
python -m pytest -q examples/buggy_calculator/test_calculator.py
```

## Ideas for the next iteration

- Add structured trace files and run summaries.
- Create a dataset of tasks and an evaluation runner.
- Experiment with tool errors, timeouts, and context limits.
- Add a restricted editing tool and verify changes with independent tests.
