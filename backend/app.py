import json
from rag import RAGEngine

# Initialize RAG engine once (cold start optimization)
rag = RAGEngine()

# Simple in-memory session memory
session_memory = {}

def format_answer(results, question):
    intro = f'Here is what we found about "{question}":\n\n'
    summary = results[0]["content"][:350]

    related_titles = [f'• {doc["title"]}' for doc in results]
    sources = [doc["title"] for doc in results]

    formatted = (
        intro +
        summary +
        "\n\nKey related content:\n" +
        "\n".join(related_titles)
    )

    return formatted, sources



def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            },
            "body": ""
        }
    try:
        body = json.loads(event.get("body", "{}"))
        question = body.get("question", "").strip()

        if not question:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS"
                },
                "body": json.dumps({"answer": "Question is required.", "sources": []})
            }

        results = rag.retrieve(question)

        if not results:
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "POST, OPTIONS"
                },
                "body": json.dumps({"answer": "No relevant content found.", "sources": []})
            }

        answer, sources = format_answer(results, question)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            },
            "body": json.dumps({
                "answer": answer,
                "sources": sources
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            },
            "body": json.dumps({
                "answer": f"Internal error: {str(e)}",
                "sources": []
            })
        }