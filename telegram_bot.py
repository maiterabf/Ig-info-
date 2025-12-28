import logging
import requests
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

# ================= CONFIGURATION =================
BOT_TOKEN = "8074815981:AAGl3ZdVVGL4oaALLNOhWN85Y93pOBDiVMY"
OWNER_ID = 5783508606  # Your ID
API_URL = "https://anmolinstainfo.worldgreeker.workers.dev/user"

# Channels users MUST join
CHANNELS = ["@Fsociety_in", "@xploit_tech"]

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= HELPER FUNCTIONS =================
async def check_subscription(user_id, bot):
    """Checks if user is in the required channels."""
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except BadRequest:
            print(f"❌ Error: Bot must be Admin in {channel}")
            return False
    return True

async def get_join_keyboard():
    """Returns the buttons to join channels."""
    keyboard = [
        [InlineKeyboardButton("🚀 Join Channel 1", url="https://t.me/TheApophisCode")],
        [InlineKeyboardButton("🔥 Join Channel 2", url="https://t.me/xploit_tech")],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = html.escape(update.effective_user.first_name)
    
    # 1. Check Subscription
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text(
            f"⚠️ <b>Access Denied</b>\n\n"
            f"Hello {first_name}, you must join our channels to use this bot.",
            reply_markup=await get_join_keyboard(),
            parse_mode="HTML"
        )
        return

    # 2. If Subscribed, Show Welcome
    greeting = "👑 <b>Welcome Boss!</b>" if user_id == OWNER_ID else f"👋 <b>Hello {first_name}!</b>"
    
    await update.message.reply_text(
        f"{greeting}\n\n"
        "✅ <b>Verification Success.</b>\n"
        "Send <code>/info username</code> to fetch Instagram details.",
        parse_mode="HTML"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I Have Joined' button."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if await check_subscription(user_id, context.bot):
        await query.answer("Welcome!")
        await query.edit_message_text(
            "✅ <b>Verification Successful!</b>\n\n"
            "You can now use the bot.\n"
            "Try: <code>/info username</code>",
            parse_mode="HTML"
        )
    else:
        await query.answer("❌ You are NOT in the channels yet!", show_alert=True)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 1. Security Check (Force Join)
    if not await check_subscription(user_id, context.bot):
        await update.message.reply_text(
            "❌ <b>Access Lost.</b> Please rejoin our channels.",
            reply_markup=await get_join_keyboard(),
            parse_mode="HTML"
        )
        return

    # 2. Argument Check
    if not context.args:
        await update.message.reply_text("⚠️ <b>Usage:</b> <code>/info username</code>", parse_mode="HTML")
        return

    target_username = context.args[0]
    status_msg = await update.message.reply_text(f"🔍 Fetching data for <code>{target_username}</code>...", parse_mode="HTML")

    try:
        # 3. API Request
        response = requests.get(API_URL, params={'username': target_username}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 4. Extract Data Fields
            username = data.get("username", "N/A")
            full_name = data.get("full_name", "N/A")
            bio = data.get("biography", "No Bio")
            followers = data.get("followers", 0)
            following = data.get("following", 0)
            posts = data.get("posts", 0)
            pic_url = data.get("profile_pic")
            
            is_verified = "☑️ Yes" if data.get("is_verified") else "No"
            is_private = "🔒 Yes" if data.get("is_private") else "🔓 No"

            # 5. Format Caption
            caption = (
                f"👤 <b>{html.escape(full_name)}</b> (@{html.escape(username)})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>Bio:</b> {html.escape(bio)}\n\n"
                f"👥 <b>Followers:</b> {followers}\n"
                f"👣 <b>Following:</b> {following}\n"
                f"📸 <b>Posts:</b> {posts}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 <b>Verified:</b> {is_verified}\n"
                f"🔹 <b>Private:</b> {is_private}\n"
            )

            # 6. Send Photo or Fallback to Text
            if pic_url:
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=pic_url,
                        caption=caption,
                        parse_mode="HTML"
                    )
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
                except Exception:
                    await status_msg.edit_text(caption, parse_mode="HTML")
            else:
                await status_msg.edit_text(caption, parse_mode="HTML")

        elif response.status_code == 404:
            await status_msg.edit_text(f"❌ User <code>{target_username}</code> not found.", parse_mode="HTML")
        else:
            await status_msg.edit_text(f"⚠️ API Error: {response.status_code}", parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}", parse_mode="HTML")

# ================= MAIN RUNNER =================
def main():
    print("🚀 Bot Started with Force Join & Instagram Data...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("info", info_command))

    application.run_polling()

if __name__ == '__main__':
    main()