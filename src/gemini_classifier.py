from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

MODEL_NAME = "gemini-2.8-flash"


class ReviewClassification(BaseModel):
    sentiment: Literal[
        "Positive",
        "Neutral",
        "Negative",
    ]
    category: Literal[
        "Billing",
        "Technical",
        "Account Access",
        "Delivery",
        "Other",
    ]
    confidence: float = Field(
        ge=0,
        le=1,
    )


SYSTEM_INSTRUCTION = """
You are a customer-support review classifier for a Nigerian fintech app.
Classify the customer review into exactly one sentiment and one category.
SENTIMENT:
- Positive: the customer is mainly satisfied, praising the app,
or reporting a successful experience.
- Neutral: the review is mainly informational, unclear,
or does not show a clear positive or negative feeling.
- Negative: the customer is mainly complaining, dissatisfied,
reporting a problem, or asking for an issue to be fixed.
CATEGORY:
- Billing: money, charges, fees, transactions, transfers,
payment problems, deductions, refunds, or financial issues.
- Technical: app errors, crashes, bugs, loading problems,
network-related app problems, or technical failures.
- Account Access: login, password, OTP, verification,
account restriction, account recovery, or access problems.
- Delivery: card delivery, physical card delivery,
receiving a card, or delivery-related problems.
- Other: anything that does not clearly belong to the
categories above.
IMPORTANT:
If a review mentions more than one issue, choose the category
for the primary problem or what the customer mainly wants fixed.
Return only the structured classification.
"""


def get_client(api_key):
    """
    Create a Gemini client.
    """
    return genai.Client(api_key=api_key)


def classify_review(client, review_text):
    """
    Classify one customer review using Gemini.
    """
    if not review_text or not str(review_text).strip():
        raise ValueError("Review text cannot be empty.")

    prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"Customer Review:\n{str(review_text).strip()}"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=ReviewClassification,
        ),
    )

    result = ReviewClassification.model_validate_json(response.text)
    return result
