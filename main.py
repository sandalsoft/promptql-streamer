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

USER_PROMPT = "Hello, ready to talk?"
# USER_PROMPT = "How many iphone customers are there?"
# USER_PROMPT = "Get the student performance data for the class 78be2705-b0cc-4294-8ac8-d439e1526c25 (Demo Class) and limit to 10 students. 1. use ids suffix for roster 2. Query AssessmentAssessmentCompletedEvent table with minimal fields 3. Skip enrollment checks and focus on assessments 4. Simplify the aggregations to use basic COUNT and SUM 5. Get the basic assessment data for the class 6. Keep the query simple without complex joins 7. Ignore visualizations"

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


def interactive_conversation(conversation):
    while True:
        prompt = input("You: ")
        if prompt.lower() in ["exit", "quit"]:
            print("Exiting conversation.")
            break
        logging.info(f"Sending message: '{prompt}'")
        with yaspin(text="Waiting for response...", color="cyan") as spinner:
            try:
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
            except Exception as e:
                spinner.fail("✗")
                logging.error("Error during conversation: %s", str(e))
        process_artifacts(conversation)


def main():
    # Load environment variables from .env.example (not .env as instructed)
    load_dotenv(dotenv_path='.env')
    logging.info("Environment variables loaded.")

    initial_prompt = get_initial_prompt()

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

    # Warm-up call: initialize conversation with the initial prompt
    try:
        logging.info(
            f"Initializing conversation with initial prompt: '{initial_prompt}'")
        response = conversation.send_message(initial_prompt, stream=False)
        print(response.message)
        process_artifacts(conversation)
        # Ensure the conversation has at least one assistant action to avoid index errors
        if not conversation.interactions or not conversation.interactions[-1].assistant_actions:
            from promptql_api_sdk.types.models import AssistantAction, Interaction, UserMessage
            if conversation.interactions:
                conversation.interactions[-1].assistant_actions = [AssistantAction()]
            else:
                conversation.interactions.append(
                    Interaction(
                        user_message=UserMessage(text=initial_prompt),
                        assistant_actions=[AssistantAction()]
                    )
                )
    except Exception as e:
        logging.error("Error during initial conversation: %s", str(e))

    interactive_conversation(conversation)


if __name__ == "__main__":
    main()
