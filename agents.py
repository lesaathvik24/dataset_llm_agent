import os
import csv
import anthropic
from prompts import *

if not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = input(
        "Please enter your Anthropic API key")

client = anthropic.Anthropic()
sonnet = "claude-3-5-sonnet-20240620"


def read_csv(file_path):
    data = []
    with open(file_path, "r", newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            data.append(row)
    return data


def save_to_csv(data, output_file, headers=None):
    mode = "w" if headers else 'a'
    with open(output_file, mode, newline="") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        for row in csv.reader(data.splitlines()):
            writer.writerow(row)


def analyzer_agent(sample_data):
    message = client.messages.create(
        model=sonnet,
        max_tokens=400,
        temperature=0.1,
        system=ANALYZER_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": ANALYZER_USER_PROMPT.format(sample_data=sample_data)
            }
        ]
    )
    return message.content[0].text


def generator_agent(analysis_result, sample_data, num_rows=30):
    message = client.messages.create(
        model=sonnet,
        max_tokens=1500,
        temperature=1,
        system=GENERATOR_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": GENERATOR_USER_PROMPT.format(
                    num_rows=num_rows,
                    analysis_result=analysis_result,
                    sample_data=sample_data
                )
            }
        ]
    )
    print("Generated data from agent:",
          message.content[0].text)  # Debugging line
    return message.content[0].text


file_path = input("\nEnter the name of your CSV file: ")
file_path = os.path.join('/app/data', file_path)
desired_rows = int(
    input("Enter the number of rows you want in the new dataset: "))
sample_data = read_csv(file_path)
sample_data_str = "\n".join(",".join(row) for row in sample_data)

print("Analyzing the sample data...")  # Debugging line
analysis_result = analyzer_agent(sample_data_str)
print("\n#### Analyzer Agent Output:####\n")
print(analysis_result)  # Debugging line
print("\n----------------------------------------------------\n\nGenerating new data.....")

output_file = "/app/data/new_dataset.csv"
headers = sample_data[0]
save_to_csv("", output_file, headers)
batch_size = 30
generated_rows = 0

while generated_rows < desired_rows:
    rows_to_generate = min(batch_size, desired_rows - generated_rows)
    generated_data = generator_agent(
        analysis_result, sample_data_str, rows_to_generate)
    print("Generated rows:", generated_data)  # Debugging line
    save_to_csv(generated_data, output_file)
    generated_rows += rows_to_generate
    print(f"Generated {generated_rows} rows out of {desired_rows}")

print(f"Generated data has been saved to {output_file}")
