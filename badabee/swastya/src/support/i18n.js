const words = {
  home: ["Home", "होम", "ಮುಖಪುಟ"],
  checkin: ["Weekly check-in", "साप्ताहिक चेक-इन", "ವಾರದ ಚೆಕ್-ಇನ್"],
  chat: ["Support chat", "सहायता चैट", "ಸಹಾಯ ಚಾಟ್"],
  resources: ["Support resources", "सहायता संसाधन", "ಸಹಾಯ ಸಂಪನ್ಮೂಲಗಳು"],
  caseload: ["My caseload", "मेरे मामले", "ನನ್ನ ಪ್ರಕರಣಗಳು"],
  alerts: ["Alerts", "अलर्ट", "ಎಚ್ಚರಿಕೆಗಳು"],
  notifications: ["Notifications", "सूचनाएँ", "ಅಧಿಸೂಚನೆಗಳು"],
  logout: ["Sign out", "साइन आउट", "ಸೈನ್ ಔಟ್"],
  emergency: ["Emergency support", "आपात सहायता", "ತುರ್ತು ಸಹಾಯ"],
  language: ["Language", "भाषा", "ಭಾಷೆ"],
  welcome: [
    "A little support, every step.",
    "हर कदम पर थोड़ा साथ।",
    "ಪ್ರತಿ ಹೆಜ್ಜೆಯಲ್ಲೂ ಸ್ವಲ್ಪ ಬೆಂಬಲ.",
  ],
  intro: [
    "Your care, case updates and support team in one place.",
    "आपकी देखभाल, मामले की जानकारी और सहायता दल एक जगह।",
    "ನಿಮ್ಮ ಆರೈಕೆ, ಪ್ರಕರಣದ ಮಾಹಿತಿ ಮತ್ತು ಸಹಾಯ ತಂಡ ಒಂದೇ ಕಡೆ.",
  ],
  care: ["Your support team", "आपका सहायता दल", "ನಿಮ್ಮ ಸಹಾಯ ತಂಡ"],
  counsellor: ["Counsellor", "परामर्शदाता", "ಸಮಾಲೋಚಕರು"],
  legal: ["Legal officer", "कानूनी अधिकारी", "ಕಾನೂನು ಅಧಿಕಾರಿ"],
  noAssignment: [
    "Not assigned yet",
    "अभी नियुक्त नहीं",
    "ಇನ್ನೂ ನಿಯೋಜಿಸಲಾಗಿಲ್ಲ",
  ],
  case: ["Your case progress", "आपके मामले की प्रगति", "ನಿಮ್ಮ ಪ್ರಕರಣದ ಪ್ರಗತಿ"],
  hearing: ["Next hearing", "अगली सुनवाई", "ಮುಂದಿನ ವಿಚಾರಣೆ"],
  notRecorded: ["Not recorded", "दर्ज नहीं", "ದಾಖಲಾಗಿಲ್ಲ"],
  noCase: [
    "No case is linked yet. Contact your support team.",
    "अभी कोई मामला जुड़ा नहीं है। सहायता दल से संपर्क करें।",
    "ಇನ್ನೂ ಪ್ರಕರಣ ಜೋಡಿಸಿಲ್ಲ. ಸಹಾಯ ತಂಡವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
  ],
  nextFollowup: ["Next follow-up", "अगला फॉलो-अप", "ಮುಂದಿನ ಸಂಪರ್ಕ"],
  lastCheckin: ["Last check-in", "पिछला चेक-इन", "ಹಿಂದಿನ ಚೆಕ್-ಇನ್"],
  nextCheckin: ["Next check-in due", "अगला चेक-इन", "ಮುಂದಿನ ಚೆಕ್-ಇನ್"],
  begin: [
    "Take a moment to check in",
    "चेक-इन के लिए थोड़ा समय लें",
    "ಚೆಕ್-ಇನ್ ಮಾಡಲು ಸ್ವಲ್ಪ ಸಮಯ ಕೊಡಿ",
  ],
  wellbeingExtra: [
    "Your recent check-ins suggest you may need additional support. You can ask your counsellor to review.",
    "आपके हाल के चेक-इन से अतिरिक्त सहायता की जरूरत लगती है। आप परामर्शदाता से समीक्षा मांग सकते हैं।",
    "ನಿಮ್ಮ ಇತ್ತೀಚಿನ ಚೆಕ್-ಇನ್‌ಗಳು ಹೆಚ್ಚುವರಿ ಸಹಾಯದ ಅಗತ್ಯ ಸೂಚಿಸುತ್ತವೆ. ಸಮಾಲೋಚಕರ ಪರಿಶೀಲನೆ ಕೇಳಬಹುದು.",
  ],
  wellbeingRecorded: [
    "Your wellbeing information is recorded. You can request support whenever you need it.",
    "आपकी जानकारी दर्ज है। जरूरत होने पर सहायता मांग सकते हैं।",
    "ನಿಮ್ಮ ಮಾಹಿತಿ ದಾಖಲಾಗಿದೆ. ಅಗತ್ಯವಿದ್ದಾಗ ಸಹಾಯ ಕೇಳಬಹುದು.",
  ],
  wellbeingNew: [
    "Share how you have been feeling with a short check-in.",
    "छोटे चेक-इन में बताएँ आप कैसा महसूस कर रहे हैं।",
    "ಚಿಕ್ಕ ಚೆಕ್-ಇನ್ ಮೂಲಕ ನಿಮ್ಮ ಭಾವನೆಗಳನ್ನು ತಿಳಿಸಿ.",
  ],
  request: ["Request support", "सहायता मांगें", "ಸಹಾಯ ಕೇಳಿ"],
  saved: [
    "Saved successfully.",
    "सफलतापूर्वक सहेजा गया।",
    "ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ.",
  ],
  supportSaved: [
    "Request recorded for your counsellor to review. This is not an emergency dispatch or a guaranteed response.",
    "परामर्शदाता की समीक्षा के लिए अनुरोध दर्ज है। यह आपात सेवा नहीं है और उत्तर की गारंटी नहीं है।",
    "ಸಮಾಲೋಚಕರ ಪರಿಶೀಲನೆಗೆ ವಿನಂತಿ ದಾಖಲಾಗಿದೆ. ಇದು ತುರ್ತು ಸೇವೆ ಅಥವಾ ಪ್ರತಿಕ್ರಿಯೆಯ ಖಾತರಿ ಅಲ್ಲ.",
  ],
  mood: [
    "How has your mood been?",
    "आपका मन कैसा रहा?",
    "ನಿಮ್ಮ ಮನಸ್ಥಿತಿ ಹೇಗಿತ್ತು?",
  ],
  stress: [
    "How much stress have you felt?",
    "आपने कितना तनाव महसूस किया?",
    "ನೀವು ಎಷ್ಟು ಒತ್ತಡ ಅನುಭವಿಸಿದ್ದೀರಿ?",
  ],
  sleep: [
    "How well have you been sleeping?",
    "आपकी नींद कैसी रही?",
    "ನಿಮ್ಮ ನಿದ್ರೆ ಹೇಗಿತ್ತು?",
  ],
  lowHigh: [
    "1 = very low · 5 = very good",
    "1 = बहुत कम · 5 = बहुत अच्छा",
    "1 = ತುಂಬಾ ಕಡಿಮೆ · 5 = ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ",
  ],
  stressScale: [
    "1 = very little · 5 = very high",
    "1 = बहुत कम · 5 = बहुत अधिक",
    "1 = ಬಹಳ ಕಡಿಮೆ · 5 = ಬಹಳ ಹೆಚ್ಚು",
  ],
  unsafe: [
    "I currently feel unsafe or threatened",
    "मैं अभी असुरक्षित या धमकी महसूस करता/करती हूँ",
    "ಈಗ ನನಗೆ ಅಸುರಕ್ಷಿತ ಅಥವಾ ಬೆದರಿಕೆ ಅನಿಸುತ್ತಿದೆ",
  ],
  share: [
    "Anything you would like to share? (optional)",
    "कुछ और बताना चाहेंगे? (वैकल्पिक)",
    "ಇನ್ನೇನಾದರೂ ಹಂಚಿಕೊಳ್ಳಲು ಬಯಸುವಿರಾ? (ಐಚ್ಛಿಕ)",
  ],
  consent: [
    "I understand these answers will be saved and used for support review by my assigned counsellor.",
    "मैं समझता/समझती हूँ कि उत्तर सहेजे जाएंगे और नियुक्त परामर्शदाता सहायता समीक्षा में उपयोग करेंगे।",
    "ಉತ್ತರಗಳನ್ನು ಉಳಿಸಿ ನಿಯೋಜಿತ ಸಮಾಲೋಚಕರು ಸಹಾಯ ಪರಿಶೀಲನೆಗೆ ಬಳಸುತ್ತಾರೆ ಎಂದು ತಿಳಿದಿದ್ದೇನೆ.",
  ],
  submit: ["Save check-in", "चेक-इन सहेजें", "ಚೆಕ್-ಇನ್ ಉಳಿಸಿ"],
  saving: ["Saving…", "सहेज रहे हैं…", "ಉಳಿಸಲಾಗುತ್ತಿದೆ…"],
  checkinIntro: [
    "There are no right or wrong answers. Share only what you feel comfortable sharing.",
    "कोई सही या गलत उत्तर नहीं है। जितना सहज लगे उतना साझा करें।",
    "ಸರಿ ಅಥವಾ ತಪ್ಪು ಉತ್ತರಗಳಿಲ್ಲ. ನಿಮಗೆ ಅನುಕೂಲವಾದಷ್ಟೇ ಹಂಚಿಕೊಳ್ಳಿ.",
  ],
  demo: [
    "Demo decision support · not a diagnosis",
    "डेमो सहायता · निदान नहीं",
    "ಡೆಮೊ ನಿರ್ಧಾರ ಸಹಾಯ · ರೋಗನಿರ್ಣಯವಲ್ಲ",
  ],
  chatbotIntro: [
    "A limited, case-grounded demo assistant. It does not replace a human counsellor.",
    "दर्ज मामले पर आधारित सीमित डेमो सहायक। यह मानव परामर्शदाता का विकल्प नहीं है।",
    "ದಾಖಲಾದ ಪ್ರಕರಣ ಆಧಾರಿತ ಸೀಮಿತ ಡೆಮೊ ಸಹಾಯಕ. ಇದು ಮಾನವ ಸಮಾಲೋಚಕರಿಗೆ ಪರ್ಯಾಯವಲ್ಲ.",
  ],
  message: ["Your message", "आपका संदेश", "ನಿಮ್ಮ ಸಂದೇಶ"],
  send: ["Send", "भेजें", "ಕಳುಹಿಸಿ"],
  sending: ["Sending…", "भेज रहे हैं…", "ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ…"],
  hearingQuestion: [
    "When is my next hearing?",
    "मेरी अगली सुनवाई कब है?",
    "ನನ್ನ ಮುಂದಿನ ವಿಚಾರಣೆ ಯಾವಾಗ?",
  ],
  counsellorQuestion: [
    "Who is my counsellor?",
    "मेरे परामर्शदाता कौन हैं?",
    "ನನ್ನ ಸಮಾಲೋಚಕರು ಯಾರು?",
  ],
  schemesQuestion: [
    "Which schemes may apply?",
    "कौन सी योजनाएँ लागू हो सकती हैं?",
    "ಯಾವ ಯೋಜನೆಗಳು ಅನ್ವಯಿಸಬಹುದು?",
  ],
  stageQuestion: [
    "What is my case stage?",
    "मेरे मामले का चरण क्या है?",
    "ನನ್ನ ಪ್ರಕರಣ ಯಾವ ಹಂತದಲ್ಲಿದೆ?",
  ],
  helpQuestion: [
    "I feel unsafe",
    "मैं असुरक्षित महसूस करता/करती हूँ",
    "ನನಗೆ ಅಸುರಕ್ಷಿತ ಅನಿಸುತ್ತಿದೆ",
  ],
  you: ["You", "आप", "ನೀವು"],
  assistant: ["Support assistant", "सहायता सहायक", "ಸಹಾಯ ಸಹಾಯಕ"],
  schemes: ["Government schemes", "सरकारी योजनाएँ", "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು"],
  ngos: [
    "NGOs & local support",
    "एनजीओ और स्थानीय सहायता",
    "ಎನ್‌ಜಿಒ ಮತ್ತು ಸ್ಥಳೀಯ ಸಹಾಯ",
  ],
  source: ["Official source", "आधिकारिक स्रोत", "ಅಧಿಕೃತ ಮೂಲ"],
  demoScheme: [
    "Demo scheme — not an actual programme",
    "डेमो योजना — वास्तविक कार्यक्रम नहीं",
    "ಡೆಮೊ ಯೋಜನೆ — ನಿಜವಾದ ಕಾರ್ಯಕ್ರಮವಲ್ಲ",
  ],
  demoDirectory: [
    "Demo directory: contacts and locations may be synthetic. Do not rely on demo entries for urgent help.",
    "डेमो निर्देशिका: संपर्क और स्थान काल्पनिक हो सकते हैं। तत्काल सहायता के लिए इन पर निर्भर न रहें।",
    "ಡೆಮೊ ಪಟ್ಟಿ: ಸಂಪರ್ಕ ಮತ್ತು ಸ್ಥಳಗಳು ಕಾಲ್ಪನಿಕವಾಗಿರಬಹುದು. ತುರ್ತು ಸಹಾಯಕ್ಕೆ ಇವುಗಳನ್ನು ಅವಲಂಬಿಸಬೇಡಿ.",
  ],
  empty: [
    "Nothing to show yet.",
    "अभी कोई जानकारी नहीं।",
    "ಇನ್ನೂ ತೋರಿಸಲು ಏನೂ ಇಲ್ಲ.",
  ],
  loading: ["Loading…", "लोड हो रहा है…", "ಲೋಡ್ ಆಗುತ್ತಿದೆ…"],
  retry: ["Try again", "फिर कोशिश करें", "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ"],
  back: ["Back to caseload", "मामलों पर वापस", "ಪ್ರಕರಣಗಳಿಗೆ ಹಿಂತಿರುಗಿ"],
  emergencyText: [
    "If you are in immediate danger in India, call 112 if safe. A request here is saved for human review; it does not dispatch emergency services and may not be seen immediately.",
    "भारत में तत्काल खतरे में, सुरक्षित हो तो 112 पर कॉल करें। यहाँ अनुरोध मानव समीक्षा के लिए दर्ज होता है; यह आपात सेवाएँ नहीं भेजता और तुरंत देखा जाना जरूरी नहीं।",
    "ಭಾರತದಲ್ಲಿ ತಕ್ಷಣದ ಅಪಾಯವಿದ್ದರೆ ಸುರಕ್ಷಿತವಾಗಿ 112ಕ್ಕೆ ಕರೆ ಮಾಡಿ. ಇಲ್ಲಿ ವಿನಂತಿ ಮಾನವ ಪರಿಶೀಲನೆಗೆ ಉಳಿಯುತ್ತದೆ; ತುರ್ತು ಸೇವೆ ಕಳುಹಿಸುವುದಿಲ್ಲ ಮತ್ತು ತಕ್ಷಣ ನೋಡಲಾಗದಿರಬಹುದು.",
  ],
  call: ["Call 112", "112 पर कॉल करें", "112ಕ್ಕೆ ಕರೆ ಮಾಡಿ"],
  recordEmergency: [
    "Record urgent support request",
    "तत्काल सहायता अनुरोध दर्ज करें",
    "ತುರ್ತು ಸಹಾಯ ವಿನಂತಿ ದಾಖಲಿಸಿ",
  ],
  close: ["Close", "बंद करें", "ಮುಚ್ಚಿ"],
  requests: [
    "Your support requests",
    "आपके सहायता अनुरोध",
    "ನಿಮ್ಮ ಸಹಾಯ ವಿನಂತಿಗಳು",
  ],
  skip: ["Skip to content", "मुख्य सामग्री पर जाएँ", "ವಿಷಯಕ್ಕೆ ಹೋಗಿ"],
  refresh: ["Refresh", "रीफ्रेश", "ರಿಫ್ರೆಶ್"],
  unread: ["Mark as read", "पढ़ा हुआ चिह्नित करें", "ಓದಲಾಗಿದೆ ಎಂದು ಗುರುತಿಸಿ"],
  privacy: [
    "Your information is shared only with permitted support roles.",
    "आपकी जानकारी केवल अनुमति वाले सहायता कर्मियों को उपलब्ध है।",
    "ನಿಮ್ಮ ಮಾಹಿತಿ ಅನುಮತಿಸಿದ ಸಹಾಯ ಪಾತ್ರಗಳಿಗೆ ಮಾತ್ರ ಲಭ್ಯ.",
  ],
};
export const locale = { en: "en-IN", hi: "hi-IN", kn: "kn-IN" };
export const translator = (lang) => (key) =>
  words[key]?.[{ en: 0, hi: 1, kn: 2 }[lang] ?? 0] ?? key;
export function dateTime(value, lang = "en") {
  return value
    ? new Date(value).toLocaleString(locale[lang], {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : translator(lang)("notRecorded");
}
