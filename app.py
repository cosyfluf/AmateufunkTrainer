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
        learned = sum(1 for q in qs if self._score(q["number"]) >= 5)
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
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<style>
:root {
  --bg: #1a1d23;
  --surface: #282c35;
  --surface-hover: #323642;
  --text: #e0e0e0;
  --text-dim: #9e9e9e;
  --accent: #4a9eff;
  --accent-hover: #6bb1ff;
  --correct: #4caf50;
  --incorrect: #e53935;
  --border: #3a3f4b;
  --shadow: rgba(0,0,0,0.3);
  --radius: 10px;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  padding: 20px;
  min-height: 100vh;
}
#app { max-width: 800px; margin: 0 auto; }

header {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: 0 2px 12px var(--shadow);
  margin-bottom: 20px;
}
.header-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
header select {
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 15px;
  cursor: pointer;
  outline: none;
}
header select:focus { border-color: var(--accent); }

#stats { flex: 1; min-width: 200px; }
#progress-text {
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 6px;
}
#progress-bar {
  width: 100%;
  height: 8px;
  background: var(--bg);
  border-radius: 4px;
  overflow: hidden;
}
#progress-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--accent), #6fcf97);
  border-radius: 4px;
  transition: width 0.5s ease;
}

#question-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: 0 2px 12px var(--shadow);
}
#q-number {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}
#q-text {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 20px;
}
#q-text .katex { font-size: 1.05em; }

#svg-container {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  display: none;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
#svg-container svg {
  max-width: 100%;
  height: auto;
  display: block;
}
#svg-container.show { display: flex; }

#answers { display: grid; gap: 10px; }
.answer-btn {
  display: block;
  width: 100%;
  text-align: left;
  padding: 14px 18px;
  background: var(--bg);
  border: 2px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 15px;
  line-height: 1.5;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
}
.answer-btn:hover:not(.disabled) {
  background: var(--surface-hover);
  border-color: var(--accent);
}
.answer-btn:active:not(.disabled) { transform: scale(0.99); }
.answer-btn .label {
  display: inline-block;
  font-weight: 700;
  color: var(--accent);
  margin-right: 10px;
  min-width: 22px;
}
.answer-btn.correct {
  border-color: var(--correct);
  background: rgba(76,175,80,0.12);
}
.answer-btn.correct .label { color: var(--correct); }
.answer-btn.incorrect {
  border-color: var(--incorrect);
  background: rgba(229,57,53,0.12);
}
.answer-btn.incorrect .label { color: var(--incorrect); }
.answer-btn.disabled { cursor: default; opacity: 0.85; }

.answer-svg-wrap {
  display: inline-block;
  background: #fff;
  border-radius: 6px;
  padding: 8px;
  margin: 4px 0;
  max-width: 100%;
  overflow: hidden;
}
.answer-svg-wrap svg {
  display: block;
  max-width: 100%;
  max-height: 80px;
  width: auto;
  height: auto;
}

#next-btn {
  display: none;
  width: 100%;
  margin-top: 18px;
  padding: 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
#next-btn:hover { background: var(--accent-hover); }
#next-btn.show { display: block; }

#feedback {
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  margin-top: 14px;
  min-height: 24px;
}
#feedback.correct { color: var(--correct); }
#feedback.incorrect { color: var(--incorrect); }

#done-message {
  display: none;
  background: var(--surface);
  border-radius: var(--radius);
  padding: 48px 28px;
  text-align: center;
  box-shadow: 0 2px 12px var(--shadow);
}
#done-message.show { display: block; }
#done-message h2 {
  font-size: 24px;
  margin-bottom: 10px;
  color: var(--accent);
}
#done-message p { color: var(--text-dim); font-size: 15px; }

#score-badge {
  display: inline-block;
  background: var(--bg);
  color: var(--text-dim);
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  margin-bottom: 12px;
}
</style>
</head>
<body>
<div id="app">
  <header>
    <div class="header-row">
      <select id="class-select">
        <option value="1">Klasse N</option>
        <option value="2">Klasse E</option>
        <option value="3">Klasse A</option>
      </select>
      <div id="stats">
        <div id="progress-text">0 / 0 Fragen gelernt</div>
        <div id="progress-bar"><div id="progress-fill"></div></div>
      </div>
    </div>
  </header>

  <div id="question-card">
    <div id="q-number"></div>
    <div id="q-text"></div>
    <div id="svg-container"></div>
    <div id="answers"></div>
    <div id="score-badge"></div>
    <div id="feedback"></div>
    <button id="next-btn">N&auml;chste Frage</button>
  </div>

  <div id="done-message">
    <h2>Alle Fragen gelernt!</h2>
    <p>Herzlichen Gl&uuml;ckwunsch! Du hast alle Fragen dieser Klasse erfolgreich abgeschlossen.</p>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script>
(function() {
  var currentClass = '1';
  var currentNumber = null;
  var answered = false;

  var sel = document.getElementById('class-select');
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
  var scoreBadge = document.getElementById('score-badge');

  function renderMath(el) {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(el, {delimiters:[{left:'$',right:'$',display:false},{left:'$$',right:'$$',display:true}]});
    }
  }

  function updateProgress(data) {
    progressText.textContent = data.learned + ' / ' + data.total + ' Fragen gelernt';
    progressFill.style.width = data.percent + '%';
  }

  function loadQuestion() {
    answered = false;
    nextBtn.classList.remove('show');
    feedback.textContent = '';
    feedback.className = '';
    scoreBadge.textContent = '';

    pywebview.api.get_question(currentClass).then(function(data) {
      if (data.done) {
        questionCard.style.display = 'none';
        doneMessage.classList.add('show');
        return;
      }
      questionCard.style.display = 'block';
      doneMessage.classList.remove('show');

      currentNumber = data.number;
      qNumber.textContent = data.number;
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
        scoreBadge.textContent = 'Score: ' + data.current_score + '/5';
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
          var wrap = btn.querySelector('.answer-svg-wrap');
          if (wrap) {
            wrap.style.border = '3px solid var(--correct)';
          }
        } else if (i === idx && !result.correct) {
          btn.classList.add('incorrect');
          var wrap = btn.querySelector('.answer-svg-wrap');
          if (wrap) {
            wrap.style.border = '3px solid var(--incorrect)';
          }
        }
      });

      if (result.correct) {
        feedback.textContent = 'Richtig! (+1)';
        feedback.className = 'correct';
      } else {
        feedback.textContent = 'Falsch! (-1)';
        feedback.className = 'incorrect';
      }

      nextBtn.classList.add('show');
      updateProgressFromServer();
    });
  }

  function updateProgressFromServer() {
    pywebview.api.get_progress(currentClass).then(updateProgress);
  }

  nextBtn.addEventListener('click', loadQuestion);

  sel.addEventListener('change', function() {
    currentClass = sel.value;
    loadQuestion();
    updateProgressFromServer();
  });

  function init() {
    currentClass = sel.value;
    loadQuestion();
    updateProgressFromServer();
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
