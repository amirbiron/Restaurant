#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עוזר העסק בטלגרם - דמו מקצועי
"""

import os
import sys
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from activity_reporter import create_reporter

# הגדרת לוגים
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# קובץ נתונים
DATA_FILE = 'data.json'

# טוקן הבוט (מרנדר)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# בדיקה שהטוקן קיים
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in environment variables!")
    logger.error("Please set the BOT_TOKEN in Render dashboard")
    sys.exit(1)

# Activity reporter (initialized after environment is loaded)
class _NoopReporter:
    def report_activity(self, user_id):
        return

MONGO_URI = os.environ.get('MONGO_URI')
SERVICE_ID = os.environ.get('SERVICE_ID', 'local')
SERVICE_NAME = os.environ.get('SERVICE_NAME', 'RestaurantBot')

if MONGO_URI:
    reporter = create_reporter(
        mongodb_uri=MONGO_URI,
        service_id=SERVICE_ID,
        service_name=SERVICE_NAME
    )
else:
    reporter = _NoopReporter()

# מחלקה לניהול נתונים
class DataManager:
    def __init__(self):
        self.data = self.load_data()
        if 'menu' not in self.data:
            self.data['menu'] = self.default_menu()
        if 'orders' not in self.data:
            self.data['orders'] = []
        self.save_data()
    
    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'leads': [],
                'appointments': [],
                'settings': {
                    'admin_id': None,
                    'business_phone': '03-1234567',
                    'working_hours': 'א׳-ה׳ 09:00-18:00',
                    'welcome_message': 'שלום! 👋\nברוכים הבאים לעוזר העסק בטלגרם. כאן אפשר לראות קטלוג קצר, לקבוע תור/הזמנה, לקבל תשובות מהירות וליצור קשר ישיר.\nאיך אוכל לעזור?'
                }
            }
    
    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def default_menu(self):
        return [
            {"id": 1, "name": "פיצה מרגריטה", "price": 48, "tags": ["צמחוני"], "allergens": ["גלוטן", "לקטוז"], "image": "https://via.placeholder.com/800x600?text=Pizza"},
            {"id": 2, "name": "סלט יווני", "price": 42, "tags": ["צמחוני", "ללא גלוטן"], "allergens": ["אגוזים"], "image": "https://via.placeholder.com/800x600?text=Salad"},
            {"id": 3, "name": "המבורגר", "price": 64, "tags": [], "allergens": ["גלוטן"], "image": "https://via.placeholder.com/800x600?text=Burger"},
            {"id": 4, "name": "פסטה ארביאטה", "price": 56, "tags": ["צמחוני", "חריף"], "allergens": ["גלוטן"], "image": "https://via.placeholder.com/800x600?text=Pasta"}
        ]
    
    def add_lead(self, user_id, name, phone, business_name='', interest='', source='דמו טלגרם'):
        # Deduplicate by user_id+phone: update if exists
        for existing in self.data['leads']:
            if existing.get('user_id') == user_id and existing.get('phone') == phone:
                existing.update({
                    'name': name,
                    'business_name': business_name,
                    'interest': interest,
                    'source': source,
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                self.save_data()
                return existing
        lead = {
            'id': len(self.data['leads']) + 1,
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'business_name': business_name,
            'interest': interest,
            'source': source,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.data['leads'].append(lead)
        self.save_data()
        return lead
    
    def add_appointment(self, user_id, name, phone, date, time, service=''):
        appointment = {
            'id': len(self.data['appointments']) + 1,
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'date': date,
            'time': time,
            'service': service,
            'status': 'ממתין לאישור',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.data['appointments'].append(appointment)
        self.save_data()
        return appointment

    def add_order(self, user_id, items):
        total = 0
        for it in items:
            total += it.get('price', 0) * it.get('qty', 1)
        order = {
            'id': len(self.data['orders']) + 1,
            'user_id': user_id,
            'items': items,
            'total': total,
            'status': 'חדש',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.data['orders'].append(order)
        self.save_data()
        return order

# יצירת מנהל נתונים גלובלי
dm = DataManager()

# פונקציות עזר לתפריטים
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton('🛍️ קטלוג קצר'), KeyboardButton('📆 קביעת תור/הזמנה')],
        [KeyboardButton('❓ שאלות ותמיכה'), KeyboardButton('📞 צור קשר')],
        [KeyboardButton('📍 איפה אנחנו'), KeyboardButton('💬 מה אומרים עלינו')],
        [KeyboardButton('📋 ההזמנות שלי')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def catalog_keyboard():
    keyboard = [
        [InlineKeyboardButton('🧾 פרטים', callback_data='details_basic'), 
         InlineKeyboardButton('💬 התעניינות', callback_data='interest_basic')],
        [InlineKeyboardButton('🧾 פרטים', callback_data='details_plus'), 
         InlineKeyboardButton('💬 התעניינות', callback_data='interest_plus')],
        [InlineKeyboardButton('🧾 פרטים', callback_data='details_pro'), 
         InlineKeyboardButton('💬 התעניינות', callback_data='interest_pro')],
        [InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def faq_keyboard():
    keyboard = [
        [InlineKeyboardButton('⏰ שעות פעילות', callback_data='faq_hours')],
        [InlineKeyboardButton('🚚 משלוחים/שירות מרחוק', callback_data='faq_delivery')],
        [InlineKeyboardButton('💳 תשלום וקבלות', callback_data='faq_payment')],
        [InlineKeyboardButton('🧾 חשבונית', callback_data='faq_invoice')],
        [InlineKeyboardButton('👨‍💻 נציג אנושי', callback_data='human_support')],
        [InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# הודעת פתיחה
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    user = update.effective_user
    
    # שמירת מנהל ראשון כאדמין
    if dm.data['settings']['admin_id'] is None:
        dm.data['settings']['admin_id'] = user.id
        dm.save_data()
        await update.message.reply_text('🎉 הוגדרת כמנהל הבוט!')
    
    status_prefix = '🟢 פתוח עכשיו - נענה מיד!' if is_business_open() else '🔴 סגור כרגע - נחזור בשעות הפעילות'
    await update.message.reply_text(
        f"{status_prefix}\n\n" + dm.data['settings']['welcome_message'],
        reply_markup=main_menu_keyboard()
    )

# טיפול בהודעות טקסט (תפריט ראשי)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    text = update.message.text
    
    if text == '🛍️ קטלוג קצר':
        await show_catalog(update, context)
    elif text == '📆 קביעת תור/הזמנה':
        await show_appointment_booking(update, context)
    elif text == '❓ שאלות ותמיכה':
        await show_faq(update, context)
    elif text == '📞 צור קשר':
        await show_contact_form(update, context)
    elif text == '📍 איפה אנחנו':
        await show_location_info(update, context)
    elif text == '💬 מה אומרים עלינו':
        await show_reviews(update, context)
    elif text == '📋 ההזמנות שלי':
        await show_user_history(update, context)
    else:
        await update.message.reply_text(
            'אנא בחר/י אחת מהאפשרויות בתפריט 👇',
            reply_markup=main_menu_keyboard()
        )

# קטלוג
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    await update.message.reply_text(
        get_catalog_text(),
        parse_mode='Markdown',
        reply_markup=catalog_keyboard()
    )

# קביעת תור
async def show_appointment_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    # הזמנת שולחן: בחירת תאריך וגודל קבוצה
    today = datetime.now()
    dates = []
    for i in range(1, 6):  # 5 ימים הבאים
        date = today + timedelta(days=i)
        dates.append(InlineKeyboardButton(
            date.strftime('%d/%m (%a)'), 
            callback_data=f'date_{date.strftime("%Y-%m-%d")}'
        ))
    keyboard = [dates[i:i+2] for i in range(0, len(dates), 2)]
    keyboard.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')])
    await update.message.reply_text(
        '📆 הזמנת שולחן – בחרו יום:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# שאלות ותמיכה
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    await update.message.reply_text(
        'שאלות נפוצות – לחצו לקבלת מענה מיידי:',
        reply_markup=faq_keyboard()
    )

# צור קשר
async def show_contact_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    context.user_data['contact_step'] = 'name'
    await update.message.reply_text(
        'נשמח לחזור אליך 👇\nאנא שתף/י את השם הפרטי:'
    )
    # הצעת שיתוף טלפון בכפתור ייעודי בשלב הטלפון

# חדש: מיקום ופרטי עסק
async def show_location_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    latitude = 32.0853
    longitude = 34.7818
    address = 'רחוב הרצל 15, תל אביב'
    working_hours = dm.data['settings'].get('working_hours', 'א׳-ה׳ 09:00-18:00')

    # שליחת מיקום
    await update.message.reply_location(latitude=latitude, longitude=longitude)

    # קישורים לווייז וגוגל מפות
    encoded_address = quote_plus(address)
    waze_url = f'https://waze.com/ul?q={encoded_address}&navigate=yes'
    gmaps_url = f'https://www.google.com/maps/search/?api=1&query={encoded_address}'

    keyboard = [
        [InlineKeyboardButton('🗺️ פתח בוויז', url=waze_url), InlineKeyboardButton('📍 פתח בגוגל מפות', url=gmaps_url)],
        [InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]
    ]

    text = f"📍 {address}\n⏰ שעות פעילות: {working_hours}"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# חדש: המלצות לקוחות
async def show_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    # אלבום ביקורות כתמונות עם כיתובים
    media = [
        InputMediaPhoto(
            media='https://via.placeholder.com/800x600.png?text=%E2%AD%90%E2%AD%90%E2%AD%90%E2%AD%90%E2%AD%90',
            caption='⭐⭐⭐⭐⭐\n"שירות מעולה! קיבלתי בדיוק מה שרציתי."\n- שרה כהן'
        ),
        InputMediaPhoto(
            media='https://via.placeholder.com/800x600.png?text=%D7%94%D7%9E%D7%9C%D7%A6%D7%94+%232',
            caption='⭐⭐⭐⭐⭐\n"מקצועיים, מהירים ואמינים. ממליצה בחום!"\n- דוד לוי'
        ),
        InputMediaPhoto(
            media='https://via.placeholder.com/800x600.png?text=%D7%94%D7%9E%D7%9C%D7%A6%D7%94+%233',
            caption='⭐⭐⭐⭐⭐\n"עבודה נקייה והתאמה מושלמת לדרישות שלי."\n- רחל אברהם'
        )
    ]

    try:
        await update.message.reply_media_group(media=media)
    except Exception:
        # נפילה חיננית: אם אלבום נכשל, שלח טקסטים נפרדים
        for m in media:
            await update.message.reply_text(m.caption)

    await update.message.reply_text(
        'רוצה לראות עוד? או לחזור לתפריט:',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]])
    )

# === Restaurant minimal handlers ===
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    items = dm.data.get('menu', [])
    if not items:
        await update.message.reply_text('התפריט אינו זמין כעת')
        return
    keyboard = []
    lines = []
    for item in items:
        lines.append(f"🍽️ {item['name']} — {item['price']}₪")
        tags = ', '.join(item.get('tags', []))
        if tags:
            lines.append(f"• {tags}")
        if item.get('allergens'):
            lines.append(f"אלרגנים: {', '.join(item['allergens'])}")
        keyboard.append([InlineKeyboardButton(f"➕ הוסף {item['name']}", callback_data=f"add_{item['id']}")])
        lines.append('')
    keyboard.append([InlineKeyboardButton('🧺 הצג עגלה', callback_data='cart_review')])
    await update.message.reply_text('\n'.join(lines).strip(), reply_markup=InlineKeyboardMarkup(keyboard))

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    cart = context.user_data.get('cart', {})
    if not cart:
        await update.message.reply_text('העגלה ריקה. אפשר להוסיף מנות מהתפריט 🙂')
        return
    items = {i['id']: i for i in dm.data.get('menu', [])}
    total = 0
    lines = ['🧺 העגלה שלי:\n']
    kb = []
    for item_id, qty in cart.items():
        item = items.get(int(item_id))
        if not item:
            continue
        line_total = item['price'] * qty
        total += line_total
        lines.append(f"{item['name']} x{qty} — {line_total}₪")
        kb.append([InlineKeyboardButton(f"➖ הסר {item['name']}", callback_data=f"remove_{item_id}")])
    lines.append('')
    lines.append(f"סה""כ: {total}₪")
    kb.append([InlineKeyboardButton('✅ בצע הזמנה', callback_data='order_confirm')])
    kb.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='back_menu')])
    await update.message.reply_text('\n'.join(lines), reply_markup=InlineKeyboardMarkup(kb))

async def show_delivery_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    text = """🚚 משלוחים

• משלוח בטווח 5 ק""מ
• זמן משוער: 35–50 דק׳
• תשלום: מזומן/אשראי/קישור
"""
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]]))

# טיפול בלחיצות על כפתורים
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'main_menu':
        await query.edit_message_text(
            dm.data['settings']['welcome_message'],
            reply_markup=None
        )
        await query.message.reply_text(
            'איך אוכל לעזור?',
            reply_markup=main_menu_keyboard()
        )
    
    elif data.startswith('details_'):
        package = data.split('_')[1]
        details = get_package_details(package)
        keyboard = [
            [InlineKeyboardButton('🗓️ לקבוע שיחה', callback_data=f'schedule_{package}')],
            [InlineKeyboardButton('🛒 לבקש הצעת מחיר', callback_data=f'quote_{package}')],
            [InlineKeyboardButton('⬅️ חזרה לקטלוג', callback_data='back_catalog')]
        ]
        await query.edit_message_text(
            details,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('interest_'):
        package = data.split('_')[1]
        context.user_data['interest_package'] = package
        context.user_data['contact_step'] = 'name'
        await query.edit_message_text(
            f'מעולה! אתם מתעניינים ב{get_package_name(package)} 👍\nבואו נתחיל - מה השם הפרטי?'
        )
    
    # התחלת קביעת שיחה מתוך פרטי חבילה
    elif data.startswith('schedule_'):
        today = datetime.now()
        dates = []
        for i in range(1, 6):  # 5 הימים הקרובים
            date = today + timedelta(days=i)
            dates.append(InlineKeyboardButton(
                date.strftime('%d/%m (%a)'),
                callback_data=f'date_{date.strftime("%Y-%m-%d")}'
            ))
        keyboard = [dates[i:i+2] for i in range(0, len(dates), 2)]
        keyboard.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')])
        await query.edit_message_text(
            'בואו נקבע – זה לוקח חצי דקה 🙂\nבחרו יום פנוי:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # בקשת הצעת מחיר: פתיחת טופס יצירת קשר וקיבוע עניין לפי חבילה
    elif data.startswith('quote_'):
        package = data.split('_')[1]
        context.user_data['interest'] = get_package_name(package)
        context.user_data['contact_step'] = 'name'
        await query.edit_message_text('נשמח לחזור אליך 👇\nאיך לפנות אליך – מה השם הפרטי?')
    
    # חזרה לקטלוג מתוך פרטי חבילה
    elif data == 'back_catalog':
        await query.edit_message_text(
            get_catalog_text(),
            parse_mode='Markdown',
            reply_markup=catalog_keyboard()
        )
    
    elif data.startswith('date_'):
        selected_date = data.split('_')[1]
        context.user_data['selected_date'] = selected_date
        
        # שעות זמינות לפי מסעדה
        times = ['12:00', '12:30', '13:00', '18:00', '19:30', '21:00']
        keyboard = []
        for i in range(0, len(times), 3):
            row = [InlineKeyboardButton(time, callback_data=f'time_{time}') for time in times[i:i+3]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton('⬅️ חזרה לתאריכים', callback_data='back_dates')])
        
        await query.edit_message_text(
            f'נבחר תאריך: {selected_date}\nבחרו שעה:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # חזרה למסך בחירת תאריכים
    elif data == 'back_dates':
        today = datetime.now()
        dates = []
        for i in range(1, 6):
            date = today + timedelta(days=i)
            dates.append(InlineKeyboardButton(
                date.strftime('%d/%m (%a)'),
                callback_data=f'date_{date.strftime("%Y-%m-%d")}'
            ))
        keyboard = [dates[i:i+2] for i in range(0, len(dates), 2)]
        keyboard.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')])
        await query.edit_message_text(
            'בואו נקבע – זה לוקח חצי דקה 🙂\nבחרו יום פנוי:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('time_'):
        selected_time = data.split('_')[1]
        context.user_data['selected_time'] = selected_time
        context.user_data['appointment_step'] = 'name'
        
        await query.edit_message_text(
            f'מעולה! 📅 {context.user_data["selected_date"]} בשעה {selected_time}\n\nשם מלא להזמנה:'
        )
    
    elif data.startswith('faq_'):
        faq_type = data.split('_')[1]
        answer = get_faq_answer(faq_type)
        keyboard = [[InlineKeyboardButton('⬅️ חזרה לשאלות', callback_data='back_faq')]]
        await query.edit_message_text(
            answer,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # חזרה לרשימת שאלות נפוצות
    elif data == 'back_faq':
        await query.edit_message_text(
            'שאלות נפוצות – לחצו לקבלת מענה מיידי:',
            reply_markup=faq_keyboard()
        )
    
    elif data == 'human_support':
        await query.edit_message_text(
            'השאר/י הודעה קצרה – ונחזור אליך כאן בהקדם 💬'
        )
        context.user_data['human_support'] = True
    
    # אדמין: אישור/דחיית תור
    elif data.startswith('approve_appt_') or data.startswith('reject_appt_'):
        if update.effective_user.id != dm.data['settings']['admin_id']:
            await query.answer('אין הרשאה', show_alert=True)
            return
        try:
            appt_id = int(data.split('_')[-1])
            for a in dm.data['appointments']:
                if a.get('id') == appt_id:
                    if data.startswith('approve_appt_'):
                        a['status'] = 'אושר'
                    else:
                        a['status'] = 'נדחה'
                    dm.save_data()
                    # עדכון הלקוח אם אפשר
                    user_id = a.get('user_id')
                    if user_id:
                        try:
                            status_text = 'אושר' if a['status'] == 'אושר' else 'נדחה'
                            await context.bot.send_message(user_id, f"עדכון תור #{appt_id}: {status_text}\n📅 {a.get('date','')} ⏰ {a.get('time','')}")
                        except:
                            pass
                    await query.edit_message_text(f"עודכן סטטוס לתור #{appt_id}: {a['status']}")
                    return
            await query.answer('תור לא נמצא', show_alert=True)
        except Exception as e:
            await query.answer('שגיאה בטיפול', show_alert=True)
    
    # === Restaurant cart actions ===
    elif data.startswith('add_'):
        item_id = data.split('_')[1]
        cart = context.user_data.setdefault('cart', {})
        cart[item_id] = cart.get(item_id, 0) + 1
        await query.answer(text='נוסף לעגלה ✅', show_alert=False)
    
    elif data.startswith('remove_'):
        item_id = data.split('_')[1]
        cart = context.user_data.get('cart', {})
        if item_id in cart:
            cart[item_id] -= 1
            if cart[item_id] <= 0:
                del cart[item_id]
        await query.answer(text='עודכן בעגלה ✅', show_alert=False)
        await query.message.delete()
    
    elif data == 'cart_review':
        # show cart summary
        items_map = {i['id']: i for i in dm.data.get('menu', [])}
        cart = context.user_data.get('cart', {})
        if not cart:
            await query.edit_message_text('העגלה ריקה. אפשר להוסיף מנות מהתפריט 🙂')
        else:
            total = 0
            lines = ['🧺 העגלה שלי:\n']
            kb = []
            for item_id, qty in cart.items():
                item = items_map.get(int(item_id))
                if not item:
                    continue
                line_total = item['price'] * qty
                total += line_total
                lines.append(f"{item['name']} x{qty} — {line_total}₪")
                kb.append([InlineKeyboardButton(f"➖ הסר {item['name']}", callback_data=f"remove_{item_id}")])
            lines.append('')
            lines.append(f"סה""כ: {total}₪")
            kb.append([InlineKeyboardButton('✅ בצע הזמנה', callback_data='order_confirm')])
            kb.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='back_menu')])
            await query.edit_message_text('\n'.join(lines), reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == 'order_confirm':
        items_map = {i['id']: i for i in dm.data.get('menu', [])}
        cart = context.user_data.get('cart', {})
        if not cart:
            await query.answer('העגלה ריקה')
        else:
            # build items list
            items = []
            for item_id, qty in cart.items():
                item = items_map.get(int(item_id))
                if not item:
                    continue
                items.append({'id': item['id'], 'name': item['name'], 'price': item['price'], 'qty': qty})
            order = dm.add_order(update.effective_user.id, items)
            context.user_data['cart'] = {}
            # notify admin
            if dm.data['settings']['admin_id']:
                try:
                    details = '\n'.join([f"• {it['name']} x{it['qty']} — {it['price']*it['qty']}₪" for it in order['items']])
                    await context.bot.send_message(
                        dm.data['settings']['admin_id'],
                        f"🍽️ הזמנה חדשה #{order['id']}\n{details}\nסה""כ: {order['total']}₪"
                    )
                except:
                    pass
            await query.edit_message_text(f"תודה! ההזמנה התקבלה ✅\nמספר הזמנה: {order['id']}\nסה""כ: {order['total']}₪")
    
    elif data == 'back_menu':
        await query.message.delete()
        await query.message.chat.send_message('תפריט:', reply_markup=None)
 
    elif data.startswith('int_'):
        # Handle interest area selection
        interest_type = data.split('_')[1]
        interest_names = {
            'website': 'אתר אינטרנט',
            'bot': 'בוט/אוטומציה',
            'marketing': 'שיווק דיגיטלי',
            'other': 'אחר'
        }
        
        # Save the interest area
        context.user_data['interest'] = interest_names.get(interest_type, 'אחר')
        context.user_data['contact_step'] = 'phone'
        
        await query.edit_message_text(
            'תודה! ולבסוף - מספר טלפון:'
        )

# פונקציות עזר
def get_package_name(package):
    names = {
        'basic': 'חבילת הבסיס',
        'plus': 'חבילת הפלוס', 
        'pro': 'חבילת הפרו'
    }
    return names.get(package, 'החבילה')

def get_package_details(package):
    details = {
        'basic': """**חבילת בסיס - פרטים מלאים**

✅ הקמת מערכת בסיסית ויעילה
✅ הדרכה והטמעה מלאה
✅ תמיכה טכנית לשלושה חודשים
✅ עדכונים ותחזוקה שוטפת
✅ גיבוי אוטומטי של כל הנתונים

💰 **149 ₪ לחודש**""",
        
        'plus': """**חבילת פלוס - פרטים מלאים**

✅ כל מה שכלול בחבילת הבסיס
✅ התאמות אישיות לפי הצרכים
✅ דוחות ניתוח מתקדמים
✅ אינטגרציה עם מערכות קיימות
✅ תמיכה מורחבת 24/6

💰 **349 ₪ לחודש**""",
        
        'pro': """**חבילת פרו - פרטים מלאים**

✅ כל מה שכלול בחבילות הקודמות
✅ פתרון מותאם 100% לעסק
✅ תמיכה VIP 24/7
✅ יועץ אישי ייעודי
✅ עדכונים והתאמות ללא הגבלה

💰 **749 ₪ לחודש**"""
    }
    return details.get(package, 'פרטים לא זמינים')

def get_faq_answer(faq_type):
    answers = {
        'hours': f"""**⏰ שעות הפעילות שלנו:**

{dm.data['settings']['working_hours']}

בזמנים אחרים אפשר להשאיר הודעה ונחזור בהקדם!""",
        
        'delivery': """**🚚 משלוחים ושירות מרחוק:**

• שירות מרחוק זמין לכל הארץ
• התקנה והדרכה מקוונת
• תמיכה טכנית דרך טלפון/צ'אט
• ביקור במקום (אזור המרכז) - בתיאום מראש""",
        
        'payment': """**💳 תשלום וקבלות:**

• העברה בנקאית / אשראי
• תשלום חודשי או שנתי
• חשבונית + קבלה לכל תשלום
• הנחה לתשלום שנתי מראש""",
        
        'invoice': """**🧾 חשבונית:**

• חשבונית מס מלאה לכל עסקה
• נשלחת אוטומטית למייל
• אפשרות להדפסה/הורדה
• שמירה במערכת לשנים"""
    }
    return answers.get(faq_type, 'מידע לא זמין')

def get_catalog_text() -> str:
    return """הנה טעימה מהשירותים/מוצרים הפופולריים שלנו:

📦 **חבילת בסיס** - "מתאים להתחלה מהירה"
• פתרון בסיסי ויעיל לכל עסק
• כולל הכל הדרוש להתחלה
• תמיכה מלאה ושירות לקוחות
💰 **149 ₪**

📦 **חבילת פלוס** - "כולל תוספות חשובות"
• כל מה שיש בחבילת הבסיס
• תוספות מתקדמות ומותאמות אישית
• דוחות וניתוח מתקדם
💰 **349 ₪**

📦 **חבילת פרו** - "למי שרוצה מקסימום"
• הפתרון הכי מתקדם שיש לנו
• תמיכה 24/7 ושירות VIP
• התאמות מלאות לפי דרישה
💰 **749 ₪**"""

# טיפול בהודעות בתהליך איסוף מידע
async def handle_contact_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    user_data = context.user_data
    text = update.message.text
    
    # תהליך צור קשר רגיל
    if 'contact_step' in user_data:
        if user_data['contact_step'] == 'name':
            user_data['name'] = text
            user_data['contact_step'] = 'business'
            await update.message.reply_text('תודה! שם העסק (אופציונלי - אפשר לכתוב "אין"):')
        
        elif user_data['contact_step'] == 'business':
            user_data['business'] = text if text != 'אין' else ''
            user_data['contact_step'] = 'interest'
            
            keyboard = [
                [InlineKeyboardButton('🌐 אתר אינטרנט', callback_data='int_website')],
                [InlineKeyboardButton('🤖 בוט/אוטומציה', callback_data='int_bot')],
                [InlineKeyboardButton('📈 שיווק דיגיטלי', callback_data='int_marketing')],
                [InlineKeyboardButton('🔧 אחר', callback_data='int_other')]
            ]
            await update.message.reply_text(
                'תחום העניין:',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif user_data['contact_step'] == 'phone':
            # ולידציה בסיסית לטלפון ישראלי
            phone = text.strip()
            if not re.match(r'^(\+?972|0)?5\d(-?\d){7}$', phone):
                share_kb = ReplyKeyboardMarkup(
                    [[KeyboardButton('שתף מספר מהטלפון 📱', request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                await update.message.reply_text('מספר טלפון לא תקין. אפשר להקליד שוב או לשתף בלחיצה:', reply_markup=share_kb)
                return
            # שמירת הליד
            lead = dm.add_lead(
                user_id=update.effective_user.id,
                name=user_data['name'],
                phone=phone,
                business_name=user_data.get('business', ''),
                interest=user_data.get('interest', ''),
                source='דמו טלגרם'
            )
            
            # הודעה למנהל
            if dm.data['settings']['admin_id']:
                try:
                    await context.bot.send_message(
                        dm.data['settings']['admin_id'],
                        f"🔔 ליד חדש!\n\n👤 {lead['name']}\n📞 {phone}\n🏢 {lead['business_name']}\n🎯 {lead['interest']}\n📅 {lead['date']}"
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f"תודה! קיבלנו את הפרטים ✅\nמספר בקשה: {lead['id']}",
                reply_markup=main_menu_keyboard()
            )
            
            # ניקוי נתוני המשתמש
            context.user_data.clear()
    
    # תהליך קביעת תור
    elif 'appointment_step' in user_data:
        if user_data['appointment_step'] == 'name':
            user_data['appointment_name'] = text
            user_data['appointment_step'] = 'phone'
            await update.message.reply_text('ומספר טלפון:')
        
        elif user_data['appointment_step'] == 'phone':
            phone = text.strip()
            if not re.match(r'^(\+?972|0)?5\d(-?\d){7}$', phone):
                await update.message.reply_text('מספר טלפון לא תקין. נסו שוב:')
                return
            # שמירת התור
            appointment = dm.add_appointment(
                user_id=update.effective_user.id,
                name=user_data['appointment_name'],
                phone=phone,
                date=user_data['selected_date'],
                time=user_data['selected_time']
            )
            
            # הודעה למנהל עם כפתורי אישור/דחייה
            if dm.data['settings']['admin_id']:
                try:
                    approve_cb = f"approve_appt_{appointment['id']}"
                    reject_cb = f"reject_appt_{appointment['id']}"
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton('אשר ✅', callback_data=approve_cb), InlineKeyboardButton('דחה ❌', callback_data=reject_cb)]])
                    await context.bot.send_message(
                        dm.data['settings']['admin_id'],
                        f"📅 בקשת תור חדשה!\n\n👤 {appointment['name']}\n📞 {phone}\n📅 {appointment['date']}\n⏰ {appointment['time']}\n🔢 מזהה: {appointment['id']}",
                        reply_markup=kb
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f'הבקשה נקלטה ✅\n📅 {user_data["selected_date"]} בשעה {user_data["selected_time"]}\nנעדכן כאן כשמאושר.',
                reply_markup=main_menu_keyboard()
            )
            
            context.user_data.clear()
    
    # תמיכה אנושית
    elif user_data.get('human_support'):
        # שליחת ההודעה למנהל
        if dm.data['settings']['admin_id']:
            try:
                await context.bot.send_message(
                    dm.data['settings']['admin_id'],
                    f"💬 פנייה לתמיכה:\n\n👤 {update.effective_user.first_name}\n📝 {text}"
                )
            except:
                pass
        
        await update.message.reply_text(
            'תודה! הפנייה התקבלה ✅\nנחזור אליך בהקדם.',
            reply_markup=main_menu_keyboard()
        )
        context.user_data.clear()

# פקודות מנהל
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    user_id = update.effective_user.id
    
    if user_id != dm.data['settings']['admin_id']:
        await update.message.reply_text('❌ אין הרשאה')
        return
    
    # סטטיסטיקות
    leads_count = len(dm.data['leads'])
    appointments_count = len(dm.data['appointments'])
    
    # לידים אחרונים
    recent_leads = dm.data['leads'][-5:] if leads_count > 0 else []
    leads_text = '\n'.join([f"• {lead['name']} - {lead['phone']}" for lead in recent_leads])
    
    admin_text = f"""📊 **פאנל מנהל**

📈 **סטטיסטיקות:**
• לידים: {leads_count}
• תורים: {appointments_count}

📝 **לידים אחרונים:**
{leads_text if leads_text else 'אין לידים עדיין'}

🔧 **פקודות זמינות:**
/export_leads - ייצוא לידים
/export_appointments - ייצוא תורים
/settings - הגדרות"""

    await update.message.reply_text(admin_text, parse_mode='Markdown')

# ייצוא נתונים
async def export_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    if update.effective_user.id != dm.data['settings']['admin_id']:
        return
    
    if not dm.data['leads']:
        await update.message.reply_text('אין לידים לייצוא')
        return
    
    # יצירת CSV פשוט
    csv_content = "תאריך,שם,טלפון,עסק,עניין,מקור\n"
    for lead in dm.data['leads']:
        csv_content += f"{lead['date']},{lead['name']},{lead['phone']},{lead.get('business_name', '')},{lead.get('interest', '')},{lead['source']}\n"
    
    # שמירה ושליחה
    with open('leads_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    await update.message.reply_document(
        document=open('leads_export.csv', 'rb'),
        filename=f'leads_{datetime.now().strftime("%Y%m%d")}.csv',
        caption=f'📊 ייצוא לידים ({len(dm.data["leads"])} רשומות)'
    )

async def export_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    if update.effective_user.id != dm.data['settings']['admin_id']:
        return
    
    if not dm.data['appointments']:
        await update.message.reply_text('אין תורים לייצוא')
        return
    
    csv_content = "מזהה,תאריך,שעה,שם,טלפון,שירות,סטטוס\n"
    for a in dm.data['appointments']:
        csv_content += f"{a.get('id','')},{a.get('date','')},{a.get('time','')},{a.get('name','')},{a.get('phone','')},{a.get('service','')},{a.get('status','')}\n"
    
    with open('appointments_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    await update.message.reply_document(
        document=open('appointments_export.csv', 'rb'),
        filename=f'appointments_{datetime.now().strftime("%Y%m%d")}.csv',
        caption=f'📅 ייצוא תורים ({len(dm.data["appointments"])} רשומות)'
    )

# חדש: היסטוריית משתמש (ההזמנות שלי)
async def show_user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporter.report_activity(update.effective_user.id)
    user_id = update.effective_user.id
    text = get_user_history(user_id)
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')]])
    )

# סטטוס זמינות: פתוח/סגור כעת

def _parse_working_hours_to_map(hours_str: str):
    day_map = {'א': 6, 'ב': 0, 'ג': 1, 'ד': 2, 'ה': 3, 'ו': 4, 'ש': 5}
    day_order = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ש']

    def clean_day_token(tok: str) -> str:
        return tok.replace('׳', '').replace('״', '').strip()

    def time_to_minutes(t: str) -> int:
        h, m = t.split(':')
        return int(h) * 60 + int(m)

    schedule = {i: [] for i in range(7)}

    segments = re.split(r'[;\n]+', hours_str)
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        m_range = re.match(r'^([אבגדהוש][׳״]?)\s*-\s*([אבגדהוש][׳״]?)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$', seg)
        m_single = re.match(r'^([אבגדהוש][׳״]?)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$', seg)
        m_closed = re.match(r'^([אבגדהוש][׳״]?)\s+סגור$', seg)

        if m_range:
            d1 = clean_day_token(m_range.group(1))
            d2 = clean_day_token(m_range.group(2))
            t1 = m_range.group(3)
            t2 = m_range.group(4)
            if d1 in day_map and d2 in day_map:
                start_idx = day_order.index(d1)
                end_idx = day_order.index(d2)
                if start_idx <= end_idx:
                    days = day_order[start_idx:end_idx + 1]
                else:
                    days = day_order[start_idx:] + day_order[:end_idx + 1]
                for d in days:
                    schedule[day_map[d]].append((time_to_minutes(t1), time_to_minutes(t2)))
        elif m_single:
            d = clean_day_token(m_single.group(1))
            t1 = m_single.group(2)
            t2 = m_single.group(3)
            if d in day_map:
                schedule[day_map[d]].append((time_to_minutes(t1), time_to_minutes(t2)))
        elif m_closed:
            d = clean_day_token(m_closed.group(1))
            if d in day_map:
                schedule[day_map[d]] = []
        else:
            continue

    return schedule


def is_business_open() -> bool:
    try:
        hours_str = dm.data['settings'].get('working_hours', 'א׳-ה׳ 09:00-18:00')
        schedule = _parse_working_hours_to_map(hours_str)
        now = datetime.now(ZoneInfo('Asia/Jerusalem'))
        now_minutes = now.hour * 60 + now.minute
        intervals = schedule.get(now.weekday())
        if intervals is None:
            return False
        for start_min, end_min in intervals:
            if start_min <= now_minutes < end_min:
                return True
        return False
    except Exception:
        now = datetime.now(ZoneInfo('Asia/Jerusalem'))
        is_weekday_open = now.weekday() in {6, 0, 1, 2, 3}
        return 9 * 60 <= (now.hour * 60 + now.minute) < 18 * 60

# היסטוריית משתמש: לידים ותורים

def get_user_history(user_id: int) -> str:
    leads = [lead for lead in dm.data.get('leads', []) if lead.get('user_id') == user_id]
    appointments = [a for a in dm.data.get('appointments', []) if a.get('user_id') == user_id]

    if not leads and not appointments:
        return '📋 ההזמנות שלי:\n\nעדיין לא יצרת בקשות'

    def parse_dt(dt_str: str) -> datetime:
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            try:
                return datetime.fromisoformat(dt_str)
            except Exception:
                return datetime.now()

    entries = []
    # המרות לרשומות אחודות עם מפתח זמן יצירה
    for a in appointments:
        created = parse_dt(a.get('created', f"{a.get('date','1970-01-01')} 00:00:00"))
        entries.append(('appointment', a, created))
    for l in leads:
        created = parse_dt(l.get('date', '1970-01-01 00:00:00'))
        entries.append(('lead', l, created))

    # מיון מהחדש לישן
    entries.sort(key=lambda x: x[2], reverse=True)

    # הצגה של עד 5 רשומות
    show_entries = entries[:5]
    truncated = len(entries) > 5

    lines = ['📋 ההזמנות שלי:\n']

    for kind, obj, created in show_entries:
        created_str = created.strftime('%d/%m/%Y')
        if kind == 'appointment':
            status = obj.get('status', 'ממתין לאישור')
            icon_map = {
                'ממתין לאישור': '🟡',
                'אושר': '🟢',
                'הושלם': '✅'
            }
            icon = icon_map.get(status, '📅')
            label = 'בקשה' if status == 'ממתין לאישור' else 'תור'
            date_display = obj.get('date', '')
            time_display = obj.get('time', '')
            phone = obj.get('phone', '-')
            lines.append(f"{icon} {label} #{obj.get('id','')} - {status}")
            if date_display and time_display:
                try:
                    dt_disp = datetime.strptime(f"{date_display} {time_display}", '%Y-%m-%d %H:%M')
                    lines.append(f"📅 {dt_disp.strftime('%d/%m/%Y')} בשעה {dt_disp.strftime('%H:%M')}")
                except Exception:
                    lines.append(f"📅 {date_display} בשעה {time_display}")
            elif date_display:
                lines.append(f"📅 {date_display}")
            if phone:
                lines.append(f"📞 {phone}")
            lines.append(f"⏰ נוצר: {created_str}")
        else:  # lead
            phone = obj.get('phone', '-')
            interest = obj.get('interest', '')
            lines.append(f"🔵 ליד #{obj.get('id','')} - בטיפול")
            if interest:
                lines.append(f"💼 {interest}")
            if phone:
                lines.append(f"📞 {phone}")
            lines.append(f"⏰ נוצר: {created_str}")
        lines.append('')  # רווח בין רשומות

    if truncated:
        lines.append('מציג 5 רשומות אחרונות')

    return '\n'.join(lines).strip()

# הפעלת הבוט
async def main():
    """Initialize and run the bot"""
    # בניית האפליקציה עם הגדרות מתאימות ל-Python 3.13
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .get_updates_read_timeout(10.0)
        .build()
    )

    # Ensure webhook is removed before starting polling
    await app.bot.delete_webhook(drop_pending_updates=True)

    # רישום handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', admin_command))
    app.add_handler(CommandHandler('export_leads', export_leads))
    app.add_handler(CommandHandler('export_appointments', export_appointments))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_contact_process(u, c) if any(key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']) else handle_text(u, c)))
    
    # הפעלה עם polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # המתנה עד לסיום
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
