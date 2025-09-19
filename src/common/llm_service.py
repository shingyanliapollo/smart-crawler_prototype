"""LLM service for content filtering and data normalization using Claude API."""

import json
from typing import Any, Dict, List, Optional
import anthropic

from src.common.config import settings


class ClaudeService:
    """Service for interacting with Claude API for content processing."""

    def __init__(self):
        """Initialize Claude service with API key."""
        self.api_key = settings.anthropic_api_key
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set it in your .env file."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"  # Using cost-effective model

    def extract_event_info(self, content: str, source_url: str = "") -> Dict[str, Any]:
        """
        Extract event information from content using Claude.

        Args:
            content: Raw content to analyze
            source_url: Optional source URL for context

        Returns:
            Dictionary containing extracted event information
        """
        prompt = self._build_extraction_prompt(content, source_url)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse the response
            response_text = response.content[0].text

            try:
                # Try to parse as JSON
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # If not valid JSON, wrap in error response
                return {
                    "has_event": False,
                    "error": "Invalid JSON response from Claude",
                    "raw_response": response_text,
                    "source_url": source_url
                }

        except Exception as e:
            return {
                "has_event": False,
                "error": f"Claude API error: {str(e)}",
                "source_url": source_url
            }

    def normalize_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted event data to structured format.

        Args:
            event_data: Raw event data from extraction

        Returns:
            Dictionary containing normalized event data
        """
        if not event_data.get("has_event", False):
            return {
                "success": False,
                "error": "No event data to normalize"
            }

        prompt = self._build_normalization_prompt(event_data)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse the response
            response_text = response.content[0].text

            try:
                # Try to parse as JSON
                result = json.loads(response_text)
                return {
                    "success": True,
                    "normalized_events": result.get("events", [])
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response from Claude",
                    "raw_response": response_text
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Claude API error: {str(e)}"
            }

    def _build_extraction_prompt(self, content: str, source_url: str = "") -> str:
        """Build prompt for event extraction."""
        return f"""
あなたは日本のイベント情報を抽出する専門家です。提供されたコンテンツからイベント情報を抽出してください。

コンテンツ:
{content}

ソースURL: {source_url}

以下のJSON形式で回答してください:

{{
  "has_event": true/false,
  "events": [
    {{
      "title": "イベントタイトル",
      "category": "カテゴリ（例：セミナー、展示会、コンサート等）",
      "start_date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_date": "YYYY-MM-DD",
      "end_time": "HH:MM",
      "venue_name": "会場名",
      "address": "住所",
      "prefecture": "都道府県",
      "city": "市区町村",
      "description": "イベント説明",
      "target_audience": "対象者",
      "fee_amount": "料金（数値のみ）",
      "fee_unit": "料金単位（円、ドル等）",
      "registration_method": "申込方法",
      "registration_deadline": "YYYY-MM-DD",
      "contact_info": "連絡先情報"
    }}
  ],
  "source_url": "{source_url}"
}}

注意事項:
- イベント情報が見つからない場合は "has_event": false を返してください
- 日付は YYYY-MM-DD 形式で統一してください
- 時間は HH:MM 形式（24時間表記）で統一してください
- 情報が不明な場合は null を使用してください
- 複数のイベントがある場合は配列で返してください
"""

    def _build_normalization_prompt(self, event_data: Dict[str, Any]) -> str:
        """Build prompt for data normalization."""
        return f"""
以下のイベントデータを正規化して、構造化されたフォーマットに変換してください。

入力データ:
{json.dumps(event_data, indent=2, ensure_ascii=False)}

以下のJSON形式で回答してください:

{{
  "events": [
    {{
      "source_url": "ソースURL",
      "title": "正規化されたタイトル",
      "category": "正規化されたカテゴリ",
      "start_date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_date": "YYYY-MM-DD",
      "end_time": "HH:MM",
      "venue_name": "正規化された会場名",
      "address": "正規化された住所",
      "prefecture": "都道府県（標準形式）",
      "city": "市区町村（標準形式）",
      "description": "整理された説明文",
      "target_audience": "対象者",
      "fee_amount": 料金数値,
      "fee_unit": "円",
      "registration_method": "申込方法",
      "registration_deadline": "YYYY-MM-DD",
      "contact_info": "連絡先",
      "data_quality_score": 0.0-1.0の品質スコア
    }}
  ]
}}

正規化ルール:
1. 日付と時間は統一フォーマットに変換
2. 住所は都道府県・市区町村を分離
3. 料金は数値と単位を分離
4. カテゴリは標準的な分類に統一
5. データ品質スコアは情報の完全性に基づいて算出
6. 不明な情報は null を使用
"""