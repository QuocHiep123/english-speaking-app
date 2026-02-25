# ADR-004: Vietnamese Interference Detection Approach

## Status
**Accepted**

## Context
VietSpeak AI specifically targets Vietnamese learners of English. We need a strategy to detect and provide feedback on common pronunciation errors caused by L1 (Vietnamese) interference.

## Decision Drivers
- Research focus on Vietnamese speakers
- Limited labeled data for Vietnamese L1 errors
- Actionable feedback requirements
- Scalability to other L1s in future

## Considered Options

### Option 1: Rule-based Detection
- Hardcoded phoneme mapping rules
- Fast execution
- No training required
- Limited to known patterns

### Option 2: Classifier Model
- ML model trained on L1 error data
- Requires labeled dataset
- More accurate for trained patterns
- Higher development cost

### Option 3: Hybrid (Rules + GOP Analysis)
- GOP scores identify weak phonemes
- Rules map weak phonemes to L1 interference
- Combines accuracy with explainability

### Option 4: GPT-based Analysis
- LLM analyzes transcription errors
- Most flexible
- Highest latency
- Cost per request

## Decision
**Hybrid: Rules + GOP Analysis**

## Rationale
1. **GOP provides signal**: Low scores indicate pronunciation issues
2. **Rules provide interpretation**: Known Vietnamese patterns explain issues
3. **Explainable**: Can show exact reason for feedback
4. **Extensible**: Easy to add new rules from research

## Implementation

### Vietnamese Interference Rules
```python
VIETNAMESE_INTERFERENCE_RULES = {
    # Target phoneme -> Common Vietnamese substitution
    "θ": {
        "substitutes": ["t", "s"],
        "tip": "Place tongue between teeth, blow air gently",
        "example": "'think' not 'tink'",
        "vietnamese_note": "Âm này không có trong tiếng Việt"
    },
    "ð": {
        "substitutes": ["d", "z"],
        "tip": "Like 'th' but with voice, feel throat vibrate",
        "example": "'the' not 'de'"
    },
    "r": {
        "substitutes": ["l", "ɾ"],
        "tip": "Curl tongue back, don't touch roof of mouth",
        "example": "'right' vs 'light'"
    },
    # Final consonants (often dropped in Vietnamese)
    "_FINAL_CLUSTER": {
        "pattern": "word-final consonant clusters",
        "tip": "Pronounce final sounds clearly: 'talked' /tɔːkt/",
        "vietnamese_note": "Tiếng Việt không có phụ âm cuối phức tạp"
    }
}
```

### Detection Algorithm
```python
def detect_interference(phoneme: str, gop_score: float, position: str) -> dict:
    if gop_score < 0.5:  # Low confidence threshold
        if phoneme in VIETNAMESE_INTERFERENCE_RULES:
            rule = VIETNAMESE_INTERFERENCE_RULES[phoneme]
            return {
                "phoneme": phoneme,
                "likely_error": rule["substitutes"],
                "feedback": rule["tip"],
                "vietnamese_context": rule.get("vietnamese_note")
            }
    return None
```

## Consequences

### Positive
- Explainable feedback for users
- No additional training data required
- Fast execution (rule lookup)
- Easy to extend with research findings

### Negative
- May miss novel error patterns
- Requires linguistic expertise to add rules
- Rules may oversimplify complex errors

## Research Integration
- Rules derived from SLA (Second Language Acquisition) research
- VIVOS dataset analysis for Vietnamese-English patterns
- Feedback from Vietnamese ESL teachers

## Future Enhancements
- A/B test rule effectiveness
- Collect user error data to refine rules
- Train classifier when sufficient data available

## References
- Nguyen, T. (2020). Vietnamese English Pronunciation Patterns
- VIVOS: Vietnamese Speech Corpus
- L2-ARCTIC: Non-native English Speech Corpus
