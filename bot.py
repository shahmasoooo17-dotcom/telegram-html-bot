import os
import base64
import logging
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.environ.get('BOT_TOKEN')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())

# Initialize cipher
cipher = Fernet(ENCRYPTION_KEY.encode())

# ============ ENCRYPTION FUNCTIONS ============
def encrypt_html(content):
    try:
        return cipher.encrypt(content.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return None

def decrypt_html(content):
    try:
        return cipher.decrypt(content.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return None

def obfuscate_html(content, key="railway2024"):
    try:
        result = []
        for i, char in enumerate(content):
            result.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return base64.b64encode(''.join(result).encode()).decode()
    except Exception as e:
        logger.error(f"Obfuscation error: {e}")
        return None

def deobfuscate_html(content, key="railway2024"):
    try:
        decoded = base64.b64decode(content.encode()).decode()
        result = []
        for i, char in enumerate(decoded):
            result.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return ''.join(result)
    except Exception as e:
        logger.error(f"Deobfuscation error: {e}")
        return None

# ============ BOT COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Welcome to HTML Crypto Bot!\n\n"
        "Commands:\n"
        "/encrypt [html] - Encrypt HTML\n"
        "/decrypt [data] - Decrypt HTML\n"
        "/obfuscate [html] - Obfuscate HTML\n"
        "/deobfuscate [data] - Deobfuscate HTML\n\n"
        "Or upload an HTML file!"
    )

async def encrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /encrypt [your html content]")
        return
    html_content = ' '.join(context.args)
    encrypted = encrypt_html(html_content)
    if encrypted:
        await update.message.reply_text(f"🔐 Encrypted:\n\n{encrypted}")
    else:
        await update.message.reply_text("❌ Encryption failed")

async def decrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /decrypt [encrypted content]")
        return
    encrypted_content = ' '.join(context.args)
    decrypted = decrypt_html(encrypted_content)
    if decrypted:
        await update.message.reply_text(f"🔓 Decrypted:\n\n{decrypted}")
    else:
        await update.message.reply_text("❌ Decryption failed")

async def obfuscate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /obfuscate [html content]")
        return
    html_content = ' '.join(context.args)
    obfuscated = obfuscate_html(html_content)
    if obfuscated:
        await update.message.reply_text(f"🔀 Obfuscated:\n\n{obfuscated}")
    else:
        await update.message.reply_text("❌ Obfuscation failed")

async def deobfuscate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /deobfuscate [obfuscated content]")
        return
    obfuscated = ' '.join(context.args)
    deobfuscated = deobfuscate_html(obfuscated)
    if deobfuscated:
        await update.message.reply_text(f"✨ Deobfuscated:\n\n{deobfuscated}")
    else:
        await update.message.reply_text("❌ Deobfuscation failed")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = await update.message.document.get_file()
        file_content = await file.download_as_bytearray()
        content = file_content.decode('utf-8', errors='ignore')
        
        keyboard = [
            [InlineKeyboardButton("🔐 Encrypt", callback_data="encrypt_file"),
             InlineKeyboardButton("🔓 Decrypt", callback_data="decrypt_file")],
            [InlineKeyboardButton("🔀 Obfuscate", callback_data="obfuscate_file"),
             InlineKeyboardButton("✨ Deobfuscate", callback_data="deobfuscate_file")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📄 File uploaded!\nChoose an action:",
            reply_markup=reply_markup
        )
        context.user_data['file_content'] = content
    except Exception as e:
        logger.error(f"File handling error: {e}")
        await update.message.reply_text("❌ Error processing file")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content = context.user_data.get('file_content')
    if not content:
        await query.edit_message_text("❌ No file found. Upload again.")
        return
    
    action = query.data
    if action == "encrypt_file":
        result = encrypt_html(content)
        label = "🔐 Encrypted"
    elif action == "decrypt_file":
        result = decrypt_html(content)
        label = "🔓 Decrypted"
    elif action == "obfuscate_file":
        result = obfuscate_html(content)
        label = "🔀 Obfuscated"
    elif action == "deobfuscate_file":
        result = deobfuscate_html(content)
        label = "✨ Deobfuscated"
    
    if result:
        await query.edit_message_text(f"{label}:\n\n{result[:4000]}")
    else:
        await query.edit_message_text("❌ Operation failed")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ An error occurred")

def main():
    if not TOKEN:
        logger.error("BOT_TOKEN not set!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("encrypt", encrypt))
    app.add_handler(CommandHandler("decrypt", decrypt))
    app.add_handler(CommandHandler("obfuscate", obfuscate))
    app.add_handler(CommandHandler("deobfuscate", deobfuscate))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()