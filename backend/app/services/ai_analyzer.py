"""AI-powered creative performance analysis service.

Uses OpenAI API to analyze ad creatives and predict performance.
Falls back to heuristic analysis when OpenAI API key is not configured.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import openai
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class AICreativeAnalyzer:
    """Analyzes ad creatives using AI for performance prediction and optimization."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None
        if settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key, timeout=30.0)

    def analyze_creative(
        self,
        headline: str,
        body: str | None = None,
        cta: str | None = None,
        platform: str = "meta",
        historical_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze a creative and return performance predictions and recommendations.

        Uses OpenAI if configured, otherwise falls back to heuristic analysis.
        """
        if self._client:
            return self._analyze_with_ai(headline, body, cta, platform, historical_data)
        return self._analyze_heuristic(headline, body, cta, platform)

    def _analyze_with_ai(
        self,
        headline: str,
        body: str | None,
        cta: str | None,
        platform: str,
        _historical_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Use OpenAI to analyze creative performance potential."""
        try:
            system_prompt = """You are an expert ad creative analyst for affiliate marketing.
Analyze the following creative and return a JSON object with:
- ai_score: float 0-1 predicting performance
- strengths: list of strings describing what works
- weaknesses: list of strings describing what could improve
- recommendations: list of specific, actionable improvement suggestions
- predicted_ctr: float estimating click-through rate (0-1)
- predicted_conversion_rate: float estimating conversion rate (0-1)

Focus on what drives CPA/ROAS for email/SMS list building in affiliate marketing."""

            user_prompt = f"""Platform: {platform}
Headline: {headline}
Body: {body or '(none)'}
CTA: {cta or '(none)'}"""

            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty AI response")

            result = json.loads(content)
            return {
                "ai_score": float(result.get("ai_score", 0.5)),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "recommendations": result.get("recommendations", []),
                "predicted_ctr": float(result.get("predicted_ctr", 0.0)),
                "predicted_conversion_rate": float(result.get("predicted_conversion_rate", 0.0)),
                "analysis_text": json.dumps(result),
            }

        except (openai.OpenAIError, json.JSONDecodeError, ValueError) as e:
            logger.warning("AI analysis failed, falling back to heuristic: %s", e)
            return self._analyze_heuristic(headline, body, cta, platform)

    def _analyze_heuristic(
        self,
        headline: str,
        body: str | None,
        cta: str | None,
        platform: str,
    ) -> dict[str, Any]:
        """Heuristic fallback when OpenAI is unavailable."""
        score = 0.5
        strengths: list[str] = []
        weaknesses: list[str] = []
        recommendations: list[str] = []

        # Headline length analysis
        headline_len = len(headline)
        if 20 <= headline_len <= 60:
            score += 0.1
            strengths.append(f"Headline length ({headline_len} chars) is in the optimal range")
        elif headline_len < 20:
            score -= 0.05
            weaknesses.append("Headline is too short — may not capture enough interest")
            recommendations.append("Expand headline to 20-60 characters for better engagement")
        else:
            score -= 0.05
            weaknesses.append("Headline is quite long — may get truncated on mobile")
            recommendations.append("Shorten headline to under 60 characters")

        # Body analysis
        if body:
            body_len = len(body)
            if 50 <= body_len <= 500:
                score += 0.05
                strengths.append("Body copy is in optimal length range")
            elif body_len > 500:
                weaknesses.append("Body copy is very long — readers may not finish it")
                recommendations.append("Consider shortening body copy to under 500 characters")
        else:
            weaknesses.append("No body copy — adding context can improve conversion")

        # CTA analysis
        if cta:
            action_words = [
                "get", "try", "start", "join", "claim", "shop", "download",
                "sign", "learn", "discover", "see", "find", "build", "create",
            ]
            if any(word in cta.lower() for word in action_words):
                score += 0.1
                strengths.append("CTA uses action-oriented language")
            else:
                recommendations.append("Add action words to your CTA (Get, Try, Start, Join)")
        else:
            weaknesses.append("No CTA — every ad needs a clear call to action")
            recommendations.append("Add a clear, action-oriented CTA button")

        # Platform-specific analysis
        if platform == "meta":
            if headline_len <= 40:
                score += 0.05
                strengths.append("Headline is optimized for Meta's headline limit")
            else:
                recommendations.append("Meta headlines perform best under 40 characters")

        score = max(0.0, min(1.0, score))

        return {
            "ai_score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "predicted_ctr": None,
            "predicted_conversion_rate": None,
            "analysis_text": json.dumps({
                "ai_score": score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
            }),
        }


# Singleton
ai_analyzer = AICreativeAnalyzer()
