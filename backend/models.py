from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CardType = Literal["concept", "example", "quote", "comparison", "highlight"]
QuizType = Literal["inline", "section"]


class ContentCard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: CardType
    content: str = Field(min_length=1)
    emoji: str = Field(default="🧠", min_length=1)


class InlineQuiz(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: int = Field(ge=0)
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=5)
    correct: int = Field(ge=0)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def correct_must_point_to_option(self) -> "InlineQuiz":
        if self.correct >= len(self.options):
            raise ValueError("inline_quiz.correct is out of range")
        return self


class SectionQuizQuestion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct: int = Field(ge=0)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def correct_must_point_to_option(self) -> "SectionQuizQuestion":
        if self.correct >= len(self.options):
            raise ValueError("section_quiz.correct is out of range")
        return self


class InsightCardModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class SectionContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hook: str = Field(min_length=1)
    content_cards: list[ContentCard] = Field(min_length=1)
    inline_quiz: InlineQuiz
    section_quiz: list[SectionQuizQuestion] = Field(min_length=1)
    reflection: str = Field(min_length=1)
    insight_cards: list[InsightCardModel] = Field(default_factory=list)
    bridge: str = Field(min_length=1)
    recap: str = Field(min_length=1)

    @field_validator("content_cards")
    @classmethod
    def require_highlight(cls, cards: list[ContentCard]) -> list[ContentCard]:
        if not any(card.type == "highlight" for card in cards):
            raise ValueError("content_cards must include at least one highlight card")
        return cards

    @model_validator(mode="after")
    def inline_position_must_fit(self) -> "SectionContent":
        if self.inline_quiz.position > len(self.content_cards):
            self.inline_quiz.position = len(self.content_cards)
        return self


class ProgressUpdate(BaseModel):
    section_index: int = Field(ge=0)
    position: str = Field(default="start", min_length=1)


class QuizSubmitRequest(BaseModel):
    section_id: str = Field(min_length=1)
    quiz_type: QuizType
    question_index: int = Field(ge=0)
    user_answer: int = Field(ge=0)

