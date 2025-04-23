import os
import logging
import time
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider
from dotenv import load_dotenv
from tabulate import tabulate
import pprint

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to pretty-print a dictionary artifact


def print_dict_artifact(artifact):
    if isinstance(artifact, dict):
        print("\nDictionary Artifact:")
        pprint.pprint(artifact, indent=2)
        return True
    return False


# Load environment variables from .env.example
logging.info("Loading environment variables...")
load_dotenv(dotenv_path='.env')
logging.info("Environment variables loaded.")

# Initialize the client
logging.info("Initializing PromptQLClient...")

client = PromptQLClient(
    api_key=os.environ.get("PROMPTQL_APIKEY", ""),
    ddn_url=os.environ.get("PROMPTQL_DDN_URL", "your-ddn-sql-endpoint-url"),
    llm_provider=HasuraLLMProvider(),
    timezone=os.environ.get("PROMPTQL_TIMEZONE", "America/Los_Angeles"),
)
logging.info("PromptQLClient initialized.")

# Create a conversation
logging.info("Creating conversation...")
conversation = client.create_conversation(
    system_instructions="You are a helpful assistant that provides information about customers."
)
logging.info("Conversation created.")

# Send messages in the conversation
user_message = "List the first 5 customers and their emails."
logging.info(f"Sending message: '{user_message}'")
start_time = time.time()
# Using a query likely to produce tabular data
response = conversation.send_message(user_message)
end_time = time.time()
logging.info(f"Received response in {end_time - start_time:.2f} seconds.")

print("Assistant Message:")
print(response.message)
logging.info("Assistant message printed.")

# Process artifacts - Try accessing artifacts from the Conversation object
logging.info("Processing artifacts...")
artifacts_found = False
if hasattr(conversation, 'artifacts') and conversation.artifacts:
    logging.info(f"Found {len(conversation.artifacts)} artifact(s).")
    artifacts_found = True
    print("\n--- Artifacts ---")
    for i, artifact in enumerate(conversation.artifacts):
        logging.debug(f"Processing artifact {i+1}...")

        # Extract data from artifact if available
        data = None
        if hasattr(artifact, 'data'):
            data = artifact.data
            logging.info(f"Artifact {i+1} has 'data' property.")
        else:
            data = artifact  # Use the artifact itself if no data attribute
            logging.debug(
                f"Artifact {i+1} has no 'data' property, using artifact itself.")

        # Skip None data
        if data is None:
            logging.info(f"Artifact {i+1} data is None, skipping.")
            continue

        # Process data based on its type
        # Check if the data is a list of dictionaries (common tabular format)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            try:
                # Use tabulate for list of dicts
                headers = data[0].keys()
                rows = [list(item.values()) for item in data]
                print("\nTabular Data:")
                print(tabulate(rows, headers=headers, tablefmt="grid"))
                logging.info(
                    f"Artifact {i+1} data (list of dicts) processed and printed as table.")
            except Exception as e:
                print("\nError formatting tabular data: {e}")
                # Fallback only if we need to debug
                # print(data)
                logging.error(
                    f"Error formatting artifact {i+1} data as table: {e}", exc_info=True)
        # Check if data is a dictionary
        elif isinstance(data, dict):
            print("\nDictionary Data:")
            pprint.pprint(data, indent=2)
            logging.info(
                f"Artifact {i+1} data (dict) processed and pretty-printed.")
        else:
            # Print other data types if necessary
            print(f"\nArtifact Data (type: {type(data).__name__}):")
            print(data)
            logging.info(
                f"Artifact {i+1} data (type: {type(data).__name__}) printed as is.")
else:
    logging.info("No artifacts found in the conversation.")

if artifacts_found:
    logging.info("Finished processing artifacts.")
else:
    logging.info("No artifacts to process.")


logging.info("Script finished.")
