# PromptQL CLI Assistant

An interactive CLI tool to communicate with the PromptQL API and visualize the results.

## Features

- Interactive CLI interface for communicating with PromptQL
- Supports streaming responses
- Visualizes tabular data and dictionary artifacts
- Shows loading spinner during processing
- Handles errors gracefully

## Setup

1. Create an `.env.example` file with the required environment variables:

   ```
   PROMPTQL_APIKEY=your-api-key-here
   PROMPTQL_DDN_URL=your-ddn-sql-endpoint-url
   PROMPTQL_TIMEZONE=America/New_York
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

```
python main.py [prompt]
```

Where `[prompt]` is an optional initial prompt to send to the assistant. If not provided, the default prompt "Tell me what you can do" will be used.

## Recent Changes

- Fixed an issue with the SDK where an IndexError could occur on the first message
- Implemented a robust error handling approach to recreate the conversation if needed
- Added detailed logging for better debugging
