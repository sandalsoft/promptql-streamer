import os
import logging
import time
import argparse
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider
from dotenv import load_dotenv
from tabulate import tabulate
import pprint
from yaspin import yaspin

USER_PROMPT = "Tell me what you can do"

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_initial_prompt():
    parser = argparse.ArgumentParser(description="Interactive PromptQL CLI")
    parser.add_argument("user_prompt", nargs="?", default=USER_PROMPT,
                        help="User prompt to send initially (defaults to 'Tell me what you can do')")
    args = parser.parse_args()
    return args.user_prompt


def process_artifacts(conversation):
    if hasattr(conversation, 'artifacts') and conversation.artifacts:
        print("\n--- Artifacts ---")
        for i, artifact in enumerate(conversation.artifacts, start=1):
            data = artifact.data if hasattr(artifact, 'data') else artifact
            if data is None:
                print(f"Artifact {i}: No data")
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                headers = data[0].keys()
                rows = [list(item.values()) for item in data]
                print(tabulate(rows, headers=headers, tablefmt="grid"))
            elif isinstance(data, dict):
                pprint.pprint(data, indent=2)
            else:
                print(f"Artifact {i} (type: {type(data).__name__}): {data}")
    else:
        logging.info("No artifacts found in this conversation.")


def interactive_conversation(conversation, initial_prompt=None):
    first = True
    first_user_message = True  # Track if this is the very first real user prompt
    while True:
        if first and initial_prompt is not None:
            prompt = initial_prompt
            first = False
        else:
            prompt = input("You: ")
        if prompt.lower() in ["exit", "quit"]:
            print("Exiting conversation.")
            break
        logging.info(f"Sending message: '{prompt}'")
        # Use non-streaming mode for the first user prompt to avoid premature-end errors from the API
        stream_mode = False if first_user_message else True
        with yaspin(text="Waiting for response...", color="cyan") as spinner:
            try:
                if stream_mode:
                    streamer = conversation.send_message(prompt, stream=True)
                    first_chunk = True
                    for chunk in streamer:
                        if first_chunk:
                            spinner.ok("✔")
                            first_chunk = False
                        # Only print if the chunk has a non-None message attribute
                        message = getattr(chunk, "message", None)
                        if message is not None:
                            print(message, end="", flush=True)
                    print()  # New line after complete response
                else:
                    response = conversation.send_message(prompt, stream=False)
                    spinner.ok("✔")
                    print(response.message)
            except Exception as e:
                spinner.fail("✗")
                logging.error("Error during conversation: %s", str(e))
        # After first successful send, enable streaming for subsequent prompts
        if first_user_message:
            first_user_message = False
        process_artifacts(conversation)


def main():
    # Load environment variables from .env.example (not .env as instructed)
    load_dotenv(dotenv_path='.env')
    logging.info("Environment variables loaded.")

    initial_prompt = get_initial_prompt()
    user_supplied_prompt = initial_prompt != USER_PROMPT

    logging.info("Initializing PromptQLClient...")
    client = PromptQLClient(
        api_key=os.environ.get("PROMPTQL_APIKEY", ""),
        ddn_url=os.environ.get(
            "PROMPTQL_DDN_URL", "your-ddn-sql-endpoint-url"),
        llm_provider=HasuraLLMProvider(),
        timezone=os.environ.get("PROMPTQL_TIMEZONE", "America/New_York"),
    )
    logging.info("PromptQLClient initialized.")

    logging.info("Creating conversation...")
    conversation = client.create_conversation(
        system_instructions="You are a helpful assistant that provides information about the data you have access to."
    )
    logging.info("Conversation created.")

    # Helper to ensure the very first interaction in the list is API-compliant
    def _ensure_first_interaction():
        try:
            from promptql_api_sdk.types.models import AssistantAction, Interaction, UserMessage
            if not hasattr(conversation, "interactions"):
                conversation.interactions = []  # type: ignore[attr-defined]

            if conversation.interactions:
                # Patch existing first interaction if user_message is empty or whitespace
                um = getattr(
                    conversation.interactions[0], "user_message", None)
                if um is None or not getattr(um, "text", "").strip():
                    conversation.interactions[0].user_message = UserMessage(
                        text="(init)")
                if not conversation.interactions[0].assistant_actions:
                    conversation.interactions[0].assistant_actions = [
                        AssistantAction(message="(init)")]
            else:
                # Create new compliant interaction
                conversation.interactions.append(
                    Interaction(
                        user_message=UserMessage(text="(init)"),
                        assistant_actions=[AssistantAction(message="(init)")]
                    )
                )
        except Exception as e:
            logging.debug(
                "Could not ensure first interaction compliance: %s", str(e))

    # Only send the initial prompt automatically if it was provided by the user
    if user_supplied_prompt:
        try:
            logging.info(
                f"Initializing conversation with initial prompt: '{initial_prompt}'")
            response = conversation.send_message(initial_prompt, stream=False)
            print(response.message)
            process_artifacts(conversation)
            _ensure_first_interaction()
        except Exception as e:
            logging.error("Error during initial conversation: %s", str(e))
        # Start interactive mode, but don't repeat the initial prompt
        interactive_conversation(conversation, initial_prompt=None)
    else:
        # No initial prompt sent; make sure first interaction is compliant
        _ensure_first_interaction()

        interactive_conversation(conversation, initial_prompt=None)


if __name__ == "__main__":
    main()
