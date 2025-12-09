"""QueryAgent for intent classification and entity extraction.

This agent processes user queries to classify intent and extract
relevant entities before the retrieval stage.
"""

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.models.schemas import (
    AgentResult,
    Category,
    Entity,
    EntityType,
    IntentClassification,
)
from app.tools.openai_tool import get_openai_tool

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are a city services query classifier. Analyze the user query and return a JSON object with:
1. category: The service category (one of: schedule, event, report, permit, emergency, general)
2. confidence: Your confidence score from 0.0 to 1.0
3. entities: Array of extracted entities with type, value, start_pos, end_pos

Categories:
- schedule: Questions about recurring services (trash, recycling, parking sweeping)
- event: Questions about community events, meetings, public gatherings
- report: Questions about reporting issues (311, potholes, code violations)
- permit: Questions about permits, applications, licenses, fees
- emergency: Questions about emergency services, 911, disaster preparedness
- general: General city information that doesn't fit other categories

Entity types:
- date: Dates, days of week, time references
- location: Neighborhoods, streets, areas of the city
- service_type: Specific service mentioned (trash, recycling, building permit, etc.)
- department: City department mentioned (Public Works, Planning, Police, etc.)

Return ONLY valid JSON, no additional text.

Example response:
{
  "category": "schedule",
  "confidence": 0.92,
  "entities": [
    {"type": "service_type", "value": "trash", "start_pos": 8, "end_pos": 13},
    {"type": "location", "value": "downtown", "start_pos": 25, "end_pos": 33}
  ]
}

User query: {query}"""


class QueryAgent(BaseAgent[str, IntentClassification]):
    """Agent for classifying user intent and extracting entities.

    Takes a raw user query string and returns an IntentClassification
    with the predicted category, confidence, and extracted entities.
    """

    def __init__(self) -> None:
        """Initialize the QueryAgent."""
        super().__init__("QueryAgent")
        self.openai_tool = get_openai_tool()

    async def run(self, input_data: str) -> AgentResult:
        """Classify user intent and extract entities.

        Args:
            input_data: The raw user query string

        Returns:
            AgentResult containing IntentClassification
        """
        logger.info(f"QueryAgent processing: {input_data[:50]}...")

        self.use_tool("openai_chat")

        try:
            # Call OpenAI to classify intent
            prompt = CLASSIFICATION_PROMPT.format(query=input_data)
            response = await self.openai_tool.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies city service queries."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500,
            )

            # Parse the JSON response
            classification_data = json.loads(response)

            # Convert entities
            entities = []
            for entity_data in classification_data.get("entities", []):
                try:
                    entities.append(Entity(
                        type=EntityType(entity_data["type"]),
                        value=entity_data["value"],
                        start_pos=entity_data.get("start_pos"),
                        end_pos=entity_data.get("end_pos"),
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid entity: {e}")

            # Create IntentClassification
            intent = IntentClassification(
                category=Category(classification_data["category"]),
                confidence=float(classification_data["confidence"]),
                entities=entities,
            )

            reasoning = f"Classified as '{intent.category.value}' with {intent.confidence:.0%} confidence. "
            if entities:
                reasoning += f"Extracted {len(entities)} entities."

            logger.info(f"QueryAgent result: {intent.category.value} ({intent.confidence:.2f})")

            return AgentResult(
                output=intent,
                reasoning=reasoning,
                tools_used=self.tools_used,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            # Return low-confidence general classification
            return AgentResult(
                output=IntentClassification(
                    category=Category.GENERAL,
                    confidence=0.3,
                    entities=[],
                ),
                reasoning=f"Classification failed, defaulting to general: {e}",
                tools_used=self.tools_used,
            )

        except Exception as e:
            logger.error(f"QueryAgent error: {e}")
            raise
