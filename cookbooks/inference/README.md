# Telnyx Inference Cookbooks

Hands-on Colab notebooks for building with Telnyx Inference and related Telnyx AI APIs. These cookbooks show how to call Telnyx-hosted models through OpenAI-compatible clients, extract structured data, build retrieval-augmented generation flows, and combine speech-to-text with translation.

## Cookbooks

| Cookbook | What it covers | Launch |
| --- | --- | --- |
| [First Chat Completion with Telnyx Inference](./01_Chat_completion_telnyx_inference.ipynb) | Install the OpenAI SDK, configure a Telnyx-backed client, and send a first chat completion request. | [Open in Colab](https://colab.research.google.com/github/team-telnyx/telnyx-code-examples/blob/main/cookbooks/inference/01_Chat_completion_telnyx_inference.ipynb) |
| [Structured JSON Extraction with Telnyx Inference](./02_Structured_JSON_Extraction.ipynb) | Extract structured JSON from messy tickets, emails, leads, contracts, or incident reports. | [Open in Colab](https://colab.research.google.com/github/team-telnyx/telnyx-code-examples/blob/main/cookbooks/inference/02_Structured_JSON_Extraction.ipynb) |
| [RAG with Telnyx Inference](./03_RAG_Telnyx_Inference.ipynb) | Build a lightweight retrieval-augmented generation workflow using embeddings and chat completions. | [Open in Colab](https://colab.research.google.com/github/team-telnyx/telnyx-code-examples/blob/main/cookbooks/inference/03_RAG_Telnyx_Inference.ipynb) |
| [Transcription and Translation Pipeline with Telnyx AI](./04_Transcription_Translation.ipynb) | Transcribe audio with Telnyx Speech-to-Text, then translate the transcript with Telnyx Inference. | [Open in Colab](https://colab.research.google.com/github/team-telnyx/telnyx-code-examples/blob/main/cookbooks/inference/04_Transcription_Translation.ipynb) |

## Requirements

- A Telnyx API key
- Google Colab or another Python notebook environment
- The `openai` Python SDK

## Getting Started

1. Open a cookbook in GitHub or Colab.
2. Add your Telnyx API key when prompted.
3. Run the cells from top to bottom.
4. Modify the prompts, models, or generation settings for your own workflow.
