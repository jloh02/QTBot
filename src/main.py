import logging
import datetime
import constants
import storage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
)
from config import config, read_dotenv

read_dotenv()
storage.read_group_data()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("main")


def main():
    application = (
        Application.builder().token(config.get("TELEGRAM_BOT_API_KEY")).build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            constants.ConvState.SelectFrequency: [
                CallbackQueryHandler(select_frequency)
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("qtdone", qtdone))
    application.add_handler(CommandHandler("remind", remind))
    application.job_queue.run_repeating(
        remind_incomplete, interval=datetime.timedelta(minutes=30)
    )

    if config.get("PRODUCTION"):
        application.run_webhook(
            listen="0.0.0.0",
            port=config.get("PORT"),
            webhook_url=config.get("WEBHOOK_URL"),
        )
    else:
        application.run_polling()


async def register(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton(text=v, callback_data=k)]
        for k, v in constants.FREQUENCY_OPTIONS.items()
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Choose your task frequency:", reply_markup=markup)
    return constants.ConvState.SelectFrequency


async def select_frequency(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    freq = query.data
    storage.register_group(query.message.chat_id, freq)
    await query.edit_message_text(
        f"Frequency set to: {constants.FREQUENCY_OPTIONS[freq]}"
    )
    return ConversationHandler.END


async def qtdone(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user.username
    storage.mark_done(chat_id, user)
    streaks, _ = storage.get_group_summary(chat_id)
    response = "\n".join([f"@{k}: {v} days" for k, v in streaks.items()])
    await update.message.reply_text(f"Streaks:\n{response}")


async def remind(update: Update, context: CallbackContext):
    await remind_incomplete(context)


async def remind_incomplete(context: CallbackContext):
    now = datetime.datetime.now()
    for chat_id, data in storage.get_all_groups():
        freq = data.get("frequency")
        if not freq:
            continue
        deadline = datetime.datetime.combine(
            datetime.date.today(), datetime.time(23, 59)
        )
        if (deadline - now).total_seconds() > 6 * 3600:  # 6 hours
            continue
        last_completed = data.get("last_completed", {})
        all_users = data["streaks"].keys()
        incomplete = [
            u
            for u in all_users
            if last_completed.get(u) != datetime.date.today().isoformat()
        ]
        if incomplete:
            await context.bot.send_message(
                chat_id=int(chat_id),
                text="Reminder: The following users haven't marked today's task as done:\n"
                + "\n".join([f"@{u}" for u in incomplete]),
            )


if __name__ == "__main__":
    main()
