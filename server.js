// 🍽️ בוט טלגרם מתקדם למסעדה - 2025
// בנוי עם Telegraf 4.16.3, Express, MongoDB
// מוכן לפריסה ב-Render עם Webhook

require('dotenv').config();
const express = require('express');
const { Telegraf, Markup } = require('telegraf');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');

// =================================
// 🔧 הגדרות בסיסיות
// =================================

const app = express();
const bot = new Telegraf(process.env.BOT_TOKEN);

const PORT = process.env.PORT || 3000;
const WEBHOOK_URL = process.env.WEBHOOK_URL;
const WEBHOOK_PATH = process.env.WEBHOOK_PATH || '/webhook';

// =================================
// 🛡️ Security & Middleware
// =================================

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// =================================
// 🗄️ חיבור MongoDB
// =================================

async function connectDatabase() {
    try {
        await mongoose.connect(process.env.MONGODB_URI, {
            useNewUrlParser: true,
            useUnifiedTopology: true,
        });
        console.log('✅ מחובר בהצלחה ל-MongoDB Atlas');
    } catch (error) {
        console.error('❌ שגיאה בחיבור למסד הנתונים:', error);
        process.exit(1);
    }
}

// =================================
// 📊 מודלים בסיסיים
// =================================

// סכמת הזמנה
const orderSchema = new mongoose.Schema({
    userId: { type: String, required: true },
    userName: String,
    orderNumber: { type: String, unique: true },
    items: [{
        name: String,
        price: Number,
        quantity: Number,
        notes: String
    }],
    totalAmount: Number,
    deliveryAddress: String,
    phone: String,
    status: { 
        type: String, 
        enum: ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled'],
        default: 'pending'
    },
    createdAt: { type: Date, default: Date.now },
    estimatedDelivery: Date
});

const Order = mongoose.model('Order', orderSchema);

// סכמת משתמש
const userSchema = new mongoose.Schema({
    userId: { type: String, unique: true, required: true },
    firstName: String,
    lastName: String,
    username: String,
    phone: String,
    address: String,
    totalOrders: { type: Number, default: 0 },
    favoriteItems: [String],
    isBlocked: { type: Boolean, default: false },
    createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', userSchema);

// =================================
// 🍕 תפריט המסעדה (לדוגמה)
// =================================

const menuData = {
    starters: [
        { name: 'חומוס', price: 18, emoji: '🧄' },
        { name: 'סלט ישראלי', price: 22, emoji: '🥗' },
        { name: 'פלאפל (5 יח\')', price: 25, emoji: '🧆' }
    ],
    mains: [
        { name: 'שווארמה בלאפה', price: 35, emoji: '🌯' },
        { name: 'המבורגר + צ\'יפס', price: 45, emoji: '🍔' },
        { name: 'פיצה מרגריטה', price: 52, emoji: '🍕' },
        { name: 'שניצל + תוספות', price: 48, emoji: '🍗' }
    ],
    drinks: [
        { name: 'קוקה קולה', price: 8, emoji: '🥤' },
        { name: 'מיץ תפוזים', price: 12, emoji: '🧃' },
        { name: 'קפה שחור', price: 10, emoji: '☕' },
        { name: 'בירה גולדסטאר', price: 18, emoji: '🍺' }
    ]
};

// =================================
// 💾 ניהול סשן פשוט (בזיכרון)
// =================================

const userSessions = new Map();

function getSession(userId) {
    if (!userSessions.has(userId)) {
        userSessions.set(userId, { 
            cart: [], 
            currentOrder: null,
            awaitingInput: null 
        });
    }
    return userSessions.get(userId);
}

// =================================
// ⌨️ מקלדות אינטראקטיביות
// =================================

const mainMenuKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🍽️ תפריט', 'show_menu')],
    [Markup.button.callback('🛒 עגלת קניות', 'show_cart')],
    [Markup.button.callback('📋 ההזמנות שלי', 'my_orders')],
    [Markup.button.callback('📞 צור קשר', 'contact'), Markup.button.callback('ℹ️ מידע', 'info')]
]);

const menuCategoriesKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🥗 מנות פתיחה', 'category_starters')],
    [Markup.button.callback('🍽️ מנות עיקריות', 'category_mains')],
    [Markup.button.callback('🥤 משקאות', 'category_drinks')],
    [Markup.button.callback('🔙 חזרה לתפריט הראשי', 'back_to_main')]
]);

// =================================
// 🤖 פונקציות עזר
// =================================

function generateOrderNumber() {
    return 'ORD' + Date.now().toString(36).toUpperCase();
}

function formatPrice(price) {
    return `₪${price}`;
}

async function createOrUpdateUser(ctx) {
    const { id: userId, first_name, last_name, username } = ctx.from;
    
    try {
        let user = await User.findOne({ userId: userId.toString() });
        
        if (!user) {
            user = new User({
                userId: userId.toString(),
                firstName: first_name,
                lastName: last_name,
                username: username
            });
            await user.save();
            console.log(`✅ משתמש חדש נרשם: ${first_name} (${userId})`);
        }
        
        return user;
    } catch (error) {
        console.error('❌ שגיאה ביצירת משתמש:', error);
        return null;
    }
}

// =================================
// 🎯 Bot Commands & Handlers
// =================================

// פקודת התחלה
bot.start(async (ctx) => {
    await createOrUpdateUser(ctx);
    
    const welcomeMessage = `🎉 ברוכים הבאים ל${process.env.RESTAURANT_NAME || 'מסעדת הדוגמה'}!

👋 שלום ${ctx.from.first_name}!

אני הבוט החכם שלנו - אני כאן לעזור לך להזמין אוכל טעים וטרי ישירות לבית 🏠

🕐 שעות פעילות: ${process.env.RESTAURANT_HOURS || 'א׳-ה׳ 10:00-22:00'}
📍 כתובת: ${process.env.RESTAURANT_ADDRESS || 'רחוב הראשי 123'}
🚚 דמי משלוח: ${formatPrice(process.env.DELIVERY_FEE || 15)}

בחר מהתפריט למטה 👇`;

    await ctx.reply(welcomeMessage, mainMenuKeyboard);
});

// פקודת עזרה
bot.help(async (ctx) => {
    const helpText = `🆘 עזרה - ${process.env.RESTAURANT_NAME}

📋 פקודות זמינות:
• /start - התחלה
• /menu - תפריט
• /cart - עגלת קניות
• /orders - ההזמנות שלי
• /contact - צור קשר
• /help - עזרה זו

🛒 איך להזמין:
1️⃣ לחץ על "תפריט"
2️⃣ בחר קטגוריה
3️⃣ הוסף פריטים לעגלה
4️⃣ עבור לתשלום

❓ שאלות? צור איתנו קשר!`;

    await ctx.reply(helpText, mainMenuKeyboard);
});

// הצגת תפריט
bot.action('show_menu', async (ctx) => {
    await ctx.editMessageText('🍽️ תפריט המסעדה\n\nבחר קטגוריה:', menuCategoriesKeyboard);
});

// הצגת קטגוריות
bot.action(/category_(.+)/, async (ctx) => {
    const category = ctx.match[1];
    const items = menuData[category] || [];
    
    if (items.length === 0) {
        return await ctx.answerCbQuery('❌ לא נמצאו פריטים בקטגוריה זו');
    }
    
    const categoryNames = {
        starters: '🥗 מנות פתיחה',
        mains: '🍽️ מנות עיקריות', 
        drinks: '🥤 משקאות'
    };
    
    let message = `${categoryNames[category]}\n\n`;
    const keyboard = [];
    
    items.forEach((item, index) => {
        message += `${item.emoji} ${item.name} - ${formatPrice(item.price)}\n`;
        keyboard.push([Markup.button.callback(
            `➕ ${item.emoji} ${item.name}`, 
            `add_${category}_${index}`
        )]);
    });
    
    keyboard.push([Markup.button.callback('🔙 חזרה לקטגוריות', 'show_menu')]);
    
    await ctx.editMessageText(message, Markup.inlineKeyboard(keyboard));
});

// הוספה לעגלה
bot.action(/add_(.+)_(\d+)/, async (ctx) => {
    const [, category, itemIndex] = ctx.match;
    const item = menuData[category][parseInt(itemIndex)];
    
    if (!item) {
        return await ctx.answerCbQuery('❌ פריט לא נמצא');
    }
    
    const session = getSession(ctx.from.id);
    const cartItem = session.cart.find(ci => ci.name === item.name);
    
    if (cartItem) {
        cartItem.quantity++;
    } else {
        session.cart.push({
            name: item.name,
            price: item.price,
            quantity: 1,
            emoji: item.emoji
        });
    }
    
    await ctx.answerCbQuery(`✅ ${item.emoji} ${item.name} נוסף לעגלה!`);
    
    // עדכון ההודעה עם כפתור לעגלה
    const quickActions = Markup.inlineKeyboard([
        [Markup.button.callback('🛒 לעגלה', 'show_cart')],
        [Markup.button.callback('🔙 המשך קניות', `category_${category}`)]
    ]);
    
    await ctx.editMessageReplyMarkup(quickActions);
});

// הצגת עגלת קניות
bot.action('show_cart', async (ctx) => {
    const session = getSession(ctx.from.id);
    
    if (session.cart.length === 0) {
        const emptyCartKeyboard = Markup.inlineKeyboard([
            [Markup.button.callback('🍽️ לתפריט', 'show_menu')],
            [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
        ]);
        
        return await ctx.editMessageText('🛒 העגלה שלך ריקה\n\nבואו נוסיף משהו טעים!', emptyCartKeyboard);
    }
    
    let message = '🛒 העגלה שלך:\n\n';
    let total = 0;
    
    session.cart.forEach((item, index) => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        message += `${item.emoji} ${item.name}\n`;
        message += `   כמות: ${item.quantity} × ${formatPrice(item.price)} = ${formatPrice(itemTotal)}\n\n`;
    });
    
    const deliveryFee = parseInt(process.env.DELIVERY_FEE || 15);
    const finalTotal = total + deliveryFee;
    
    message += `💰 סה"כ מוצרים: ${formatPrice(total)}\n`;
    message += `🚚 דמי משלוח: ${formatPrice(deliveryFee)}\n`;
    message += `💳 סה"כ לתשלום: ${formatPrice(finalTotal)}`;
    
    const cartKeyboard = Markup.inlineKeyboard([
        [Markup.button.callback('🗑️ רוקן עגלה', 'clear_cart')],
        [Markup.button.callback('✅ המשך להזמנה', 'proceed_order')],
        [Markup.button.callback('🔙 המשך קניות', 'show_menu')]
    ]);
    
    await ctx.editMessageText(message, cartKeyboard);
});

// ניקוי עגלה
bot.action('clear_cart', async (ctx) => {
    const session = getSession(ctx.from.id);
    session.cart = [];
    
    await ctx.answerCbQuery('🗑️ העגלה נוקתה');
    await ctx.editMessageText('🛒 העגלה נוקתה בהצלחה!', 
        Markup.inlineKeyboard([[Markup.button.callback('🍽️ חזרה לתפריט', 'show_menu')]])
    );
});

// המשך להזמנה
bot.action('proceed_order', async (ctx) => {
    const session = getSession(ctx.from.id);
    session.awaitingInput = 'address';
    
    await ctx.editMessageText(`📍 נהדר! כמעט סיימנו...

אנא שלח לי את הכתובת למשלוח:
(רחוב, מספר בית, עיר)`);
});

// טיפול בהודעות טקסט (כתובת, טלפון וכו')
bot.on('text', async (ctx) => {
    const session = getSession(ctx.from.id);
    
    if (session.awaitingInput === 'address') {
        session.currentOrder = { address: ctx.message.text };
        session.awaitingInput = 'phone';
        
        await ctx.reply(`📞 תודה! 

עכשיו אנא שלח לי את מספר הטלפון שלך:
(לצורך תיאום המשלוח)`);
        
    } else if (session.awaitingInput === 'phone') {
        session.currentOrder.phone = ctx.message.text;
        session.awaitingInput = null;
        
        // יצירת ההזמנה
        await createOrder(ctx, session);
    }
});

// יצירת הזמנה חדשה
async function createOrder(ctx, session) {
    try {
        const orderNumber = generateOrderNumber();
        const user = await User.findOne({ userId: ctx.from.id.toString() });
        
        const order = new Order({
            userId: ctx.from.id.toString(),
            userName: ctx.from.first_name,
            orderNumber: orderNumber,
            items: session.cart,
            totalAmount: session.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
            deliveryAddress: session.currentOrder.address,
            phone: session.currentOrder.phone,
            estimatedDelivery: new Date(Date.now() + 45 * 60 * 1000) // 45 דקות מהיום
        });
        
        await order.save();
        
        // עדכון מספר הזמנות של המשתמש
        if (user) {
            user.totalOrders++;
            await user.save();
        }
        
        // ניקוי העגלה והסשן
        session.cart = [];
        session.currentOrder = null;
        
        // הודעת אישור
        const confirmationMessage = `🎉 הזמנה בוצעה בהצלחה!

📋 מספר הזמנה: ${orderNumber}
📍 כתובת: ${order.deliveryAddress}
📞 טלפון: ${order.phone}
💰 סה"כ: ${formatPrice(order.totalAmount + 15)}
🕐 זמן אספקה משואמן: ${order.estimatedDelivery.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}

✅ ההזמנה התקבלה במטבח ואנחנו מתחילים להכין!
📱 תקבל עדכונים על סטטוס ההזמנה

תודה שבחרת בנו! 🙏`;

        await ctx.reply(confirmationMessage, mainMenuKeyboard);
        
        console.log(`✅ הזמנה חדשה: ${orderNumber} - ${ctx.from.first_name}`);
        
    } catch (error) {
        console.error('❌ שגיאה ביצירת הזמנה:', error);
        await ctx.reply('😞 מצטערים, היתה שגיאה בעיבוד ההזמנה. אנא נסה שוב מאוחר יותר.', mainMenuKeyboard);
    }
}

// חזרה לתפריט ראשי
bot.action('back_to_main', async (ctx) => {
    await ctx.editMessageText(`🏠 תפריט ראשי - ${process.env.RESTAURANT_NAME}

בחר פעולה:`, mainMenuKeyboard);
});

// =================================
// 🌐 Express Routes & Webhook
// =================================

// בדיקת בריאות
app.get('/', (req, res) => {
    res.json({
        status: 'active',
        bot: process.env.BOT_USERNAME || 'restaurant-bot',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

// נתיב webhook
app.use(bot.webhookCallback(WEBHOOK_PATH));

// =================================
// 🚀 הפעלת השרת
// =================================

async function startServer() {
    try {
        // חיבור למסד נתונים
        await connectDatabase();
        
        // הגדרת webhook (רק בפרודקשן)
        if (process.env.NODE_ENV === 'production' && WEBHOOK_URL) {
            await bot.telegram.setWebhook(`${WEBHOOK_URL}${WEBHOOK_PATH}`);
            console.log(`✅ Webhook הוגדר: ${WEBHOOK_URL}${WEBHOOK_PATH}`);
        } else {
            // מצב פיתוח - polling
            await bot.launch();
            console.log('🔄 הבוט רץ במצב Polling (פיתוח)');
        }
        
        // הפעלת השרת
        app.listen(PORT, () => {
            console.log(`🚀 השרת רץ על פורט ${PORT}`);
            console.log(`🤖 בוט ${process.env.BOT_USERNAME || 'Restaurant Bot'} פעיל!`);
            console.log(`📊 מסד נתונים: ${mongoose.connection.readyState === 1 ? 'מחובר' : 'לא מחובר'}`);
        });
        
    } catch (error) {
        console.error('❌ שגיאה בהפעלת השרת:', error);
        process.exit(1);
    }
}

// טיפול בכיבוי graceful
process.once('SIGINT', () => {
    console.log('🛑 מקבל SIGINT, מכבה...');
    bot.stop('SIGINT');
});

process.once('SIGTERM', () => {
    console.log('🛑 מקבל SIGTERM, מכבה...');
    bot.stop('SIGTERM');
});

// הפעלה
startServer();
