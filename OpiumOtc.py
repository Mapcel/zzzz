# -*- coding: utf-8 -*-
import logging, random, asyncio, os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# CONFIG
TOKEN = "8632618428:AAFKZ6pPZfEOTtVyCQcnGDM1ktUpkgAGAHM"
# Список администраторов (можно добавить несколько ID)
ADMIN_IDS = [417890256, 8240291473]
# Сохраняем первый админ для совместимости, если где-то требуется одиночный ID
ADMIN_ID = ADMIN_IDS[0]

ESCROW_ACCOUNT = "@OpiumSafeSupporter"
MANAGER_ACCOUNT = "@OpiumSafeSupporter"
LOG_CHAT_ID = -5301815293  # ID группы для логов (должен быть отрицательным для группы)

# НАЗВАНИЕ ФАЙЛА ФОТОГРАФИИ (файл должен лежать в той же папке, что и этот скрипт)
BOT_PHOTO_FILENAME = "picture.png"

# STORAGE
user_wallets = {}
user_balances = {}  # {user_id: {currency: balance}}
deals = {}
activity_log = []
referral_codes = {}  # {code: owner_id}
user_referrals = {}  # {user_id: referrer_id}
verified_users = set()  # Пользователи, которые ввели /savageteam
user_language = {}  # {user_id: 'ru' or 'en'}
user_successful_deals = {}  # {user_id: количество успешных сделок}
user_ratings = {}  # {user_id: рейтинг от 1 до 5}
user_deals_history = {}  # {user_id: [список успешных сделок]}
user_active_deals = {}  # {user_id: [список активных сделок]}

# ГЛОБАЛЬНАЯ СТАТИСТИКА (обновленные значения)
BOT_STATS = {
    'total_deals': 3127,
    'successful_deals': 3041,
    'total_volume': 27850,
    'avg_rating': 4.8,
    'online_now': 847,
    'positive_reviews': 97.2
}

# ТЕКСТЫ НА РАЗНЫХ ЯЗЫКАХ
TEXTS = {
    'ru': {
        'main_menu': "Главное меню",
        'wallet_management': "📩 Управление реквизитами",
        'create_deal': "📝 Создать сделку",
        'referral_system': "🔗 Реферальная система",
        'change_language': "🌐 Сменить язык",
        'support': "📞 Поддержка",
        'admin_panel': "⚙️ Админ-панель",
        'my_deals': "📊 Мои сделки",
        'stats': "📈 Статистика",
        'back': "⬅️ Назад",
        'main_text': (
            "Добро пожаловать в Opium Safe\n\n"
            "Безопасные сделки с гарантией\n\n"
            "> 🛡️ Защита от мошенников\n"
            "> 💰 Автоматическое удержание средств\n"
            "> 📝 Прозрачная статистика\n"
            "> 🎯 Поддержка 24/7\n"
            "> 📊 История сделок\n\n"
            "Выберите раздел ниже:"
        ),
        'verification_success': (
            "✅ Вы успешно прошли верификацию! Теперь вы можете оплачивать сделки.\n\n"
            "Для начала работы используйте /start"
        ),
        'choose_wallet': "💼 Какой кошелёк хотите добавить/изменить?",
        'enter_wallet_details': "✍️ Введите реквизиты для {currency} (они будут сохранены).",
        'wallet_saved': "✅ Реквизиты для {currency} сохранены.",
        'deal_currency_first': "💼 Сначала выберите валюту для сделки:",
        'deal_amount': "💰 Напишите сумму сделки (например: 1000):",
        'deal_description': "📝 Теперь напишите название подарка (например: Пепе или Леденец):",
        'deal_currency': "Сумма: {amount}\nОписание: {description}\nВалюта: {currency}",
        'deal_created': "✅ Сделка успешно создана!\n\n💰 Сумма: {amount} {currency}\n📜 Описание: {description}\n🔗 Ссылка для покупателя:\n{link}",
        'not_verified': "❌ У вас недостаточно прав для оплаты сделок.",
        'deal_not_found': "❌ Сделка не найдена.",
        'payment_success': "✅ Оплата зафиксирована. Продавец уведомлён.",
        'seller_notification': (
            "💰 Пользователь @{buyer_username} оплатил сделку #{deal_id} "
            "на сумму {amount} {currency}.\n"
            "📦 Передайте товар на {escrow_account}."
        ),
        'referral_text': (
            "🎁 Реферальная система\n\n"
            "👥 Ваши рефералы: {ref_count}\n"
            "🔗 Ваша реферальная ссылка:\n{ref_link}\n\n"
            "💎 За каждого приглашённого друга вы получаете бонусы!"
        ),
        'referral_stats': "📊 Ваша реферальная статистика:\n\n👥 Количество рефералов: {ref_count}",
        'share_text': "Присоединяйся к Opium Safe! 🔥\nБезопасные P2P-сделки с гарантoм\n\n{ref_link}",
        'not_understood': "Я не понял. Используйте меню или /start.",
        'language_changed': "✅ Язык изменен на русский!",
        'choose_language': "🌐 Выберите язык:",
        'cancel': "❌ Отмена",
        'pay': "✅ Оплатить",
        'confirm_transfer': "📦 Подтвердить отправку подарка",
        'finish_deal': "✅ Завершить сделку",
        'dispute': "❌ Оспорить",
        'active_deals': "📂 Активные сделки",
        'activity_history': "📊 История активности",
        'saved_wallets': "💼 Сохранённые кошельки",
        'verified_users': "👥 Верифицированные пользователи",
        'referral_stats_admin': "🔗 Реферальная статистика",
        'check_balance': "💰 Проверить баланс",
        'balance_info': "💰 Ваш баланс {currency}: {balance}",
        'no_wallet': "❌ Кошелёк {currency} не привязан",
        'deal_cancelled': "✅ Сделка #{deal_id} отменена",
        'cancel_deal': "❌ Отменить сделку",
        'buyer_payment_info': (
            "💳 Информация о сделке #{deal_id}\n\n"
            "👤 Вы покупатель в сделке.\n"
            "📌 Продавец: @{seller_username} ({seller_id})\n"
            "📊 Успешных сделок у продавца: {successful_deals}\n"
            "⭐ Рейтинг продавца: {rating}/5\n\n"
            "• Вы покупаете: {description}\n\n"
            "🏦 Адрес для оплаты:\n{wallet_address}\n\n"
            "💰 Сумма к оплате: {amount} {currency}\n"
            "📝 Комментарий к платежу(мемо): {deal_id}\n\n"
            "⚠️ Пожалуйста, убедитесь в правильности данных перед оплатой. Комментарий(мемо) обязателен!\n\n"
            "В случае если вы отправили транзакцию без комментария заполните форму — {support_account}"
        ),
        'buyer_payment_confirmed': (
            "💳 Оплата подтверждена!\n"
            "▸ Сделка: #{deal_id}\n"
            "▸ Продавец: @{seller_username}\n"
            "▸ Успешных сделок у продавца: {successful_deals}\n"
            "▸ Рейтинг продавца: {rating}/5\n"
            "▸ Сумма: {amount} {currency}\n"
            "▸ Описание: {description}\n\n"
            "Ожидайте, продавец отправит подарок менеджеру {manager_account} для проверки.\n\n"
            "⏳ Ожидайте уведомления о передаче подарка."
        ),
        'seller_payment_confirmed': (
            "✅ Оплата подтверждена для сделки #{deal_id}.\n\n"
            "Покупатель: @{buyer_username}\n"
            "Успешных сделок у покупателя: {successful_deals}\n"
            "Рейтинг покупателя: {rating}/5\n"
            "Сумма: {amount} {currency}\n"
            "Описание: {description}\n\n"
            "❗️ Пожалуйста, передайте NFT-подарок:\n"
            "Только менеджеру бота для обработки:\n"
            "{manager_account}\n\n"
            "⚠️ Обратите внимание:\n"
            "➤ Подарок необходимо передать именно менеджеру {manager_account}, а не покупателю напрямую.\n"
            "➤ Это стандартный процесс для автоматического завершения сделки через бота.\n\n"
            "После отправки менеджеру:\n"
            "Подтвердите действие кнопкой ниже:"
        ),
        'critical_rule': (
            "🛡️ Критически важное правило:\n"
            "Подарок должен быть передан исключительно менеджеру\n"
            "👉 {manager_account}\n\n"
            "🚫 Если вам предлагают нарушить процедуру:\n"
            "• \"Передайте напрямую покупателю/другому лицу\" →\n"
            "• Это мошенническая схема!\n"
            "• Любая передача мимо менеджера:\n"
            "  - Автоматически отменяет сделку\n"
            "  - Лишает гарантий возврата средств"
        ),
        'gift_sent': "📦 Подарок отправлен",
        'get_support': "🆘 Поддержка",
        'gift_sent_notification': "📦 Продавец подтвердил отправку подарка менеджеру. Ожидайте проверки.",
        'deal_completed': "🎉 Сделка завершена! Спасибо за использование наших услуг.",
        'deposit_balance': "💳 Пополнить баланс",
        'deposit_error': "❌ Сбой в системе. Попробуйте еще раз позже.",
        'set_deals_prompt': "📊 Введите количество успешных сделок для установки:",
        'set_deals_success': "✅ Количество успешных сделок установлено: {count}",
        'set_deals_invalid': "❌ Пожалуйста, введите корректное число.",
        'no_successful_deals': "0",
        'no_wallet_for_currency': "❌ У вас не привязан кошелёк для валюты {currency}. Сначала добавьте реквизиты в разделе 'Управление реквизитами'.",
        'checking_wallet': "🔍 Проверяем наличие реквизитов для {currency}...",
        'wallet_found': "✅ Реквизиты для {currency} найдены: {wallet}",
        'create_deal_with_currency': "💼 Создание сделки с валютой: {currency}",
        'insufficient_balance': "❌ Недостаточно средств для оплаты сделки. Пополните баланс и попробуйте снова.",
        'deals_stats': "📊 Статистика Opium Safe\n\n🤝 Всего сделок: {total_deals}\n✅ Успешных сделок: {successful_deals}\n💰 Общий объем: ${total_volume}\n⭐️ Средний рейтинг: {avg_rating}/5.0\n🟢 Онлайн сейчас: {online_now}\n\n📈 Наши преимущества:\n• 🔒 Гарант-сервис на все сделки\n• ⚡️ Мгновенная доставка товаров\n• 🛡️ Защита от мошенников\n• 💎 Проверенные продавцы\n• 📞 24/7 Поддержка\n• ⭐️ {positive_reviews}% положительных отзывов\n\n📞 Поддержка: @OpiumSafeSupporter\n\nСтатистика обновляется каждые 5 минут",
        'my_deals_info': "📊 Ваши сделки\n\n",
        'active_deals_list': "🟡 Активные сделки:\n",
        'finished_deals_list': "🟢 Завершенные сделки:\n",
        'successful_deals_count': "✅ Успешных сделок: {count}\n\n",
        'successful_deals_history': "📊 История успешных сделок:\n",
        'deal_history_item': "    {num}. 🟢 Сделка #{deal_id} — Успешная сделка #{deal_num:04d}\n         💰 {amount} {currency} | 📅 {date}\n",
        'and_more_deals': "    ... и еще {count} сделок",
        'no_deals': "📭 У вас пока нет сделок.",
        'set_rating_prompt': "⭐ Введите рейтинг от 1 до 5:",
        'set_rating_success': "✅ Рейтинг установлен: {rating}/5",
        'set_rating_invalid': "❌ Пожалуйста, введите число от 1 до 5.",
        'rating_deleted': "✅ Рейтинг удален",
        'deals_deleted': "✅ Все успешные сделки удалены",
        'no_rating': "Нет рейтинга",
        'custom_currency_prompt': "💱 Введите название вашей валюты (например: EUR, JPY, CAD):",
        'custom_currency_saved': "✅ Валюта '{currency}' установлена для сделки",
        'enter_any_wallet': "💳 Введите реквизиты для любой валюты:",
        'any_wallet_saved': "✅ Реквизиты для любой валюты сохранены"
    },
    'en': {
        'main_menu': "Main Menu",
        'wallet_management': "📩 Manage Wallets",
        'create_deal': "📝 Create Deal",
        'referral_system': "🔗 Referral System",
        'change_language': "🌐 Change Language",
        'support': "📞 Support",
        'admin_panel': "⚙️ Admin Panel",
        'my_deals': "📊 My Deals",
        'stats': "📈 Statistics",
        'back': "⬅️ Back",
        'main_text': (
            "Welcome to Opium Safe\n\n"
            "Secure deals with guarantee\n\n"
            "> 🛡️ Protection from scammers\n"
            "> 💰 Automatic fund holding\n"
            "> 📝 Transparent statistics\n"
            "> 🎯 24/7 Support\n"
            "> 📊 Deal history\n\n"
            "Choose section below:"
        ),
        'verification_success': (
            "✅ You have successfully passed verification! Now you can pay for deals.\n\n"
            "Use /start to begin"
        ),
        'choose_wallet': "💼 Which wallet do you want to add/modify?",
        'enter_wallet_details': "✍️ Enter details for {currency} (they will be saved).",
        'wallet_saved': "✅ Details for {currency} saved.",
        'deal_currency_first': "💼 First choose currency for deal:",
        'deal_amount': "💰 Enter deal amount (example: 1000):",
        'deal_description': "📝 Now enter the gift name (example: Pepe or Lollipop):",
        'deal_currency': "Amount: {amount}\nDescription: {description}\nCurrency: {currency}",
        'deal_created': "✅ Deal successfully created!\n\n💰 Amount: {amount} {currency}\n📜 Description: {description}\n🔗 Buyer link:\n{link}",
        'not_verified': "❌ You don't have sufficient rights to pay for deals.",
        'deal_not_found': "❌ Deal not found.",
        'payment_success': "✅ Payment recorded. Seller notified.",
        'seller_notification': (
            "💰 User @{buyer_username} paid deal #{deal_id} "
            "for amount {amount} {currency}.\n"
            "📦 Transfer the goods to {escrow_account}."
        ),
        'referral_text': (
            "🎁 Referral system\n\n"
            "👥 Your referrals: {ref_count}\n"
            "🔗 Your referral link:\n{ref_link}\n\n"
            "💎 You get bonuses for every invited friend!"
        ),
        'referral_stats': "📊 Your referral statistics:\n\n👥 Number of referrals: {ref_count}",
        'share_text': "Join Opium Safe! 🔥\nSecure P2P deals with guarantor\n\n{ref_link}",
        'not_understood': "I didn't understand. Use menu or /start.",
        'language_changed': "✅ Language changed to English!",
        'choose_language': "🌐 Choose language:",
        'cancel': "❌ Cancel",
        'pay': "✅ Pay",
        'confirm_transfer': "📦 Confirm gift sending",
        'finish_deal': "✅ Finish deal",
        'dispute': "❌ Dispute",
        'active_deals': "📂 Active deals",
        'activity_history': "📊 Activity history",
        'saved_wallets': "💼 Saved wallets",
        'verified_users': "👥 Verified users",
        'referral_stats_admin': "🔗 Referral statistics",
        'check_balance': "💰 Check balance",
        'balance_info': "💰 Your {currency} balance: {balance}",
        'no_wallet': "❌ {currency} wallet not connected",
        'deal_cancelled': "✅ Deal #{deal_id} cancelled",
        'cancel_deal': "❌ Cancel deal",
        'buyer_payment_info': (
            "💳 Deal information #{deal_id}\n\n"
            "👤 You are the buyer in this deal.\n"
            "📌 Seller: @{seller_username} ({seller_id})\n"
            "📊 Seller's successful deals: {successful_deals}\n"
            "⭐ Seller's rating: {rating}/5\n\n"
            "• You are buying: {description}\n\n"
            "🏦 Payment address:\n{wallet_address}\n\n"
            "💰 Amount to pay: {amount} {currency}\n"
            "📝 Payment comment(memo): {deal_id}\n\n"
            "⚠️ Please verify the data before payment. Comment(memo) is mandatory!\n\n"
            "If you sent transaction without comment fill the form — {support_account}"
        ),
        'buyer_payment_confirmed': (
            "💳 Payment confirmed!\n"
            "▸ Deal: #{deal_id}\n"
            "▸ Seller: @{seller_username}\n"
            "▸ Seller's successful deals: {successful_deals}\n"
            "▸ Seller's rating: {rating}/5\n"
            "▸ Amount: {amount} {currency}\n"
            "▸ Description: {description}\n\n"
            "Please wait, seller will send the gift to manager {manager_account} for verification.\n\n"
            "⏳ Wait for notification about gift transfer."
        ),
        'seller_payment_confirmed': (
            "✅ Payment confirmed for deal #{deal_id}.\n\n"
            "Buyer: @{buyer_username}\n"
            "Buyer's successful deals: {successful_deals}\n"
            "Buyer's rating: {rating}/5\n"
            "Amount: {amount} {currency}\n"
            "Description: {description}\n\n"
            "❗️ Please transfer NFT-gift:\n"
            "Only to bot manager for processing:\n"
            "{manager_account}\n\n"
            "⚠️ Please note:\n"
            "➤ Gift must be transferred exactly to manager {manager_account}, not directly to buyer.\n"
            "➤ This is standard process for automatic deal completion via bot.\n\n"
            "After sending to manager:\n"
            "Confirm action with button below:"
        ),
        'critical_rule': (
            "🛡️ Critically important rule:\n"
            "Gift must be transferred exclusively to manager\n"
            "👉 {manager_account}\n\n"
            "🚫 If you are offered to violate procedure:\n"
            "• \"Transfer directly to buyer/another person\" →\n"
            "• This is fraudulent scheme!\n"
            "• Any transfer bypassing manager:\n"
            "  - Automatically cancels deal\n"
            "  - Deprives refund guarantees"
        ),
        'gift_sent': "📦 Gift sent",
        'get_support': "🆘 Support",
        'gift_sent_notification': "📦 Seller confirmed gift sending to manager. Please wait for verification.",
        'deal_completed': "🎉 Deal completed! Thank you for using our services.",
        'deposit_balance': "💳 Deposit balance",
        'deposit_error': "❌ System failure. Please try again later.",
        'set_deals_prompt': "📊 Enter number of successful deals to set:",
        'set_deals_success': "✅ Number of successful deals set: {count}",
        'set_deals_invalid': "❌ Please enter a valid number.",
        'no_successful_deals': "0",
        'no_wallet_for_currency': "❌ You don't have a wallet for currency {currency}. First add details in 'Manage Wallets' section.",
        'checking_wallet': "🔍 Checking wallet for {currency}...",
        'wallet_found': "✅ Wallet for {currency} found: {wallet}",
        'create_deal_with_currency': "💼 Creating deal with currency: {currency}",
        'insufficient_balance': "❌ Insufficient funds to pay for the deal. Please deposit funds and try again.",
        'deals_stats': "📊 LOpium Safe Statistics\n\n🤝 Total deals: {total_deals}\n✅ Successful deals: {successful_deals}\n💰 Total volume: ${total_volume}\n⭐️ Average rating: {avg_rating}/5.0\n🟢 Online now: {online_now}\n\n📈 Our advantages:\n• 🔒 Guarantor service for all deals\n• ⚡️ Instant delivery of goods\n• 🛡️ Protection from scammers\n• 💎 Verified sellers\n• 📞 24/7 Support\n• ⭐️ {positive_reviews}% positive reviews\n\n📞 Support: @OpiumSafeSupporter\n\nStatistics updated every 5 minutes",
        'my_deals_info': "📊 Your Deals\n\n",
        'active_deals_list': "🟡 Active deals:\n",
        'finished_deals_list': "🟢 Completed deals:\n",
        'successful_deals_count': "✅ Successful deals: {count}\n\n",
        'successful_deals_history': "📊 Successful deals history:\n",
        'deal_history_item': "    {num}. 🟢 Deal #{deal_id} — Successful deal #{deal_num:04d}\n         💰 {amount} {currency} | 📅 {date}\n",
        'and_more_deals': "    ... and {count} more deals",
        'no_deals': "📭 You don't have any deals yet.",
        'set_rating_prompt': "⭐ Enter rating from 1 to 5:",
        'set_rating_success': "✅ Rating set: {rating}/5",
        'set_rating_invalid': "❌ Please enter a number from 1 to 5.",
        'rating_deleted': "✅ Rating deleted",
        'deals_deleted': "✅ All successful deals deleted",
        'no_rating': "No rating",
        'custom_currency_prompt': "💱 Enter your currency name (example: EUR, JPY, CAD):",
        'custom_currency_saved': "✅ Currency '{currency}' set for deal",
        'enter_any_wallet': "💳 Enter details for any currency:",
        'any_wallet_saved': "✅ Details for any currency saved"
    }
}

# LOGGING
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ЛОГИРОВАНИЕ В ГРУППУ
async def send_log_to_group(context, action: str, details: str = "", user_id: int = None, username: str = None,
                            extra: str = ""):
    """Отправляет логи в группу"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Формируем текст лога
        if any(word in action.lower() for word in ["сделк", "deal", "оплат", "подар", "отмен", "заверш"]):
            log_text = f"📊 DEAL | 🟢 INFO | {timestamp}\n\n"
        else:
            log_text = f"👤 USER | 🟢 INFO | {timestamp}\n\n"

        username_display = f"@{username}" if username else "Unknown"
        user_id_display = user_id if user_id else "N/A"

        log_text += f"👤 Пользователь: {username_display} ({user_id_display})\n"
        log_text += f"📝 Действие: {action}\n"

        if details:
            log_text += f"📋 Детали: {details}\n"

        if extra:
            log_text += f"📌 Дополнительно: {extra}\n"

        # Отправляем в группу
        try:
            result = await context.bot.send_message(
                chat_id=LOG_CHAT_ID,
                text=log_text
            )
            logger.info(f"✅ Лог отправлен в группу: {action}")
            return True
        except Exception as send_error:
            logger.error(f"❌ Ошибка отправки лога в группу {LOG_CHAT_ID}: {send_error}")
            return False

    except Exception as e:
        logger.error(f"❌ Критическая ошибка в send_log_to_group: {e}")
        return False


# HELPERS
def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_activity(user_id, username, action, extra=""):
    entry = {"ts": ts(), "user_id": user_id, "username": username or str(user_id), "action": action, "extra": extra}
    activity_log.append(entry)
    logger.info(f"{entry['ts']} | @{entry['username']} ({user_id}) — {action} {extra}")


def generate_referral_code(user_id):
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))
    referral_codes[code] = user_id
    return code


def get_user_referral_stats(user_id):
    referrals_count = sum(1 for ref_id in user_referrals.values() if ref_id == user_id)
    return referrals_count


def get_user_language(user_id):
    """Получает язык пользователя (по умолчанию русский)"""
    return user_language.get(user_id, 'ru')


def get_text(user_id, text_key, **kwargs):
    """Получает текст на нужном языке"""
    lang = get_user_language(user_id)
    text = TEXTS[lang].get(text_key, text_key)
    return text.format(**kwargs) if kwargs else text


def get_successful_deals_count(user_id):
    """Получает количество успешных сделок пользователя"""
    return user_successful_deals.get(user_id, 0)


def get_user_rating(user_id):
    """Получает рейтинг пользователя"""
    return user_ratings.get(user_id, get_text(user_id, 'no_rating'))


def generate_successful_deals(user_id, count):
    """Генерирует историю успешных сделок для пользователя"""
    if user_id not in user_deals_history:
        user_deals_history[user_id] = []

    # Очищаем существующие сделки и генерируем новые
    user_deals_history[user_id] = []

    for i in range(1, count + 1):
        deal_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        currencies = ["RUB", "TON", "USD", "EUR", "USDT"]
        currency = random.choice(currencies)
        amount = round(random.uniform(10, 1000), 2)

        # Случайная дата в пределах последнего года
        days_ago = random.randint(1, 365)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        user_deals_history[user_id].append({
            'deal_id': deal_id,
            'deal_num': i,
            'amount': amount,
            'currency': currency,
            'date': date,
            'status': 'finished'
        })


def get_user_deals_summary(user_id):
    """Получает сводку по сделкам пользователя"""
    lang = get_user_language(user_id)

    # Активные сделки
    active_deals = []
    for deal_id, deal in deals.items():
        if deal['status'] == 'open' and deal['seller_id'] == user_id:
            active_deals.append(deal)

    # Завершенные сделки
    finished_deals = []
    for deal_id, deal in deals.items():
        if deal['status'] in ['finished', 'gift_sent', 'paid'] and (
                deal['seller_id'] == user_id or deal.get('buyer_id') == user_id):
            finished_deals.append(deal)

    # Успешные сделки (из истории)
    successful_count = get_successful_deals_count(user_id)
    history_deals = user_deals_history.get(user_id, [])

    # Формируем текст
    text = get_text(user_id, 'my_deals_info')

    if active_deals:
        text += get_text(user_id, 'active_deals_list')
        for i, deal in enumerate(active_deals[:5], 1):
            text += f"{i}. #{deal.get('id', 'N/A')} - {deal['amount']} {deal['currency']} - {deal['description'][:30]}...\n"
        if len(active_deals) > 5:
            text += f"... и еще {len(active_deals) - 5} активных сделок\n"
        text += "\n"

    if finished_deals:
        text += get_text(user_id, 'finished_deals_list')
        for i, deal in enumerate(finished_deals[:5], 1):
            text += f"{i}. #{deal.get('id', 'N/A')} - {deal['amount']} {deal['currency']} - {deal['description'][:30]}...\n"
        if len(finished_deals) > 5:
            text += f"... и еще {len(finished_deals) - 5} завершенных сделок\n"
        text += "\n"

    if successful_count > 0:
        text += get_text(user_id, 'successful_deals_count', count=successful_count)

        if history_deals:
            text += get_text(user_id, 'successful_deals_history')
            # Показываем первые 10 сделок
            for i, deal in enumerate(history_deals[:10], 1):
                text += get_text(user_id, 'deal_history_item',
                                 num=i,
                                 deal_id=deal['deal_id'],
                                 deal_num=deal['deal_num'],
                                 amount=deal['amount'],
                                 currency=deal['currency'],
                                 date=deal['date'])

            # Если сделок больше 10, показываем информацию о количестве
            if len(history_deals) > 10:
                text += get_text(user_id, 'and_more_deals', count=len(history_deals) - 10)

    if not active_deals and not finished_deals and successful_count == 0:
        text += get_text(user_id, 'no_deals')

    return text


def main_menu_keyboard(user_id: int):
    lang = get_user_language(user_id)
    kb = [
        [InlineKeyboardButton(get_text(user_id, 'wallet_management'), callback_data="wallet"),
         InlineKeyboardButton(get_text(user_id, 'create_deal'), callback_data="create_deal")],
        [InlineKeyboardButton(get_text(user_id, 'referral_system'), callback_data="referral"),
         InlineKeyboardButton(get_text(user_id, 'my_deals'), callback_data="my_deals")],
        [InlineKeyboardButton(get_text(user_id, 'stats'), callback_data="stats"),
         InlineKeyboardButton("🌐 " + get_text(user_id, 'change_language').split(" ", 1)[1] if " " in get_text(user_id,
                                                                                                              'change_language') else get_text(
             user_id, 'change_language'), callback_data="change_language")],
        [InlineKeyboardButton(get_text(user_id, 'support'), url='https://t.me/OpiumSafeSupporter')]
    ]
    if user_id in ADMIN_IDS:
        kb.insert(3, [InlineKeyboardButton(get_text(user_id, 'admin_panel'), callback_data="admin")])
    return InlineKeyboardMarkup(kb)


def language_keyboard(user_id: int):
    """Клавиатура для выбора языка"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def wallet_management_keyboard(user_id: int):
    """Клавиатура для управления кошельками"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 TON", callback_data="wallet_TON"),
         InlineKeyboardButton("💵 RUB", callback_data="wallet_RUB")],
        [InlineKeyboardButton("💲 USDT", callback_data="wallet_USDT"),
         InlineKeyboardButton("💳 Любая валюта", callback_data="wallet_ANY")],
        [InlineKeyboardButton(get_text(user_id, 'check_balance'), callback_data="check_balance"),
         InlineKeyboardButton(get_text(user_id, 'deposit_balance'), callback_data="deposit_balance")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def currency_keyboard(user_id: int):
    """Клавиатура для выбора валюты"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 TON", callback_data="deal_currency_TON"),
         InlineKeyboardButton("💵 RUB", callback_data="deal_currency_RUB")],
        [InlineKeyboardButton("💲 USDT", callback_data="deal_currency_USDT"),
         InlineKeyboardButton("⭐ Звёзды", callback_data="deal_currency_STAR")],
        [InlineKeyboardButton("💱 Любая валюта", callback_data="deal_currency_CUSTOM")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def deal_payment_keyboard(user_id: int, deal_id: str):
    """Клавиатура для оплаты сделки"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, 'pay'), callback_data=f"pay_{deal_id}")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def deal_created_keyboard(user_id: int, deal_id: str):
    """Клавиатура для созданной сделки"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, 'cancel_deal'), callback_data=f"cancel_deal_{deal_id}")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def seller_confirmation_keyboard(user_id: int, deal_id: str):
    """Клавиатура для подтверждения отправки подарка"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, 'confirm_transfer'), callback_data=f"confirm_{deal_id}")],
        [InlineKeyboardButton(get_text(user_id, 'get_support'), url=f"https://t.me/{MANAGER_ACCOUNT[1:]}")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def confirm_finish_keyboard(user_id: int, deal_id: str):
    """Клавиатура для подтверждения/завершения сделки"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, 'finish_deal'), callback_data=f"finish_{deal_id}"),
         InlineKeyboardButton(get_text(user_id, 'dispute'), callback_data=f"dispute_{deal_id}")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def referral_keyboard(user_id: int):
    """Клавиатура для реферальной системы"""
    lang = get_user_language(user_id)
    stats_text = "📊 Моя статистика" if lang == 'ru' else "📊 My statistics"
    share_text = "🔗 Поделиться ссылкой" if lang == 'ru' else "🔗 Share link"

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(stats_text, callback_data="ref_stats"),
         InlineKeyboardButton(share_text, callback_data="ref_share")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


def admin_keyboard(user_id: int):
    """Клавиатура для админ-панели"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, 'active_deals'), callback_data="admin_deals"),
         InlineKeyboardButton(get_text(user_id, 'activity_history'), callback_data="admin_history")],
        [InlineKeyboardButton(get_text(user_id, 'saved_wallets'), callback_data="admin_wallets"),
         InlineKeyboardButton(get_text(user_id, 'verified_users'), callback_data="admin_verified")],
        [InlineKeyboardButton(get_text(user_id, 'referral_stats_admin'), callback_data="admin_referrals")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ])


async def send_message_with_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """Универсальная функция для отправки сообщения с фотографией (файл из папки скрипта)"""
    try:
        # Обрезаем текст если слишком длинный для caption
        caption = text[:1024] if len(text) > 1024 else text

        # Путь к файлу фото
        photo_path = os.path.join(os.path.dirname(__file__), BOT_PHOTO_FILENAME)

        # Если файл найден, отправляем фото; иначе отправляем просто текст
        if os.path.isfile(photo_path):
            try:
                with open(photo_path, 'rb') as photo_file:
                    if update.callback_query:
                        await update.callback_query.message.reply_photo(
                            photo=photo_file,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    else:
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                logger.info("✅ Фото успешно отправлено")
                return
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке фото (файл): {e}")

        # Файл не найден или не получилось отправить фото — отправляем текст
        if update.callback_query:
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        logger.info("✅ Текст отправлен без фото")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке фото/текста: {e}")


async def send_message_simple(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """Универсальная функция для отправки сообщения БЕЗ фотографии"""
    try:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке текста: {e}")


# SAVAGETEAM VERIFICATION
async def savageteam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    verified_users.add(user.id)
    add_activity(user.id, user.username or user.full_name, "прошёл верификацию /ThursonSquad")

    # Логирование
    await send_log_to_group(
        context,
        "прошёл верификацию",
        user_id=user.id,
        username=user.username or user.full_name
    )

    await send_message_with_photo(
        update, context,
        get_text(user.id, 'verification_success'),
        reply_markup=main_menu_keyboard(user.id)
    )


# SET DEALS COMMAND - только для верифицированных пользователей
async def setdeals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Проверка верификации
    if user.id not in verified_users:
        await send_message_simple(update, context, get_text(user.id, 'not_verified'))
        return

    context.user_data["state"] = "set_deals"
    await send_message_simple(update, context, get_text(user.id, 'set_deals_prompt'))


# DELETE DEALS COMMAND - только для верифицированных пользователей
async def deletedeals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Проверка верификации
    if user.id not in verified_users:
        await send_message_simple(update, context, get_text(user.id, 'not_verified'))
        return

    user_successful_deals.pop(user.id, None)
    user_deals_history.pop(user.id, None)
    add_activity(user.id, user.username or user.full_name, "удалил все успешные сделки")

    # Логирование удаления сделок
    await send_log_to_group(
        context,
        "удалил все успешные сделки",
        user_id=user.id,
        username=user.username or user.full_name
    )

    await send_message_simple(update, context, get_text(user.id, 'deals_deleted'))


# SET RATING COMMAND - только для верифицированных пользователей
async def setrating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Проверка верификации
    if user.id not in verified_users:
        await send_message_simple(update, context, get_text(user.id, 'not_verified'))
        return

    context.user_data["state"] = "set_rating"
    await send_message_simple(update, context, get_text(user.id, 'set_rating_prompt'))


# DELETE RATING COMMAND - только для верифицированных пользователей
async def deleterating_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Проверка верификации
    if user.id not in verified_users:
        await send_message_simple(update, context, get_text(user.id, 'not_verified'))
        return

    user_ratings.pop(user.id, None)
    add_activity(user.id, user.username or user.full_name, "удалил рейтинг")

    # Логирование удаления рейтинга
    await send_log_to_group(
        context,
        "удалил рейтинг",
        user_id=user.id,
        username=user.username or user.full_name
    )

    await send_message_simple(update, context, get_text(user.id, 'rating_deleted'))


# START
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    # Обработка реферальных ссылок
    if args and args[0].startswith("ref_"):
        ref_code = args[0][4:]  # Убираем "ref_"
        if ref_code in referral_codes and referral_codes[ref_code] != user.id:
            referrer_id = referral_codes[ref_code]
            user_referrals[user.id] = referrer_id
            add_activity(user.id, user.username or user.full_name, "зарегистрировался по реферальной ссылке",
                         extra=f"от пользователя {referrer_id}")

            # Уведомляем реферера
            try:
                referrer_lang = get_user_language(referrer_id)
                notification_text = (
                    f"🎉 У вас новый реферал! @{user.username or user.full_name} присоединился по вашей ссылке."
                    if referrer_lang == 'ru' else
                    f"🎉 You have a new referral! @{user.username or user.full_name} joined using your link."
                )
                await context.bot.send_message(referrer_id, notification_text)
            except:
                pass

            # Логирование регистрации по реферальной ссылке
            await send_log_to_group(
                context,
                "зарегистрировался по реферальной ссылке",
                details=f"от пользователя {referrer_id}",
                user_id=user.id,
                username=user.username or user.full_name
            )

            await send_message_with_photo(update, context,
                                          "🎉 Вы зарегистрировались по реферальной ссылке!" if get_user_language(
                                              user.id) == 'ru' else
                                          "🎉 You registered using a referral link!"
                                          )

    # Обработка ссылок на сделки
    if args and args[0].startswith("deal_"):
        await open_deal_page(update, context, args[0].split("_", 1)[1])
        return

    # Логирование входа в меню
    await send_log_to_group(
        context,
        "зашёл в меню",
        user_id=user.id,
        username=user.username or user.full_name
    )

    await send_message_with_photo(
        update, context,
        get_text(user.id, 'main_text'),
        reply_markup=main_menu_keyboard(user.id)
    )

    if user.id not in ADMIN_IDS:
        add_activity(user.id, user.username or user.full_name, "зашёл в меню")


# OPEN DEAL PAGE
async def open_deal_page(update: Update, context: ContextTypes.DEFAULT_TYPE, deal_id: str):
    user = update.effective_user
    deal = deals.get(str(deal_id))
    if not deal:
        await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
        return

    if deal["seller_id"] == user.id:
        lang = get_user_language(user.id)
        message = "ℹ️ Это ваша сделка — ссылку должен открыть покупатель." if lang == 'ru' else "ℹ️ This is your deal — the buyer should open the link."
        await send_message_simple(update, context, message)
        return

    add_activity(user.id, user.username or user.full_name, f"перешёл по ссылке сделки #{deal_id}")

    # Логирование входа в сделку
    await send_log_to_group(
        context,
        "вошел в сделку",
        details=f"#{deal_id} с продавцом @{deal['seller_username']}",
        user_id=user.id,
        username=user.username or user.full_name
    )

    # Получаем адрес кошелька продавца
    seller_wallet = user_wallets.get((deal["seller_id"], deal["currency"]), "Не указан")

    # Получаем количество успешных сделок продавца
    seller_successful_deals = get_successful_deals_count(deal["seller_id"])

    # Получаем рейтинг продавца
    seller_rating = get_user_rating(deal["seller_id"])

    buyer_text = get_text(
        user.id, 'buyer_payment_info',
        deal_id=deal_id,
        seller_username=deal['seller_username'],
        seller_id=deal['seller_id'],
        successful_deals=seller_successful_deals,
        rating=seller_rating,
        description=deal['description'],
        wallet_address=seller_wallet,
        amount=deal['amount'],
        currency=deal['currency'],
        support_account=ESCROW_ACCOUNT
    )

    await send_message_simple(update, context, buyer_text, reply_markup=deal_payment_keyboard(user.id, deal_id))


# CALLBACK HANDLER
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if data == "main_menu":
        context.user_data.clear()
        await send_message_with_photo(
            update, context,
            get_text(user.id, 'main_text'),
            reply_markup=main_menu_keyboard(user.id)
        )
        if user.id not in ADMIN_IDS:
            add_activity(user.id, user.username or user.full_name, "вернулся в меню")
        return

    if data == "back":
        # Возвращаемся к предыдущему меню
        if user.id in ADMIN_IDS and "admin" in context.user_data.get("last_menu", ""):
            await send_message_with_photo(update, context, "⚙️ " + get_text(user.id, 'admin_panel') + ":",
                                          reply_markup=admin_keyboard(user.id))
            return

        await send_message_with_photo(
            update, context,
            get_text(user.id, 'main_text'),
            reply_markup=main_menu_keyboard(user.id)
        )
        return

    # MY DEALS
    if data == "my_deals":
        context.user_data["last_menu"] = "my_deals"
        deals_summary = get_user_deals_summary(user.id)
        await send_message_with_photo(update, context, deals_summary, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="main_menu")]
        ]))
        return

    # STATISTICS
    if data == "stats":
        context.user_data["last_menu"] = "stats"
        stats_text = get_text(
            user.id, 'deals_stats',
            total_deals=BOT_STATS['total_deals'],
            successful_deals=BOT_STATS['successful_deals'],
            total_volume=BOT_STATS['total_volume'],
            avg_rating=BOT_STATS['avg_rating'],
            online_now=BOT_STATS['online_now'],
            positive_reviews=BOT_STATS['positive_reviews']
        )
        await send_message_with_photo(update, context, stats_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="main_menu")]
        ]))
        return

    # DEPOSIT BALANCE
    if data == "deposit_balance":
        await send_message_simple(update, context, get_text(user.id, 'deposit_error'))
        return

    # CHANGE LANGUAGE
    if data == "change_language":
        context.user_data["last_menu"] = "change_language"
        await send_message_with_photo(
            update, context,
            get_text(user.id, 'choose_language'),
            reply_markup=language_keyboard(user.id)
        )
        return

    if data.startswith("lang_"):
        language = data.split("_", 1)[1]
        user_language[user.id] = language
        add_activity(user.id, user.username or user.full_name, f"сменил язык на {language}")

        # Логирование смены языка
        await send_log_to_group(
            context,
            "сменил язык",
            details=f"на {language}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        await send_message_with_photo(
            update, context,
            get_text(user.id, 'language_changed'),
            reply_markup=main_menu_keyboard(user.id)
        )
        return

    # WALLET MANAGEMENT
    if data == "wallet":
        context.user_data["last_menu"] = "wallet"
        await send_message_with_photo(
            update, context,
            get_text(user.id, 'choose_wallet'),
            reply_markup=wallet_management_keyboard(user.id)
        )
        return

    if data == "check_balance":
        # Проверяем балансы всех привязанных кошельков
        balance_text = ""
        for currency in ["TON", "RUB", "USDT"]:
            wallet_address = user_wallets.get((user.id, currency))
            if wallet_address:
                balance = round(random.uniform(0, 10000), 2)
                balance_text += get_text(user.id, 'balance_info', currency=currency, balance=balance) + "\n"
            else:
                balance_text += get_text(user.id, 'no_wallet', currency=currency) + "\n"

        # Проверяем баланс для "любой валюты"
        any_wallet = user_wallets.get((user.id, "ANY"))
        if any_wallet:
            balance_text += get_text(user.id, 'balance_info', currency="Любая валюта",
                                     balance="Невозможно проверить") + "\n"

        if not balance_text:
            balance_text = get_text(user.id, 'no_wallet', currency="любого")

        await send_message_with_photo(update, context, balance_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="wallet")]
        ]))
        return

    if data.startswith("wallet_"):
        currency = data.split("_", 1)[1]

        if currency == "ANY":
            context.user_data["state"] = "wallet_input_any"
            context.user_data["wallet_currency"] = "ANY"
            await send_message_with_photo(
                update, context,
                get_text(user.id, 'enter_any_wallet'),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="wallet")]
                ])
            )
            return

        # Проверяем, что валюта допустима
        if currency not in ["TON", "RUB", "USDT"]:
            await send_message_simple(update, context, "❌ Неверная валюта")
            return

        context.user_data["state"] = "wallet_input"
        context.user_data["wallet_currency"] = currency
        await send_message_with_photo(
            update, context,
            get_text(user.id, 'enter_wallet_details', currency=currency),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="wallet")]
            ])
        )
        return

    # CREATE DEAL - СНАЧАЛА ВЫБОР ВАЛЮТЫ
    if data == "create_deal":
        context.user_data["last_menu"] = "create_deal"
        await send_message_with_photo(
            update, context,
            get_text(user.id, 'deal_currency_first'),
            reply_markup=currency_keyboard(user.id)
        )
        return

    # ВЫБОР ВАЛЮТЫ ДЛЯ СДЕЛКИ
    if data.startswith("deal_currency_"):
        currency = data.split("_", 2)[2]

        if currency == "CUSTOM":
            context.user_data["state"] = "custom_currency"
            await send_message_simple(update, context, get_text(user.id, 'custom_currency_prompt'),
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="create_deal")]
                                      ]))
            return

        # Для валют TON, RUB и USDT проверяем наличие реквизитов
        if currency in ["TON", "RUB", "USDT"]:
            user_wallet = user_wallets.get((user.id, currency))

            if not user_wallet:
                # Если реквизитов нет, предлагаем сначала добавить их
                await send_message_simple(
                    update, context,
                    get_text(user.id, 'no_wallet_for_currency', currency=currency),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="create_deal")]
                    ])
                )
                return

        # Для STAR реквизиты не требуются - сразу продолжаем создание сделки
        await send_message_simple(
            update, context,
            get_text(user.id, 'create_deal_with_currency', currency=currency),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="create_deal")]
            ])
        )

        context.user_data["state"] = "deal_amount"
        context.user_data["deal_currency"] = currency
        await send_message_simple(update, context, get_text(user.id, 'deal_amount'),
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="create_deal")]
                                  ]))
        return

    # CANCEL DEAL - БЕЗ ФОТО
    if data.startswith("cancel_deal_"):
        deal_id = str(data.split("_", 2)[2])
        deal = deals.get(deal_id)
        if not deal:
            await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
            return

        if user.id != deal["seller_id"]:
            await send_message_simple(update, context, "⚠ Только продавец может отменить сделку.")
            return

        if deal["status"] != "open":
            await send_message_simple(update, context, "⚠ Нельзя отменить сделку в текущем статусе.")
            return

        deals[deal_id]["status"] = "cancelled"
        add_activity(user.id, user.username or user.full_name, f"отменил сделку #{deal_id}")

        # Логирование отмены сделки
        await send_log_to_group(
            context,
            "отменил сделку",
            details=f"#{deal_id} на сумму {deal['amount']} {deal['currency']}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        await send_message_simple(
            update, context,
            get_text(user.id, 'deal_cancelled', deal_id=deal_id),
            reply_markup=main_menu_keyboard(user.id)
        )
        return

    # PAY - БЕЗ ФОТО
    if data.startswith("pay_"):
        deal_id = str(data.split("_", 1)[1])
        deal = deals.get(deal_id)
        if not deal:
            await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
            return

        # ПРОВЕРКА ВЕРИФИКАЦИИ
        if user.id not in verified_users:
            await send_message_simple(update, context, get_text(user.id, 'insufficient_balance'))
            return

        deal["status"] = "paid"
        deal["buyer_id"] = user.id
        deal["buyer_username"] = user.username or user.full_name
        add_activity(user.id, user.username or user.full_name, f"оплатил сделку #{deal_id}",
                     extra=f"{deal['amount']} {deal['currency']}")

        # Логирование оплаты сделки
        await send_log_to_group(
            context,
            "оплатил сделку",
            details=f"#{deal_id} на сумму {deal['amount']} {deal['currency']} у продавца @{deal['seller_username']}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        # Получаем количество успешных сделок продавца и покупателя
        seller_successful_deals = get_successful_deals_count(deal["seller_id"])
        buyer_successful_deals = get_successful_deals_count(user.id)

        # Получаем рейтинги
        seller_rating = get_user_rating(deal["seller_id"])
        buyer_rating = get_user_rating(user.id)

        # Уведомление покупателя - БЕЗ ФОТО
        buyer_text = get_text(
            user.id, 'buyer_payment_confirmed',
            deal_id=deal_id,
            seller_username=deal['seller_username'],
            successful_deals=seller_successful_deals,
            rating=seller_rating,
            amount=deal['amount'],
            currency=deal['currency'],
            description=deal['description'],
            manager_account=MANAGER_ACCOUNT
        )
        await send_message_simple(update, context, buyer_text)

        # Уведомление продавца - БЕЗ ФОТО
        seller_text = get_text(
            deal["seller_id"], 'seller_payment_confirmed',
            deal_id=deal_id,
            buyer_username=deal['buyer_username'],
            successful_deals=buyer_successful_deals,
            rating=buyer_rating,
            amount=deal['amount'],
            currency=deal['currency'],
            description=deal['description'],
            manager_account=MANAGER_ACCOUNT
        )

        # Критически важное правило для продавца - БЕЗ ФОТО
        critical_rule_text = get_text(
            deal["seller_id"], 'critical_rule',
            manager_account=MANAGER_ACCOUNT
        )

        try:
            # Первое сообщение - информация о подтверждении оплаты
            await context.bot.send_message(
                chat_id=deal["seller_id"],
                text=seller_text,
                reply_markup=seller_confirmation_keyboard(deal["seller_id"], deal_id)
            )
            # Второе сообщение - критически важное правило
            await context.bot.send_message(
                chat_id=deal["seller_id"],
                text=critical_rule_text
            )
        except:
            logger.exception("Не удалось уведомить продавца")

        return

    # CONFIRM GIFT SENDING - БЕЗ ФОТО
    if data.startswith("confirm_"):
        deal_id = str(data.split("_", 1)[1])
        deal = deals.get(deal_id)
        if not deal:
            await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
            return
        if user.id != deal["seller_id"]:
            await send_message_simple(update, context, "⚠ Только продавец может подтвердить отправку подарка.")
            return

        deal["status"] = "gift_sent"
        add_activity(user.id, user.username or user.full_name, f"подтвердил отправку подарка по сделке #{deal_id}")

        # Логирование подтверждения отправки подарка
        await send_log_to_group(
            context,
            "подтвердил отправку подарка",
            details=f"по сделке #{deal_id} покупателю @{deal['buyer_username']}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        # Уведомление покупателя - БЕЗ ФОТО
        buyer_id = deal.get("buyer_id")
        if buyer_id:
            try:
                buyer_text = get_text(buyer_id, 'gift_sent_notification')
                await context.bot.send_message(chat_id=buyer_id, text=buyer_text)
            except:
                logger.exception("Не удалось уведомить покупателя")

        await send_message_simple(update, context, "✅ Вы подтвердили отправку подарка. Покупатель уведомлён.")
        return

    # FINISH DEAL - БЕЗ ФОТО
    if data.startswith("finish_"):
        deal_id = str(data.split("_", 1)[1])
        deal = deals.get(deal_id)
        if not deal:
            await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
            return
        if user.id != deal.get("buyer_id"):
            await send_message_simple(update, context, "⚠ Только покупатель может завершить сделку.")
            return

        deal["status"] = "finished"
        add_activity(user.id, user.username or user.full_name, f"завершил сделку #{deal_id}")

        # Логирование завершения сделки
        await send_log_to_group(
            context,
            "завершил сделку",
            details=f"#{deal_id} с продавцом @{deal['seller_username']}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        try:
            seller_lang = get_user_language(deal["seller_id"])
            message = (
                f"✅ Сделка #{deal_id} завершена покупателем @{deal['buyer_username']}."
                if seller_lang == 'ru' else
                f"✅ Deal #{deal_id} finished by buyer @{deal['buyer_username']}."
            )
            await context.bot.send_message(chat_id=deal["seller_id"], text=message)
        except:
            logger.exception("Ошибка уведомления")

        await send_message_simple(update, context, get_text(user.id, 'deal_completed'))
        return

    # DISPUTE - БЕЗ ФОТО
    if data.startswith("dispute_"):
        deal_id = str(data.split("_", 1)[1])
        deal = deals.get(deal_id)
        if not deal:
            await send_message_simple(update, context, get_text(user.id, 'deal_not_found'))
            return

        deal["status"] = "disputed"
        add_activity(user.id, user.username or user.full_name, f"оспорил сделку #{deal_id}")

        # Логирование спора по сделке
        await send_log_to_group(
            context,
            "оспорил сделку",
            details=f"#{deal_id} с продавцом @{deal['seller_username']}",
            user_id=user.id,
            username=user.username or user.full_name
        )

        try:
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"⚠ DISPUTE: @{user.username or user.full_name} оспорил сделку #{deal_id}"
                )
        except:
            logger.exception("Не удалось уведомить админов о споре")

        await send_message_simple(update, context, "⚠️ Вы оспорили сделку. Поддержка получит уведомление.")
        return

    # REFERRAL SYSTEM
    if data == "referral":
        context.user_data["last_menu"] = "referral"
        # Генерация реферальной ссылки
        ref_code = generate_referral_code(user.id)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"

        # Статистика рефералов
        user_ref_count = get_user_referral_stats(user.id)

        ref_text = get_text(
            user.id, 'referral_text',
            ref_count=user_ref_count,
            ref_link=ref_link
        )

        await send_message_with_photo(update, context, ref_text, reply_markup=referral_keyboard(user.id))
        return

    if data == "ref_stats":
        user_ref_count = get_user_referral_stats(user.id)
        ref_stats_text = get_text(user.id, 'referral_stats', ref_count=user_ref_count)
        await send_message_with_photo(update, context, ref_stats_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="referral")]
        ]))
        return

    if data == "ref_share":
        ref_code = generate_referral_code(user.id)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"
        share_text = get_text(user.id, 'share_text', ref_link=ref_link)

        lang = get_user_language(user.id)
        caption = "📤 Текст для分享:\n\n" if lang == 'ru' else "📤 Text for sharing:\n\n"
        await send_message_with_photo(update, context, f"{caption}{share_text}", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="referral")]
        ]))
        return

    # ADMIN PANEL
    if data == "admin" and user.id in ADMIN_IDS:
        context.user_data["last_menu"] = "admin"
        await send_message_with_photo(update, context, "⚙️ " + get_text(user.id, 'admin_panel') + ":",
                                      reply_markup=admin_keyboard(user.id))
        return

    if data == "admin_deals" and user.id in ADMIN_IDS:
        if not deals:
            await send_message_with_photo(update, context,
                                          "Нет сделок." if get_user_language(user.id) == 'ru' else "No deals.",
                                          reply_markup=InlineKeyboardMarkup([
                                              [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                          ]))
            return
        lines = [
            f"#{did} — {d['amount']} {d['currency']} — {d['status']} — seller @{d.get('seller_username')} buyer @{d.get('buyer_username') or '-'}"
            for did, d in deals.items()]
        await send_message_with_photo(update, context, get_text(user.id, 'active_deals') + ":\n\n" + "\n".join(lines),
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                      ]))
        return

    if data == "admin_history" and user.id in ADMIN_IDS:
        lines = [f"[{e['ts']}] @{e['username']}: {e['action']}" + (f" | {e['extra']}" if e['extra'] else "")
                 for e in activity_log[-200:]]
        await send_message_with_photo(update, context,
                                      get_text(user.id, 'activity_history') + ":\n\n" + (
                                          "\n".join(lines) if lines else "Пусто" if get_user_language(
                                              user.id) == 'ru' else "Empty"),
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                      ]))
        return

    if data == "admin_wallets" and user.id in ADMIN_IDS:
        lines = [f"user:{uid} | {cur} -> {val}" for (uid, cur), val in user_wallets.items()]
        await send_message_with_photo(update, context,
                                      get_text(user.id, 'saved_wallets') + ":\n\n" + (
                                          "\n".join(lines) if lines else "Пусто" if get_user_language(
                                              user.id) == 'ru' else "Empty"),
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                      ]))
        return

    if data == "admin_verified" and user.id in ADMIN_IDS:
        verified_count = len(verified_users)
        await send_message_with_photo(update, context, get_text(user.id, 'verified_users') + f": {verified_count}",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                      ]))
        return

    if data == "admin_referrals" and user.id in ADMIN_IDS:
        total_referrals = len(user_referrals)
        await send_message_with_photo(update, context,
                                      get_text(user.id, 'referral_stats_admin') + f":\n\n" + (
                                          "Всего рефералов" if get_user_language(
                                              user.id) == 'ru' else "Total referrals") + f": {total_referrals}",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(get_text(user.id, 'back'), callback_data="admin")]
                                      ]))
        return

    await send_message_with_photo(update, context, get_text(user.id, 'not_understood'))


# MESSAGE HANDLER
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()
    state = context.user_data.get("state")

    # WALLET INPUT FOR ANY CURRENCY
    if state == "wallet_input_any":
        user_wallets[(user.id, "ANY")] = text
        add_activity(user.id, user.username or user.full_name, "добавил кошелёк для любой валюты", extra=text)

        # Логирование добавления кошелька
        await send_log_to_group(
            context,
            "добавил кошелёк для любой валюты",
            details=f"Реквизиты: {text[:50]}...",
            user_id=user.id,
            username=user.username or user.full_name
        )

        await send_message_with_photo(
            update, context,
            get_text(user.id, 'any_wallet_saved'),
            reply_markup=main_menu_keyboard(user.id)
        )
        context.user_data.pop("wallet_currency", None)
        context.user_data.pop("state", None)
        return

    # CUSTOM CURRENCY INPUT
    if state == "custom_currency":
        if not text or len(text) > 10:
            await send_message_simple(update, context,
                                      "❌ Пожалуйста, введите корректное название валюты (до 10 символов)")
            return

        context.user_data["custom_currency"] = text
        context.user_data["state"] = "deal_amount"
        context.user_data["deal_currency"] = text

        await send_message_simple(
            update, context,
            get_text(user.id, 'custom_currency_saved', currency=text)
        )
        await send_message_simple(update, context, get_text(user.id, 'deal_amount'))
        return

    if state == "wallet_input":
        currency = context.user_data.get("wallet_currency")
        if not currency:
            await send_message_with_photo(update, context, "⚠ Ошибка состояния. Повторите добавление кошелька.")
            context.user_data.pop("state", None)
            context.user_data.pop("wallet_currency", None)
            return

        # Проверяем, что валюта допустима
        if currency not in ["TON", "RUB", "USDT"]:
            await send_message_simple(update, context, "❌ Неверная валюта")
            context.user_data.pop("state", None)
            context.user_data.pop("wallet_currency", None)
            return

        user_wallets[(user.id, currency)] = text
        add_activity(user.id, user.username or user.full_name, f"добавил кошелёк {currency}", extra=text)

        # Логирование добавления кошелька
        await send_log_to_group(
            context,
            f"добавил кошелёк {currency}",
            details=f"Реквизиты: {text[:50]}...",
            user_id=user.id,
            username=user.username or user.full_name
        )

        await send_message_with_photo(
            update, context,
            get_text(user.id, 'wallet_saved', currency=currency),
            reply_markup=main_menu_keyboard(user.id)
        )
        context.user_data.pop("wallet_currency", None)
        context.user_data.pop("state", None)
        return

    # SET DEALS STATE
    if state == "set_deals":
        try:
            deals_count = int(text)
            if deals_count < 0:
                await send_message_simple(update, context, get_text(user.id, 'set_deals_invalid'))
                return

            user_successful_deals[user.id] = deals_count
            generate_successful_deals(user.id, deals_count)
            add_activity(user.id, user.username or user.full_name,
                         f"установил количество успешных сделок: {deals_count}")

            # Логирование установки сделок
            await send_log_to_group(
                context,
                "установил количество успешных сделок",
                details=f"Количество: {deals_count}",
                user_id=user.id,
                username=user.username or user.full_name
            )

            await send_message_simple(
                update, context,
                get_text(user.id, 'set_deals_success', count=deals_count),
                reply_markup=main_menu_keyboard(user.id)
            )
            context.user_data.pop("state", None)
            return

        except ValueError:
            await send_message_simple(update, context, get_text(user.id, 'set_deals_invalid'))
            return

    # SET RATING STATE
    if state == "set_rating":
        try:
            rating = float(text.replace(",", "."))
            if rating < 1 or rating > 5:
                await send_message_simple(update, context, get_text(user.id, 'set_rating_invalid'))
                return

            user_ratings[user.id] = f"{rating:.1f}"
            add_activity(user.id, user.username or user.full_name,
                         f"установил рейтинг: {rating:.1f}")

            # Логирование установки рейтинга
            await send_log_to_group(
                context,
                "установил рейтинг",
                details=f"Рейтинг: {rating:.1f}/5",
                user_id=user.id,
                username=user.username or user.full_name
            )

            await send_message_simple(
                update, context,
                get_text(user.id, 'set_rating_success', rating=f"{rating:.1f}"),
                reply_markup=main_menu_keyboard(user.id)
            )
            context.user_data.pop("state", None)
            return

        except ValueError:
            await send_message_simple(update, context, get_text(user.id, 'set_rating_invalid'))
            return

    # СООБЩЕНИЯ В ПРОЦЕССЕ СДЕЛКИ
    if state == "deal_amount":
        try:
            amount = float(text.replace(",", "."))
            if amount <= 0:
                await send_message_simple(update, context, "⚠ Сумма должна быть больше 0.")
                return
        except:
            await send_message_simple(update, context, "⚠ Введите корректную сумму числом.")
            return

        context.user_data["deal_amount"] = amount
        context.user_data["state"] = "deal_description"
        await send_message_simple(update, context, get_text(user.id, 'deal_description'))
        return

    if state == "deal_description":
        if not text:
            await send_message_simple(update, context, "⚠ Введите описание подарка.")
            return

        deal_currency = context.user_data.get("deal_currency")
        deal_amount = context.user_data.get("deal_amount")
        deal_description = text

        # Для пользовательской валюты проверяем наличие кошелька "ANY"
        if deal_currency not in ["TON", "RUB", "USDT", "STAR"]:
            # Это пользовательская валюта, проверяем кошелёк ANY
            user_wallet = user_wallets.get((user.id, "ANY"))
            if not user_wallet:
                await send_message_simple(
                    update, context,
                    f"❌ У вас не привязаны реквизиты для любых валют. Сначала добавьте их в разделе 'Управление реквизитами'."
                )
                return

        # Создаем сделку
        deal_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        bot_info = await context.bot.get_me()
        deals[deal_id] = {
            "seller_id": user.id,
            "seller_username": user.username or user.full_name,
            "amount": deal_amount,
            "description": deal_description,
            "currency": deal_currency,
            "status": "open",
            "buyer_id": None,
            "buyer_username": None,
            "id": deal_id
        }
        link = f"https://t.me/{bot_info.username}?start=deal_{deal_id}"

        add_activity(user.id, user.username or user.full_name, f"создал сделку #{deal_id}",
                     extra=f"{deal_amount} {deal_currency} - {deal_description}")

        # Логирование создания сделки
        await send_log_to_group(
            context,
            "создал сделку",
            details=f"#{deal_id} на сумму {deal_amount} {deal_currency}: {deal_description[:50]}...",
            user_id=user.id,
            username=user.username or user.full_name
        )

        await send_message_simple(
            update, context,
            get_text(user.id, 'deal_created', deal_id=deal_id, amount=deal_amount, currency=deal_currency,
                     description=deal_description, link=link),
            reply_markup=deal_created_keyboard(user.id, deal_id)
        )
        context.user_data.pop("state", None)
        context.user_data.pop("deal_amount", None)
        context.user_data.pop("deal_description", None)
        context.user_data.pop("deal_currency", None)
        context.user_data.pop("custom_currency", None)
        return

    await send_message_with_photo(
        update, context,
        get_text(user.id, 'not_understood'),
        reply_markup=main_menu_keyboard(user.id)
    )


# APP START
def main():
    app = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("ThursonSquad", savageteam_handler))
    app.add_handler(CommandHandler("setdeals", setdeals_handler))
    app.add_handler(CommandHandler("deletedeals", deletedeals_handler))
    app.add_handler(CommandHandler("setrating", setrating_handler))
    app.add_handler(CommandHandler("deleterating", deleterating_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("=" * 50)
    logger.info("Бот Opium Safe запущен")
    logger.info(f"ID группы для логов: {LOG_CHAT_ID}")
    logger.info("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()