import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==============================
# 🔌 FLASK SERVER FOR RENDER HEALTH
# ==============================
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

@app.route('/health')
def health():
    return "Bot is alive", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

print("🚀 Запускаем Flask-сервер для здоровья...")
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ==============================
# 🎛️ LOGGING & CONFIG
# ==============================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("❌ BOT_TOKEN не задан!")
    exit(1)

ADMIN_ID = 397090905

# ==============================
# 📊 GOOGLE SHEETS INTEGRATION
# ==============================
def init_google_sheets():
    """Инициализация Google Таблиц"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        # Загружаем JSON-ключ из переменной окружения
        json_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not json_key:
            logger.error("❌ GOOGLE_SERVICE_ACCOUNT_JSON не задан!")
            return None, None

        import json
        credentials_dict = json.loads(json_key)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(credentials)

        # Открываем таблицу (замени на свой URL)
        spreadsheet = client.open_by_url(os.getenv("GOOGLE_SHEET_URL", ""))
        
        # Получаем листы
        users_sheet = spreadsheet.worksheet("Пользователи")
        tests_sheet = spreadsheet.worksheet("Тесты")
        
        # Создаём заголовки, если их нет
        if not users_sheet.get_all_values():
            users_sheet.append_row(["user_id", "username", "fio", "city", "register_date", "last_activity"])
        
        if not tests_sheet.get_all_values():
            tests_sheet.append_row(["user_id", "fio", "test_name", "score", "max_score", "pass_date", "answers"])
            
        return users_sheet, tests_sheet
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Google Таблиц: {e}")
        return None, None

# Инициализируем Google Таблицы
USERS_SHEET, TESTS_SHEET = init_google_sheets()

# ==============================
# 🧠 USER STATE & TESTS
# ==============================
USER_STATE = {}  # {user_id: {"state": "awaiting_fio", "fio": "", "city": "", ...}}
TESTS = {
    "test_order": {
        "title": "Тест: Приём заказа",
        "questions": [
            {
                "question": "Что нужно сделать первым при приёме заказа?",
                "options": [
                    "Поприветствовать клиента по имени",
                    "Сразу запросить оплату",
                    "Уточнить адрес доставки",
                    "Открыть CRM-систему"
                ],
                "correct": 0  # индекс правильного ответа
            },
            {
                "question": "Как правильно подтвердить заказ клиенту?",
                "options": [
                    "Отправить SMS или email с деталями",
                    "Позвонить и устно подтвердить",
                    "Ничего не делать — клиент сам разберётся",
                    "Отправить сообщение в WhatsApp"
                ],
                "correct": 0
            }
        ]
    },
    "test_shipping": {
        "title": "Тест: Отгрузка товара",
        "questions": [
            {
                "question": "Что проверить перед отгрузкой?",
                "options": [
                    "Оплату в системе",
                    "Цвет упаковки",
                    "Погоду на улице",
                    "Наличие кофе у сотрудника"
                ],
                "correct": 0
            }
        ]
    }
}

# ==============================
# 🎯 COMMAND HANDLERS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Проверяем, зарегистрирован ли пользователь
    if is_user_registered(user_id):
        await show_main_menu(update, context)
    else:
        USER_STATE[user_id] = {"state": "awaiting_fio"}
        await update.message.reply_text("👋 Добро пожаловать!\nПожалуйста, введите ваше ФИО:")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *Доступные команды:*\n"
        "/start — начать регистрацию или вернуться в меню\n"
        "/help — помощь\n"
        "/about — о боте\n\n"
        "Сначала необходимо зарегистрироваться (ФИО, город ПВЗ)."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🎓 *Бот обучения партнёров ПВЗ*\n"
        "Интерактивная платформа для обучения и тестирования сотрудников пунктов выдачи заказов.\n\n"
        "© 2025 Команда разработки"
    )
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=reply_markup)

# ==============================
# 📝 TEXT HANDLER (for FIO and City)
# ==============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    if user_id not in USER_STATE:
        await update.message.reply_text("Пожалуйста, начните с команды /start")
        return

    state = USER_STATE[user_id].get("state")

    if state == "awaiting_fio":
        USER_STATE[user_id]["fio"] = text
        USER_STATE[user_id]["state"] = "awaiting_city"
        await update.message.reply_text(f"Спасибо, {text}!\nТеперь введите город вашего ПВЗ:")

    elif state == "awaiting_city":
        USER_STATE[user_id]["city"] = text
        USER_STATE[user_id]["username"] = user.username or "unknown"
        
        # Сохраняем пользователя в Google Таблицу
        save_user_to_sheet(user_id, USER_STATE[user_id])
        
        await update.message.reply_text(
            f"✅ Регистрация завершена!\n\n"
            f"ФИО: {USER_STATE[user_id]['fio']}\n"
            f"Город ПВЗ: {text}\n\n"
            f"Теперь вы можете приступить к обучению!"
        )
        await show_main_menu(update, context)

# ==============================
# 🖱️ CALLBACK HANDLER (Buttons)
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_id = user.id

    # Проверка регистрации
    if not is_user_registered(user_id) and query.data not in ['back_to_main']:
        await query.edit_message_text("Пожалуйста, сначала зарегистрируйтесь через /start")
        return

    # 📚 Меню обучения
    if query.data == 'menu_training':
        keyboard = [
            [InlineKeyboardButton("📦 Приём заказа", callback_data='material_order')],
            [InlineKeyboardButton("🚚 Отгрузка товара", callback_data='material_shipping')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📚 *Выберите обучающий материал:*", reply_markup=reply_markup, parse_mode="Markdown")

    # 📥 Материал: Приём заказа
    elif query.data == 'material_order':
        text = (
            "📦 *Материал: Приём заказа*\n\n"
            "*Текстовый мануал:*\n"
            "1️⃣ Всегда начинайте с приветствия по имени клиента.\n"
            "2️⃣ Уточните артикул и количество товара.\n"
            "3️⃣ Согласуйте способ доставки и сроки.\n"
            "4️⃣ Создайте заказ в CRM-системе.\n"
            "5️⃣ Отправьте клиенту подтверждение (SMS/email).\n\n"
            "*Видео-инструкция:* https://youtu.be/dQw4w9WgXcQ"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Пройти тест", callback_data='start_test_order')],
            [InlineKeyboardButton("🔙 Назад к материалам", callback_data='menu_training')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 📤 Материал: Отгрузка товара
    elif query.data == 'material_shipping':
        text = (
            "🚚 *Материал: Отгрузка товара*\n\n"
            "*Текстовый мануал:*\n"
            "1️⃣ Проверьте статус оплаты в системе.\n"
            "2️⃣ Скомплектуйте заказ на складе.\n"
            "3️⃣ Передайте посылку службе доставки.\n"
            "4️⃣ Отсканируйте трек-номер и внесите в систему.\n"
            "5️⃣ Уведомите клиента о передаче заказа.\n\n"
            "*Видео-инструкция:* https://youtu.be/dQw4w9WgXcQ"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Пройти тест", callback_data='start_test_shipping')],
            [InlineKeyboardButton("🔙 Назад к материалам", callback_data='menu_training')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 🧠 Начать тест
    elif query.data.startswith('start_test_'):
        test_key = query.data.replace('start_test_', '')
        if test_key in TESTS:
            USER_STATE[user_id]['test'] = {
                'key': test_key,
                'current_question': 0,
                'score': 0,
                'answers': []
            }
            await send_test_question(update, context, user_id)

    # 📝 Ответ на вопрос теста
    elif query.data.startswith('answer_'):
        _, test_key, q_index, is_correct = query.data.split('_')
        q_index = int(q_index)
        is_correct = is_correct == '1'
        
        user_test = USER_STATE[user_id]['test']
        user_test['answers'].append(is_correct)
        
        if is_correct:
            user_test['score'] += 1
            await query.edit_message_text("✅ Правильно!", reply_markup=None)
        else:
            await query.edit_message_text("❌ Неправильно!", reply_markup=None)
        
        # Следующий вопрос или результат
        user_test['current_question'] += 1
        if user_test['current_question'] < len(TESTS[test_key]['questions']):
            await send_test_question(update, context, user_id)
        else:
            await show_test_result(update, context, user_id)

    # ℹ️ О боте
    elif query.data == 'about':
        await about(update, context)

    # 🔙 Назад в главное меню
    elif query.data == 'back_to_main':
        await show_main_menu(update, context)

# ==============================
# 🎥 TEST FUNCTIONS
# ==============================
async def send_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет текущий вопрос теста"""
    user_test = USER_STATE[user_id]['test']
    test_key = user_test['key']
    q_index = user_test['current_question']
    
    if q_index >= len(TESTS[test_key]['questions']):
        await show_test_result(update, context, user_id)
        return
    
    question_data = TESTS[test_key]['questions'][q_index]
    
    keyboard = []
    for i, option in enumerate(question_data['options']):
        callback_data = f"answer_{test_key}_{q_index}_{'1' if i == question_data['correct'] else '0'}"
        keyboard.append([InlineKeyboardButton(option, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📝 *Вопрос {q_index + 1} из {len(TESTS[test_key]['questions'])}:*\n\n{question_data['question']}"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)

async def show_test_result(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Показывает результат теста"""
    user_test = USER_STATE[user_id]['test']
    test_key = user_test['key']
    total_questions = len(TESTS[test_key]['questions'])
    score = user_test['score']
    
    # Сохраняем результат в Google Таблицу
    save_test_result_to_sheet(
        user_id=user_id,
        fio=USER_STATE[user_id]['fio'],
        test_name=TESTS[test_key]['title'],
        score=score,
        max_score=total_questions,
        answers=user_test['answers']
    )
    
    text = (
        f"🎉 *Тест завершён!*\n\n"
        f"Тест: {TESTS[test_key]['title']}\n"
        f"Результат: {score} из {total_questions}\n\n"
    )
    
    if score == total_questions:
        text += "🌟 Отлично! Вы прекрасно справились!"
    elif score >= total_questions * 0.7:
        text += "👍 Хорошо! Почти всё правильно."
    else:
        text += "📚 Нужно повторить материал."
    
    keyboard = [
        [InlineKeyboardButton("📚 Вернуться к материалам", callback_data='menu_training')],
        [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)

# ==============================
# 🖥️ MAIN MENU & UTILS
# ==============================
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    keyboard = [
        [InlineKeyboardButton("📚 Обучение", callback_data='menu_training')],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "👋 Добро пожаловать в бот обучения партнёров ПВЗ!"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

def is_user_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь"""
    if USERS_SHEET:
        try:
            cell = USERS_SHEET.find(str(user_id))
            return cell is not None
        except:
            pass
    # Fallback на временное хранилище
    return user_id in USER_STATE and "city" in USER_STATE[user_id]

def save_user_to_sheet(user_id: int, user_data: dict):
    """Сохраняет пользователя в Google Таблицу"""
    if not USERS_SHEET:
        return
    
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        USERS_SHEET.append_row([
            str(user_id),
            user_data.get("username", ""),
            user_data.get("fio", ""),
            user_data.get("city", ""),
            now,
            now
        ])
        logger.info(f"✅ Пользователь {user_id} сохранён в Google Таблицу")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя: {e}")

def save_test_result_to_sheet(user_id: int, fio: str, test_name: str, score: int, max_score: int, answers: list):
    """Сохраняет результат теста в Google Таблицу"""
    if not TESTS_SHEET:
        return
    
    try:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        TESTS_SHEET.append_row([
            str(user_id),
            fio,
            test_name,
            str(score),
            str(max_score),
            now,
            str(answers)
        ])
        logger.info(f"✅ Результат теста для {user_id} сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения результата теста: {e}")

# ==============================
# 🚀 MAIN FUNCTION
# ==============================
def main():
    logger.info("🚀 Запуск Бота обучения партнёров ПВЗ...")
    application = Application.builder().token(TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button))

    logger.info("✅ Бот готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()