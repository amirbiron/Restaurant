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
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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

# מחלקה לניהול נתונים
class DataManager:
    def __init__(self):
        self.data = self.load_data()
    
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
    
    def add_lead(self, user_id, name, phone, business_name='', interest='', source='דמו טלגרם'):
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

# יצירת מנהל נתונים גלובלי
dm = DataManager()

# פונקציות עזר לתפריטים
def main_menu_keyboard():
    keyboard = [
        [KeyboardButton('🛍️ קטלוג קצר'), KeyboardButton('📆 קביעת תור/הזמנה')],
        [KeyboardButton('❓ שאלות ותמיכה'), KeyboardButton('📞 צור קשר')]
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
    user = update.effective_user
    
    # שמירת מנהל ראשון כאדמין
    if dm.data['settings']['admin_id'] is None:
        dm.data['settings']['admin_id'] = user.id
        dm.save_data()
        await update.message.reply_text('🎉 הוגדרת כמנהל הבוט!')
    
    await update.message.reply_text(
        dm.data['settings']['welcome_message'],
        reply_markup=main_menu_keyboard()
    )

# טיפול בהודעות טקסט (תפריט ראשי)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '🛍️ קטלוג קצר':
        await show_catalog(update, context)
    elif text == '📆 קביעת תור/הזמנה':
        await show_appointment_booking(update, context)
    elif text == '❓ שאלות ותמיכה':
        await show_faq(update, context)
    elif text == '📞 צור קשר':
        await show_contact_form(update, context)
    else:
        await update.message.reply_text(
            'אנא בחר/י אחת מהאפשרויות בתפריט 👇',
            reply_markup=main_menu_keyboard()
        )

# קטלוג
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    catalog_text = """הנה טעימה מהשירותים/מוצרים הפופולריים שלנו:

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

    await update.message.reply_text(
        catalog_text,
        parse_mode='Markdown',
        reply_markup=catalog_keyboard()
    )

# קביעת תור
async def show_appointment_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # תאריכים זמינים לדוגמה
    today = datetime.now()
    dates = []
    for i in range(1, 6):  # 5 ימים הבאים
        date = today + timedelta(days=i)
        dates.append(InlineKeyboardButton(
            date.strftime('%d/%m (%a)'), 
            callback_data=f'date_{date.strftime("%Y-%m-%d")}'
        ))
    
    keyboard = [dates[i:i+2] for i in range(0, len(dates), 2)]  # שורות של 2
    keyboard.append([InlineKeyboardButton('⬅️ חזרה לתפריט', callback_data='main_menu')])
    
    await update.message.reply_text(
        'בואו נקבע – זה לוקח חצי דקה 🙂\nבחרו יום פנוי:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# שאלות ותמיכה
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'שאלות נפוצות – לחצו לקבלת מענה מיידי:',
        reply_markup=faq_keyboard()
    )

# צור קשר
async def show_contact_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['contact_step'] = 'name'
    await update.message.reply_text(
        'נשמח לחזור אליך 👇\nאנא שתף/י את השם הפרטי:'
    )

# טיפול בלחיצות על כפתורים
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    elif data.startswith('date_'):
        selected_date = data.split('_')[1]
        context.user_data['selected_date'] = selected_date
        
        # שעות זמינות
        times = ['09:00', '11:00', '13:00', '15:00', '17:00', '19:00']
        keyboard = []
        for i in range(0, len(times), 3):
            row = [InlineKeyboardButton(time, callback_data=f'time_{time}') for time in times[i:i+3]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton('⬅️ חזרה לתאריכים', callback_data='back_dates')])
        
        await query.edit_message_text(
            f'נבחר תאריך: {selected_date}\nשעה מועדפת?',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('time_'):
        selected_time = data.split('_')[1]
        context.user_data['selected_time'] = selected_time
        context.user_data['appointment_step'] = 'name'
        
        await query.edit_message_text(
            f'מעולה! 📅 {context.user_data["selected_date"]} בשעה {selected_time}\n\nכדי לאשר, אנא שתף/י שם מלא:'
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
    
    elif data == 'human_support':
        await query.edit_message_text(
            'השאר/י הודעה קצרה – ונחזור אליך כאן בהקדם 💬'
        )
        context.user_data['human_support'] = True

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

# טיפול בהודעות בתהליך איסוף מידע
async def handle_contact_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            # שמירת הליד
            lead = dm.add_lead(
                user_id=update.effective_user.id,
                name=user_data['name'],
                phone=text,
                business_name=user_data.get('business', ''),
                interest=user_data.get('interest', ''),
                source='דמו טלגרם'
            )
            
            # הודעה למנהל
            if dm.data['settings']['admin_id']:
                try:
                    await context.bot.send_message(
                        dm.data['settings']['admin_id'],
                        f"🔔 ליד חדש!\n\n👤 {lead['name']}\n📞 {text}\n🏢 {lead['business_name']}\n🎯 {lead['interest']}\n📅 {lead['date']}"
                    )
                except:
                    pass
            
            await update.message.reply_text(
                'תודה! קיבלנו את הפרטים ✅\nמנהל יחזור אליך בהקדם.',
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
            # שמירת התור
            appointment = dm.add_appointment(
                user_id=update.effective_user.id,
                name=user_data['appointment_name'],
                phone=text,
                date=user_data['selected_date'],
                time=user_data['selected_time']
            )
            
            # הודעה למנהל
            if dm.data['settings']['admin_id']:
                try:
                    await context.bot.send_message(
                        dm.data['settings']['admin_id'],
                        f"📅 בקשת תור חדשה!\n\n👤 {appointment['name']}\n📞 {text}\n📅 {appointment['date']}\n⏰ {appointment['time']}\n🔢 מזהה: {appointment['id']}"
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f'תודה! הזמנה נקלטה ✅\n📅 {user_data["selected_date"]} בשעה {user_data["selected_time"]}\n\nתקבלו אישור כאן בצ\'אט.',
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

# הפעלת הבוט
async def main():
    """Initialize and run the bot"""
    # בניית האפליקציה עם הגדרות מתאימות ל-Python 3.13
    app = Application.builder().token(BOT_TOKEN).build()
    
    # רישום handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', admin_command))
    app.add_handler(CommandHandler('export_leads', export_leads))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_contact_process(u, c) if any(key in c.user_data for key in ['contact_step', 'appointment_step', 'human_support']) else handle_text(u, c)))
    
    # הפעלה עם polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
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
