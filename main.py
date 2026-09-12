"""
Telegram Bot — Main Entry Point
Commands:
  - Send any URL → bot processes it automatically
  - /start        → welcome message
  - /help         → usage instructions
  - /status       → bot status
"""

import asyncio
import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

sys.path.insert(0, "D:\\link_bot")

from config import BOT_TOKEN, DOWNLOAD_DIR
from resolver.engine import resolve_link
from downloader import download_file

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("D:\\link_bot\\bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


# ─── Command Handlers ───────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Link Opener Bot*\n\n"
        "আমাকে যেকোনো shortener link পাঠাও।\n"
        "আমি automatically:\n"
        "  ✅ Link খুলব\n"
        "  ✅ Countdown bypass করব\n"
        "  ✅ File থাকলে download করে পাঠাব\n\n"
        "Supported: Bindass, Linkfolo, TN Link, এবং যেকোনো shortener\n\n"
        "/help — সাহায্য",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *কীভাবে ব্যবহার করবো:*\n\n"
        "1. যেকোনো URL paste করো\n"
        "2. Bot automatically process করবে\n"
        "3. File থাকলে download করে পাঠাবে\n"
        "4. File না থাকলে final link দেবে\n\n"
        "⚠️ Captcha থাকলে bot bypass করতে পারবে না।",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot চলছে এবং ready!")


# ─── Link Handler ────────────────────────────────────────────────────────────

async def handle_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("⚠️ Valid URL পাঠাও (http:// দিয়ে শুরু হওয়া)")
        return

    log.info(f"Processing: {url}")
    status_msg = await update.message.reply_text("⏳ Processing link... একটু অপেক্ষা করো")

    try:
        # Step 1: Resolve
        await status_msg.edit_text("🔗 Link resolving করছি...")
        result = await resolve_link(url)

        if not result["success"]:
            await status_msg.edit_text(
                f"❌ Link resolve করা যায়নি।\n"
                f"Error: `{result.get('error', 'Unknown')}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        final_url = result["file_url"] or result["final_url"]
        method = result.get("method", "Unknown")
        log.info(f"Resolved via {method}: {final_url}")

        # Step 2: Try to download if it's a file
        if result["file_url"]:
            await status_msg.edit_text("📥 File download করছি...")
            dl = download_file(result["file_url"])

            if dl["success"]:
                await status_msg.edit_text(f"📤 File পাঠাচ্ছি ({dl['size_mb']} MB)...")
                try:
                    with open(dl["filepath"], "rb") as f:
                        await update.message.reply_document(
                            document=f,
                            filename=dl["filename"],
                            caption=(
                                f"✅ *{dl['filename']}*\n"
                                f"📦 Size: {dl['size_mb']} MB\n"
                                f"🔧 Method: {method}"
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    await status_msg.delete()
                    # Clean up downloaded file
                    try:
                        os.remove(dl["filepath"])
                    except Exception:
                        pass
                    return
                except Exception as e:
                    await status_msg.edit_text(
                        f"✅ File downloaded কিন্তু Telegram-এ পাঠানো যায়নি।\n"
                        f"📁 File saved: `{dl['filepath']}`\n"
                        f"Error: {e}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            else:
                # Download failed, just send the link
                await status_msg.edit_text(
                    f"⚠️ File download হয়নি। Error: {dl['error']}\n\n"
                    f"🔗 Final link:\n{final_url}"
                )
                return

        # Step 3: No file — send the final link
        await status_msg.edit_text(
            f"✅ *Link resolved!*\n\n"
            f"🔗 Final URL:\n`{final_url}`\n\n"
            f"🔧 Method: {method}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as exc:
        log.error(f"Unexpected error: {exc}", exc_info=True)
        try:
            await status_msg.edit_text(f"❌ Unexpected error: {exc}")
        except Exception:
            pass


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN set করো config.py-তে!")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🤖 Bot started! Telegram-এ link পাঠাও।")
    log.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
