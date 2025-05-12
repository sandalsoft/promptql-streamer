## Interactive CLI Mode

The application now supports an interactive conversation mode using the PromptQL Python SDK.

- When running the application (`main.py`), if no user prompt is supplied as an argument, the default prompt "Tell me what you can do" is used.
- The CLI dynamically accepts user input, streams responses as they are received from the PromptQL API, and displays a spinner (powered by Yaspin) while waiting for responses.
- After each response, the application processes any artifacts and then prompts the user for the next input.
- To exit the conversation, type "exit" or "quit" at the prompt.

### Installation

1. **Clone the repository** and navigate to the project directory.
2. **Install Python 3.12 or higher** (see your OS instructions).
3. **Install dependencies:**

```
pip install -r requirements.txt
```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in the required values.

```
cp .env.example .env
```

### Running the Application

Run the application with an optional initial prompt:

```
python main.py [optional initial prompt]
```

If no argument is provided, the application defaults to using:

```
Tell me what you can do
```

### Running Tests

To run the tests, install test dependencies:

```
pip install pytest pandas phoenix
```

Then run:

```
pytest
```

_Note: `pandas`, `phoenix`, and `pytest` are only required for testing and not for running the main application._
