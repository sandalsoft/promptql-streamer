## Interactive CLI Mode

The application now supports an interactive conversation mode using the PromptQL Python SDK.

- When running the application (`main.py`), if no user prompt is supplied as an argument, the default prompt "Tell me what you can do" is used.
- The CLI dynamically accepts user input, streams responses as they are received from the PromptQL API, and displays a spinner (powered by Yaspin) while waiting for responses.
- After each response, the application processes any artifacts and then prompts the user for the next input.
- To exit the conversation, type "exit" or "quit" at the prompt.

### Usage

Run the application with an optional initial prompt:

```
python main.py [optional initial prompt]
```

If no argument is provided, the application defaults to using:

```
Tell me what you can do
```
