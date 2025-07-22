import os
import base64
import tempfile
import random
import string
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)

# === CONFIG ===
BOT_TOKEN = "8097491089:AAG9iWVpS9WNxst3C6-QUJFYpRRKu61-oEw"
XOR_KEY = "UTF-8"

# === DECRYPT LOGIC ===
def xor_decrypt(enc: str, key: str) -> str:
    try:
        decoded = base64.b64decode(enc)
        key_bytes = key.encode()
        return ''.join([chr(b ^ key_bytes[i % len(key_bytes)]) for i, b in enumerate(decoded)])
    except:
        return None

def patch_smali_dir(smali_root, key):
    for root, _, files in os.walk(smali_root):
        for file in files:
            if file.endswith(".smali"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                changed = False
                new_lines = []
                for line in lines:
                    if 'const-string' in line and '"' in line:
                        parts = line.split('"')
                        if len(parts) >= 2:
                            enc_str = parts[1]
                            dec_str = xor_decrypt(enc_str, key)
                            if dec_str:
                                line = line.replace(enc_str, dec_str)
                                changed = True
                    new_lines.append(line)

                if changed:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)

def random_name(ext="apk"):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "." + ext

def process_apk(apk_path, key):
    temp_dir = tempfile.mkdtemp()
    output_apk = random_name("apk")

    try:
        os.system(f"java -jar apktool.jar d '{apk_path}' -o {temp_dir} -f")
        for folder in os.listdir(temp_dir):
            if folder.startswith("smali"):
                patch_smali_dir(os.path.join(temp_dir, folder), key)
        os.system(f"java -jar apktool.jar b '{temp_dir}' -o '{output_apk}'")
    except Exception:
        return None

    return output_apk if os.path.exists(output_apk) else None

# === TELEGRAM HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *THIS BOT MADE BY SATYAM*\n📩 *ANY PROBLEM? DM* @SATYM_ONLY\n\n📤 *Send your APK or DEX file to decrypt.*",
        parse_mode="Markdown"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file = update.message.document
        file_path = os.path.join(tempfile.gettempdir(), file.file_name)
        await file.get_file().download_to_drive(file_path)

        await update.message.reply_text("✅ File uploaded.\n🔐 Decryption started...")

        # Simulate progress
        for progress in range(10, 101, 10):
            await update.message.reply_text(f"🛠️ Decrypting... {progress}%")
            await asyncio.sleep(0.4)

        await update.message.reply_text("📦 Sending decrypted APK...")

        output_apk = process_apk(file_path, XOR_KEY)

        if output_apk and os.path.exists(output_apk):
            await update.message.reply_document(document=open(output_apk, "rb"))
        else:
            await update.message.reply_text("❌ Failed to decrypt or build APK.")

        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ Error occurred: {str(e)}")

# === MAIN ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("✅ Decryption Bot is running...")
    app.run_polling()