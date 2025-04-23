import pandas as pd
import phoenix as px

df = pd.DataFrame(
    [
        {
            "question": "What is Paul Graham known for?",
            "answer": "Co-founding Y Combinator and writing on startups and techology.",
            "metadata": {"topic": "tech"},
        }
    ]
)
phoenix_client = px.Client()
dataset = phoenix_client.upload_dataset(
    dataframe=df,
    dataset_name="test-dataset",
    input_keys=["question"],
    output_keys=["answer"],
    metadata_keys=["metadata"],
)
