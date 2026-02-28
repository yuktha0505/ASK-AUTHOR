# Ask Author – AI Content Companion

## Overview
Ask Author is a Generative AI-powered conversational assistant built using AWS serverless architecture.

It enables users to ask natural language questions and receive intelligent, contextual responses.

## Architecture

User → Amazon S3 (Frontend)
      → Amazon API Gateway
      → AWS Lambda
      → LLM (Amazon Bedrock / AI Service)

## AWS Services Used
- Amazon S3 – Static frontend hosting
- Amazon API Gateway – REST interface
- AWS Lambda – Backend compute
- Amazon Bedrock – Foundation model access

## Why AI?
Traditional rule-based systems cannot handle unstructured queries. Generative AI enables contextual understanding and dynamic response generation.

## Live Prototype
http://ask-autor-prototype.s3-website.ap-south-1.amazonaws.com

## Repository Structure
frontend/
backend/
design.md
requirements.md

## Setup Instructions
(Short deployment steps)
