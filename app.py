import webview
import json
import os
import random
import sys


if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "PruefungsfragenZIP", "fragenkatalog3b.json")
SVG_DIR = os.path.join(BASE_DIR, "PruefungsfragenZIP", "svgs")
PROGRESS_FILE = os.path.join(BASE_DIR, "fortschritt.json")


def extract_questions(sections, target_class):
    questions = []
    for section in sections:
        if "questions" in section:
            for q in section["questions"]:
                if str(q.get("class", "")) == str(target_class):
                    questions.append(q)
        if "sections" in section:
            questions.extend(extract_questions(section["sections"], target_class))
    return questions


def load_svg(name):
    if not name:
        return None
    filename = name if name.endswith(".svg") else name + ".svg"
    candidates = [
        os.path.join(SVG_DIR, filename),
        os.path.join(BASE_DIR, "PruefungsfragenZIP", "Bilder", filename),
        os.path.join(BASE_DIR, "PruefungsfragenZIP", "images", filename),
        os.path.join(BASE_DIR, "PruefungsfragenZIP", filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return None


class Api:
    def __init__(self):
        self.questions_by_class = {}
        self.progress = {}
        self._current_qnum = None
        self._current_correct_idx = None
        self.load_data()

    def load_data(self):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        sections = data.get("sections", [])
        for cls in ("1", "2", "3"):
            self.questions_by_class[cls] = extract_questions(sections, cls)
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    self.progress = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.progress = {}

    def save_progress(self):
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)

    def _score(self, qnum):
        return self.progress.get(qnum, 0)

    def _set_score(self, qnum, val):
        self.progress[qnum] = max(0, min(5, val))

    def get_progress(self, class_id):
        cls = str(class_id)
        qs = self.questions_by_class.get(cls, [])
        total = len(qs)
        learned = sum(1 for q in qs if self._score(q["number"]) >= 1)
        return {
            "total": total,
            "learned": learned,
            "percent": round(learned / total * 100) if total else 0,
        }

    def get_question(self, class_id):
        cls = str(class_id)
        qs = self.questions_by_class.get(cls, [])
        unlearned = [q for q in qs if self._score(q["number"]) < 5]
        if not unlearned:
            return {"done": True}
        q = random.choice(unlearned)
        qnum = q["number"]

        answers = [
            {
                "key": "a",
                "text": q.get("answer_a", ""),
                "correct": True,
                "image_svg": load_svg(q.get("picture_a")),
            },
            {
                "key": "b",
                "text": q.get("answer_b", ""),
                "correct": False,
                "image_svg": load_svg(q.get("picture_b")),
            },
            {
                "key": "c",
                "text": q.get("answer_c", ""),
                "correct": False,
                "image_svg": load_svg(q.get("picture_c")),
            },
            {
                "key": "d",
                "text": q.get("answer_d", ""),
                "correct": False,
                "image_svg": load_svg(q.get("picture_d")),
            },
        ]
        random.shuffle(answers)
        self._current_qnum = qnum
        self._current_correct_idx = next(i for i, a in enumerate(answers) if a["correct"])

        image_svg = None
        pic = q.get("picture_question")
        if pic:
            image_svg = load_svg(pic)
        if image_svg is None:
            img = q.get("image")
            if img:
                image_svg = load_svg(img)

        return {
            "number": qnum,
            "question": q["question"],
            "answers": [
                {"key": a["key"], "text": a["text"], "image_svg": a["image_svg"]}
                for a in answers
            ],
            "image_svg": image_svg,
            "current_score": self._score(qnum),
            "done": False,
        }

    def check_answer(self, question_number, selected_index):
        if self._current_qnum != question_number:
            return {"error": "No active question"}
        is_correct = selected_index == self._current_correct_idx
        score = self._score(question_number)
        if is_correct:
            score = min(5, score + 1)
        else:
            score = max(0, score - 1)
        self._set_score(question_number, score)
        self.save_progress()
        return {
            "correct": is_correct,
            "correct_index": self._current_correct_idx,
            "new_score": score,
        }


HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amateurfunk Prüfungsvorbereitung</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<style>
:root {
  --bg: #0f1117;
  --bg-alt: #161922;
  --surface: #1e2230;
  --surface-hover: #262b3d;
  --surface-elevated: #2a3045;
  --text: #e8edf5;
  --text-dim: #8891a8;
  --text-muted: #5b647e;
  --accent: #5b8def;
  --accent-glow: rgba(91,141,239,0.25);
  --accent-hover: #7aa3ff;
  --correct: #34d399;
  --correct-bg: rgba(52,211,153,0.12);
  --incorrect: #f87171;
  --incorrect-bg: rgba(248,113,113,0.12);
  --border: #2a3045;
  --radius: 14px;
  --radius-sm: 10px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  position: relative;
}
body::before {
  content: '';
  position: fixed;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at 30% 20%, rgba(91,141,239,0.06) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 80%, rgba(52,211,153,0.04) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}
#app {
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 24px 48px;
  position: relative;
  z-index: 1;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}
.app-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.class-picker {
  display: flex;
  gap: 4px;
  background: var(--surface);
  padding: 4px;
  border-radius: var(--radius-sm);
}
.class-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-dim);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.class-btn:hover { color: var(--text); }
.class-btn.active {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 2px 8px var(--accent-glow);
}

#stats-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 22px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
}
#stats-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
#stats-body { flex: 1; min-width: 0; }
#stats-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}
#stats-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
#progress-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}
#progress-bar {
  width: 100%;
  height: 6px;
  background: var(--bg-alt);
  border-radius: 3px;
  overflow: hidden;
}
#progress-fill {
  height: 100%;
  width: 0%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--accent), #34d399);
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

#question-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  transition: opacity 0.2s;
}
#q-number {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 14px;
  padding: 4px 12px;
  background: var(--accent-glow);
  border-radius: 6px;
}
#q-number .num-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}
#q-text {
  font-size: 16.5px;
  line-height: 1.7;
  font-weight: 500;
  margin-bottom: 22px;
  color: var(--text);
}
#q-text .katex { font-size: 1.05em; }

#svg-container {
  background: #fff;
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-bottom: 22px;
  display: none;
  justify-content: center;
  align-items: center;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
}
#svg-container svg { width: 100%; height: auto; max-width: 100%; max-height: 70vh; display: block; }
#svg-container.show { display: flex; }

#score-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
#score-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  padding: 4px 12px;
  background: var(--bg-alt);
  border-radius: 20px;
}
#score-badge .score-star {
  color: #fbbf24;
  font-size: 11px;
}

#answers {
  display: grid;
  gap: 10px;
}
.answer-btn {
  display: flex;
  align-items: center;
  width: 100%;
  text-align: left;
  padding: 16px 20px;
  background: var(--bg-alt);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: 15px;
  line-height: 1.5;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
  overflow: hidden;
}
.answer-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.18s;
}
.answer-btn:hover:not(.disabled) {
  border-color: var(--accent);
  background: var(--surface-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(91,141,239,0.1);
}
.answer-btn:active:not(.disabled) {
  transform: translateY(0);
  box-shadow: none;
}
.answer-btn .label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  color: var(--accent);
  background: var(--accent-glow);
  margin-right: 14px;
  flex-shrink: 0;
  transition: all 0.18s;
}
.answer-btn.correct {
  border-color: var(--correct);
  background: var(--correct-bg);
}
.answer-btn.correct .label {
  background: var(--correct);
  color: #fff;
}
.answer-btn.incorrect {
  border-color: var(--incorrect);
  background: var(--incorrect-bg);
  animation: shake 0.35s ease;
}
.answer-btn.incorrect .label {
  background: var(--incorrect);
  color: #fff;
}
.answer-btn.disabled { cursor: default; }
.answer-btn.disabled:not(.correct):not(.incorrect) { opacity: 0.5; }

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

.answer-svg-wrap {
  display: inline-flex;
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  margin: 2px 0;
  max-width: 100%;
  overflow: hidden;
  transition: border-color 0.18s;
}
.answer-svg-wrap svg {
  display: block;
  max-width: 100%;
  max-height: 70px;
  width: auto;
  height: auto;
}

#feedback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 700;
  min-height: 48px;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.25s ease;
}
#feedback.show {
  opacity: 1;
  transform: translateY(0);
}
#feedback.correct {
  background: var(--correct-bg);
  color: var(--correct);
}
#feedback.incorrect {
  background: var(--incorrect-bg);
  color: var(--incorrect);
}

#next-btn {
  display: none;
  width: 100%;
  margin-top: 14px;
  padding: 16px;
  background: linear-gradient(135deg, var(--accent), #7c6df0);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 16px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.2px;
  position: relative;
  overflow: hidden;
}
#next-btn::after {
  content: '\2192';
  margin-left: 6px;
  display: inline-block;
  transition: transform 0.2s;
}
#next-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px var(--accent-glow);
}
#next-btn:hover::after { transform: translateX(3px); }
#next-btn.show { display: block; }
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
#next-btn.show { animation: fadeSlideUp 0.3s ease; }

#done-message {
  display: none;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 56px 32px;
  text-align: center;
}
#done-message.show { display: block; }
#done-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}
#done-message h2 {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, var(--accent), #34d399);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
#done-message p {
  color: var(--text-dim);
  font-size: 15px;
  line-height: 1.6;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}
#done-message.show { animation: fadeIn 0.4s ease; }

.loading-dots::after {
  content: '';
  animation: dots 1.2s steps(4, end) infinite;
}
@keyframes dots {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
}
</style>
</head>
<body>
<div id="app">
  <div class="app-header">
    <div class="app-title">Amateurfunk Trainer</div>
    <div class="class-picker" id="class-picker">
      <button class="class-btn active" data-class="1">N</button>
      <button class="class-btn" data-class="2">E</button>
      <button class="class-btn" data-class="3">A</button>
    </div>
  </div>

  <div id="stats-card">
    <div id="stats-icon">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
    </div>
    <div id="stats-body">
      <div id="stats-header">
        <span id="stats-label">Lernfortschritt</span>
        <span id="progress-text">0 / 0</span>
      </div>
      <div id="progress-bar"><div id="progress-fill"></div></div>
    </div>
  </div>

  <div id="question-card">
    <div id="q-number"><span class="num-dot"></span> Frage laden...</div>
    <div id="q-text"></div>
    <div id="svg-container"></div>
    <div id="answers"></div>
    <div id="score-row" style="display:none">
      <div id="score-badge">&#9733; <span id="score-val">0</span>/5</div>
    </div>
    <div id="feedback"></div>
    <button id="next-btn">N&auml;chste Frage</button>
  </div>

  <div id="done-message">
    <span id="done-icon">&#10004;</span>
    <h2>Alle Fragen gelernt!</h2>
    <p>Herzlichen Gl&uuml;ckwunsch!<br>Du hast alle Fragen dieser Klasse erfolgreich abgeschlossen.</p>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script>
(function() {
  var currentClass = '1';
  var currentNumber = null;
  var answered = false;

  var picker = document.getElementById('class-picker');
  var qNumber = document.getElementById('q-number');
  var qText = document.getElementById('q-text');
  var svgContainer = document.getElementById('svg-container');
  var answersEl = document.getElementById('answers');
  var nextBtn = document.getElementById('next-btn');
  var feedback = document.getElementById('feedback');
  var progressText = document.getElementById('progress-text');
  var progressFill = document.getElementById('progress-fill');
  var questionCard = document.getElementById('question-card');
  var doneMessage = document.getElementById('done-message');
  var scoreRow = document.getElementById('score-row');
  var scoreVal = document.getElementById('score-val');

  function renderMath(el) {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(el, {delimiters:[{left:'$',right:'$',display:false},{left:'$$',right:'$$',display:true}]});
    }
  }

  function switchClass(cls) {
    currentClass = cls;
    picker.querySelectorAll('.class-btn').forEach(function(b) {
      b.classList.toggle('active', b.getAttribute('data-class') === cls);
    });
    loadQuestion();
    updateProgressFromServer();
  }

  function updateProgress(data) {
    progressText.textContent = data.learned + ' / ' + data.total;
    progressFill.style.width = data.percent + '%';
  }

  function loadQuestion() {
    answered = false;
    nextBtn.classList.remove('show');
    feedback.textContent = '';
    feedback.className = '';
    feedback.classList.remove('show');
    scoreRow.style.display = 'none';
    questionCard.style.display = 'block';
    doneMessage.classList.remove('show');

    pywebview.api.get_question(currentClass).then(function(data) {
      if (data.done) {
        questionCard.style.display = 'none';
        doneMessage.classList.add('show');
        return;
      }

      currentNumber = data.number;
      qNumber.innerHTML = '<span class="num-dot"></span> ' + data.number;
      qText.innerHTML = data.question;
      renderMath(qText);

      if (data.image_svg) {
        svgContainer.innerHTML = data.image_svg;
        svgContainer.classList.add('show');
      } else {
        svgContainer.innerHTML = '';
        svgContainer.classList.remove('show');
      }

      if (data.current_score > 0) {
        scoreRow.style.display = 'flex';
        scoreVal.textContent = data.current_score;
      }

      answersEl.innerHTML = '';
      var labels = ['A', 'B', 'C', 'D'];
      data.answers.forEach(function(ans, idx) {
        var btn = document.createElement('button');
        btn.className = 'answer-btn';

        var labelSpan = document.createElement('span');
        labelSpan.className = 'label';
        labelSpan.textContent = labels[idx];
        btn.appendChild(labelSpan);

        if (ans.image_svg) {
          var wrap = document.createElement('span');
          wrap.className = 'answer-svg-wrap';
          wrap.innerHTML = ans.image_svg;
          btn.appendChild(wrap);
        }

        if (ans.text && ans.text.trim()) {
          var textSpan = document.createElement('span');
          if (ans.image_svg) {
            textSpan.style.marginLeft = '8px';
          }
          textSpan.textContent = ans.text;
          btn.appendChild(textSpan);
          renderMath(textSpan);
        }

        btn.addEventListener('click', function() { selectAnswer(idx, data.number); });
        answersEl.appendChild(btn);
      });
    });
  }

  function selectAnswer(idx, qnum) {
    if (answered) return;
    answered = true;

    pywebview.api.check_answer(qnum, idx).then(function(result) {
      if (result.error) return;

      var btns = answersEl.querySelectorAll('.answer-btn');
      btns.forEach(function(btn, i) {
        btn.classList.add('disabled');
        if (i === result.correct_index) {
          btn.classList.add('correct');
        } else if (i === idx && !result.correct) {
          btn.classList.add('incorrect');
        }
      });

      feedback.textContent = result.correct ? '\u2713 Richtig! (+1)' : '\u2717 Falsch! (-1)';
      feedback.className = result.correct ? 'correct' : 'incorrect';
      feedback.classList.add('show');

      nextBtn.classList.add('show');
      updateProgressFromServer();
    });
  }

  function updateProgressFromServer() {
    pywebview.api.get_progress(currentClass).then(updateProgress);
  }

  nextBtn.addEventListener('click', loadQuestion);

  picker.addEventListener('click', function(e) {
    var btn = e.target.closest('.class-btn');
    if (btn) {
      var cls = btn.getAttribute('data-class');
      if (cls !== currentClass) switchClass(cls);
    }
  });

  function init() {
    switchClass('1');
  }

  document.addEventListener('pywebviewready', init);
  if (typeof pywebview !== 'undefined' && pywebview.api) {
    init();
  }
})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    api = Api()
    window = webview.create_window(
        "Amateurfunk Prüfungsvorbereitung",
        html=HTML,
        js_api=api,
        width=900,
        height=750,
        min_size=(700, 600),
        text_select=True,
    )
    webview.start()
