# 🍽️ בוט טלגרם מתקדם למסעדה

> בוט טלגרם מקצועי לניהול הזמנות מסעדה עם מערכת עגלת קניות, תשלומים וניהול משתמשים

[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Telegraf](https://img.shields.io/badge/Telegraf-4.16.3-blue.svg)](https://telegraf.js.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Deploy](https://img.shields.io/badge/Deploy-Render-purple.svg)](https://render.com/)

## ✨ תכונות עיקריות

- 🤖 **בוט אינטראקטיבי** - תפריט עם כפתורים וניווט קל
- 🛒 **עגלת קניות חכמה** - הוספה, הסרה וניהול פריטים
- 📋 **מערכת הזמנות מלאה** - מעקב אחר סטטוס והיסטוריה
- 👥 **ניהול משתמשים** - פרופילים אישיים וסטטיסטיקות
- 🗄️ **בסיס נתונים MongoDB** - אחסון מאובטח ויעיל
- 🌐 **Webhook Ready** - מוכן לפריסה ברנדר עם HTTPS
- 📱 **ממשק מותאם לטלפון** - חוויית משתמש מושלמת
- 🔒 **אבטחה מתקדמת** - הגנה מפני התקפות וספאם

## 🚀 התחלה מהירה

### 1. הכנת הסביבה

```bash
# שכפול הפרויקט
git clone <repository-url>
cd restaurant-telegram-bot

# התקנת תלויות
npm install

# העתקת קובץ משתני הסביבה
cp .env.example .env
```

### 2. יצירת בוט טלגרם

1. פתח טלגרם וחפש את **@BotFather**
2. שלח `/newbot` ובחר שם לבוט
3. שמור את הטוקן שתקבל
4. הכנס את הטוקן ב-`.env` בשדה `BOT_TOKEN`

### 3. הגדרת MongoDB Atlas (חינמי!)

1. היכנס ל-[MongoDB Atlas](https://www.mongodb.com/atlas)
2. צור חשבון וקלאסטר חינמי
3. בחר **Connect Your Application**
4. העתק את connection string ל-`.env`

### 4. הרצה מקומית

```bash
# מצב פיתוח עם auto-reload
npm run dev

# או הרצה רגילה
npm start
```

## 🌐 פריסה ברנדר (Render)

### שלב 1: הכנת הפרויקט

1. העלה את הקוד ל-GitHub
2. ודא שקובץ `.env` **לא** מועלה (הוסף ל-`.gitignore`)

### שלב 2: יצירת שירות ברנדר

1. היכנס ל-[Render.com](https://render.com)
2. צור חשבון והתחבר ל-GitHub
3. לחץ **New → Web Service**
4. בחר את הריפו שלך

### שלב 3: הגדרות השירות

```yaml
Name: restaurant-bot-demo
Environment: Node
Region: Frankfurt (או קרוב אליך)
Branch: main
Build Command: npm install
Start Command: npm start
```

### שלב 4: משתני סביבה ברנדר

הוסף את המשתנים הבאים ב-**Environment Variables**:

```bash
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=YourRestaurantBot
NODE_ENV=production
MONGODB_URI=mongodb+srv://...
WEBHOOK_URL=https://your-app-name.onrender.com
RESTAURANT_NAME=מסעדת הדוגמה
RESTAURANT_PHONE=03-1234567
DELIVERY_FEE=15
```

### שלב 5: הפעלת Webhook

לאחר הפריסה, הבוט יגדיר אוטומטית את ה-webhook ויעבור למצב פרודקשן.

## 📖 שימוש בבוט

### פקודות בסיסיות

- `/start` - התחלת הבוט וחזרה לתפריט הראשי
- `/help` - רשימת פקודות ועזרה
- `/menu` - פתיחת התפריט ישירות
- `/cart` - הצגת עגלת הקניות
- `/orders` - הצגת ההזמנות שלי

### תהליך הזמנה

1. **התחלה** - לחץ על "תפריט" 
2. **בחירת קטגוריה** - מנות פתיחה, עיקריות או משקאות
3. **הוספה לעגלה** - לחץ על ➕ ליד כל פריט
4. **סקירת עגלה** - בדוק את הפריטים והמחיר
5. **הזמנה** - הכנס כתובת וטלפון
6. **אישור** - קבל מספר הזמנה וזמן אספקה

## 🛠️ התאמה אישית

### עריכת התפריט

ערוך את האובייקט `menuData` בקובץ `server.js`:

```javascript
const menuData = {
    starters: [
        { name: 'המנה שלך', price: 25, emoji: '🍽️' }
    ],
    // הוסף עוד קטגוריות...
};
```

### שינוי עיצוב ההודעות

כל ההודעות נמצאות בתחילת הקבצים ונתונות לעריכה קלה.

### הוספת תכונות

הפרויקט בנוי במודולריות ומאפשר הוספה קלה של:
- אמצעי תשלום נוספים
- מערכת קופונים והנחות
- התרעות למטבח
- דירוגים וביקורות

## 📊 ניטור ותחזוקה

### לוגים ופיתוח תקלות

```bash
# צפייה בלוגים ברנדר
# היכנס לדאשבורד → בחר השירות → Logs

# לוגים מקומיים
tail -f logs/bot.log
```

### מדדי ביצועים

הבוט כולל מדדים בסיסיים:
- מספר משתמשים פעילים
- מספר הזמנות יומי
- זמני תגובה
- שגיאות ותקלות

## 🔒 אבטחה

### נקודות חשובות

- ✅ טוקן הבוט מוגן במשתני סביבה
- ✅ חיבור מאובטח ל-MongoDB
- ✅ HTTPS מאולץ (ברנדר)
- ✅ הגנה מפני DDOS (ברנדר)
- ✅ ולידציה של נתוני קלט

### המלצות נוספות

- שנה את טוקן הבוט באופן תקופתי
- הגבל גישה למסד הנתונים לכתובות IP ידועות
- עקוב אחר תנועה חשודה בלוגים

## 💰 עלויות

### שירותים חינמיים

- **Render**: 750 שעות חינם/חודש (מספיק לבוט אחד)
- **MongoDB Atlas**: 512MB חינם לעד
- **Telegram**: חינמי לחלוטין

### שדרוגים אפשריים

- **Render Pro** ($7/חודש): Always-on, custom domains
- **MongoDB**: $9/חודש למסד נתונים מתקדם
- **CDN**: להגשת תמונות מהר יותר

## 🐛 פתרון בעיות נפוצות

### הבוט לא עונה

1. בדוק שהטוקן נכון ב-`.env`
2. ודא שה-webhook מוגדר נכון
3. בדוק את הלוגים ברנדר

### שגיאות בסיס נתונים

1. ודא שה-connection string נכון
2. בדוק שהרשת מורשית ב-MongoDB Atlas
3. נסה להתחבר דרך MongoDB Compass

### בעיות Webhook

1. ודא ש-WEBHOOK_URL מכיל HTTPS
2. בדוק שהשירות ברנדר רץ
3. נסה לאפס את ה-webhook: `/deleteWebhook`

## 🤝 תמיכה ופיתוח

### קבלת עזרה

- 📧 **אימייל**: support@yourbotservices.com
- 💬 **טלגרם**: @YourBotSupport
- 🐛 **באגים**: פתח Issue ב-GitHub

### רוצה לפתח בוט משלך?

הבוט הזה הוא דוגמה למה שאפשר לבנות! 

**צור קשר לקבלת הצעת מחיר אישית לבוט טלגרם מותאם אישית** 🚀

---

**נבנה עם ❤️ בישראל | Ready for 2025**
