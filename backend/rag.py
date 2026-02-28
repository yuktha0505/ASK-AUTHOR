import json
import boto3
import re

s3 = boto3.client("s3")

BUCKET_NAME = "ask-author-content-yuktha-2026"
FILE_KEY = "content/sample_articles.json"


class RAGEngine:
    def __init__(self):
        self.documents = self.load_documents()

    def load_documents(self):
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        return json.loads(obj["Body"].read().decode("utf-8"))

    def tokenize(self, text):
        text = text.lower()
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        return set(text.split())

    def retrieve(self, query, top_k=2):
        query_tokens = self.tokenize(query)
        scored = []

        for doc in self.documents:
            content_tokens = self.tokenize(doc["content"])
            overlap = len(query_tokens & content_tokens)
            scored.append((overlap, doc))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [doc for score, doc in scored[:top_k] if score > 0]