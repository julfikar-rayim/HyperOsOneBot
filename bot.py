import os
from telegram import Update, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ------------ ENV -------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
ALLOWED_CHAT_IDS = [int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x]
# --------------------------------

# Allowed links list
ALLOWED_LINKS = []


# ---------------- OWNER COMMANDS -------------------

async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.reply_text("Usage: /addlink https://example.com")
        return

    link = context.args[0].strip()
    ALLOWED_LINKS.append(link)
    await update.reply_text(f"✅ Allowed link added:\n{link}")


async def remove_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.reply_text("Usage: /removelink https://example.com")
        return

    link = context.args[0].strip()
    if link in ALLOWED_LINKS:
        ALLOWED_LINKS.remove(link)
        await update.reply_text(f"❌ Link removed:\n{link}")
    else:
        await update.reply_text("Link not found.")


async def show_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not ALLOWED_LINKS:
        await update.reply_text("No allowed links added.")
        return

    out = "🔗 Allowed Links:\n" + "\n".join(f"- {l}" for l in ALLOWED_LINKS)
    await update.reply_text(out)


# ---------------- USERNAME BASED ACTIONS -------------------

async def kick_by_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.reply_text("Usage: /kick @username")
        return

    username = context.args[0].replace("@", "")

    chat = update.effective_chat
    members = await chat.get_administrators()
    target = None

    async for msg in chat.get_members():
        if msg.user.username and msg.user.username.lower() == username.lower():
            target = msg.user
            break

    if not target:
        await update.reply_text("User not found in group.")
        return

    try:
        await chat.ban_member(target.id)
        await update.reply_text(f"❌ {target.full_name} has been kicked.")
    except:
        await update.reply_text("Bot needs ban permission!")


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.reply_text("Usage: /adduser @username")
        return

    username = context.args[0].replace("@", "")
    chat = update.effective_chat

    try:
        await chat.unban_member(username=username)
        await update.reply_text(f"✅ {username} can join again.")
    except:
        await update.reply_text("Bot needs permissions!")


# ---------------- MESSAGE CHECKER -------------------

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.effective_user

    if chat_id not in ALLOWED_CHAT_IDS:
        return

    # owner exempted
    if user.id == OWNER_ID:
        return

    text = update.message.text.lower()

    # link detected
    if "http://" in text or "https://" in text or ".com" in text:

        # check allowed links
        if any(link in text for link in ALLOWED_LINKS):
            return  # safe link

        # otherwise ban user
        try:
            await update.message.chat.ban_member(user.id)

            # PM message
            try:
                await context.bot.send_message(
                    user.id,
                    text=f"🚫 আপনি গ্রুপে অনুমোদনবিহীন লিংক শেয়ার করায় আপনাকে রিমুভ করা হয়েছে।"
                )
            except:
                pass

            await update.message.reply_text(
                f"❌ {user.full_name} কে লিংক শেয়ার করার জন্য রিমুভ করা হয়েছে।"
            )
        except:
            await update.message.reply_text("Bot needs ban permission!")


# ---------------- START -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.reply_text("Bot Running Successfully!")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # owner commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlink", add_link))
    app.add_handler(CommandHandler("removelink", remove_link))
    app.add_handler(CommandHandler("showlinks", show_links))
    app.add_handler(CommandHandler("kick", kick_by_username))
    app.add_handler(CommandHandler("adduser", add_user))

    # message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
