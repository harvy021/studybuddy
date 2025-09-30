from flask import Flask, render_template, request, session, redirect, url_for
import re, random, os

app = Flask(_name_)
# secret key for session storage (ok for demo; change for production)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_for_prod_123")

# --- Extensive rule-based knowledge base ---
SUBJECT_SNIPPETS = {
    "math": [
        "Basic algebra tip: isolate the variable by moving other terms to the other side.",
        "To solve quadratic ax^2+bx+c=0 use the quadratic formula: x = (-b ± sqrt(b^2-4ac)) / (2a).",
        "For geometry, remember: area of a circle = πr², circumference = 2πr."
    ],
    "physics": [
        "Newton's 2nd law: F = ma (force = mass × acceleration).",
        "Energy types: kinetic (motion) and potential (position).",
        "Ohm's law for circuits: V = I × R (voltage = current × resistance)."
    ],
    "chemistry": [
        "The periodic table groups elements with similar properties. Alkali metals are in group 1.",
        "pH < 7 is acidic, pH = 7 neutral, pH > 7 basic.",
        "Common reaction types: synthesis, decomposition, single replacement, double replacement, combustion."
    ],
    "history": [
        "When studying history, timeline and cause-effect are most important — link events to outcomes.",
        "Tip: make short notes on 'who, when, where, why' for every historical event."
    ],
    "programming": [
        "Practice by building small projects. Break problems into functions and test each part.",
        "Common Python tip: use list comprehensions for concise loops, but prefer readability for complex logic."
    ]
}

GENERAL_RESPONSES = {
    "greeting": ["Hi! I'm StudyBuddy — your study assistant. How can I help you today?",
                 "Hello! Ready to study? Ask me for a study plan, explanations, or motivation."],
    "thanks": ["You're welcome! 😊", "Anytime — glad to help."],
    "bye": ["Goodbye! Study smart.", "Take care — good luck with your studies!"],
    "fallback": [
        "Hmm, I didn't quite get that. Try asking for a study plan, a quick explanation, or a motivational tip.",
        "I can help with study plans, summaries, and subject tips. Try: 'Give me a 2-hour study plan for physics.'"
    ],
    "motivation": [
        "Small steps every day lead to big results. Start with 25 minutes focused work.",
        "Remember: consistency beats intensity. Keep going — you’re doing fine!"
    ]
}

# helper: simple intent matcher
def match_intent(text):
    t = text.lower()
    # greetings
    if re.search(r'\b(hi|hello|hey|hii|hola)\b', t):
        return ("greeting", None)
    if re.search(r'\b(thank|thanks|thx|thnks)\b', t):
        return ("thanks", None)
    if re.search(r'\b(bye|goodbye|see you)\b', t):
        return ("bye", None)
    if re.search(r'\b(motivat|i am lazy|i feel lazy|encourag)\b', t):
        return ("motivation", None)
    if re.search(r'\b(study plan|timetable|study schedule|plan for)\b', t):
        return ("study_plan", None)
    if re.search(r'\b(explain|what is|define|why is|how to)\b', t):
        return ("explain", None)
    # subject requests
    for subj in SUBJECT_SNIPPETS.keys():
        if re.search(r'\b' + re.escape(subj) + r'\b', t):
            return ("subject", subj)
    # quick math help pattern
    if re.search(r'\bsolve|calculate|what is the value of\b', t):
        return ("calculate", None)
    # default
    return (None, None)

def generate_study_plan(text):
    # try to parse duration or subject from text
    subj = None
    m = re.search(r'for (\d+\s*(?:hour|hr|hours|h))', text, re.I)
    hours = None
    if m:
        hours_text = m.group(1)
        hours = int(re.search(r'\d+', hours_text).group())
    m2 = re.search(r'for ([a-zA-Z]+)$', text.strip())
    if m2 and m2.group(1).lower() in SUBJECT_SNIPPETS:
        subj = m2.group(1).lower()
    # default plan = 2 hours split in pomodoro blocks
    total_minutes = (hours * 60) if hours else 120
    block = 25
    short_break = 5
    blocks = total_minutes // (block + short_break)
    if blocks < 1:
        blocks = 1
    plan_lines = [f"Study Plan (~{total_minutes} minutes):"]
    for i in range(1, blocks+1):
        plan_lines.append(f"• Block {i}: {block} min focused study + {short_break} min break")
    plan_lines.append("• After 3–4 blocks take a longer 20–30 min break.")
    if subj:
        plan_lines.append(f"Focus topic: {subj.capitalize()}. Try to divide the topic into 3 subtopics.")
    plan_lines.append("Tip: Remove distractions, set a clear goal for each block.")
    return "\n".join(plan_lines)

def provide_explanation(text):
    # try to detect a subject keyword
    for subj in SUBJECT_SNIPPETS:
        if re.search(r'\b' + subj + r'\b', text.lower()):
            return random.choice(SUBJECT_SNIPPETS[subj])
    # fallback short explanations for common words
    if "pythagoras" in text.lower():
        return "Pythagoras theorem: in a right triangle, a² + b² = c² (c is the hypotenuse)."
    if "molecule" in text.lower():
        return "A molecule is two or more atoms chemically bonded together."
    return "Here's a short explanation: break the topic into smaller parts, understand definitions, then practice examples."

def calculate_answer(text):
    # VERY simple arithmetic parser (safe eval-like)
    # extract basic arithmetic expressions like 2+2, 3*4, 10/2
    m = re.search(r'([0-9\.\s]+\s*[\+\-\\/]\s[0-9\.\s]+)', text)
    if m:
        expr = m.group(1)
        try:
            # safe eval: allow only digits, operators and dots
            if re.match(r'^[0-9\.\s\+\-\*\/]+$', expr):
                val = eval(expr)
                return f"The answer is: {val}"
        except Exception:
            pass
    return "I couldn't parse the calculation. Try a simple expression like 'Calculate 12 + 7'."

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'chat' not in session:
        session['chat'] = []
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            session['chat'].append(('You', message))
            intent, data = match_intent(message)
            if intent == 'greeting':
                reply = random.choice(GENERAL_RESPONSES['greeting'])
            elif intent == 'thanks':
                reply = random.choice(GENERAL_RESPONSES['thanks'])
            elif intent == 'bye':
                reply = random.choice(GENERAL_RESPONSES['bye'])
            elif intent == 'motivation':
                reply = random.choice(GENERAL_RESPONSES['motivation'])
            elif intent == 'study_plan':
                reply = generate_study_plan(message)
            elif intent == 'subject' and data:
                # craft a helpful subject reply with a short tip + example
                tip = random.choice(SUBJECT_SNIPPETS.get(data, ["Try to practice examples."]))
                reply = f"Subject: {data.capitalize()}\n{tip}"
            elif intent == 'explain':
                reply = provide_explanation(message)
            elif intent == 'calculate':
                reply = calculate_answer(message)
            else:
                # enhanced fallback: try small-talk keywords
                if re.search(r'\bhow are you\b', message.lower()):
                    reply = "I'm StudyBuddy — ready and eager to help! How are your studies going?"
                elif re.search(r'\bwhat can you do\b', message.lower()):
                    reply = ("I can create study plans, give quick subject tips (math, physics, chemistry, history, programming), "
                             "motivate you, and answer simple calculation or explanation requests.")
                else:
                    reply = random.choice(GENERAL_RESPONSES['fallback'])
            session['chat'].append(('StudyBuddy', reply))
    return render_template('index.html', chat=session.get('chat', []))

@app.route('/clear')
def clear():
    session.pop('chat', None)
    return redirect(url_for('index'))

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
