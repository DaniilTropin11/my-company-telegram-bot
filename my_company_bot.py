import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🎛️ Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🔐 Получаем токен
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("❌ BOT_TOKEN не задан! Добавь его в Environment Variables на Render.")
    exit(1)

# 🧑‍💼 ID администратора (узнать можно через @userinfobot в Telegram)
ADMIN_ID = 397090905  # ← ЗАМЕНИ НА СВОЙ ID (или ID заказчика)

# 🖥️ Главное меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Операции", callback_data='menu_operations')],
        [InlineKeyboardButton("📚 Обучение", callback_data='menu_training')],
        [InlineKeyboardButton("🛠️ Поддержка", callback_data='menu_support')],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("👋 Добро пожаловать в Корпоративного Помощника!", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("👋 Добро пожаловать в Корпоративного Помощника!", reply_markup=reply_markup)

# 🎯 Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"👤 Пользователь {user.id} ({user.full_name}) запустил бота")
    await show_main_menu(update, context)

# 🆘 Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *Доступные команды:*\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/about — о боте\n\n"
        "Используйте кнопки для навигации."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ❓ Обработчик команды /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 *Корпоративный Помощник v1.0*\n"
        "Автоматизированный ассистент для сотрудников компании.\n"
        "Разработан для повышения эффективности и стандартизации процессов.\n\n"
        "© 2025 Команда разработки"
    )
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(about_text, parse_mode="Markdown", reply_markup=reply_markup)

# 🖱️ Обработчик нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 📋 Меню операций
    if query.data == 'menu_operations':
        keyboard = [
            [InlineKeyboardButton("📥 Приём заказа", callback_data='instr_order')],
            [InlineKeyboardButton("📤 Отгрузка", callback_data='instr_shipping')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📋 *Операции:*", reply_markup=reply_markup, parse_mode="Markdown")

    # 📚 Меню обучения
    elif query.data == 'menu_training':
        keyboard = [
            [InlineKeyboardButton("🎓 Новичку", callback_data='instr_newbie')],
            [InlineKeyboardButton("📈 Продвинутому", callback_data='instr_pro')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📚 *Обучение:*", reply_markup=reply_markup, parse_mode="Markdown")

    # 🛠️ Меню поддержки
    elif query.data == 'menu_support':
        keyboard = [
            [InlineKeyboardButton("🆘 Запросить помощь", callback_data='request_help')],
            [InlineKeyboardButton("📞 Контакты", callback_data='show_contacts')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🛠️ *Поддержка:*", reply_markup=reply_markup, parse_mode="Markdown")

    # 📥 Инструкция: Приём заказа
    elif query.data == 'instr_order':
        text = (
            "📥 *Приём заказа:*\n\n"
            "1️⃣ Поприветствуйте клиента по имени.\n"
            "2️⃣ Уточните артикул и количество.\n"
            "3️⃣ Согласуйте способ доставки.\n"
            "4️⃣ Отправьте счёт в CRM.\n"
            "5️⃣ Подтвердите заказ SMS/email."
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад к операциям", callback_data='menu_operations')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 📤 Инструкция: Отгрузка
    elif query.data == 'instr_shipping':
        text = (
            "📤 *Отгрузка:*\n\n"
            "1️⃣ Проверьте оплату в системе.\n"
            "2️⃣ Скомплектуйте заказ на складе.\n"
            "3️⃣ Передайте в службу доставки.\n"
            "4️⃣ Отсканируйте трек-номер.\n"
            "5️⃣ Уведомите клиента."
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад к операциям", callback_data='menu_operations')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 🎓 Инструкция: Новичку
    elif query.data == 'instr_newbie':
        text = (
            "🎓 *Для новичка:*\n\n"
            "✅ Пройдите вводный курс на портале.\n"
            "✅ Запомните 3 ключевых продукта.\n"
            "✅ Первую неделю — только приём звонков.\n"
            "✅ Ежедневно — отчёт наставнику."
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад к обучению", callback_data='menu_training')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 📈 Инструкция: Продвинутому
    elif query.data == 'instr_pro':
        text = (
            "📈 *Для продвинутого:*\n\n"
            "✅ Ведите переговоры с VIP-клиентами.\n"
            "✅ Формируйте индивидуальные предложения.\n"
            "✅ Анализируйте отчёты продаж.\n"
            "✅ Менторьте новичков."
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад к обучению", callback_data='menu_training')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # 🆘 Запрос помощи
    elif query.data == 'request_help':
        user = update.effective_user
        message = f"🆘 *Запрос помощи от:* @{user.username or 'user'} (ID: {user.id})\nИмя: {user.full_name}"
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="Markdown")
            await query.edit_message_text("✅ Ваш запрос отправлен администратору. Ожидайте ответа!", parse_mode="Markdown")
            logger.info(f"🆘 Запрос помощи от {user.id} отправлен админу {ADMIN_ID}")
        except Exception as e:
            logger.error(f"❌ Не удалось отправить сообщение админу: {e}")
            await query.edit_message_text("❌ Ошибка отправки. Попробуйте позже.", parse_mode="Markdown")

    # 📞 Контакты
    elif query.data == 'show_contacts':
        text = (
            "📞 *Контакты поддержки:*\n\n"
            "🧑‍💼 Руководитель: +7 (XXX) XXX-XX-XX\n"
            "📧 Email: support@company.com\n"
            "🕒 Рабочие часы: Пн-Пт, 9:00–18:00"
        )
        keyboard = [[InlineKeyboardButton("🔙 Назад к поддержке", callback_data='menu_support')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    # ℹ️ О боте (через кнопку)
    elif query.data == 'about':
        await about(update, context)  # вызываем ту же функцию, что и для /about

    # 🔙 Назад в главное меню
    elif query.data == 'back_to_main':
        await show_main_menu(update, context)

# 🚀 Основная функция
def main():
    logger.info("🚀 Запуск Корпоративного Помощника...")
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button))

    logger.info("✅ Бот готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()