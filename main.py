import os
import logging
import time
from promptql_api_sdk import PromptQLClient
from promptql_api_sdk.types.models import HasuraLLMProvider
from dotenv import load_dotenv
from tabulate import tabulate
import pprint

# USER_PROMPT = "How are you?"
# USER_PROMPT = "How many iphone customers are there?"
USER_PROMPT = "Get the student performance data for the class 78be2705-b0cc-4294-8ac8-d439e1526c25 (Demo Class) and limit to 10 students. 1. use ids suffix for roster 2. Query AssessmentAssessmentCompletedEvent table with minimal fields 3. Skip enrollment checks and focus on assessments 4. Simplify the aggregations to use basic COUNT and SUM 5. Get the basic assessment data for the class 6. Keep the query simple without complex joins 7. Ignore visualizations"

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
    timezone=os.environ.get("PROMPTQL_TIMEZONE", "America/New_York"),
)
logging.info("PromptQLClient initialized.")
response = client.query(USER_PROMPT)

# Create a conversation
logging.info("Creating conversation...")
conversation = client.create_conversation(
    system_instructions="You are a helpful assistant that provides information about the data you have access to."
)
logging.info("Conversation created.")

# Send messages in the conversation
logging.info(f"Sending message: '{USER_PROMPT}'")
start_time = time.time()

# Display the conversation response with streaming
print("\n" + "=" * 50)
print("ASSISTANT RESPONSE:")
print("=" * 50)

# First, send a normal non-streaming message to initialize the conversation
# This avoids the "list index out of range" error in the SDK
logging.info("Sending initial message (non-streaming)...")
response = conversation.send_message(USER_PROMPT)
final_answer = response.message
print(response.message)

# For follow-up questions, we could use streaming
# Commented out for now as it's causing errors on the first message
"""
print("\n" + "=" * 50)
print("FOLLOW-UP (streaming):")
print("=" * 50)

full_response = ""
try:
    # Create a streaming response for a follow-up question
    for chunk in conversation.send_message("Give me more details", stream=True):
        if hasattr(chunk, "message") and chunk.message:
            print(chunk.message, end="", flush=True)
            full_response += chunk.message
except Exception as e:
    logging.error(f"Error during streaming: {e}", exc_info=True)
    # Fallback to non-streaming in case of error
    logging.info("Falling back to non-streaming mode...")
    response = conversation.send_message("Give me more details")
    print(response.message)
"""

end_time = time.time()
print("\n" + "=" * 50)  # End of response
logging.info(f"Received response in {end_time - start_time:.2f} seconds.")


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


# Print the final answer as a separate output
print("\n" + "=" * 50)
print("FINAL ANSWER:")
print("=" * 50)
print(final_answer)

logging.info("Script finished.")
