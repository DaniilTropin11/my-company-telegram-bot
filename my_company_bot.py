from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔑 ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ BOTFATHER
import os
TOKEN = os.getenv("BOT_TOKEN")

# 📖 Словарь с инструкциями
INSTRUCTIONS = {
    'instr1': (
        "📘 Инструкция 1: Как принять заказ\n\n"
        "1. Поприветствуйте клиента.\n"
        "2. Уточните детали заказа.\n"
        "3. Зафиксируйте в CRM.\n"
        "4. Отправьте подтверждение клиенту."
    ),
    'instr2': (
        "📙 Инструкция 2: Как обработать возврат\n\n"
        "1. Проверьте причину возврата.\n"
        "2. Убедитесь, что товар не использовался.\n"
        "3. Оформите возврат в системе.\n"
        "4. Сообщите клиенту сроки возврата денег."
    ),
    'instr3': (
        "📗 Инструкция 3: Что делать при жалобе\n\n"
        "1. Выслушайте клиента без перебиваний.\n"
        "2. Извинитесь за доставленные неудобства.\n"
        "3. Предложите решение (скидка, замена, возврат).\n"
        "4. Зафиксируйте инцидент в журнале."
    ),
}

# 🎛️ Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Как принять заказ", callback_data='instr1')],
        [InlineKeyboardButton("📙 Как обработать возврат", callback_data='instr2')],
        [InlineKeyboardButton("📗 Что делать при жалобе", callback_data='instr3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('👇 Выберите инструкцию:', reply_markup=reply_markup)

# 🖱️ Обработчик нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    instruction_text = INSTRUCTIONS.get(query.data, "❌ Инструкция не найдена.")
    await query.edit_message_text(text=instruction_text)

# 🚀 Основная функция запуска бота
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    print("🚀 Бот запущен...")
    application.run_polling()

# 🔁 Запуск
if __name__ == '__main__':
    main()