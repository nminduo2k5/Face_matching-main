import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Cấu hình logging cho Telegram bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramNotificationBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.user_data_file = 'telegram_users.json'
        self.user_data = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.setup_handlers()
        logger.info("Bot initialized")

    def setup_handlers(self):
        """Setup command handlers"""
        try:
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("register", self.register))
            self.application.add_handler(CommandHandler("unregister", self.unregister))
            logger.info("Handlers set up successfully")
        except Exception as e:
            logger.error(f"Error setting up handlers: {e}")

    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_user_data(self):
        with open(self.user_data_file, 'w') as f:
            json.dump(self.user_data, f, indent=4)

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Handle the /start command"""
        try:
            logger.info(f"Received /start command from user {update.effective_user.id}")
            welcome_message = (
                "👋 Chào mừng bạn đến với Bot Thông Báo Nhận Diện!\n\n"
                "Các lệnh có sẵn:\n"
                "🔹 /register <MNV> - Đăng ký nhận thông báo\n"
                "   Ví dụ: /register ABC123\n"
                "🔹 /unregister - Hủy đăng ký nhận thông báo\n\n"
                "ℹ️ Sau khi đăng ký, bạn sẽ nhận được thông báo mỗi khi được nhận diện."
            )
            await update.message.reply_text(welcome_message)
            logger.info(f"Sent welcome message to user {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Có lỗi xảy ra, vui lòng thử lại sau.")

    async def register(self, update: Update, context: CallbackContext) -> None:
        """Handle the /register command"""
        try:
            logger.info(f"Received /register command from user {update.effective_user.id}")
            if len(context.args) < 1:
                await update.message.reply_text('Vui lòng nhập MNV của bạn. Ví dụ: /register ABC123')
                return

            pin = context.args[0]
            
            # Đọc dữ liệu trong executor thread
            self.user_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.load_user_data
            )
            
            # Cập nhật dữ liệu
            self.user_data[pin] = {
                'user_id': str(update.effective_user.id),
                'username': update.effective_user.username,
                'chat_id': update.effective_chat.id
            }
            
            # Lưu dữ liệu trong executor thread
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.save_user_data
            )
            
            await update.message.reply_text(
                f'✅ Đã đăng ký thành công với MNV: {pin}\n\nBạn sẽ nhận được thông báo khi được nhận diện.'
            )
            logger.info(f"Successfully registered user {update.effective_user.id} with PIN {pin}")
        except Exception as e:
            logger.error(f"Error in register command: {e}")
            await update.message.reply_text("Có lỗi xảy ra khi đăng ký, vui lòng thử lại sau.")

    async def unregister(self, update: Update, context: CallbackContext) -> None:
        """Handle the /unregister command"""
        try:
            logger.info(f"Received /unregister command from user {update.effective_user.id}")
            user_id = str(update.effective_user.id)
            
            # Đọc dữ liệu trong executor thread
            self.user_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.load_user_data
            )
            
            pins_to_remove = []
            for pin, data in self.user_data.items():
                if data.get('user_id') == user_id:
                    pins_to_remove.append(pin)
            
            if pins_to_remove:
                for pin in pins_to_remove:
                    del self.user_data[pin]
                
                # Lưu dữ liệu trong executor thread
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.save_user_data
                )
                await update.message.reply_text('✅ Đã hủy đăng ký thành công!')
                logger.info(f"Successfully unregistered user {update.effective_user.id}")
            else:
                await update.message.reply_text('❌ Bạn chưa đăng ký MNV nào.')
        except Exception as e:
            logger.error(f"Error in unregister command: {e}")
            await update.message.reply_text("Có lỗi xảy ra khi hủy đăng ký, vui lòng thử lại sau.")

    async def send_recognition_notification(self, pin, time):
        """Send recognition notification"""
        try:
            logger.info(f"Attempting to send notification for PIN {pin}")
            # Đọc dữ liệu trong executor thread
            self.user_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.load_user_data
            )
            
            if pin in self.user_data:
                chat_id = self.user_data[pin]['chat_id']
                message = f"🔔 Thông báo: Bạn đã được nhận diện vào lúc {time}"
                await self.application.bot.send_message(chat_id=chat_id, text=message)
                logger.info(f"Successfully sent notification to PIN {pin}")
                return True
            else:
                logger.warning(f"PIN {pin} not found in user_data")
                return False
        except Exception as e:
            logger.error(f"Error sending notification to PIN {pin}: {e}")
            return False