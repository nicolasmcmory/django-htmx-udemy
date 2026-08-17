---
description: A description of your rule
---

# Key Learn — Agent Instructions

## 1 · HARD CONSTRAINTS — Read First

### 1.1 Conflict Priority

When rules conflict, resolve in this order (highest → lowest):

1. Security & data safety
2. Architecture boundaries & service-layer purity
3. Token / cost / latency constraints
4. Active learning product behavior
5. Developer ergonomics

### 1.2 Blocklist — NEVER Introduce

DO NOT add, import, or recommend any of the following:

| Banned                                                                    | Use instead                                                                   |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Redis, RabbitMQ, Celery, `django-q2`, `django-rq`                         | Django Tasks framework + `django-tasks-db`                                    |
| `websockets` (pip), Django Channels, WebSockets                           | HTMX polling                                                                  |
| Vector DBs (Pinecone, pgvector), embeddings, semantic search              | Relational PostgreSQL queries only                                            |
| React, Angular, Vue, any SPA framework                                    | Django templates + HTMX + Alpine.js                                           |
| Bootstrap, SASS, hand-rolled CSS utility classes (`.l-flex-row`, etc.)    | Tailwind CSS                                                                  |
| `axios`, `jQuery`, any JS framework except Alpine.js                      | Alpine.js directives + native `fetch()`                                       |
| `innerHTML`                                                               | `textContent` or `<template>` cloning                                         |
| `django-picklefield`, pickle-based serialization                          | JSON fields only (pickle = arbitrary code execution)                          |
| `localStorage`                                                            | Alpine.js `x-data` reactive state (see §5.6)                                  |
| Vanilla JS orchestrator patterns (`main.js` action registry)              | Alpine.js declarative directives (`x-data`, `@click`, `x-show`)               |
| Cross-app model imports (`from study.models import X` inside another app) | Call target app's `services.py`                                               |
| Django model inheritance in service classes                               | Composition via `__init__` (model inheritance creates ghost migration tables) |
| `django-csp` (third-party CSP package)                                    | Django auto-escaping (template engine escapes `{{ }}` output by default)      |
| Hardcoded secrets                                                         | `os.getenv()` / Secret Manager                                                |

### 1.3 Product Guardrails

- All AI outputs MUST stay grounded in user-curated course material (academic safety).
- DO NOT auto-shortcut core learning actions that should remain effortful (active learning).

---

## 2 · PROJECT MAP

### 2.1 Stack

- **Backend:** Django 6 · PostgreSQL · `google-genai` (Vertex AI)
- **Frontend:** Django templates · HTMX (Local Vendor via `static/vendor/`) · Alpine.js (Local Vendor via `static/vendor/`) · Tailwind CSS
- **Queue:** PostgreSQL-backed via Django Tasks + `django-tasks-db` — no Redis
- **Deploy:** Cloud Run (scale-to-zero)

### 2.2 Django Apps

| App             | Purpose                   | Key models                                                        |
| --------------- | ------------------------- | ----------------------------------------------------------------- |
| `users`         | Auth & profile            | `CustomUser` (`AbstractUser` + `token_balance`)                   |
| `knowledge_hub` | Content ingestion & bins  | `Bin`, `Document` (queued→processing→completed→failed), `KeyClip` |
| `study`         | SRS, quizzes, Socratic AI | `Summary`, `Flashcard` (SRS priority), `StudySession`             |

### 2.3 File Conventions Per App

- `models.py` — schema only (nouns).
- `services.py` — all behavior / orchestration (verbs).
- `views.py` — thin: request → service → template. No business logic.
- `forms.py` — validation authority.
- `urls.py` — route definitions.

### 2.4 Prototyping Sandbox

`in_dev/` contains prototyping scripts only. **NEVER import from `in_dev/` in any app module.** Production logic lives in `services.py`.

### 2.5 Template Blocks

Base template: `templates/base.html`
Available blocks: `{% block custom_style %}`, `{% block title %}`, `{% block content %}`.

---

## 3 · ARCHITECTURE

### 3.1 App Isolation (Modular Monolith)

- Each app is self-contained.
- Cross-app data access goes through the target app's `services.py`.
- ✅ `from study.services import create_summary`
- ❌ `from study.models import Summary` (in another app)

### 3.2 Service Layer (Composition over Inheritance)

- `models.py` = nouns. `services.py` = verbs.
- Views MUST be thin: request → instantiate service → return template.
- Stateful operations MUST be encapsulated in service classes.
- Private helpers (e.g., `_read_document_text`) are acceptable for stateless utilities.
- Service classes receive models via `__init__`. NEVER inherit from a model.

```python
# ✅ CORRECT
class QuizEngine:
    def __init__(self, session: StudySession, payload: dict):
        self._session = session
        self._payload = payload

# ❌ WRONG — creates ghost migration table
class QuizEngine(StudySession): ...
```

### 3.3 Rational Block Comments

- Every file MUST start with a docstring/comment block explaining its purpose and key decisions.
- When editing a file, update its Rational Block to reflect the change.

---

## 4 · BACKEND

### 4.1 Python & Type Safety

- All Python code MUST use strict type hints (PEP 484), especially in `services.py`.
- Run Mypy with `django-stubs` for static checking.
- Validate all Vertex AI JSON responses with **Pydantic** models before passing to the ORM. Never trust raw LLM dictionaries.

### 4.2 AI / Vertex AI

**Model routing:**

- **Gemini 2.5 Flash** → stateless data tasks (transcription, summarization, formatting).
- **Gemini 3.5 Flash** → high-cognitive tasks (Socratic dialogue, metacognition, quizzes).

**Context window discipline:**

- Every API call is stateless — inject all necessary context per call.
- Sliding chat history: max 4 recent turns (never full history).
- System prompt: ≤ 300 tokens.
- Retrieved payload: ≤ 1,300 tokens (e.g., 5 interleaved summaries).
- **Total target: ≤ 2,000 tokens. Hard ceiling: 4,000 tokens (Socratic dialogue only).**

**Retrieval (Behavioral RAG):**

- Purely relational: PostgreSQL queries + deterministic logic. No embeddings.
- Socratic priority: inject summaries with lowest mastery, then lowest `generation_count`.

**Reliability:**

- All Vertex AI calls MUST include retries, timeouts, and circuit-breaker fallback.
- Background AI tasks MUST use `select_for_update()` to prevent duplicate billing.

### 4.3 Database (PostgreSQL)

- Complex reads MUST use compound B-tree indexes (e.g., `Index(fields=['user', 'mastery', 'review_count'])`).
- Eradicate N+1: use `select_related()` / `prefetch_related()` before passing QuerySets to templates.
- DB-rendering paths: synchronous by default.
- Heavy I/O (AI calls): offload to Django Tasks async queue.

### 4.4 Background Tasks (Django Tasks Framework)

- Install both packages: `pip install django-tasks django-tasks-db` (framework + PostgreSQL backend).
- Author tasks using `from django.tasks import task`.
- Backend: `django-tasks-db` (PostgreSQL-backed, row-level locks via `SELECT FOR UPDATE`).
- Signal-Driven State Transitions: To maintain absolute architectural consistency, all background operations MUST be chained via Django Signals on state transitions (e.g., triggering the calendar recalibration task on a StudySession completion or cleaning up infrastructure via `post_delete`). Service classes handle the synchronous database mutations, while `signals.py` acts as the exclusive orchestrator for offloading asynchronous side-effects to the task queue.
- **Exception**: Background cleanups of inactive records may be executed via standard Django management commands scheduled via a cron-job.

**Required `settings.py` configuration:**

```python
INSTALLED_APPS = [
    # ...existing apps...
    "django_tasks_db",  # single app — registers the backend + DB models
]

TASKS = {
    "default": {
        "BACKEND": "django_tasks_db.DatabaseBackend",
        "QUEUES": ["default"],
    }
}
```

After adding, run `python manage.py migrate`. Start worker with `python manage.py db_worker`. Prune old completed tasks periodically with `python manage.py prune_db_task_results`.

### 4.5 Migrations

- Run `python manage.py makemigrations` after any model change; review the generated file before committing.
- DO NOT manually edit migration files unless resolving a merge conflict.
- Squash migrations only in development branches before merging to main.

### 4.6 Logging

- Use Python `logging` with structured JSON output (Cloud Run compatible).
- Each `services.py` MUST define: `logger = logging.getLogger(__name__)`.
- Levels: `ERROR` = exceptions/failures · `WARNING` = degraded paths (AI fallback) · `INFO` = task lifecycle · `DEBUG` = dev-only tracing.
- NEVER log secrets, passwords, API keys, or PII.

---

## 5 · FRONTEND

### 5.1 Rendering Ownership

- **Server** owns structure + persistent state (Django templates + HTMX).
- **Browser** owns ephemeral UI state (Alpine.js).
- HTMX: server-driven DOM updates, data-mutating flows, async polling.
- Alpine.js: local-only UI (drag, resize, toggle, show/hide, tabs).

### 5.2 JavaScript Architecture (Alpine.js)

- **Declarative directives.** Use `x-data`, `@click`, `x-show`, `x-bind`, `x-ref` directly in HTML templates. No separate JS orchestrator file.
- **No `main.js` action registry.** Alpine's event binding replaces global event delegation entirely.
- **Inline vs. external `Alpine.data()` — choose by complexity (see §5.2.1).** Small-to-medium UI helpers (toggles, tabs, basic limits) stay inline as `x-data="{...}"`. Complex components (dozens of lines of math, heavy UI algorithms, multi-step state machines) move to an external file registered via `Alpine.data('componentName', () => ({...}))`.
- **External component files live in `static/js/components/<name>.js`** (one component per file). A shared `static/js/alpine-components.js` may aggregate simple reusable behaviors (e.g., splitter resize) loaded before `Alpine.start()`. Either way, registration happens inside a `document.addEventListener('alpine:init', ...)` listener.
- **HTMX + Alpine interop:** After HTMX swaps, Alpine must re-initialize new DOM nodes. Add a global listener: `document.body.addEventListener('htmx:afterSettle', e => Alpine.initTree(e.detail.elt))`.
- Use `textContent` for DOM text injection. NEVER `innerHTML`.
- Type-cast all `data-*` reads: `Number(el.dataset.value)`.

#### 5.2.1 When to Externalize Alpine Logic

Choose your approach based on component scale and team needs:

**Stay inline (`x-data="{...}"` in the template) when:**

- The component is a small-to-medium UI helper (toggle, tab, basic limit, live counter).
- You want a zero-configuration "no-build" setup that works out of the box with the standard Alpine CDN build.
- The logic fits comfortably inside an HTML attribute without harming template readability.

**Move to an external file + `Alpine.data()` when:**

- Component logic is highly complex (dozens of lines of math, heavy UI algorithms, custom integration, multi-step state machines).
- You are working in a team where separating frontend scripts from HTML keeps Git commits cleaner.
- You want full JavaScript syntax highlighting, linting, and autocomplete in your IDE.

**External file pattern:**

```javascript
// static/js/components/calculator.js
function mortgageCalculator(defaultRate = 5.5) {
  return {
    amount: 250000,
    years: 30,
    rate: defaultRate,
    config: {},
    init() {
      // Still parse a single data-* config blob from the host element (§5.4)
      this.config = JSON.parse(this.$el.dataset.config);
    },
    get monthlyPayment() {
      // ...computation...
    },
  };
}

document.addEventListener('alpine:init', () => {
  Alpine.data('mortgageCalculator', mortgageCalculator);
});
```

```html
<script
  src="{% static 'js/components/calculator.js' %}"
  defer></script>

<div
  x-data="mortgageCalculator(6.0)"
  data-config="{{ calculator_config_json }}"
  class="p-6 bg-white border rounded">
  <input
    type="number"
    x-model.number="amount" />
  <span x-text="monthlyPayment"></span>
</div>
```

**CSP note:** This project does NOT enable CSP middleware (§6) and loads the **standard Alpine CDN build**, which relies on `new Function()` to evaluate inline `x-data`/`x-text` expressions. Externalizing logic to `Alpine.data()` does _not_ by itself satisfy a strict CSP — only Alpine's dedicated CSP build does, and that build _requires_ the external `Alpine.data()` approach (it disables inline attribute evaluation entirely). If a strict CSP is ever introduced later, switch to Alpine's CSP build and migrate every inline component to external files at that time.

### 5.2.2 Interaction & Animation: Tailwind vs. Alpine Transitions

Use Pure Tailwind or Alpine + Tailwind Class Binding (:class) if: The element stays visible on the screen, and you are just animating colors, shadows, positioning, or sizing. (No x-transition needed).

**State driven ui changes** - Use Alpine's x-transition ONLY if: You are actively introducing or removing an element from the flow of the document using x-show or x-if.

### 5.3 The Island Threshold (Alpine.js Islands)

Default to HTMX + Alpine.js for all interactive UI. Alpine.js handles reactive state, show/hide, tabs, and multi-step flows natively. A heavier framework is only justified when a feature requires:

1. **Canvas / WebGL rendering** — drawing, animation, or 3D that Alpine cannot express.
2. **Virtual DOM diffing** — rendering 1,000+ dynamic list items where Alpine's DOM approach becomes a bottleneck.

For all other interactive patterns (flashcard decks, quizzes, Socratic chat, drag-resize, modals), Alpine.js + HTMX is sufficient.

### 5.4 Server → Client State Passing

**The DHAT insight: if you combine Django + HTMX + Alpine correctly, you rarely pass Django variables into Alpine at all.** HTMX shifts the data flow away from SPA-style client/server synchronization. Django does what it does best — render HTML — and the frontend stays a thin shell over server-rendered truth.

**Mental model (three layers, no data crossing over):**

1. **Django holds the data and renders it.** Query the DB, process forms, embed values straight into HTML text, input `value="..."`, or classes. No JSON payload, no client-side state mirror.
2. **HTMX handles data mutations.** `hx-post` / `hx-put` sends raw form fields straight back to Django. Django saves, then returns a new chunk of plain HTML that HTMX swaps in. Alpine never holds that data in a JS variable.
3. **Alpine controls only the "CSS classes."** Alpine doesn't care _what_ the user data is — only whether a menu is `open`, a modal is `visible`, a tab is `active`. Its `x-data` is local UI state, not a mirror of DB rows.

**Streamlined workflow (default):**

1. Django renders a record into standard HTML: `<p>{{ user.email }}</p>`.
2. **Instant hide/show?** Alpine handles it with pure local state — `x-data="{ open: false }"`. No Django variable needed.
3. **Edit and save?** HTMX swaps the `<p>` for a Django-rendered form fragment: `<input value="{{ user.email }}">`. The user types into a standard HTML input and clicks save.
4. HTMX posts the raw form to Django, Django saves, and returns the updated `<p>` tag.

```html
<!-- ✅ CORRECT — Django renders data as HTML, HTMX moves it, Alpine only toggles -->
<p
  hx-get="{% url 'edit_email' %}"
  hx-target="this">
  {{ user.email }}
</p>

<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div
    x-show="open"
    x-cloak>
    …menu…
  </div>
</div>
```

```html
<!-- ❌ WRONG — over-engineered: Alpine trying to manage DB data -->
<div
  x-data="{ user: JSON.parse($el.dataset.user) }"
  data-user="{{ user_json }}">
  <input x-model="user.email" />
  <!-- now you need a custom fetch() to sync this JS object back to Django -->
</div>
```

**The one exception — client-side configuration, not user data.** The only time a Django variable crosses into Alpine is for _pure client-side configuration or limits_ that Alpine must enforce _before_ a network request: a max-length for a live countdown, a warn/error ratio, a blacklist of words for instant local feedback, drag-bounds, resize-limits. Core user data, DB records, and form state stay in HTML and let HTMX move them.

**Single-JSON-blob handoff (mandatory when the exception applies):** When you do need to pass multiple configuration values to an Alpine component, NEVER spread them across multiple `data-*` attributes and NEVER interpolate Django variables directly inside an `x-data="..."` attribute. Bundle them into ONE Python dict, serialize with `json.dumps()`, render into ONE `data-*` attribute, and expand via `JSON.parse($el.dataset.*)` in `init()`. This keeps a single source of truth (the rendered DOM), avoids attribute clutter, eliminates kebab-case ↔ camelCase friction (Python dict keys map 1:1 to JS object keys), and prevents template-injection vectors from leaking into Alpine's evaluator.

**1. Django view — package _configuration_ (not submission data) into one dict:**

```python
import json
from django.shortcuts import render

def form_page_view(request: HttpRequest) -> HttpResponse:
    # Front-end configuration rules — NOT the form data the user is editing
    input_rules = {
        'maxLen': 150,
        'warnRatio': 0.8,
        'blacklistedWords': ['spam', 'advertisement', 'buy-now'],
    }
    return render(request, 'my_form.html', {
        'rules_json': json.dumps(input_rules),
    })
```

**2. Template — Alpine reads config from one `data-*`, HTMX owns the form submission:**

```html
<!-- ✅ CORRECT — Alpine references static config for CSS toggles;
     HTMX reads the raw <textarea> and posts it to Django -->
<form
  hx-post="{% url 'submit_comment' %}"
  hx-target="#response-message">
  {% csrf_token %}
  <div
    x-data="{
      config: {},
      text: '',
      hasBadWord: false,
      init() { this.config = JSON.parse($el.dataset.config); },
      checkText() {
        this.hasBadWord = this.config.blacklistedWords.some(w =>
          this.text.toLowerCase().includes(w));
      }
    }"
    data-config="{{ rules_json }}"
    class="p-4 border rounded bg-white">
    <textarea
      name="comment_text"
      x-model="text"
      @input="checkText()"
      rows="3"></textarea>
    <span
      x-show="hasBadWord"
      x-cloak
      class="text-red-500"
      >⚠️ Avoid promotional language.</span
    >
    <span x-text="text.length"></span>/<span x-text="config.maxLen"></span>
  </div>
  <button type="submit">Post Comment</button>
</form>
<div id="response-message"></div>
```

```html
<!-- ❌ WRONG — Django var interpolated directly into x-data -->
<div x-data="{ maxLen: {{ form.message.field.max_length }} }">...</div>

<!-- ❌ WRONG — config spread across multiple data-* attributes -->
<div
  x-data="{ maxLen: Number($el.dataset.maxLen), warnRatio: Number($el.dataset.warnRatio) }"
  data-max-len="{{ max_len }}"
  data-warn-ratio="{{ warn_ratio }}">
  ...
</div>
```

Rules for the handoff:

1. **Default to no handoff.** Render data as HTML; let HTMX move it; let Alpine toggle. Reach for `data-*` only for client-side config/limits.
2. In the view, bundle every config value the component needs into ONE Python dict and serialize it with `json.dumps()` into a single context variable (e.g., `rules_json`).
3. Render that single JSON string into ONE `data-*` attribute on the element that carries `x-data` (e.g., `data-config="{{ rules_json }}"`).
4. Inside `x-data`, declare the target object as an empty placeholder (`config: {}`) and populate it in `init()` via `JSON.parse($el.dataset.config)`. This is reading from the DOM, not client hydration — the JSON is server-escaped by Django auto-escaping and re-parsed on the client.
5. Python dict keys MUST use the same casing as the intended JS object keys (e.g., `warnRatio`), so they map 1:1 without kebab-case conversion.
6. Never use `|safe` on user-derived content bound for `data-*`; rely on Django auto-escaping and re-parse on the client.
7. For reusable behavior registered via `Alpine.data('componentName', () => ({...}))` in `static/js/alpine-components.js`, pass the parsed blob as the factory argument: `x-data="charCounter(JSON.parse($el.dataset.config))" data-config="{{ rules_json }}"`.

**`HX-Trigger` headers** are the second permitted channel, used only for _global UI events_ (toasts, balance updates, navigation refreshes): `response['HX-Trigger'] = json.dumps({...})` → `body.addEventListener(...)`. This uses `json.dumps` only to format the HTTP header value — standard Django/HTMX practice, not client hydration.

### 5.5 Client → Server State Passing (Alpine → Django via HTMX)

**The reverse DHAT loop:** Alpine tracks rapid, ephemeral UI state locally (a ticking stopwatch, a countdown, a drag offset); HTMX catches the final snapshot and hands it back to Django as a standard form field. No custom `fetch()`, no JSON API endpoint, no `X-CSRFToken` plumbing by hand. Two methods cover every case:

| Method                         | When to use                                               | Trigger                          |
| ------------------------------ | --------------------------------------------------------- | -------------------------------- |
| **Hidden input + `hx-post`**   | Value should be saved when the user submits a form        | User clicks submit               |
| **`$dispatch` + `hx-trigger`** | Value should auto-save in the background at a fixed event | Timer hits zero, drag ends, etc. |

**Method 1 — Hidden input bound to Alpine state (default for submit-on-click):**

Bind Alpine's reactive value to a hidden `<input>` with `:value`. HTMX automatically includes it in the form POST alongside the other fields. Django reads it as a normal `request.POST` parameter.

```html
<form
  hx-post="{% url 'save_quiz_results' %}"
  hx-target="#quiz-response"
  x-data="{
    secondsElapsed: 0,
    timerInterval: null,
    init() {
      this.timerInterval = setInterval(() => this.secondsElapsed++, 1000);
    }
  }"
  @destroy="clearInterval(timerInterval)">
  {% csrf_token %}

  <!-- Alpine binds its local state into a standard hidden field; HTMX submits it -->
  <input
    type="hidden"
    name="time_taken"
    :value="secondsElapsed" />

  <p>Time Elapsed: <span x-text="secondsElapsed"></span> seconds</p>
  <input
    type="text"
    name="answer" />
  <button type="submit">Submit Answer</button>
</form>
<div id="quiz-response"></div>
```

**Method 2 — `$dispatch` custom event + `hx-trigger` (for background auto-save):**

When a value must reach Django the instant a client-side condition is met (countdown hits zero, drag ends) without waiting for a submit click, Alpine dispatches a custom event carrying the payload; HTMX listens for that event and fires the request.

```html
<div
  x-data="{
    timeLeft: 10,
    timerInterval: null,
    init() {
      this.timerInterval = setInterval(() => {
        if (this.timeLeft > 0) this.timeLeft--;
        else {
          clearInterval(this.timerInterval);
          $dispatch('timer-done', { secondsSpent: 10 });
        }
      }, 1000);
    }
  }"
  @timer-done.window="
    $el.setAttribute('hx-vals', JSON.stringify({ final_time: $event.detail.secondsSpent }));
    htmx.trigger($el, 'execute-submit');
  "
  hx-post="{% url 'timeout_auto_save' %}"
  hx-trigger="execute-submit"
  hx-target="#timer-status">
  {% csrf_token %}
  <span x-text="timeLeft">10</span>
</div>
<div id="timer-status"></div>
```

**Django side — identical for both methods.** The value arrives as a plain `POST` parameter; no special parsing, no JSON body handling.

```python
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST

@require_POST
def save_quiz_results(request: HttpRequest) -> HttpResponse:
    time_taken = request.POST.get('time_taken')  # Method 1
    final_time = request.POST.get('final_time')  # Method 2
    # ...service-layer call to persist...
    return HttpResponse("<p class='text-green-600'>Time recorded.</p>")
```

Rules for the reverse loop:

1. **Prefer Method 1.** If the value is part of a form the user submits anyway, a hidden `:value`-bound input is the simplest, most declarative option.
2. **Use Method 2 only for unsolicited background saves** — a timer expiring, a drag ending, an autosave tick — where there is no submit click to piggyback on.
3. **Never build a custom `fetch()` to a JSON endpoint** for this. HTMX already owns the Django ↔ browser mutation channel; duplicating it with a parallel `fetch()` creates two CSRF surfaces and desync risks.
4. **Alpine owns the rapid updates; HTMX owns the network.** A stopwatch ticking 60 times a minute stays in Alpine's `x-data`; only the final snapshot crosses to Django.

### 5.6 Client-Side State (Alpine Reactive State)

Alpine's `x-data` is a UI-state ledger, **not** a mirror of database records. Per §5.4, DB data lives in server-rendered HTML and is moved by HTMX; Alpine only tracks ephemeral UI (open/closed, current tab, drag position, multi-step progress, a live character counter). When a session interaction does need client-side working state (flashcard study, multi-step quiz):

- **NO `localStorage`.** Causes client/server desync and unnecessary serialization.
- **Two-Request Architecture:** Request 1 (HTMX `hx-get`) delivers the entire session as server-rendered HTML — Alpine reads any client-side _config_ it needs from a single `data-*` JSON blob (§5.4 exception), but the cards/questions themselves stay in the DOM. Request 2 (HTMX `hx-post`) submits the final state back as one batched form payload; Django re-renders the result. No custom `fetch()` to a JSON API.
- **Declare reactive UI state in `x-data` on the component root** (e.g., `currentCard`, `flipped`, `answers`). Alpine reads/mutates reactively. No parallel vanilla JS state objects, no raw `data-*` mutation from JS.
- **`x-data` initializes from the DOM, not from Django `{{ }}`.** When config must cross the SSR boundary, `x-data` pulls it from a single `data-*` attribute containing a server-serialized JSON blob (`JSON.parse($el.dataset.*)`) in `init()` — never from `{{ }}` interpolation inside the `x-data` expression. After initialization, `x-data` is the sole reactive ledger — do not mutate the underlying `data-*` attribute from JS.

### 5.7 CSS (Tailwind CSS v4.x via tailwind standalone cli)

- **Tailwind CSS** is the sole styling approach. No hand-written CSS files except for rare edge cases (e.g., third-party widget overrides).
- **Toolchain:** Standalone Tailwind CSS v4 CLI binary. NEVER introduce an npm-based Tailwind setup.
- **Tailwind version:** v4.x (current: v4.3).

**CSS-first configuration (v4 — no `tailwind.config.js`):**

All theme customization lives in the CSS entry file (`input.css`) using the `@theme` block. Design tokens become native CSS variables automatically.

```css
/* src/styles/input.css */
@import 'tailwindcss';

/* Explicitly declare template sources — v4 does NOT use a `content` array.
   Add one @source per template root so the scanner finds your classes. */
@source "../../templates";
@source "../../knowledge_hub/templates";
@source "../../study/templates";
@source "../../users/templates";

@theme {
  --color-brand-500: oklch(0.65 0.18 250);
  --font-display: 'Satoshi', sans-serif;
  --breakpoint-3xl: 1920px;
}
```

**Custom component utilities (v4 `@utility`, NOT `@utilities`):**

For repeating component patterns (`btn`, `card`, `modal`, `drawer`, `alert`, `badge`, `form-control`, etc. — mandatory if a pattern repeats more than twice), define them with the singular `@utility` directive:

```css
@utility btn {
  display: inline-flex;
  align-items: center;
  border-radius: 0.5rem;
  padding-inline: calc(var(--spacing) * 4);
  /* ... */
}
```

**Base template inclusion — use the template tag, not a hardcoded `<link>`:**

```html
{% load static%}
<!DOCTYPE html>
<html lang="en">
  <head>
    {% tailwind_css %} {% block custom_style %}{% endblock %}
  </head>
</html>
```

**Conventions:**

- **Mobile-first.** Tailwind is mobile-first by default. Responsive prefixes: `md:` (768px) · `lg:` (1024px) · `xl:` (1440px) · `3xl:` (custom, 1920px if defined in `@theme`).
- **No BEM naming.** No custom CSS classes for layout (`.l-flex-row`, `.l-stack`). Use Tailwind utilities directly in templates.
- **No `tailwind.config.js`.** v4 is CSS-first; all config lives in `input.css` via `@theme` / `@source` / `@utility`.
- **Every template directory MUST be covered by an `@source` directive** — v4 discovers classes exclusively through them. Missing `@source` = missing styles.

### 5.8 HTML, Alpine, and Third-Party Library Delivery

- **Zero External Network Dependencies:** DO NOT load HTMX, Alpine.js, Leaflet, or any other third-party frontend primitives directly from external public CDNs in production templates. -**Standard build** — no CSP middleware is enabled, so the CSP build is unnecessary.
- **The Vendor Repository:** All third-party library files MUST be downloaded locally during development and committed to the source control repository under the `static/vendor/` directory.
- **Environment Targeting:**
  - **Development:** Use the full, unminified vendor scripts (e.g., `static/vendor/leaflet.js`) inside templates to ensure clean browser console debugging and accurate stack traces.
  - **Production:** Point exclusively to the pre-minified vendor assets (e.g., `static/vendor/leaflet.min.js`) to minimize container image overhead and maximize browser rendering speeds.
- Inline `x-data="..."` with function bodies is permitted for simple components (§5.2.1). For complex or reusable behavior, move logic to an external file under `static/js/components/` (or `static/js/alpine-components.js` for small shared utilities) and register via `Alpine.data('componentName', () => ({...}))` inside a `document.addEventListener('alpine:init', ...)` listener, loaded before `Alpine.start()`. -**Dynamic DOM Reconciliation**: To ensure components loaded via async HTMX fragments are parsed correctly, the global lifecycle listener MUST be active on the base template to trigger Alpine initialization upon DOM settlement:
  `document.body.addEventListener('htmx:afterSettle', e => Alpine.initTree(e.detail.elt));`
- **Template Script Resolution:** Load all vendor assets using Django's native `{% static %}` template tag.
  ```html
  {% load static %}
  <script
    src="{% static 'vendor/htmx.min.js' %}"
    defer></script>
  <script
    src="{% static 'vendor/alpine.min.js' %}"
    defer></script>
  <script
    src="{% static 'vendor/leaflet.min.js' %}"
    defer></script>
  ```

### 5.9 Forms

- Django forms = validation authority (server-side truth).
- Templates = all presentation (Tailwind classes, `hx-*`, Alpine directives).
- Dual-layer validation: HTML5 client-side + Django server-side with consistent error UI.
- Use base inline Tailwind CSS classes or custom utilities for components repeating themselves more than twice.

---

## 6 · SECURITY

- CSRF middleware is always enabled. Alpine.js `fetch()` calls MUST include `X-CSRFToken`.
- **No Content-Security-Policy (CSP) middleware.** Do NOT install `django-csp` or enable Django 6's built-in `ContentSecurityPolicyMiddleware`. Rely on Django's template auto-escaping (the `{{ }}` tag escapes HTML by default) as the primary XSS defense. When rendering user-supplied content, prefer `textContent` (Alpine.js) over `innerHTML`, and never mark untrusted content as `|safe`.
- NEVER use `pickle` for user-facing or external data. JSON only.
- Validate all uploaded files (PDFs, audio) for type and size before processing.
- NEVER pass user input to `eval()`, `exec()`, or shell commands.
- Run `pip audit` periodically.
- All secrets via `os.getenv()` or Secret Manager. Never hardcode.

---

## 7 · i18n

- Django `gettext` as source of truth.
- Prefer server-side translated rendering.
- Use i18n URL routing for locale-aware routes.

---

## 8 · TESTING & DEPLOYMENT

### Testing

- Test through the service layer: each `services.py` class/function gets tests in `tests.py`.
- Use `TestCase` for DB tests, `SimpleTestCase` for pure logic.
- Mock Vertex AI calls with `unittest.mock.patch`. Never hit real APIs.
- Test task functions synchronously (call directly, no running worker).
- Run full suite: `python manage.py test`.
- Frontend: manual verification (no JS test framework at this stage).

### Deployment

- Cloud Run containerized, scale-to-zero.
- All env vars documented in `.env.example`.
