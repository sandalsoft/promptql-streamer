import os
import logging
import time
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider
from promptql_api_sdk.types import AssistantActionChunk, ErrorChunk
from dotenv import load_dotenv
from tabulate import tabulate
import pprint
import argparse
import sys
import threading

# Default user prompt if no argument is provided
DEFAULT_USER_PROMPT = "Tell me what you can do"

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def print_dict_artifact(artifact):
    if isinstance(artifact, dict):
        print("\nDictionary Artifact:")
        pprint.pprint(artifact, indent=2)
        return True
    return False


# Spinner specific functions
spinner_running = False


def spin():
    spinner_chars = ['-', '\\', '|', '/']
    idx = 0
    while spinner_running:
        sys.stdout.write(
            f"\r{spinner_chars[idx % len(spinner_chars)]} Waiting for response...")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 30 + '\r')  # Clear spinner
    sys.stdout.flush()


def start_spinner():
    global spinner_running
    spinner_running = True
    spinner_thread = threading.Thread(target=spin)
    spinner_thread.daemon = True
    spinner_thread.start()


def stop_spinner():
    global spinner_running
    spinner_running = False
    time.sleep(0.1)  # Give spinner a moment to stop


# Load environment variables from .env.example
logging.info("Loading environment variables from .env.example...")
load_dotenv(dotenv_path='.env.example')
logging.info("Environment variables loaded.")

# Initialize the client
logging.info("Initializing PromptQLClient...")
client = PromptQLClient(
    api_key=os.environ.get("PROMPTQL_APIKEY", ""),
    ddn_url=os.environ.get("PROMPTQL_DDN_URL", "your-ddn-sql-endpoint-url"),
    llm_provider=HasuraLLMProvider(),
    timezone=os.environ.get("PROMPTQL_TIMEZONE", "America/New_York"),
)
logging.info("PromptQLClient initialized.")

logging.info("Creating conversation...")
conversation = client.create_conversation(
    system_instructions="You are a helpful assistant that provides information about the data you have access to."
)
logging.info("Conversation created.")


def safe_send_message(conversation_obj, message, stream=True):
    """A wrapper function to safely send messages to the conversation,
    handling potential IndexError in the SDK."""
    global conversation  # Ensure we can update the global conversation object
    try:
        return conversation_obj.send_message(message, stream=stream)
    except IndexError:
        # If we encounter an IndexError (likely because interactions list is empty)
        logging.warning(
            "IndexError in SDK, recreating conversation and retrying")
        # Recreate the conversation
        conversation = client.create_conversation(
            system_instructions="You are a helpful assistant that provides information about the data you have access to."
        )
        logging.info("Created new conversation after IndexError")
        # Try again with the new conversation
        return conversation.send_message(message, stream=stream)


def process_artifacts(conversation_artifacts):
    """Processes and prints artifacts from the conversation."""
    artifacts_found = False
    if conversation_artifacts:
        logging.info(f"Found {len(conversation_artifacts)} artifact(s).")
        artifacts_found = True
        print("\n--- Artifacts ---")
        for i, artifact_obj in enumerate(conversation_artifacts):
            logging.debug(f"Processing artifact {i+1}...")

            data = None
            if hasattr(artifact_obj, 'data'):
                data = artifact_obj.data
                logging.info(f"Artifact {i+1} has 'data' property.")
            else:
                # This case might not be typical if artifacts are always structured
                # For safety, let's assume artifact_obj itself could be the data if no 'data' field
                data = artifact_obj
                logging.debug(
                    f"Artifact {i+1} has no 'data' property, using artifact object itself.")

            if data is None:
                logging.info(f"Artifact {i+1} data is None, skipping.")
                continue

            if isinstance(data, list) and data and isinstance(data[0], dict):
                try:
                    headers = data[0].keys()
                    rows = [list(item.values()) for item in data]
                    print("\nTabular Data:")
                    print(tabulate(rows, headers=headers, tablefmt="grid"))
                    logging.info(
                        f"Artifact {i+1} data (list of dicts) processed and printed as table.")
                except Exception as e:
                    print("\nError formatting tabular data: {e}")
                    logging.error(
                        f"Error formatting artifact {i+1} data as table: {e}", exc_info=True)
            elif isinstance(data, dict):
                print("\nDictionary Data:")
                pprint.pprint(data, indent=2)
                logging.info(
                    f"Artifact {i+1} data (dict) processed and pretty-printed.")
            else:
                print(f"\nArtifact Data (type: {type(data).__name__}):")
                print(data)
                logging.info(
                    f"Artifact {i+1} data (type: {type(data).__name__}) printed as is.")
    else:
        logging.info("No artifacts found in the conversation for this turn.")

    if artifacts_found:
        logging.info("Finished processing artifacts for this turn.")
    else:
        logging.info("No artifacts to process for this turn.")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive PromptQL CLI assistant.")
    parser.add_argument("prompt", nargs="?", default=None,
                        help="Initial prompt to send to the assistant. If not provided, uses a default or asks for input.")
    args = parser.parse_args()

    initial_prompt = args.prompt if args.prompt else None

    print("Welcome to the Interactive PromptQL Assistant!")
    print("Type 'exit' or 'quit' to end the conversation.")

    first_message = True

    while True:
        if first_message and initial_prompt:
            user_input = initial_prompt
            print(f"You (initial): {user_input}")
            first_message = False
        elif first_message and not initial_prompt:
            user_input = input(f"You (default: '{DEFAULT_USER_PROMPT}'): ")
            if not user_input:
                user_input = DEFAULT_USER_PROMPT
            first_message = False
        else:
            user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']:
            print("Exiting assistant. Goodbye!")
            break

        if not user_input.strip():
            continue

        logging.info(f"Sending message: '{user_input}'")
        start_spinner()
        start_time = time.time()

        try:
            response_stream = safe_send_message(conversation, user_input)

            full_response_message = ""
            print("Assistant: ", end="", flush=True)

            for chunk in response_stream:
                stop_spinner()  # Stop spinner as soon as first chunk arrives
                if isinstance(chunk, AssistantActionChunk) and chunk.message:
                    print(chunk.message, end="", flush=True)
                    full_response_message += chunk.message
                elif isinstance(chunk, ErrorChunk):
                    print(
                        f"\nError from API: {chunk.error_message}", flush=True)
                    logging.error(f"API Error Chunk: {chunk.error_message}")
                    break
                # ArtifactUpdateChunk is handled by the conversation object internally
                # and artifacts are retrieved after the stream.
            print()  # Newline after assistant's full message

            end_time = time.time()
            logging.info(
                f"Received response in {end_time - start_time:.2f} seconds.")

            # Process artifacts after the stream is complete
            # The conversation object updates its artifacts list internally during streaming
            if conversation.artifacts:  # Check if there are any artifacts at all
                # Process all current artifacts
                process_artifacts(conversation.artifacts)
                # conversation.artifacts = [] # Optionally clear after processing if you only want turn-based artifacts

        except Exception as e:
            stop_spinner()
            print(f"\nAn error occurred: {e}")
            logging.error(f"Error during conversation: {e}", exc_info=True)

        finally:
            # Ensure spinner is stopped if it was running and an error occurred before first chunk
            if spinner_running:
                stop_spinner()


if __name__ == "__main__":
    main()
