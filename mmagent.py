"""A small, observable tool-calling agent for learning."""

import json
import os
from pathlib import Path

from openai import OpenAI

from tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

DEFAULT_TASK = "Run the tests, inspect the relevant code, and explain the failure."


def get_api_key():
    """Use the environment first, then the project's local .env file."""
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "DEEPSEEK_API_KEY" and value.strip():
                return value.strip().strip("\"'")
    raise RuntimeError("Set DEEPSEEK_API_KEY in the environment or in .env.")


def print_section(title):
    print(f"\n{'=' * 20} {title} {'=' * 20}")


def print_value(label, value):
    if value is None:
        return
    print(f"  {label}:")
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    for line in value.splitlines() or [""]:
        print(f"    {line}")


def print_message(item, index=None):
    """Show dictionary messages and SDK message objects in the same format."""
    data = item if isinstance(item, dict) else item.model_dump(exclude_none=True)
    role = data.get("role", "unknown")
    prefix = f"{index}. " if index is not None else ""
    print(f"\n  [{prefix}{role}]")
    if data.get("tool_call_id"):
        print(f"  Tool call ID: {data['tool_call_id']}")
    content = data.get("content")
    if role == "tool" and isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                print_value(key, value)
            content = None
    print_value("Content", content)
    for call in data.get("tool_calls") or []:
        function = call.get("function", {})
        print(f"  Tool call: {function.get('name', '?')}")
        print(f"  Tool call ID: {call.get('id', '?')}")
        arguments = function.get("arguments", "{}")
        try:
            arguments = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            pass
        print_value("Arguments", arguments)


def query_llm(question, tools, client, max_rounds=6):
    messages = [
        {"role": "system", "content": "You are a helpful code diagnosis assistant."},
        {"role": "user", "content": question},
    ]
    api_tools = [{"type": "function", "function": tool} for tool in tools]

    for step in range(max_rounds):
        print_section(f"Round {step + 1}: Request")
        print(f"  Available tools: {', '.join(tool['name'] for tool in tools)}")
        for index, item in enumerate(messages, 1):
            print_message(item, index)

        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=api_tools,
            stream=False,
            extra_body={"thinking": {"type": "disabled"}},
        )
        message = response.choices[0].message
        title = "Model response" if message.tool_calls else "Model response: Final answer"
        print_section(f"Round {step + 1}: {title}")
        print_message(message)
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            raw_arguments = tool_call.function.arguments
            print_section(f"Execute tool: {name}")
            print(f"  Tool call ID: {tool_call.id}")
            print_value("Arguments", raw_arguments)
            try:
                arguments = json.loads(raw_arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")
                function = TOOL_FUNCTIONS.get(name)
                if function is None:
                    raise ValueError(f"Unknown tool: {name}")
                result = function(**arguments)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                result = {"ok": False, "error": str(exc)}
            print("\n  Result:")
            for key, value in result.items():
                print_value(key, value)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    print("\nMaximum number of model requests reached.")
    return None


def main():
    client = OpenAI(api_key=get_api_key(), base_url="https://api.deepseek.com")
    query_llm(DEFAULT_TASK, TOOL_DEFINITIONS, client)


if __name__ == "__main__":
    main()
