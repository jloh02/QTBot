import logging
import datetime
import constants
import storage
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
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
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)


TBOT = Bot(config.get("TELEGRAM_BOT_API_KEY"))
COMMANDS_DICT = {
    "register": "Add yourself to the QT group",
    "qtdone": "Finish QT today! Share something about it too!",
}
TBOT.set_my_commands(COMMANDS_DICT.items())


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

    # Times in GMT+0
    application.job_queue.run_daily(
        remind_incomplete, time=datetime.time(hour=21 - 8, minute=0)
    )
    application.job_queue.run_daily(
        remind_incomplete, time=datetime.time(hour=10 - 8, minute=0)
    )

    if config.get("PRODUCTION"):
        application.run_webhook(
            listen="0.0.0.0",
            port=config.get("PORT"),
            webhook_url=config.get("WEBHOOK_URL"),
            secret_token=config.get("WEBHOOK_SECRET"),
        )
    else:
        application.run_polling()


async def register(update: Update, context: CallbackContext):
    buttons = [
        [InlineKeyboardButton(text=v, callback_data=k)]
        for k, v in constants.FREQUENCY_OPTIONS.items()
    ] + [[InlineKeyboardButton(text="I want out!", callback_data="cancel")]]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "How often would you like to do your QT?", reply_markup=markup
    )
    return constants.ConvState.SelectFrequency


async def select_frequency(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    freq = query.data

    if freq == "cancel":
        storage.remove_user(query.message.chat_id, query.from_user.username)
        await query.edit_message_text(f"Byeee @{query.from_user.username}!👋")
        return ConversationHandler.END

    user = query.from_user.username
    storage.register_user(query.message.chat_id, user, freq)
    await query.edit_message_text(
        f"@{user} committed to do QT {constants.FREQUENCY_OPTIONS[freq].lower()}! 🎉"
    )
    return ConversationHandler.END


async def qtdone(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user.username
    deadline_str = storage.get_user_next_deadline(chat_id, user)

    if not deadline_str:
        await update.message.reply_text(
            "You are not registered! Please use /register to join the QT group."
        )
        return

    now = datetime.datetime.now()

    last_completed_str = storage.get_user_last_completed(chat_id, user)
    if last_completed_str:
        last_completed = datetime.datetime.fromisoformat(last_completed_str)
        time_from_last = now - last_completed
        if (
            time_from_last.total_seconds()
            < constants.MIN_TIME_BETWEEN_QT_IN_HOURS * 3600
        ):
            await update.message.reply_text(
                f"QT already done within the last {constants.MIN_TIME_BETWEEN_QT_IN_HOURS} hours! Stop being so ups 🔥🔥🔥"
            )
            return

    deadline = datetime.datetime.fromisoformat(deadline_str)
    storage.mark_done(chat_id, user, deadline < now, now.isoformat())
    streak = storage.get_user_streak(chat_id, user)
    await update.message.reply_text(f"{streak}🔥")

    await remind(update, context)  # Send reminder immediately after marking done


async def remind(update: Update, context: CallbackContext):
    await remind_incomplete(context, update.effective_chat.id)


async def remind_incomplete(context: CallbackContext, group: str | None = None):
    groups = storage.get_all_groups() if group is None else [group]
    now = datetime.datetime.now()
    for chat_id in groups:
        deadlines = storage.get_group_next_deadline(chat_id)
        incomplete = []

        last_remind = storage.get_last_reminder(chat_id)
        if (
            last_remind
            and now.timestamp() - last_remind
            < constants.REMINDER_DEADLINE_IN_HOURS * 3600
        ):
            continue

        for user, deadline_str in deadlines.items():
            try:
                deadline = datetime.datetime.fromisoformat(deadline_str)
            except Exception:
                continue
            time_left = deadline - now
            # Ping if within 6h of deadline and still not today
            if time_left.total_seconds() <= constants.REMINDER_DEADLINE_IN_HOURS * 3600:
                incomplete.append([int(time_left.total_seconds() // 3600), user])
        incomplete.sort(key=lambda x: x[0])

        if incomplete:
            await context.bot.send_message(
                chat_id=int(chat_id),
                text="⏰🙏 Reminder ⛪️✝️\n\n"
                + "\n".join(
                    [
                        f"@{u} | {abs(t)} hours {'overdue' if t < 0 else 'left'}"
                        for [t, u] in incomplete
                    ]
                ),
            )
            storage.set_last_reminder(chat_id, int(now.timestamp()))


if __name__ == "__main__":
    main()
