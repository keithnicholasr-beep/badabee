"""Unvalidated, transparent demo rules; confidence is not a clinical probability."""
from dataclasses import dataclass
from typing import Protocol
import re


@dataclass(frozen=True)
class Features:
    mood: int
    stress: int
    sleep: int
    feels_unsafe: bool
    text: str
    missed_followups: int = 0
    hearing_soon: bool = False
    previous_score: float | None = None
    interaction_count: int = 0


class DistressProvider(Protocol):
    def predict_distress(self, features: Features) -> dict: ...


# Deliberately narrow phrase matching, not an emotion classifier. Negated English
# phrases are removed to avoid interpreting "not unsafe" as a positive flag.
def text_signals(text):
    normalized = re.sub(r'\b(?:not|never)\s+(?:unsafe|afraid|threatened)\b', '', text.casefold())
    return {
        'threat': any(x in normalized for x in ('threat', 'unsafe', 'intimidat', 'धमकी', 'असुरक्षित', 'ಬೆದರಿಕೆ', 'ಅಸುರಕ್ಷಿತ')),
        'distress': any(x in normalized for x in ('overwhelmed', 'hopeless', 'afraid', 'डर', 'परेशान', 'ಭಯ', 'ಒತ್ತಡ')),
    }


class DemoRulesProvider:
    version = 'demo-rules-v1-unvalidated'

    def predict_distress(self, features: Features) -> dict:
        f = features
        signals = text_signals(f.text)
        score = (5 - f.mood) * 7 + (f.stress - 1) * 7 + (5 - f.sleep) * 3
        factors = []
        if f.mood <= 2: factors.append('Low self-reported mood')
        if f.stress >= 4: factors.append('High self-reported stress')
        if f.sleep <= 2: factors.append('Poor self-reported sleep')
        if f.missed_followups:
            score += min(f.missed_followups, 3) * 5
            factors.append(f'{f.missed_followups} missed or overdue follow-ups in the past 30 days')
        if f.hearing_soon:
            score += 5
            factors.append('Scheduled hearing within seven days')
        if signals['threat']:
            score += 15
            factors.append('Possible safety-related phrase; human interpretation required')
        if signals['distress']:
            score += 5
            factors.append('Possible distress-related phrase; human interpretation required')
        if f.feels_unsafe:
            score = max(score, 85)
            factors.append('Person explicitly reported feeling unsafe')
        score = min(100, max(0, score))
        level = 'CRITICAL' if score >= 85 else 'HIGH' if score >= 65 else 'MODERATE' if score >= 35 else 'LOW'
        change = score - f.previous_score if f.previous_score is not None else 0
        trend = 'RISING' if change >= 10 else 'FALLING' if change <= -10 else 'STABLE'
        return {'score': score, 'level': level, 'trend': trend,
                'factors': factors or ['No elevated signals in the available check-in answers'],
                'confidence': 0.0, 'model_version': self.version,
                'recommended_action': 'Urgent human counsellor review' if level == 'CRITICAL' else
                    'Priority human counsellor review' if level == 'HIGH' else 'Offer a counsellor follow-up' if level == 'MODERATE' else 'Continue weekly check-ins'}


provider: DistressProvider = DemoRulesProvider()


def predict_distress(features: Features) -> dict:
    return provider.predict_distress(features)
