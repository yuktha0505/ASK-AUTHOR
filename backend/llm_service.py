import os
import json
import boto3

MODE = "local"   
AWS_REGION = "ap-south-1"  

def generate_answer(question, contexts):
    if MODE == "local":
        return local_response(question, contexts)
    elif MODE == "bedrock":
        return bedrock_response(question, contexts)
    else:
        raise ValueError("Invalid MODE")

# ---------------- LOCAL MODE ----------------

def local_response(question, contexts):
    if not contexts:
        return "No relevant content found."

    combined = " ".join([c["content"] for c in contexts])
    summary = combined[:500]

    return f"""
Answer:
{summary}

Sources:
{", ".join([c["title"] for c in contexts])}
""".strip()

# ---------------- BEDROCK MODE ----------------

def bedrock_response(question, contexts):
    if not contexts:
        return "No relevant content found."

    context_text = "\n\n".join([c["content"] for c in contexts])

    prompt = f"""
You are an AI assistant for an Indian media platform.
Answer ONLY using the provided context.
If answer is not present, say:
"The information is not available in the content library."

Be clear, structured, and concise.
If question is in Hindi, respond in Hindi.

Context:
{context_text}

Question:
{question}
"""

    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION
    )

    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 500,
            "temperature": 0.2,
            "topP": 0.9
        }
    }

    response = client.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response["body"].read())
    answer = response_body["results"][0]["outputText"]

    return f"""
{answer.strip()}

Sources:
{", ".join([c["title"] for c in contexts])}
""".strip()