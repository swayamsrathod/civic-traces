// English, Kannada and Hindi labels for the citizen pages.
// Mark an element with data-i18n="key" (text) or data-i18n-ph="key" (placeholder).
const I18N = {
  en: {
    nav_report: "Report", nav_track: "Track", nav_dash: "Dashboard", nav_dept: "Department",
    r_title: "Report a civic issue",
    r_lead: "Snap it. We'll chase it. The agent finds the right department, files only after you approve, and follows up until it's fixed.",
    r_s1: "1. What's the problem?", r_photo: "📷 Tap to add a photo (optional)", r_desc: "Describe it",
    r_desc_ph: "e.g. Deep pothole near Gate 2 on Main Road, dangerous for bikes",
    r_s2: "2. Where is it?", r_locate: "📍 Use my location", r_maphint: "Or tap the map to move the pin.",
    r_landmark: "Landmark (optional)", r_landmark_ph: "e.g. Gate 2, Main Road", r_send: "Send to the CIVIC TRACE agent",
    r_working: "The agent is working", r_s3: "3. Review and approve", r_english: "The complaint is written in English for the department, with your description included.",
    r_how: "How should it be filed?", r_email: "Official email", r_portal: "Grievance portal",
    r_approve: "✓ Approve and file", r_notnow: "Not now", r_nothing: "Nothing is sent in your name until you approve.",
    r_filed: "Complaint filed", r_trackbtn: "Track this complaint", r_next: "What happens next",
    r_n1: "The agent identifies the issue and the right department.", r_n2: "If others reported it nearby, your report joins theirs.",
    r_n3: "You approve the formal complaint before anything is sent.", r_n4: "If there's no response, it sends a reminder, then escalates.",
    r_need: "Add a photo or a short description.", r_sending: "Sending…", r_filing: "Filing…",
    t_rti_h: "Still not fixed? Ask officially with RTI", t_rti_p: "Under the Right to Information Act, 2005, the department must reply within 30 days and say what action was taken. CIVIC TRACE drafts the application from this complaint's record.",
    t_rti_name: "Your name", t_rti_addr: "Your address, phone or email", t_rti_btn: "Draft RTI application", t_rti_copy: "Copy text", t_rti_copied: "Copied", t_rti_dl: "Download .txt",
    ev_reported: "Reported", ev_merged: "Another citizen joined", ev_filed: "Filed", ev_reminder: "Reminder sent", ev_escalated: "Escalated", ev_resolved: "Fixed", ev_notified: "Reporters notified",
    r_done_dup: "This issue was already filed. Your report was added, so {n} citizens are now on this complaint.",
    r_done_ok: "Filed with the department. If there's no response within {t}, CIVIC TRACE sends a reminder, then escalates.",
    t_title: "Track a complaint", t_lead: "Every step CIVIC TRACE takes is recorded here.",
    t_ph: "Reference number, e.g. CT-0004 or GRV-604281", t_btn: "Track", t_citizens: "Citizens", t_filed: "Filed",
    t_days: "Days open", t_follow: "Follow-up", t_photos: "Photos", t_trail: "Audit trail", t_notfound: "No complaint with that reference number.",
  },
  kn: {
    nav_report: "ವರದಿ", nav_track: "ಟ್ರ್ಯಾಕ್", nav_dash: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", nav_dept: "ಇಲಾಖೆ",
    r_title: "ನಾಗರಿಕ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ",
    r_lead: "ಫೋಟೋ ತೆಗೆಯಿರಿ, ಉಳಿದದ್ದು ನಾವು ನೋಡಿಕೊಳ್ಳುತ್ತೇವೆ. ಏಜೆಂಟ್ ಸರಿಯಾದ ಇಲಾಖೆಯನ್ನು ಹುಡುಕುತ್ತದೆ, ನಿಮ್ಮ ಒಪ್ಪಿಗೆಯ ನಂತರವೇ ದೂರು ಸಲ್ಲಿಸುತ್ತದೆ ಮತ್ತು ಸಮಸ್ಯೆ ಸರಿಯಾಗುವವರೆಗೆ ಬೆನ್ನಟ್ಟುತ್ತದೆ.",
    r_s1: "1. ಸಮಸ್ಯೆ ಏನು?", r_photo: "📷 ಫೋಟೋ ಸೇರಿಸಲು ಟ್ಯಾಪ್ ಮಾಡಿ (ಐಚ್ಛಿಕ)", r_desc: "ವಿವರಿಸಿ",
    r_desc_ph: "ಉದಾ: ಮುಖ್ಯ ರಸ್ತೆಯ ಗೇಟ್ 2 ಬಳಿ ಆಳವಾದ ಗುಂಡಿ, ಬೈಕ್‌ಗಳಿಗೆ ಅಪಾಯಕಾರಿ",
    r_s2: "2. ಎಲ್ಲಿದೆ?", r_locate: "📍 ನನ್ನ ಸ್ಥಳ ಬಳಸಿ", r_maphint: "ಅಥವಾ ಪಿನ್ ಸರಿಸಲು ನಕ್ಷೆಯ ಮೇಲೆ ಟ್ಯಾಪ್ ಮಾಡಿ.",
    r_landmark: "ಹೆಗ್ಗುರುತು (ಐಚ್ಛಿಕ)", r_landmark_ph: "ಉದಾ: ಗೇಟ್ 2, ಮುಖ್ಯ ರಸ್ತೆ", r_send: "CIVIC TRACE ಏಜೆಂಟ್‌ಗೆ ಕಳುಹಿಸಿ",
    r_working: "ಏಜೆಂಟ್ ಕೆಲಸ ಮಾಡುತ್ತಿದೆ", r_s3: "3. ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಒಪ್ಪಿಗೆ ನೀಡಿ", r_english: "ದೂರನ್ನು ಇಲಾಖೆಗಾಗಿ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಬರೆಯಲಾಗಿದೆ, ನಿಮ್ಮ ವಿವರಣೆಯೊಂದಿಗೆ.",
    r_how: "ಹೇಗೆ ಸಲ್ಲಿಸಬೇಕು?", r_email: "ಅಧಿಕೃತ ಇಮೇಲ್", r_portal: "ಕುಂದುಕೊರತೆ ಪೋರ್ಟಲ್",
    r_approve: "✓ ಒಪ್ಪಿ ಸಲ್ಲಿಸಿ", r_notnow: "ಈಗ ಬೇಡ", r_nothing: "ನಿಮ್ಮ ಒಪ್ಪಿಗೆ ಇಲ್ಲದೆ ನಿಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಏನನ್ನೂ ಕಳುಹಿಸಲಾಗುವುದಿಲ್ಲ.",
    r_filed: "ದೂರು ಸಲ್ಲಿಸಲಾಗಿದೆ", r_trackbtn: "ಈ ದೂರನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ", r_next: "ಮುಂದೆ ಏನಾಗುತ್ತದೆ",
    r_n1: "ಏಜೆಂಟ್ ಸಮಸ್ಯೆ ಮತ್ತು ಸರಿಯಾದ ಇಲಾಖೆಯನ್ನು ಗುರುತಿಸುತ್ತದೆ.", r_n2: "ಹತ್ತಿರದಲ್ಲಿ ಬೇರೆಯವರು ವರದಿ ಮಾಡಿದ್ದರೆ, ನಿಮ್ಮ ವರದಿ ಅದಕ್ಕೆ ಸೇರುತ್ತದೆ.",
    r_n3: "ಏನನ್ನಾದರೂ ಕಳುಹಿಸುವ ಮೊದಲು ನೀವು ದೂರಿಗೆ ಒಪ್ಪಿಗೆ ನೀಡುತ್ತೀರಿ.", r_n4: "ಪ್ರತಿಕ್ರಿಯೆ ಬರದಿದ್ದರೆ, ಅದು ಜ್ಞಾಪನೆ ಕಳುಹಿಸಿ ನಂತರ ಮೇಲಧಿಕಾರಿಗೆ ತಲುಪಿಸುತ್ತದೆ.",
    r_need: "ಫೋಟೋ ಅಥವಾ ಸಣ್ಣ ವಿವರಣೆ ಸೇರಿಸಿ.", r_sending: "ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ…", r_filing: "ಸಲ್ಲಿಸಲಾಗುತ್ತಿದೆ…",
    t_rti_h: "ಇನ್ನೂ ಸರಿಯಾಗಿಲ್ಲವೇ? RTI ಮೂಲಕ ಅಧಿಕೃತವಾಗಿ ಕೇಳಿ", t_rti_p: "ಮಾಹಿತಿ ಹಕ್ಕು ಕಾಯ್ದೆ 2005ರ ಅಡಿ, ಇಲಾಖೆ 30 ದಿನಗಳಲ್ಲಿ ಉತ್ತರಿಸಿ ಯಾವ ಕ್ರಮ ಕೈಗೊಂಡಿದೆ ಎಂದು ತಿಳಿಸಬೇಕು. CIVIC TRACE ಈ ದೂರಿನ ದಾಖಲೆಯಿಂದ ಅರ್ಜಿಯನ್ನು ಸಿದ್ಧಪಡಿಸುತ್ತದೆ.",
    t_rti_name: "ನಿಮ್ಮ ಹೆಸರು", t_rti_addr: "ನಿಮ್ಮ ವಿಳಾಸ, ಫೋನ್ ಅಥವಾ ಇಮೇಲ್", t_rti_btn: "RTI ಅರ್ಜಿ ಸಿದ್ಧಪಡಿಸಿ", t_rti_copy: "ಪಠ್ಯ ನಕಲಿಸಿ", t_rti_copied: "ನಕಲಿಸಲಾಗಿದೆ", t_rti_dl: ".txt ಡೌನ್‌ಲೋಡ್",
    ev_reported: "ವರದಿ ಮಾಡಲಾಗಿದೆ", ev_merged: "ಇನ್ನೊಬ್ಬ ನಾಗರಿಕರು ಸೇರಿದರು", ev_filed: "ಸಲ್ಲಿಸಲಾಗಿದೆ", ev_reminder: "ಜ್ಞಾಪನೆ ಕಳುಹಿಸಲಾಗಿದೆ", ev_escalated: "ಮೇಲಧಿಕಾರಿಗೆ ತಲುಪಿಸಲಾಗಿದೆ", ev_resolved: "ಸರಿಪಡಿಸಲಾಗಿದೆ", ev_notified: "ವರದಿಗಾರರಿಗೆ ತಿಳಿಸಲಾಗಿದೆ",
    r_done_dup: "ಈ ಸಮಸ್ಯೆಯ ದೂರು ಈಗಾಗಲೇ ಸಲ್ಲಿಕೆಯಾಗಿದೆ. ನಿಮ್ಮ ವರದಿಯನ್ನು ಸೇರಿಸಲಾಗಿದೆ, ಈಗ {n} ನಾಗರಿಕರು ಈ ದೂರಿನಲ್ಲಿದ್ದಾರೆ.",
    r_done_ok: "ಇಲಾಖೆಗೆ ಸಲ್ಲಿಸಲಾಗಿದೆ. {t} ಒಳಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಬರದಿದ್ದರೆ, CIVIC TRACE ಜ್ಞಾಪನೆ ಕಳುಹಿಸಿ ನಂತರ ಮೇಲಧಿಕಾರಿಗೆ ತಲುಪಿಸುತ್ತದೆ.",
    t_title: "ದೂರನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ", t_lead: "CIVIC TRACE ತೆಗೆದುಕೊಳ್ಳುವ ಪ್ರತಿಯೊಂದು ಹೆಜ್ಜೆಯನ್ನು ಇಲ್ಲಿ ದಾಖಲಿಸಲಾಗುತ್ತದೆ.",
    t_ph: "ಉಲ್ಲೇಖ ಸಂಖ್ಯೆ, ಉದಾ: CT-0004", t_btn: "ಟ್ರ್ಯಾಕ್", t_citizens: "ನಾಗರಿಕರು", t_filed: "ಸಲ್ಲಿಸಿದ ದಿನ",
    t_days: "ತೆರೆದ ದಿನಗಳು", t_follow: "ಫಾಲೋ-ಅಪ್", t_photos: "ಫೋಟೋಗಳು", t_trail: "ಕ್ರಮಗಳ ದಾಖಲೆ", t_notfound: "ಈ ಉಲ್ಲೇಖ ಸಂಖ್ಯೆಯ ದೂರು ಇಲ್ಲ.",
  },
  hi: {
    nav_report: "रिपोर्ट", nav_track: "ट्रैक", nav_dash: "डैशबोर्ड", nav_dept: "विभाग",
    r_title: "नागरिक समस्या की शिकायत करें",
    r_lead: "फ़ोटो लीजिए, बाकी हम संभालेंगे। एजेंट सही विभाग ढूँढता है, आपकी मंज़ूरी के बाद ही शिकायत दर्ज करता है, और समस्या ठीक होने तक पीछा करता है।",
    r_s1: "1. समस्या क्या है?", r_photo: "📷 फ़ोटो जोड़ने के लिए टैप करें (वैकल्पिक)", r_desc: "विवरण लिखें",
    r_desc_ph: "जैसे: मेन रोड पर गेट 2 के पास गहरा गड्ढा, बाइक के लिए खतरनाक",
    r_s2: "2. यह कहाँ है?", r_locate: "📍 मेरी लोकेशन इस्तेमाल करें", r_maphint: "या पिन हटाने के लिए नक्शे पर टैप करें।",
    r_landmark: "पास का कोई निशान (वैकल्पिक)", r_landmark_ph: "जैसे: गेट 2, मेन रोड", r_send: "CIVIC TRACE एजेंट को भेजें",
    r_working: "एजेंट काम कर रहा है", r_s3: "3. जाँचें और मंज़ूरी दें", r_english: "शिकायत विभाग के लिए अंग्रेज़ी में लिखी गई है, आपके विवरण के साथ।",
    r_how: "शिकायत कैसे दर्ज हो?", r_email: "आधिकारिक ईमेल", r_portal: "शिकायत पोर्टल",
    r_approve: "✓ मंज़ूरी दें और दर्ज करें", r_notnow: "अभी नहीं", r_nothing: "आपकी मंज़ूरी के बिना आपके नाम से कुछ नहीं भेजा जाता।",
    r_filed: "शिकायत दर्ज हो गई", r_trackbtn: "इस शिकायत को ट्रैक करें", r_next: "आगे क्या होगा",
    r_n1: "एजेंट समस्या और सही विभाग पहचानता है।", r_n2: "अगर आस-पास किसी और ने शिकायत की है, तो आपकी रिपोर्ट उसमें जुड़ जाती है।",
    r_n3: "कुछ भी भेजने से पहले आप शिकायत को मंज़ूरी देते हैं।", r_n4: "जवाब न आने पर यह रिमाइंडर भेजता है, फिर वरिष्ठ अधिकारी तक ले जाता है।",
    r_need: "फ़ोटो या छोटा विवरण जोड़ें।", r_sending: "भेजा जा रहा है…", r_filing: "दर्ज किया जा रहा है…",
    t_rti_h: "अब भी ठीक नहीं हुआ? RTI से आधिकारिक जवाब माँगें", t_rti_p: "सूचना का अधिकार अधिनियम, 2005 के तहत विभाग को 30 दिनों में जवाब देना होता है कि क्या कार्रवाई हुई। CIVIC TRACE इस शिकायत के रिकॉर्ड से आवेदन तैयार करता है।",
    t_rti_name: "आपका नाम", t_rti_addr: "आपका पता, फ़ोन या ईमेल", t_rti_btn: "RTI आवेदन तैयार करें", t_rti_copy: "टेक्स्ट कॉपी करें", t_rti_copied: "कॉपी हो गया", t_rti_dl: ".txt डाउनलोड करें",
    ev_reported: "रिपोर्ट की गई", ev_merged: "एक और नागरिक जुड़ा", ev_filed: "दर्ज की गई", ev_reminder: "रिमाइंडर भेजा गया", ev_escalated: "वरिष्ठ अधिकारी को भेजी गई", ev_resolved: "ठीक हो गई", ev_notified: "रिपोर्ट करने वालों को सूचना दी गई",
    r_done_dup: "यह शिकायत पहले ही दर्ज है। आपकी रिपोर्ट जोड़ दी गई है, अब {n} नागरिक इस शिकायत में हैं।",
    r_done_ok: "विभाग में दर्ज हो गई। {t} में जवाब न आने पर CIVIC TRACE रिमाइंडर भेजेगा, फिर वरिष्ठ अधिकारी तक ले जाएगा।",
    t_title: "शिकायत ट्रैक करें", t_lead: "CIVIC TRACE का हर कदम यहाँ दर्ज होता है।",
    t_ph: "संदर्भ संख्या, जैसे CT-0004", t_btn: "ट्रैक", t_citizens: "नागरिक", t_filed: "दर्ज",
    t_days: "खुले दिन", t_follow: "फ़ॉलो-अप", t_photos: "फ़ोटो", t_trail: "कार्रवाई का रिकॉर्ड", t_notfound: "इस संदर्भ संख्या की कोई शिकायत नहीं मिली।",
  },
};

let LANG = "en";
try { LANG = localStorage.getItem("ct_lang") || "en"; } catch (e) { /* storage unavailable */ }
if (!I18N[LANG]) LANG = "en";

function t(key) { return (I18N[LANG] && I18N[LANG][key]) || I18N.en[key] || key; }

function applyLang(lang) {
  if (lang && I18N[lang]) LANG = lang;
  try { localStorage.setItem("ct_lang", LANG); } catch (e) { /* ignore */ }
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll(".lang button").forEach(b => b.classList.toggle("on", b.dataset.lang === LANG));
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".lang button").forEach(b => b.onclick = () => applyLang(b.dataset.lang));
  applyLang();
});
