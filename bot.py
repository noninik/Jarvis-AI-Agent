import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
HISTORY_FILE = "chat_history.json"
OFFSET_FILE = "offset.txt"


# ============================================
# РЕЖИМЫ РАБОТЫ
# ============================================

MODES = {
    "helper": {
        "name": "💬 Помощник",
        "prompt": "Ты универсальный AI-помощник Jarvis. Отвечай кратко и по делу на русском. Конкретные ответы с примерами. Если просят код — давай готовый.",
        "emoji": "💬",
    },
    "business": {
        "name": "📊 Бизнес-аналитик",
        "prompt": "Ты бизнес-аналитик Jarvis. Анализируй рынки, конкурентов, тренды. Структурированные ответы с цифрами. Конкретные стратегии. На русском.",
        "emoji": "📊",
    },
    "content": {
        "name": "✍️ Контент-менеджер",
        "prompt": "Ты контент-менеджер Jarvis. Пишешь посты, статьи, рекламу. Живой дерзкий язык без воды. Цепляющие заголовки. На русском.",
        "emoji": "✍️",
    },
    "coder": {
        "name": "💻 Программист",
        "prompt": "Ты full-stack разработчик Jarvis. Пишешь чистый рабочий код на Python, JavaScript, HTML. Объясняешь просто. Готовый код. На русском.",
        "emoji": "💻",
    },
    "startup": {
        "name": "📋 Стартап-консультант",
        "prompt": "Ты стартап-консультант Jarvis. Бизнес-планы, идеи, unit-экономика. Разделы: идея, ЦА, конкуренты, MVP, монетизация, маркетинг, финансы. На русском.",
        "emoji": "📋",
    },
    "research": {
        "name": "🔍 Исследователь",
        "prompt": "Ты исследователь рынка Jarvis. Анализируй ниши, тренды, спрос, конкуренцию. Конкретные данные и рекомендации. На русском.",
        "emoji": "🔍",
    },
    "automate": {
        "name": "🚀 Автоматизатор",
        "prompt": "Ты эксперт по автоматизации Jarvis. Скрипты, боты, парсеры, автоматизация рутины. Готовый код на Python. На русском.",
        "emoji": "🚀",
    },
    "copywriter": {
        "name": "📝 Копирайтер",
        "prompt": "Ты профессиональный копирайтер Jarvis. Продающие тексты, лендинги, email-рассылки, УТП. Формулы AIDA, PAS. Без воды. На русском.",
        "emoji": "📝",
    },
    "coach": {
        "name": "🎯 Коуч",
        "prompt": "Ты лайф-коуч Jarvis. Помогаешь ставить цели, планировать, находить мотивацию. Задаёшь правильные вопросы. Конкретные шаги. На русском.",
        "emoji": "🎯",
    },
    "translator": {
        "name": "🌍 Переводчик",
        "prompt": "Ты профессиональный переводчик Jarvis. Переводишь тексты на/с английского. Объясняешь нюансы, идиомы. Даёшь варианты перевода. На русском.",
        "emoji": "🌍",
    },
}

DEFAULT_MODE = "helper"


# ============================================
# БЫСТРЫЕ ШАБЛОНЫ
# ============================================

TEMPLATES = {
    "biz_plan": {
        "name": "📋 Бизнес-план",
        "prompt": "Создай детальный бизнес-план. Спроси у меня нишу и бюджет, потом создай план с разделами: 1) Идея 2) Целевая аудитория 3) Конкуренты 4) MVP 5) Монетизация 6) Маркетинг 7) Финансы на 6 месяцев 8) Риски",
    },
    "content_plan": {
        "name": "📅 Контент-план",
        "prompt": "Создай контент-план на 2 недели. Спроси нишу, потом дай план: дата, тема, формат (пост/рилс/сторис), хештеги. 3 поста в день.",
    },
    "competitor": {
        "name": "🔍 Анализ конкурентов",
        "prompt": "Проведи анализ конкурентов. Спроси нишу, потом проанализируй: 5 главных конкурентов, их сильные и слабые стороны, ценообразование, УТП, что можно сделать лучше.",
    },
    "resume": {
        "name": "📄 Резюме",
        "prompt": "Помоги составить идеальное резюме. Спроси должность и опыт, потом создай структурированное резюме с разделами: контакты, о себе, опыт, навыки, образование.",
    },
    "post_pack": {
        "name": "✍️ Пак постов",
        "prompt": "Создай пак из 10 постов для соцсетей. Спроси нишу и тон, потом напиши 10 готовых постов разных форматов: продающий, развлекательный, экспертный, вовлекающий.",
    },
    "landing": {
        "name": "🌐 Текст лендинга",
        "prompt": "Напиши текст для лендинга. Спроси продукт/услугу, потом создай: заголовок, подзаголовок, блок проблем, решение, преимущества, отзывы (шаблоны), призыв к действию.",
    },
    "email_chain": {
        "name": "📧 Email-цепочка",
        "prompt": "Создай email-цепочку из 5 писем для прогрева клиента. Спроси нишу и продукт, потом напиши: приветственное, полезное, кейс, оффер, дожим.",
    },
    "swot": {
        "name": "📊 SWOT-анализ",
        "prompt": "Проведи SWOT-анализ. Спроси бизнес/идею, потом детально разбери: Strengths (сильные стороны), Weaknesses (слабые), Opportunities (возможности), Threats (угрозы).",
    },
}


# ============================================
# РАБОТА С ДАННЫМИ
# ============================================

def load_data(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f) if filename.endswith(".json") else f.read().strip()
    return default


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        if filename.endswith(".json"):
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            f.write(str(data))


def load_offset():
    try:
        return int(load_data(OFFSET_FILE, "0"))
    except:
        return 0


def load_history():
    return load_data(HISTORY_FILE, {})


def get_user_data(history, chat_id, key, default=""):
    return history.get(f"{chat_id}_{key}", default)


def set_user_data(history, chat_id, key, value):
    history[f"{chat_id}_{key}"] = value


def get_context(history, chat_id):
    return get_user_data(history, chat_id, "context", [])


def add_context(history, chat_id, role, text):
    ctx = get_context(history, chat_id)
    ctx.append({"role": role, "text": text[:1000]})
    if len(ctx) > 20:
        ctx = ctx[-20:]
    set_user_data(history, chat_id, "context", ctx)


# ============================================
# ИНСТРУМЕНТЫ
# ============================================

def search_web(query):
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result__body")[:5]:
            t = r.select_one(".result__title")
            s = r.select_one(".result__snippet")
            if t and s:
                results.append(f"• {t.get_text().strip()}\n  {s.get_text().strip()}")
        return "\n\n".join(results) if results else "Ничего не найдено"
    except Exception as e:
        return f"Ошибка: {e}"


def parse_website(url):
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        lines = [l.strip() for l in soup.get_text().splitlines() if l.strip()]
        return "\n".join(lines[:50])[:2000]
    except Exception as e:
        return f"Ошибка: {e}"


def summarize_text(text):
    return call_gemini(
        "Ты эксперт по суммаризации текстов на русском.",
        f"Сделай краткое содержание этого текста. Выдели 5 главных мыслей:\n\n{text[:3000]}",
        []
    )


def translate_text(text, direction="en-ru"):
    if direction == "en-ru":
        prompt = f"Переведи на русский и объясни сложные слова:\n\n{text}"
    else:
        prompt = f"Переведи на английский, дай 2 варианта (формальный и неформальный):\n\n{text}"
    return call_gemini("Ты профессиональный переводчик.", prompt, [])


# ============================================
# GEMINI API
# ============================================

def call_gemini(system_prompt, user_message, context):
    contents = []
    for msg in context[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["text"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 3000},
    }

    resp = requests.post(GEMINI_URL + "?key=" + GEMINI_API_KEY, json=body, timeout=60)
    if resp.status_code != 200:
        print("Gemini error:", resp.status_code, resp.text[:200])
        return "⚠️ AI временно недоступен. Попробуй через минуту."

    try:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Не удалось получить ответ"


# ============================================
# TELEGRAM API
# ============================================

def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    while text:
        chunk = text[:4000]
        text = text[4000:]
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"}
        if keyboard and not text:
            payload["reply_markup"] = json.dumps(keyboard)
        requests.post(url, json=payload, timeout=30)


def send_typing(chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=10)


def answer_callback(callback_id, text=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=10)


def get_updates(offset):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset, "timeout": 5, "limit": 20}, timeout=15)
    return resp.json() if resp.status_code == 200 else {"ok": False, "result": []}


# ============================================
# КЛАВИАТУРЫ
# ============================================

def main_keyboard():
    return {"inline_keyboard": [
        [
            {"text": "💬 Помощник", "callback_data": "mode_helper"},
            {"text": "📊 Бизнес", "callback_data": "mode_business"},
        ],
        [
            {"text": "✍️ Контент", "callback_data": "mode_content"},
            {"text": "💻 Код", "callback_data": "mode_coder"},
        ],
        [
            {"text": "📋 Стартап", "callback_data": "mode_startup"},
            {"text": "🔍 Исследование", "callback_data": "mode_research"},
        ],
        [
            {"text": "🚀 Автоматизация", "callback_data": "mode_automate"},
            {"text": "📝 Копирайтинг", "callback_data": "mode_copywriter"},
        ],
        [
            {"text": "🎯 Коуч", "callback_data": "mode_coach"},
            {"text": "🌍 Переводчик", "callback_data": "mode_translator"},
        ],
        [
            {"text": "📦 Шаблоны", "callback_data": "show_templates"},
            {"text": "🛠 Инструменты", "callback_data": "show_tools"},
        ],
    ]}


def templates_keyboard():
    return {"inline_keyboard": [
        [{"text": "📋 Бизнес-план", "callback_data": "tpl_biz_plan"}],
        [{"text": "📅 Контент-план", "callback_data": "tpl_content_plan"}],
        [{"text": "🔍 Анализ конкурентов", "callback_data": "tpl_competitor"}],
        [{"text": "📄 Резюме", "callback_data": "tpl_resume"}],
        [{"text": "✍️ Пак постов", "callback_data": "tpl_post_pack"}],
        [{"text": "🌐 Текст лендинга", "callback_data": "tpl_landing"}],
        [{"text": "📧 Email-цепочка", "callback_data": "tpl_email_chain"}],
        [{"text": "📊 SWOT-анализ", "callback_data": "tpl_swot"}],
        [{"text": "⬅️ Назад", "callback_data": "back_main"}],
    ]}


def tools_keyboard():
    return {"inline_keyboard": [
        [{"text": "🔍 Поиск в интернете", "callback_data": "tool_search"}],
        [{"text": "🌐 Спарсить сайт", "callback_data": "tool_parse"}],
        [{"text": "📝 Суммаризация текста", "callback_data": "tool_summarize"}],
        [{"text": "🇬🇧➡️🇷🇺 Перевод EN→RU", "callback_data": "tool_translate_enru"}],
        [{"text": "🇷🇺➡️🇬🇧 Перевод RU→EN", "callback_data": "tool_translate_ruen"}],
        [{"text": "🗑 Очистить контекст", "callback_data": "tool_clear"}],
        [{"text": "⬅️ Назад", "callback_data": "back_main"}],
    ]}


def after_response_keyboard():
    return {"inline_keyboard": [
        [
            {"text": "🔄 Подробнее", "callback_data": "act_more"},
            {"text": "📝 Переписать", "callback_data": "act_rewrite"},
        ],
        [
            {"text": "📋 Список", "callback_data": "act_list"},
            {"text": "🎯 Пример", "callback_data": "act_example"},
        ],
        [
            {"text": "🏠 Меню", "callback_data": "back_main"},
        ],
    ]}


# ============================================
# ОБРАБОТКА СООБЩЕНИЙ
# ============================================

def handle_callback(callback_query, history):
    chat_id = callback_query["message"]["chat"]["id"]
    callback_id = callback_query["id"]
    data = callback_query["data"]

    # Режимы
    if data.startswith("mode_"):
        mode_key = data[5:]
        if mode_key in MODES:
            set_user_data(history, chat_id, "mode", mode_key)
            set_user_data(history, chat_id, "context", [])
            set_user_data(history, chat_id, "waiting", "")
            mode = MODES[mode_key]
            answer_callback(callback_id, f"Режим: {mode['name']}")
            send_message(chat_id, f"{mode['emoji']} Режим: {mode['name']}\n\nЗадавай вопросы!", after_response_keyboard())

    # Шаблоны
    elif data == "show_templates":
        answer_callback(callback_id)
        send_message(chat_id, "📦 Выбери шаблон:", templates_keyboard())

    elif data.startswith("tpl_"):
        tpl_key = data[4:]
        if tpl_key in TEMPLATES:
            tpl = TEMPLATES[tpl_key]
            answer_callback(callback_id, tpl["name"])
            mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
            send_typing(chat_id)
            answer = call_gemini(
                MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
                tpl["prompt"],
                get_context(history, chat_id)
            )
            add_context(history, chat_id, "user", tpl["prompt"])
            add_context(history, chat_id, "assistant", answer)
            send_message(chat_id, answer, after_response_keyboard())

    # Инструменты
    elif data == "show_tools":
        answer_callback(callback_id)
        send_message(chat_id, "🛠 Выбери инструмент:", tools_keyboard())

    elif data == "tool_search":
        answer_callback(callback_id)
        set_user_data(history, chat_id, "waiting", "search")
        send_message(chat_id, "🔍 Напиши поисковый запрос:")

    elif data == "tool_parse":
        answer_callback(callback_id)
        set_user_data(history, chat_id, "waiting", "parse")
        send_message(chat_id, "🌐 Отправь ссылку на сайт:")

    elif data == "tool_summarize":
        answer_callback(callback_id)
        set_user_data(history, chat_id, "waiting", "summarize")
        send_message(chat_id, "📝 Отправь текст для суммаризации:")

    elif data == "tool_translate_enru":
        answer_callback(callback_id)
        set_user_data(history, chat_id, "waiting", "translate_enru")
        send_message(chat_id, "🇬🇧➡️🇷🇺 Отправь текст на английском:")

    elif data == "tool_translate_ruen":
        answer_callback(callback_id)
        set_user_data(history, chat_id, "waiting", "translate_ruen")
        send_message(chat_id, "🇷🇺➡️🇬🇧 Отправь текст на русском:")

    elif data == "tool_clear":
        answer_callback(callback_id, "Контекст очищен!")
        set_user_data(history, chat_id, "context", [])
        send_message(chat_id, "🗑 Контекст очищен!", main_keyboard())

    # Действия после ответа
    elif data == "act_more":
        answer_callback(callback_id)
        send_typing(chat_id)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            "Расскажи подробнее про последний ответ. Добавь деталей, цифр, примеров.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", "Подробнее")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, answer, after_response_keyboard())

    elif data == "act_rewrite":
        answer_callback(callback_id)
        send_typing(chat_id)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            "Перепиши последний ответ другими словами. Сделай лучше и интереснее.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", "Переписать")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, answer, after_response_keyboard())

    elif data == "act_list":
        answer_callback(callback_id)
        send_typing(chat_id)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            "Оформи последний ответ в виде нумерованного списка с пунктами.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", "В виде списка")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, answer, after_response_keyboard())

    elif data == "act_example":
        answer_callback(callback_id)
        send_typing(chat_id)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            "Дай конкретный практический пример к последнему ответу. С цифрами и деталями.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", "Пример")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, answer, after_response_keyboard())

    # Назад
    elif data == "back_main":
        answer_callback(callback_id)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        mode_name = MODES.get(mode, MODES[DEFAULT_MODE])["name"]
        send_message(chat_id, f"🤖 Jarvis 2.0 | Режим: {mode_name}\n\nВыбери действие или напиши вопрос:", main_keyboard())


def handle_message(chat_id, text, history):
    text = text.strip()

    # /start
    if text == "/start":
        welcome = "🤖 <b>Jarvis AI Agent 2.0</b>\n\n"
        welcome += "Я твой персональный AI-агент. Умею:\n\n"
        welcome += "💬 Отвечать на любые вопросы\n"
        welcome += "🔍 Искать в интернете\n"
        welcome += "🌐 Парсить сайты\n"
        welcome += "💻 Писать код\n"
        welcome += "📊 Анализировать рынок\n"
        welcome += "📋 Создавать бизнес-планы\n"
        welcome += "✍️ Писать контент\n"
        welcome += "📝 Суммаризировать тексты\n"
        welcome += "🌍 Переводить тексты\n"
        welcome += "📦 8 готовых шаблонов\n\n"
        welcome += "Выбери режим или напиши вопрос:"
        send_message(chat_id, welcome, main_keyboard())
        return

    if text == "/menu":
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        mode_name = MODES.get(mode, MODES[DEFAULT_MODE])["name"]
        send_message(chat_id, f"🤖 Режим: {mode_name}", main_keyboard())
        return

    # Проверяем ожидание инструмента
    waiting = get_user_data(history, chat_id, "waiting", "")

    if waiting == "search":
        set_user_data(history, chat_id, "waiting", "")
        send_typing(chat_id)
        results = search_web(text)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            f"Результаты поиска по '{text}':\n\n{results}\n\nСделай анализ и выводы.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", f"Поиск: {text}")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, f"🔍 Результаты по: {text}\n\n{answer}", after_response_keyboard())
        return

    if waiting == "parse":
        set_user_data(history, chat_id, "waiting", "")
        send_typing(chat_id)
        content = parse_website(text)
        mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
        answer = call_gemini(
            MODES.get(mode, MODES[DEFAULT_MODE])["prompt"],
            f"Содержимое сайта {text}:\n\n{content}\n\nАнализ: что за сайт, что полезного.",
            get_context(history, chat_id)
        )
        add_context(history, chat_id, "user", f"Парсинг: {text}")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, f"🌐 Анализ: {text}\n\n{answer}", after_response_keyboard())
        return

    if waiting == "summarize":
        set_user_data(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = summarize_text(text)
        add_context(history, chat_id, "user", "Суммаризация текста")
        add_context(history, chat_id, "assistant", answer)
        send_message(chat_id, f"📝 Краткое содержание:\n\n{answer}", after_response_keyboard())
        return

    if waiting == "translate_enru":
        set_user_data(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = translate_text(text, "en-ru")
        send_message(chat_id, f"🇬🇧➡️🇷🇺 Перевод:\n\n{answer}", after_response_keyboard())
        return

    if waiting == "translate_ruen":
        set_user_data(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = translate_text(text, "ru-en")
        send_message(chat_id, f"🇷🇺➡️🇬🇧 Перевод:\n\n{answer}", after_response_keyboard())
        return

    # Обычное сообщение
    send_typing(chat_id)
    mode = get_user_data(history, chat_id, "mode", DEFAULT_MODE)
    system = MODES.get(mode, MODES[DEFAULT_MODE])["prompt"]
    context = get_context(history, chat_id)

    answer = call_gemini(system, text, context)
    add_context(history, chat_id, "user", text)
    add_context(history, chat_id, "assistant", answer)
    send_message(chat_id, answer, after_response_keyboard())


# ============================================
# MAIN
# ============================================

def main():
    print("=== JARVIS 2.0 START ===")

    if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
        print("ERROR: env vars not set")
        sys.exit(1)

    offset = load_offset()
    history = load_history()
    updates = get_updates(offset)

    if not updates.get("ok"):
        print("Error getting updates")
        sys.exit(1)

    results = updates.get("result", [])
    print(f"Updates: {len(results)}")

    for update in results:
        offset = update["update_id"] + 1

        # Обработка нажатий кнопок
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            print(f"Callback {chat_id}: {cb['data']}")
            handle_callback(cb, history)
            continue

        # Обработка текстовых сообщений
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            continue

        print(f"Message {chat_id}: {text[:50]}")
        handle_message(chat_id, text, history)

    save_data(OFFSET_FILE, str(offset))
    save_data(HISTORY_FILE, history)
    print("=== DONE ===")


if __name__ == "__main__":
    main()
