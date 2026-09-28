"""Grounded intent-based assistant. Replace through ChatProvider, not the API/UI."""
from typing import Protocol

TEXT = {
'en': {
'hearing': 'Your next recorded hearing is', 'no_hearing': 'No upcoming hearing is recorded. Please confirm with your legal officer.',
'counsellor': 'Your assigned counsellor is', 'no_counsellor': 'No active counsellor assignment is recorded.',
'schemes': 'These schemes may apply; eligibility still needs confirmation:', 'no_schemes': 'No potentially applicable schemes are recorded.',
'stage': 'Your recorded case stage is', 'no_case': 'No case is recorded for your account.',
'safety': 'I am sorry you are feeling unsafe. Use the emergency support button to record a request for human review. This chat does not contact emergency services or guarantee a response. If there is immediate danger in India, call 112 if it is safe to do so.',
'fallback': 'I am a limited demo support assistant, not a counsellor. I can show your recorded hearing, assigned counsellor, case stage or schemes. For personal support, use Request support.',
'demo': '(demo scheme)', 'stage_help': 'A case stage is the latest milestone recorded by your legal team. Ask your legal officer what it means for your specific case.'},
'hi': {
'hearing': 'आपकी अगली दर्ज सुनवाई है', 'no_hearing': 'अगली सुनवाई दर्ज नहीं है। अपने कानूनी अधिकारी से पुष्टि करें।',
'counsellor': 'आपके नियुक्त परामर्शदाता हैं', 'no_counsellor': 'अभी कोई परामर्शदाता नियुक्त नहीं है।',
'schemes': 'ये योजनाएँ लागू हो सकती हैं; पात्रता की पुष्टि आवश्यक है:', 'no_schemes': 'अभी कोई संभावित योजना दर्ज नहीं है।',
'stage': 'आपके मामले का दर्ज चरण है', 'no_case': 'आपके खाते में कोई मामला दर्ज नहीं है।',
'safety': 'यदि आप असुरक्षित हैं, मानव सहायता के लिए आपात सहायता बटन से अनुरोध दर्ज करें। यह चैट आपात सेवाओं से संपर्क नहीं करती और उत्तर की गारंटी नहीं देती। भारत में तत्काल खतरे में, सुरक्षित हो तो 112 पर कॉल करें।',
'fallback': 'मैं सीमित डेमो सहायक हूँ, परामर्शदाता नहीं। मैं दर्ज सुनवाई, परामर्शदाता, मामले का चरण या योजनाएँ दिखा सकता हूँ। व्यक्तिगत सहायता के लिए सहायता अनुरोध करें।',
'demo': '(डेमो योजना)', 'stage_help': 'चरण आपके कानूनी दल द्वारा दर्ज नवीनतम पड़ाव है। अपने मामले का अर्थ कानूनी अधिकारी से पूछें।'},
'kn': {
'hearing': 'ನಿಮ್ಮ ಮುಂದಿನ ದಾಖಲಾದ ವಿಚಾರಣೆ', 'no_hearing': 'ಮುಂದಿನ ವಿಚಾರಣೆ ದಾಖಲಾಗಿಲ್ಲ. ಕಾನೂನು ಅಧಿಕಾರಿಯಿಂದ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.',
'counsellor': 'ನಿಮಗೆ ನಿಯೋಜಿಸಲಾದ ಸಮಾಲೋಚಕರು', 'no_counsellor': 'ಈಗ ಯಾವುದೇ ಸಮಾಲೋಚಕರ ನಿಯೋಜನೆ ದಾಖಲಾಗಿಲ್ಲ.',
'schemes': 'ಈ ಯೋಜನೆಗಳು ಅನ್ವಯಿಸಬಹುದು; ಅರ್ಹತೆಯನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಬೇಕು:', 'no_schemes': 'ಅನ್ವಯಿಸಬಹುದಾದ ಯೋಜನೆಗಳು ದಾಖಲಾಗಿಲ್ಲ.',
'stage': 'ನಿಮ್ಮ ಪ್ರಕರಣದ ದಾಖಲಾದ ಹಂತ', 'no_case': 'ನಿಮ್ಮ ಖಾತೆಗೆ ಪ್ರಕರಣ ದಾಖಲಾಗಿಲ್ಲ.',
'safety': 'ನೀವು ಅಸುರಕ್ಷಿತವಾಗಿದ್ದರೆ ಮಾನವ ಸಹಾಯಕ್ಕಾಗಿ ತುರ್ತು ಸಹಾಯ ಬಟನ್ ಮೂಲಕ ವಿನಂತಿ ದಾಖಲಿಸಿ. ಈ ಚಾಟ್ ತುರ್ತು ಸೇವೆಗಳನ್ನು ಸಂಪರ್ಕಿಸುವುದಿಲ್ಲ ಅಥವಾ ಪ್ರತಿಕ್ರಿಯೆ ಖಾತರಿ ನೀಡುವುದಿಲ್ಲ. ಭಾರತದಲ್ಲಿ ತಕ್ಷಣದ ಅಪಾಯವಿದ್ದರೆ, ಸುರಕ್ಷಿತವಾಗಿದ್ದಾಗ 112ಕ್ಕೆ ಕರೆ ಮಾಡಿ.',
'fallback': 'ನಾನು ಸೀಮಿತ ಡೆಮೊ ಸಹಾಯಕ, ಸಮಾಲೋಚಕನಲ್ಲ. ದಾಖಲಾದ ವಿಚಾರಣೆ, ಸಮಾಲೋಚಕರು, ಪ್ರಕರಣದ ಹಂತ ಅಥವಾ ಯೋಜನೆಗಳನ್ನು ತೋರಿಸಬಲ್ಲೆ. ವೈಯಕ್ತಿಕ ಸಹಾಯಕ್ಕಾಗಿ ಸಹಾಯ ವಿನಂತಿಸಿ.',
'demo': '(ಡೆಮೊ ಯೋಜನೆ)', 'stage_help': 'ಹಂತವು ನಿಮ್ಮ ಕಾನೂನು ತಂಡ ದಾಖಲಿಸಿದ ಇತ್ತೀಚಿನ ಮೈಲಿಗಲ್ಲು. ನಿಮ್ಮ ಪ್ರಕರಣದ ವಿವರಕ್ಕೆ ಕಾನೂನು ಅಧಿಕಾರಿಯನ್ನು ಕೇಳಿ.'}}


class ChatProvider(Protocol):
    def respond(self, message: str, language: str, context: dict, intent: str | None = None) -> tuple[str, str]: ...


class GroundedDemoChat:
    def respond(self, message, language, context, intent=None):
        words = message.casefold()
        # Safety phrases take precedence over an explicitly selected shortcut.
        if any(x in words for x in ('unsafe', 'suicide', 'kill myself', 'hurt myself', 'danger', 'need help', 'असुरक्षित', 'मदद', 'आत्महत्या', 'ಅಸುರಕ್ಷಿತ', 'ಸಹಾಯ', 'ಆತ್ಮಹತ್ಯೆ')):
            intent = 'safety'
        if not intent:
            groups = {'hearing': ('hearing', 'court date', 'सुनवाई', 'ವಿಚಾರಣೆ'),
                      'counsellor': ('counsellor', 'counselor', 'परामर्शदाता', 'ಸಮಾಲೋಚಕ'),
                      'schemes': ('scheme', 'योजना', 'ಯೋಜನೆ'), 'stage': ('stage', 'चरण', 'ಹಂತ')}
            intent = next((key for key, terms in groups.items() if any(t in words for t in terms)), 'fallback')
        t = TEXT[language]
        if intent == 'hearing':
            return intent, f"{t['hearing']}: {context['hearing']} (UTC)." if context['hearing'] else t['no_hearing']
        if intent == 'counsellor':
            return intent, f"{t['counsellor']}: {', '.join(context['counsellors'])}." if context['counsellors'] else t['no_counsellor']
        if intent == 'schemes':
            names = [s['name'] + (' ' + t['demo'] if s['is_demo'] else '') for s in context['schemes'] if s['eligibility'] != 'NOT_ELIGIBLE']
            return intent, t['schemes'] + ' ' + '; '.join(names) if names else t['no_schemes']
        if intent == 'stage':
            return intent, t['stage'] + ': ' + '; '.join(context['stages']) + '. ' + t['stage_help'] if context['stages'] else t['no_case']
        return intent, t.get(intent, t['fallback'])


provider: ChatProvider = GroundedDemoChat()
