"""Validate every model response before downstream agents or UI consume it."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Score = Annotated[int, Field(ge=1, le=10)]
Text = Annotated[str, Field(min_length=1)]


class Result(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")


class TranscriptionQA(Result):
    cleaned_transcript: Text
    corrections_made: list[str]
    unclear_segments: list[str]
    transcript_quality: Literal["good", "fair", "poor"]


class ClinicalContent(Result):
    score: Score
    elements_present: list[str]
    elements_missing: list[str]
    terminology_issues: list[str]
    content_analysis: Text
    service_specific_notes: str


class ClinicalReasoning(Result):
    score: Score
    differential_assessment: Text
    summary_statement_quality: str
    data_selectivity: str
    plan_coherence: Text
    reasoning_analysis: Text
    reasoning_strengths: list[str]
    reasoning_gaps: list[str]


class SemanticDensity(Result):
    analysis: Text
    over_represented: list[str]
    under_represented: list[str]
    efficiency_rating: Literal["efficient", "mostly efficient", "inefficient"]


class StructureDelivery(Result):
    score: Score
    format_conformance: Text
    sections_present: list[str]
    sections_missing: list[str]
    organization_flow: str
    semantic_density: SemanticDensity
    delivery_notes: str
    structure_strengths: list[str]
    structure_improvements: list[str]


class Communication(Result):
    score: Score
    audience_adaptation: Text
    patient_centered_language: str
    language_appropriateness: str
    confidence_assessment: str
    communication_strengths: list[str]
    communication_improvements: list[str]


class Thought(Result):
    transcript_segment: str
    attending_thought: Text
    thought_type: Literal[
        "questioning", "expecting", "satisfied", "concerned", "confused", "impressed", "noting"
    ]


class AnticipatoryReasoning(Result):
    inner_monologue: list[Thought]
    unanswered_questions: list[str]
    anticipatory_strengths: list[str]
    missed_anticipations: list[str]
    overall_impression: Text


class TeachingPoint(Result):
    topic: Text
    point: Text
    relevance: str


class LiteratureLearning(Result):
    teaching_points: list[TeachingPoint]
    suggested_reading: list[str]
    case_learning_summary: Text


class ContestedPoint(Result):
    dimension: Text
    generous_view: str
    strict_view: str
    resolution: Text
    adjustment: Literal["raise", "lower", "keep"]


class Debate(Result):
    contested_points: list[ContestedPoint]
    consensus_strengths: list[str]
    consensus_weaknesses: list[str]
    overall_calibration: Text


class Rewrite(Result):
    area: Text
    original: str
    improved: Text
    why_better: str
    uses_illustrative_data: bool


class ContrastiveFeedback(Result):
    rewrites: list[Rewrite]
    note: str


class LegacyFeedback(Result):
    overall_score: Score
    overall_assessment: Text
    clinical_content: Text
    clinical_reasoning: Text
    presentation_structure: Text
    service_specific_feedback: str
    strengths: list[str]
    areas_for_improvement: list[str]
    teaching_points: list[str]


class Synthesis(LegacyFeedback):
    communication_professionalism: Text
    suggested_reading: list[str]
    semantic_density_summary: str
    plan_coherence_summary: str


class CriticIssue(Result):
    type: Literal["contradiction", "vague_advice", "missed_priority", "tone_inconsistency"]
    description: Text
    location: str
    suggested_fix: Text


class SynthesisCritic(Result):
    issues_found: list[CriticIssue]
    is_acceptable: bool
    revision_instructions: Text


AGENT_SCHEMAS = {
    "transcription_qa": TranscriptionQA,
    "clinical_content": ClinicalContent,
    "clinical_reasoning": ClinicalReasoning,
    "structure_delivery": StructureDelivery,
    "communication_professionalism": Communication,
    "anticipatory_reasoning": AnticipatoryReasoning,
    "literature_learning": LiteratureLearning,
    "debate": Debate,
    "contrastive_feedback": ContrastiveFeedback,
    "synthesizer": Synthesis,
    "synthesis_critic": SynthesisCritic,
    "legacy": LegacyFeedback,
}
