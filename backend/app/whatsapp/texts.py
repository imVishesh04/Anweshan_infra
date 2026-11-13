"""Everything the WhatsApp bot says, in English, Hindi and Odia.

WhatsApp limits: button titles <= 20 characters, list row titles <= 24,
list button label <= 20, message body <= 1024. Keep new texts inside these.
The Odia and Hindi texts should be checked once by a native speaker.
"""

LANGS = ("en", "hi", "or")

GREETING = (
    "🙏 Namaste! Welcome to *ANWESHAN Infra* — Interiors · Spaces · Lifestyle.\n"
    "We design and build homes, modular kitchens, wardrobes, shops and offices, "
    "and we also repair & polish furniture.\n"
    "Answer a few quick questions and our designer will call you back. 😊\n\n"
    "Please choose your language (tap a button or type the number):\n"
    "कृपया अपनी भाषा चुनें · ଦୟାକରି ଆପଣଙ୍କ ଭାଷା ବାଛନ୍ତୁ\n\n"
    "1. English\n2. हिंदी\n3. ଓଡ଼ିଆ"
)

LANGUAGE_BUTTONS = [("lang_en", "English"), ("lang_hi", "हिंदी"), ("lang_or", "ଓଡ଼ିଆ")]

T = {
    "choose": {"en": "Choose", "hi": "चुनें", "or": "ବାଛନ୍ତୁ"},
    "invalid": {
        "en": "Please choose one of the options above 🙏",
        "hi": "कृपया ऊपर दिए गए विकल्पों में से एक चुनें 🙏",
        "or": "ଦୟାକରି ଉପର ବିକଳ୍ପରୁ ଗୋଟିଏ ବାଛନ୍ତୁ 🙏",
    },
    "got_service": {
        "en": "Thanks for your enquiry about *{service}* 👍 Just a few quick questions.",
        "hi": "*{service}* के बारे में पूछने के लिए धन्यवाद 👍 बस कुछ छोटे सवाल।",
        "or": "*{service}* ବିଷୟରେ ପଚାରିବା ପାଇଁ ଧନ୍ୟବାଦ 👍 କେବଳ କିଛି ଛୋଟ ପ୍ରଶ୍ନ।",
    },
    "ask_service": {
        "en": "What do you need help with?",
        "hi": "आपको किस काम में मदद चाहिए?",
        "or": "ଆପଣଙ୍କୁ କେଉଁ କାମରେ ସାହାଯ୍ୟ ଦରକାର?",
    },
    "ask_size": {
        "en": "How big is the place?",
        "hi": "जगह कितनी बड़ी है?",
        "or": "ଜାଗାଟି କେତେ ବଡ଼?",
    },
    "ask_furniture": {
        "en": "Which furniture needs work, and how many pieces?\n(e.g. 1 sofa, 4 chairs, dining table)",
        "hi": "कौन-सा फर्नीचर ठीक करवाना है, और कितने पीस?\n(जैसे 1 सोफा, 4 कुर्सी, डाइनिंग टेबल)",
        "or": "କେଉଁ ଫର୍ଣ୍ଣିଚର ଠିକ୍ କରିବାକୁ ହେବ, ଏବଂ କେତେ ପିସ୍?\n(ଯେପରି 1 ସୋଫା, 4 ଚେୟାର, ଡାଇନିଂ ଟେବୁଲ୍)",
    },
    "ask_other": {
        "en": "Please tell us in a few words what you need.",
        "hi": "कृपया कुछ शब्दों में बताएं कि आपको क्या चाहिए।",
        "or": "ଦୟାକରି କିଛି ଶବ୍ଦରେ କୁହନ୍ତୁ ଆପଣଙ୍କୁ କ'ଣ ଦରକାର।",
    },
    "too_short": {
        "en": "Please type a little more detail 🙏",
        "hi": "कृपया थोड़ा और विस्तार से लिखें 🙏",
        "or": "ଦୟାକରି ଟିକେ ଅଧିକ ବିବରଣୀ ଲେଖନ୍ତୁ 🙏",
    },
    "ask_location": {
        "en": "In which area and city is the place? Please type it.",
        "hi": "जगह किस एरिया और शहर में है? कृपया टाइप करें।",
        "or": "ଜାଗାଟି କେଉଁ ଅଞ୍ଚଳ ଓ ସହରରେ ଅଛି? ଦୟାକରି ଟାଇପ୍ କରନ୍ତୁ।",
    },
    "ask_status": {
        "en": "Is it a new place, or an old one to renovate?",
        "hi": "यह नई जगह है या पुरानी (रिनोवेशन)?",
        "or": "ଏହା ନୂଆ ଜାଗା ନା ପୁରୁଣା (ମରାମତି)?",
    },
    "ask_budget": {
        "en": "What is your approximate budget?",
        "hi": "आपका अनुमानित बजट कितना है?",
        "or": "ଆପଣଙ୍କ ଆନୁମାନିକ ବଜେଟ୍ କେତେ?",
    },
    "ask_timeline": {
        "en": "When do you want to start?",
        "hi": "काम कब शुरू करना है?",
        "or": "କାମ କେବେ ଆରମ୍ଭ କରିବାକୁ ଚାହାଁନ୍ତି?",
    },
    "ask_photos": {
        "en": "Please send 2–3 photos of the place (or the floor plan). It helps us give you the right ideas.\nNo photos right now? Tap *Skip*.",
        "hi": "कृपया जगह की 2–3 फोटो (या नक्शा) भेजें। इससे हम आपको सही आइडिया दे पाएंगे।\nअभी फोटो नहीं है? *छोड़ें* दबाएं।",
        "or": "ଦୟାକରି ଜାଗାର 2–3ଟି ଫଟୋ (କିମ୍ବା ନକ୍ସା) ପଠାନ୍ତୁ। ଏହା ଆମକୁ ଠିକ୍ ଆଇଡିଆ ଦେବାରେ ସାହାଯ୍ୟ କରିବ।\nବର୍ତ୍ତମାନ ଫଟୋ ନାହିଁ? *ଛାଡ଼ନ୍ତୁ* ଦବାନ୍ତୁ।",
    },
    "photo_received": {
        "en": "Got it ✅ Send more photos, or tap *Done*.",
        "hi": "मिल गई ✅ और फोटो भेजें, या *हो गया* दबाएं।",
        "or": "ପାଇଲୁ ✅ ଆଉ ଫଟୋ ପଠାନ୍ତୁ, କିମ୍ବା *ହୋଇଗଲା* ଦବାନ୍ତୁ।",
    },
    "ask_visit": {
        "en": "When can our designer visit or call you?",
        "hi": "हमारे डिज़ाइनर कब आ सकते हैं या कॉल कर सकते हैं?",
        "or": "ଆମ ଡିଜାଇନର୍ କେବେ ଆସିପାରିବେ ବା କଲ୍ କରିପାରିବେ?",
    },
    "done": {
        "en": "Thank you, {name}! 🙏 We have your details:\n\n{summary}\n\nOur team will call you on this number soon.{contact}\nTo start again, type *MENU*.",
        "hi": "धन्यवाद, {name}! 🙏 हमें आपकी जानकारी मिल गई है:\n\n{summary}\n\nहमारी टीम जल्द ही इसी नंबर पर आपको कॉल करेगी।{contact}\nफिर से शुरू करने के लिए *MENU* लिखें।",
        "or": "ଧନ୍ୟବାଦ, {name}! 🙏 ଆମେ ଆପଣଙ୍କ ବିବରଣୀ ପାଇଲୁ:\n\n{summary}\n\nଆମ ଟିମ୍ ଶୀଘ୍ର ଏହି ନମ୍ବରରେ ଆପଣଙ୍କୁ କଲ୍ କରିବେ।{contact}\nପୁଣି ଆରମ୍ଭ କରିବାକୁ *MENU* ଲେଖନ୍ତୁ।",
    },
    "after_done": {
        "en": "Thank you! 🙏 Our team has your details and will call you soon.{contact}\nTo start again, type *MENU*.",
        "hi": "धन्यवाद! 🙏 हमारी टीम के पास आपकी जानकारी है, वे जल्द ही कॉल करेंगे।{contact}\nफिर से शुरू करने के लिए *MENU* लिखें।",
        "or": "ଧନ୍ୟବାଦ! 🙏 ଆମ ଟିମ୍ ପାଖରେ ଆପଣଙ୍କ ବିବରଣୀ ଅଛି, ସେମାନେ ଶୀଘ୍ର କଲ୍ କରିବେ।{contact}\nପୁଣି ଆରମ୍ଭ କରିବାକୁ *MENU* ଲେଖନ୍ତୁ।",
    },
    "contact_line": {
        "en": "\nYou can also call or WhatsApp us on {phone}.",
        "hi": "\nआप हमें {phone} पर कॉल या WhatsApp भी कर सकते हैं।",
        "or": "\nଆପଣ ଆମକୁ {phone} ରେ କଲ୍ ବା WhatsApp ମଧ୍ୟ କରିପାରିବେ।",
    },
    "customer": {"en": "there", "hi": "जी", "or": "ଆଜ୍ଞା"},
}

# Labels used in the summary the customer sees at the end.
SUMMARY_LABELS = {
    "service": {"en": "Work", "hi": "काम", "or": "କାମ"},
    "details": {"en": "Details", "hi": "जानकारी", "or": "ବିବରଣୀ"},
    "size": {"en": "Size", "hi": "साइज़", "or": "ଆକାର"},
    "location": {"en": "Area", "hi": "एरिया", "or": "ଅଞ୍ଚଳ"},
    "status": {"en": "Place", "hi": "जगह", "or": "ଜାଗା"},
    "budget": {"en": "Budget", "hi": "बजट", "or": "ବଜେଟ୍"},
    "timeline": {"en": "Start", "hi": "शुरुआत", "or": "ଆରମ୍ଭ"},
    "photos": {"en": "Photos", "hi": "फोटो", "or": "ଫଟୋ"},
    "visit": {"en": "Visit / call", "hi": "विज़िट / कॉल", "or": "ଭିଜିଟ୍ / କଲ୍"},
}

# Each option: (id, {lang: title}). The English title is also what the owner
# sees in the admin panel, so keep the English clear.
OPTIONS = {
    "service": [
        ("svc_home", {"en": "Full home interior", "hi": "पूरा घर इंटीरियर", "or": "ପୂରା ଘର ଇଣ୍ଟେରିଅର"}),
        ("svc_kitchen", {"en": "Kitchen & wardrobe", "hi": "किचन और वॉर्डरोब", "or": "କିଚେନ ଓ ୱାର୍ଡରୋବ"}),
        ("svc_shop", {"en": "Shop / office", "hi": "दुकान / ऑफिस", "or": "ଦୋକାନ / ଅଫିସ"}),
        ("svc_furniture", {"en": "Furniture repair", "hi": "फर्नीचर रिपेयर", "or": "ଫର୍ଣ୍ଣିଚର ମରାମତି"}),
        ("svc_other", {"en": "Something else", "hi": "कुछ और", "or": "ଅନ୍ୟ କିଛି"}),
    ],
    "size": [
        ("size_1bhk", {"en": "1 BHK", "hi": "1 BHK", "or": "1 BHK"}),
        ("size_2bhk", {"en": "2 BHK", "hi": "2 BHK", "or": "2 BHK"}),
        ("size_3bhk", {"en": "3 BHK", "hi": "3 BHK", "or": "3 BHK"}),
        ("size_4bhk", {"en": "4+ BHK / Villa", "hi": "4+ BHK / विला", "or": "4+ BHK / ଭିଲା"}),
        ("size_shop", {"en": "Shop / office", "hi": "दुकान / ऑफिस", "or": "ଦୋକାନ / ଅଫିସ"}),
        ("size_unknown", {"en": "Not sure", "hi": "पता नहीं", "or": "ଜଣା ନାହିଁ"}),
    ],
    "status": [
        ("status_new", {"en": "New place", "hi": "नई जगह", "or": "ନୂଆ ଜାଗା"}),
        ("status_old", {"en": "Old (renovate)", "hi": "पुरानी (रिनोवेशन)", "or": "ପୁରୁଣା (ମରାମତି)"}),
    ],
    "budget": [
        ("budget_1", {"en": "Under ₹1 lakh", "hi": "₹1 लाख से कम", "or": "₹1 ଲକ୍ଷରୁ କମ୍"}),
        ("budget_2", {"en": "₹1–2 lakh", "hi": "₹1–2 लाख", "or": "₹1–2 ଲକ୍ଷ"}),
        ("budget_3", {"en": "₹2–5 lakh", "hi": "₹2–5 लाख", "or": "₹2–5 ଲକ୍ଷ"}),
        ("budget_4", {"en": "₹5–10 lakh", "hi": "₹5–10 लाख", "or": "₹5–10 ଲକ୍ଷ"}),
        ("budget_5", {"en": "Above ₹10 lakh", "hi": "₹10 लाख से ज़्यादा", "or": "₹10 ଲକ୍ଷରୁ ଅଧିକ"}),
        ("budget_unknown", {"en": "Not decided yet", "hi": "अभी तय नहीं", "or": "ସ୍ଥିର ହୋଇନାହିଁ"}),
    ],
    "timeline": [
        ("time_now", {"en": "Right away", "hi": "तुरंत", "or": "ତୁରନ୍ତ"}),
        ("time_month", {"en": "Within 1 month", "hi": "1 महीने में", "or": "1 ମାସ ଭିତରେ"}),
        ("time_later", {"en": "Later", "hi": "बाद में", "or": "ପରେ"}),
    ],
    "visit": [
        ("visit_tmr_am", {"en": "Tomorrow morning", "hi": "कल सुबह", "or": "କାଲି ସକାଳ"}),
        ("visit_tmr_pm", {"en": "Tomorrow evening", "hi": "कल शाम", "or": "କାଲି ସନ୍ଧ୍ୟା"}),
        ("visit_weekend", {"en": "This weekend", "hi": "इस वीकेंड", "or": "ଏହି ସପ୍ତାହାନ୍ତ"}),
        ("visit_call", {"en": "Call me first", "hi": "पहले कॉल करें", "or": "ପ୍ରଥମେ କଲ୍ କରନ୍ତୁ"}),
    ],
    "photos": [
        ("photos_skip", {"en": "Skip", "hi": "छोड़ें", "or": "ଛାଡ଼ନ୍ତୁ"}),
    ],
    "photos_more": [
        ("photos_done", {"en": "Done", "hi": "हो गया", "or": "ହୋଇଗଲା"}),
    ],
}
