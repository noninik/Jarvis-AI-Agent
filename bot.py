import os
import sys
import json
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
HISTORY_FILE = "chat_history.json"
OFFSET_FILE = "offset.txt"

MODES = {
    "helper": {"name": "💬 Помощник", "prompt": "Ты универсальный AI-помощник Jarvis. Отвечай кратко и по делу на русском. Конкретные ответы с примерами.", "emoji": "💬"},
    "business": {"name": "📊 Бизнес-аналитик", "prompt": "Ты бизнес-аналитик Jarvis. Анализируй рынки, конкурентов, тренды. Структурированные ответы с цифрами. На русском.", "emoji": "📊"},
    "content": {"name": "✍️ Контент-менеджер", "prompt": "Ты контент-менеджер Jarvis. Пишешь посты, статьи, рекламу. Живой дерзкий язык без воды. На русском.", "emoji": "✍️"},
    "coder": {"name": "💻 Программист", "prompt": "Ты full-stack разработчик Jarvis. Пишешь чистый рабочий код на Python, JavaScript, HTML. Готовый код. На русском.", "emoji": "💻"},
    "startup": {"name": "📋 Стартап-консультант", "prompt": "Ты стартап-консультант Jarvis. Бизнес-планы, идеи, unit-экономика. На русском.", "emoji": "📋"},
    "research": {"name": "🔍 Исследователь", "prompt": "Ты исследователь рынка Jarvis. Анализируй ниши, тренды, спрос. Конкретные данные. На русском.", "emoji": "🔍"},
    "automate": {"name": "🚀 Автоматизатор", "prompt": "Ты эксперт по автоматизации Jarvis. Скрипты, боты, парсеры. Готовый код на Python. На русском.", "emoji": "🚀"},
    "copywriter": {"name": "📝 Копирайтер", "prompt": "Ты копирайтер Jarvis. Продающие тексты, лендинги, email-рассылки. Формулы AIDA, PAS. На русском.", "emoji": "📝"},
    "coach": {"name": "🎯 Коуч", "prompt": "Ты лайф-коуч Jarvis. Помогаешь ставить цели, планировать, находить мотивацию. На русском.", "emoji": "🎯"},
    "translator": {"name": "🌍 Переводчик", "prompt": "Ты переводчик Jarvis. Переводишь тексты на/с английского. Объясняешь нюансы. На русском.", "emoji": "🌍"},
}

DEFAULT_MODE = "helper"

TEMPLATES = {
    "biz_plan": {"name": "📋 Бизнес-план", "prompt": "Создай детальный бизнес-план. Спроси нишу и бюджет, потом создай план: идея, ЦА, конкуренты, MVP, монетизация, маркетинг, финансы, риски."},
    "content_plan": {"name": "📅 Контент-план", "prompt": "Создай контент-план на 2 недели. Спроси нишу, дай план: дата, тема, формат, хештеги. 3 поста в день."},
    "competitor": {"name": "🔍 Анализ конкурентов", "prompt": "Проведи анализ конкурентов. Спроси нишу, проанализируй 5 конкурентов: сильные и слабые стороны, цены, УТП."},
    "resume": {"name": "📄 Резюме", "prompt": "Помоги составить резюме. Спроси должность и опыт, создай резюме: контакты, о себе, опыт, навыки, образование."},
    "post_pack": {"name": "✍️ Пак постов", "prompt": "Создай 10 постов для соцсетей. Спроси нишу и тон, напиши 10 постов: продающий, развлекательный, экспертный, вовлекающий."},
    "landing": {"name": "🌐 Текст лендинга", "prompt": "Напиши текст лендинга. Спроси продукт, создай: заголовок, проблемы, решение, преимущества, призыв к действию."},
    "email_chain": {"name": "📧 Email-цепочка", "prompt": "Создай 5 писем для прогрева клиента. Спроси нишу, напиши: приветственное, полезное, кейс, оффер, дожим."},
    "swot": {"name": "📊 SWOT-анализ", "prompt": "Проведи SWOT-анализ. Спроси бизнес, разбери: Strengths, Weaknesses, Opportunities, Threats."},
}


def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_offset():
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def get_user(history, chat_id, key, default=""):
    return history.get(str(chat_id) + "_" + key, default)


def set_user(history, chat_id, key, value):
    history[str(chat_id) + "_" + key] = value


def get_context(history, chat_id):
    return get_user(history, chat_id, "context", [])


def add_context(history, chat_id, role, text):
    ctx = get_context(history, chat_id)
    ctx.append({"role": role, "text": text[:1000]})
    if len(ctx) > 20:
        ctx = ctx[-20:]
    set_user(history, chat_id, "context", ctx)


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
                results.append(t.get_text().strip() + ": " + s.get_text().strip())
        return "\n\n".join(results) if results else "Ничего не найдено"
    except Exception as e:
        return "Ошибка поиска: " + str(e)


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
        return "Ошибка: " + str(e)


def call_ai(system_prompt, user_message, context):
    messages = [{"role": "system", "content": system_prompt}]
    for msg in context[-10:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["text"]})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 3000,
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=body, timeout=60)
        if resp.status_code != 200:
            print("AI error:", resp.status_code)
            return "AI временно недоступен. Попробуй через минуту."
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("AI exception:", e)
        return "Ошибка соединения с AI."


def send_msg(chat_id, text, keyboard=None):
    url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
    while text:
        chunk = text[:4000]
        text = text[4000:]
        payload = {"chat_id": chat_id, "text": chunk}
        if keyboard and not text:
            payload["reply_markup"] = json.dumps(keyboard)
        try:
            requests.post(url, json=payload, timeout=30)
        except:
            pass


def send_typing(chat_id):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendChatAction"
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=10)
    except:
        pass


def answer_cb(callback_id, text=""):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/answerCallbackQuery"
        requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=10)
    except:
        pass


def main_kb():
    return {"inline_keyboard": [
        [{"text": "💬 Помощник", "callback_data": "mode_helper"}, {"text": "📊 Бизнес", "callback_data": "mode_business"}],
        [{"text": "✍️ Контент", "callback_data": "mode_content"}, {"text": "💻 Код", "callback_data": "mode_coder"}],
        [{"text": "📋 Стартап", "callback_data": "mode_startup"}, {"text": "🔍 Исследование", "callback_data": "mode_research"}],
        [{"text": "🚀 Автоматизация", "callback_data": "mode_automate"}, {"text": "📝 Копирайтинг", "callback_data": "mode_copywriter"}],
        [{"text": "🎯 Коуч", "callback_data": "mode_coach"}, {"text": "🌍 Переводчик", "callback_data": "mode_translator"}],
        [{"text": "📦 Шаблоны", "callback_data": "show_templates"}, {"text": "🛠 Инструменты", "callback_data": "show_tools"}],
    ]}


def tpl_kb():
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


def tools_kb():
    return {"inline_keyboard": [
        [{"text": "🔍 Поиск в интернете", "callback_data": "tool_search"}],
        [{"text": "🌐 Спарсить сайт", "callback_data": "tool_parse"}],
        [{"text": "📝 Суммаризация", "callback_data": "tool_summarize"}],
        [{"text": "🇬🇧→🇷🇺 EN→RU", "callback_data": "tool_enru"}],
        [{"text": "🇷🇺→🇬🇧 RU→EN", "callback_data": "tool_ruen"}],
        [{"text": "🗑 Очистить контекст", "callback_data": "tool_clear"}],
        [{"text": "⬅️ Назад", "callback_data": "back_main"}],
    ]}


def after_kb():
    return {"inline_keyboard": [
        [{"text": "🔄 Подробнее", "callback_data": "act_more"}, {"text": "📝 Переписать", "callback_data": "act_rewrite"}],
        [{"text": "📋 Список", "callback_data": "act_list"}, {"text": "🎯 Пример", "callback_data": "act_example"}],
        [{"text": "🏠 Меню", "callback_data": "back_main"}],
    ]}


def get_mode_prompt(history, chat_id):
    mode = get_user(history, chat_id, "mode", DEFAULT_MODE)
    return MODES.get(mode, MODES[DEFAULT_MODE])["prompt"]


def handle_callback(cb, history):
    chat_id = cb["message"]["chat"]["id"]
    cb_id = cb["id"]
    data = cb["data"]

    if data.startswith("mode_"):
        mode_key = data[5:]
        if mode_key in MODES:
            set_user(history, chat_id, "mode", mode_key)
            set_user(history, chat_id, "context", [])
            set_user(history, chat_id, "waiting", "")
            m = MODES[mode_key]
            answer_cb(cb_id, m["name"])
            send_msg(chat_id, m["emoji"] + " Режим: " + m["name"] + "\n\nЗадавай вопросы!", after_kb())

    elif data == "show_templates":
        answer_cb(cb_id)
        send_msg(chat_id, "📦 Выбери шаблон:", tpl_kb())

    elif data.startswith("tpl_"):
        key = data[4:]
        if key in TEMPLATES:
            answer_cb(cb_id, TEMPLATES[key]["name"])
            send_typing(chat_id)
            answer = call_ai(get_mode_prompt(history, chat_id), TEMPLATES[key]["prompt"], get_context(history, chat_id))
            add_context(history, chat_id, "user", TEMPLATES[key]["prompt"])
            add_context(history, chat_id, "assistant", answer)
            send_msg(chat_id, answer, after_kb())

    elif data == "show_tools":
        answer_cb(cb_id)
        send_msg(chat_id, "🛠 Выбери инструмент:", tools_kb())

    elif data == "tool_search":
        answer_cb(cb_id)
        set_user(history, chat_id, "waiting", "search")
        send_msg(chat_id, "🔍 Напиши поисковый запрос:")

    elif data == "tool_parse":
        answer_cb(cb_id)
        set_user(history, chat_id, "waiting", "parse")
        send_msg(chat_id, "🌐 Отправь ссылку на сайт:")

    elif data == "tool_summarize":
        answer_cb(cb_id)
        set_user(history, chat_id, "waiting", "summarize")
        send_msg(chat_id, "📝 Отправь текст:")

    elif data == "tool_enru":
        answer_cb(cb_id)
        set_user(history, chat_id, "waiting", "enru")
        send_msg(chat_id, "🇬🇧→🇷🇺 Отправь текст на английском:")

    elif data == "tool_ruen":
        answer_cb(cb_id)
        set_user(history, chat_id, "waiting", "ruen")
        send_msg(chat_id, "🇷🇺→🇬🇧 Отправь текст на русском:")

    elif data == "tool_clear":
        answer_cb(cb_id, "Очищено!")
        set_user(history, chat_id, "context", [])
        send_msg(chat_id, "🗑 Контекст очищен!", main_kb())

    elif data == "act_more":
        answer_cb(cb_id)
        send_typing(chat_id)
        answer = call_ai(get_mode_prompt(history, chat_id), "Расскажи подробнее. Добавь деталей, цифр, примеров.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Подробнее")
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, answer, after_kb())

    elif data == "act_rewrite":
        answer_cb(cb_id)
        send_typing(chat_id)
        answer = call_ai(get_mode_prompt(history, chat_id), "Перепиши последний ответ лучше.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Переписать")
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, answer, after_kb())

    elif data == "act_list":
        answer_cb(cb_id)
        send_typing(chat_id)
        answer = call_ai(get_mode_prompt(history, chat_id), "Оформи последний ответ нумерованным списком.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Списком")
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, answer, after_kb())

    elif data == "act_example":
        answer_cb(cb_id)
        send_typing(chat_id)
        answer = call_ai(get_mode_prompt(history, chat_id), "Дай конкретный пример с цифрами и деталями.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Пример")
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, answer, after_kb())

    elif data == "back_main":
        answer_cb(cb_id)
        mode = get_user(history, chat_id, "mode", DEFAULT_MODE)
        send_msg(chat_id, "🤖 Jarvis 2.0 | " + MODES.get(mode, MODES[DEFAULT_MODE])["name"], main_kb())


def handle_message(chat_id, text, history):
    text = text.strip()

    if text == "/start" or text == "/menu":
        send_msg(chat_id, "🤖 Jarvis AI Agent 2.0\n\nВыбери режим или напиши вопрос:", main_kb())
        return

    waiting = get_user(history, chat_id, "waiting", "")

    if waiting == "search":
        set_user(history, chat_id, "waiting", "")
        send_typing(chat_id)
        results = search_web(text)
        answer = call_ai(get_mode_prompt(history, chat_id), "Результаты поиска '" + text + "':\n\n" + results + "\n\nАнализ и выводы.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Поиск: " + text)
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, "🔍 " + text + "\n\n" + answer, after_kb())
        return

    if waiting == "parse":
        set_user(history, chat_id, "waiting", "")
        send_typing(chat_id)
        content = parse_website(text)
        answer = call_ai(get_mode_prompt(history, chat_id), "Сайт " + text + ":\n\n" + content + "\n\nАнализ.", get_context(history, chat_id))
        add_context(history, chat_id, "user", "Парсинг: " + text)
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, "🌐 " + text + "\n\n" + answer, after_kb())
        return

    if waiting == "summarize":
        set_user(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = call_ai("Ты эксперт по суммаризации на русском.", "Краткое содержание, 5 главных мыслей:\n\n" + text[:3000], [])
        add_context(history, chat_id, "user", "Суммаризация")
        add_context(history, chat_id, "assistant", answer)
        send_msg(chat_id, "📝\n\n" + answer, after_kb())
        return

    if waiting == "enru":
        set_user(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = call_ai("Ты переводчик.", "Переведи на русский и объясни сложные слова:\n\n" + text, [])
        send_msg(chat_id, "🇬🇧→🇷🇺\n\n" + answer, after_kb())
        return

    if waiting == "ruen":
        set_user(history, chat_id, "waiting", "")
        send_typing(chat_id)
        answer = call_ai("Ты переводчик.", "Переведи на английский, 2 варианта:\n\n" + text, [])
        send_msg(chat_id, "🇷🇺→🇬🇧\n\n" + answer, after_kb())
        return

    send_typing(chat_id)
    answer = call_ai(get_mode_prompt(history, chat_id), text, get_context(history, chat_id))
    add_context(history, chat_id, "user", text)
    add_context(history, chat_id, "assistant", answer)
    send_msg(chat_id, answer, after_kb())


def main():
    print("=== JARVIS 2.0 START ===")

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set")
        sys.exit(1)

    print("Tokens OK")

    offset = load_offset()
    print("Offset:", offset)

    history = load_json(HISTORY_FILE)

    print("Getting updates...")
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/getUpdates"
        resp = requests.get(url, params={"offset": offset, "timeout": 5, "limit": 20}, timeout=15)
        print("Telegram status:", resp.status_code)
        updates = resp.json()
    except Exception as e:
        print("Connection error:", e)
        sys.exit(0)

    print("OK:", updates.get("ok"))

    if not updates.get("ok"):
        print("Resetting offset to 0")
        save_offset(0)
        try:
            resp = requests.get(url, params={"offset": 0, "timeout": 5, "limit": 20}, timeout=15)
            updates = resp.json()
            print("Retry OK:", updates.get("ok"))
        except:
            print("Still failing")
            sys.exit(0)

    results = updates.get("result", [])
    print("Updates:", len(results))

    if not results:
        print("No new messages")
        sys.exit(0)

    for update in results:
        offset = update["update_id"] + 1

        if "callback_query" in update:
            cb = update["callback_query"]
            print("Callback:", cb.get("data", ""))
            try:
                handle_callback(cb, history)
            except Exception as e:
                print("Callback error:", e)
            continue

        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            continue

        print("Message:", text[:50])
        try:
            handle_message(chat_id, text, history)
        except Exception as e:
            print("Message error:", e)
            send_msg(chat_id, "Произошла ошибка. Попробуй ещё раз.")

    save_offset(offset)
    save_json(HISTORY_FILE, history)
    print("=== DONE ===")


if __name__ == "__main__":
    main()
