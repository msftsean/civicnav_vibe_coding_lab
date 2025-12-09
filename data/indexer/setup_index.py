#!/usr/bin/env python3
"""Setup script for Azure AI Search index.

Creates the search index and populates it with knowledge base entries.
Uses DefaultAzureCredential for authentication.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from openai import AzureOpenAI
from azure.identity import get_bearer_token_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "civicnav-index")
OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536


def create_index_definition() -> SearchIndex:
    """Create the search index definition."""
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="service_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="department", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="updated_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="default",
        ),
    ]

    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
    )

    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    return SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def get_openai_client() -> AzureOpenAI:
    """Create Azure OpenAI client with managed identity."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version="2024-02-15-preview",
    )


def create_embedding(client: AzureOpenAI, text: str) -> list[float]:
    """Create an embedding for the given text."""
    response = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


def load_knowledge_base() -> list[dict]:
    """Load knowledge base entries from JSON file."""
    kb_path = Path(__file__).parent.parent / "knowledge_base.json"
    with open(kb_path) as f:
        data = json.load(f)
    return data["entries"]


def main() -> None:
    """Main setup function."""
    logger.info("Starting CivicNav index setup...")

    if not SEARCH_ENDPOINT or not OPENAI_ENDPOINT:
        logger.error("AZURE_SEARCH_ENDPOINT and AZURE_OPENAI_ENDPOINT must be set")
        sys.exit(1)

    credential = DefaultAzureCredential()

    # Create or update index
    logger.info(f"Creating/updating index: {INDEX_NAME}")
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    index_definition = create_index_definition()

    try:
        index_client.create_or_update_index(index_definition)
        logger.info(f"Index '{INDEX_NAME}' created/updated successfully")
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        sys.exit(1)

    # Load knowledge base
    logger.info("Loading knowledge base...")
    entries = load_knowledge_base()
    logger.info(f"Loaded {len(entries)} entries")

    # Create OpenAI client for embeddings
    logger.info("Initializing OpenAI client...")
    openai_client = get_openai_client()

    # Generate embeddings and prepare documents
    logger.info("Generating embeddings...")
    documents = []
    for i, entry in enumerate(entries):
        # Combine title and content for embedding
        text_to_embed = f"{entry['title']}\n\n{entry['content']}"
        embedding = create_embedding(openai_client, text_to_embed)

        doc = {
            "id": entry["id"],
            "title": entry["title"],
            "content": entry["content"],
            "category": entry["category"],
            "service_type": entry["service_type"],
            "department": entry["department"],
            "updated_date": entry["updated_date"],
            "content_vector": embedding,
        }
        documents.append(doc)

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(entries)} entries")

    # Upload documents
    logger.info("Uploading documents to index...")
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential,
    )

    result = search_client.upload_documents(documents)
    succeeded = sum(1 for r in result if r.succeeded)
    logger.info(f"Uploaded {succeeded}/{len(documents)} documents successfully")

    if succeeded < len(documents):
        failed = [r for r in result if not r.succeeded]
        for f in failed[:5]:  # Show first 5 failures
            logger.error(f"Failed to upload {f.key}: {f.error_message}")

    logger.info("Index setup complete!")


if __name__ == "__main__":
    main()
