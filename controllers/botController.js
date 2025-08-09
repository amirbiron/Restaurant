// 🤖 בקר הבוט הראשי - ניהול כל הפעולות והלוגיקה
// Separated logic for better maintainability

const { Order, User } = require('../models/Order');
const keyboards = require('../utils/keyboards');
const menuData = require('../data/menu');

// =================================
// 💾 ניהול Sessions (זיכרון זמני)
// =================================

class SessionManager {
    constructor() {
        this.sessions = new Map();
        this.cleanup(); // ניקוי תקופתי
    }
    
    getSession(userId) {
        if (!this.sessions.has(userId)) {
            this.sessions.set(userId, {
                cart: [],
                currentOrder: null,
                awaitingInput: null,
                lastActivity: Date.now(),
                preferences: {},
                tempData: {}
            });
        }
        
        // עדכון זמן פעילות אחרון
        const session = this.sessions.get(userId);
        session.lastActivity = Date.now();
        return session;
    }
    
    clearSession(userId) {
        this.sessions.delete(userId);
    }
    
    // ניקוי sessions ישנים (מעל שעה)
    cleanup() {
        setInterval(() => {
            const oneHourAgo = Date.now() - (60 * 60 * 1000);
            for (const [userId, session] of this.sessions.entries()) {
                if (session.lastActivity < oneHourAgo) {
                    this.sessions.delete(userId);
                }
            }
        }, 15 * 60 * 1000); // כל 15 דקות
    }
}

const sessionManager = new SessionManager();

// =================================
// 🎯 Bot Controller Class
// =================================

class BotController {
    constructor() {
        this.orderNumber = 1000; // התחלה מ-1000
    }
    
    // =================================
    // 👤 ניהול משתמשים
    // =================================
    
    async createOrUpdateUser(ctx) {
        const { id: userId, first_name, last_name, username } = ctx.from;
        
        try {
            let user = await User.findOne({ userId: userId.toString() });
            
            if (!user) {
                user = new User({
                    userId: userId.toString(),
                    firstName: first_name,
                    lastName: last_name,
                    username: username,
                    source: 'telegram'
                });
                await user.save();
                console.log(`✅ משתמש חדש נרשם: ${first_name} (${userId})`);
                
                // הודעת ברוכים הבאים למשתמש חדש
                await this.sendWelcomeBonus(ctx, user);
            } else {
                // עדכון פרטים אם השתנו
                let updated = false;
                if (user.firstName !== first_name) {
                    user.firstName = first_name;
                    updated = true;
                }
                if (user.username !== username) {
                    user.username = username;
                    updated = true;
                }
                if (updated) {
                    await user.save();
                }
            }
            
            return user;
        } catch (error) {
            console.error('❌ שגיאה ביצירת משתמש:', error);
            return null;
        }
    }
    
    async sendWelcomeBonus(ctx, user) {
        // בונוס למשתמש חדש
        user.loyaltyPoints = 50;
        await user.save();
        
        await ctx.reply(`🎉 ברוכים הבאים למשפחה שלנו!

🎁 קיבלת 50 נקודות נאמנות מתנה!
💰 ב-100 נקודות תקבל הנחה של 10₪
🏆 אחרי 5 הזמנות תהפוך ללקוח VIP`);
    }
    
    // =================================
    // 🏠 פקודות בסיסיות
    // =================================
    
    async handleStart(ctx) {
        const user = await this.createOrUpdateUser(ctx);
        const session = sessionManager.getSession(ctx.from.id);
        
        // בדיקה אם המשתמש VIP
        const vipText = user?.isVip ? '👑 סטטוס VIP פעיל!' : '';
        
        const welcomeMessage = `🎉 ברוכים הבאים ל${process.env.RESTAURANT_NAME || 'מסעדת הדוגמה'}!

👋 שלום ${ctx.from.first_name}! ${vipText}

אני הבוט החכם שלנו - אני כאן לעזור לך להזמין אוכל טעים וטרי ישירות לבית 🏠

🕐 שעות פעילות: ${process.env.RESTAURANT_HOURS || 'א׳-ה׳ 10:00-22:00'}
📍 כתובת: ${process.env.RESTAURANT_ADDRESS || 'רחוב הראשי 123'}
🚚 דמי משלוח: ₪${process.env.DELIVERY_FEE || 15}

${user?.loyaltyPoints > 0 ? `💎 נקודות נאמנות: ${user.loyaltyPoints}` : ''}

בחר מהתפריט למטה 👇`;

        const keyboard = user?.isVip ? keyboards.createVipKeyboard() : keyboards.mainMenuKeyboard;
        await ctx.reply(welcomeMessage, keyboard);
    }
    
    async handleHelp(ctx) {
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

💡 טיפים שימושיים:
• השתמש בכפתורים במקום להקליד
• ניתן לערוך כמויות בעגלה
• הוסף הערות לפריטים
• שמור כתובות למשלוחים הבאים

❓ שאלות? צור איתנו קשר!`;

        await ctx.reply(helpText, keyboards.mainMenuKeyboard);
    }
    
    // =================================
    // 🍽️ ניהול תפריט ופריטים
    // =================================
    
    async handleShowMenu(ctx) {
        await this.editMessage(ctx, '🍽️ תפריט המסעדה\n\nבחר קטגוריה:', keyboards.menuCategoriesKeyboard);
    }
    
    async handleCategory(ctx) {
        const category = ctx.match[1];
        const items = menuData.getCategory(category);
        
        if (!items || items.length === 0) {
            return await ctx.answerCbQuery('❌ לא נמצאו פריטים בקטגוריה זו');
        }
        
        const categoryName = menuData.getCategoryName(category);
        let message = `${categoryName}\n\n`;
        
        items.forEach(item => {
            message += `${item.emoji} **${item.name}**\n`;
            message += `   ${item.description || ''}\n`;
            message += `   💰 ${this.formatPrice(item.price)}\n\n`;
        });
        
        const keyboard = keyboards.createItemsKeyboard(category, items);
        await this.editMessage(ctx, message, keyboard);
    }
    
    async handleAddItem(ctx) {
        const [, category, itemIndex] = ctx.match;
        const item = menuData.getItem(category, parseInt(itemIndex));
        
        if (!item) {
            return await ctx.answerCbQuery('❌ פריט לא נמצא');
        }
        
        const session = sessionManager.getSession(ctx.from.id);
        const existingItem = session.cart.find(ci => ci.name === item.name);
        
        if (existingItem) {
            existingItem.quantity++;
            existingItem.subtotal = existingItem.price * existingItem.quantity;
        } else {
            session.cart.push({
                name: item.name,
                price: item.price,
                quantity: 1,
                category: category,
                emoji: item.emoji,
                subtotal: item.price,
                notes: ''
            });
        }
        
        await ctx.answerCbQuery(`✅ ${item.emoji} ${item.name} נוסף לעגלה!`);
        
        // עדכון הודעה עם אפשרויות מהירות
        const quickActions = keyboards.createCartKeyboard(session.cart.length);
        await ctx.editMessageReplyMarkup(quickActions);
        
        // עדכון סטטיסטיקות משתמש
        await this.updateUserFavorites(ctx.from.id, item.name, category);
    }
    
    // =================================
    // 🛒 ניהול עגלת קניות
    // =================================
    
    async handleShowCart(ctx) {
        const session = sessionManager.getSession(ctx.from.id);
        
        if (session.cart.length === 0) {
            return await this.editMessage(ctx, 
                '🛒 העגלה שלך ריקה\n\nבואו נוסיף משהו טעים!', 
                keyboards.emptyCartKeyboard
            );
        }
        
        const cartMessage = await this.generateCartMessage(session.cart);
        const keyboard = keyboards.createCartKeyboard(session.cart.length);
        
        await this.editMessage(ctx, cartMessage, keyboard);
    }
    
    async generateCartMessage(cart) {
        let message = '🛒 העגלה שלך:\n\n';
        let subtotal = 0;
        
        cart.forEach((item, index) => {
            subtotal += item.subtotal;
            message += `${item.emoji} **${item.name}**\n`;
            message += `   כמות: ${item.quantity} × ${this.formatPrice(item.price)} = ${this.formatPrice(item.subtotal)}\n`;
            if (item.notes) {
                message += `   📝 ${item.notes}\n`;
            }
            message += '\n';
        });
        
        const deliveryFee = parseInt(process.env.DELIVERY_FEE || 15);
        const total = subtotal + deliveryFee;
        
        message += `💰 סה"כ מוצרים: ${this.formatPrice(subtotal)}\n`;
        message += `🚚 דמי משלוח: ${this.formatPrice(deliveryFee)}\n`;
        message += `💳 **סה"כ לתשלום: ${this.formatPrice(total)}**`;
        
        return message;
    }
    
    async handleClearCart(ctx) {
        const session = sessionManager.getSession(ctx.from.id);
        session.cart = [];
        
        await ctx.answerCbQuery('🗑️ העגלה נוקתה');
        await this.editMessage(ctx, 
            '🛒 העגלה נוקתה בהצלחה!',
            keyboards.emptyCartKeyboard
        );
    }
    
    // =================================
    // 📋 ניהול הזמנות
    // =================================
    
    async handleProceedOrder(ctx) {
        const session = sessionManager.getSession(ctx.from.id);
        
        if (session.cart.length === 0) {
            return await ctx.answerCbQuery('❌ העגלה ריקה');
        }
        
        // בדיקת מינימום הזמנה
        const subtotal = session.cart.reduce((sum, item) => sum + item.subtotal, 0);
        const minOrder = parseInt(process.env.MIN_ORDER_AMOUNT || 50);
        
        if (subtotal < minOrder) {
            return await ctx.answerCbQuery(`❌ הזמנה מינימלית: ${this.formatPrice(minOrder)}`);
        }
        
        // קבלת כתובות שמורות של המשתמש
        const user = await User.findOne({ userId: ctx.from.id.toString() });
        
        if (user && user.addresses.length > 0) {
            const message = '📍 בחר כתובת למשלוח:';
            const keyboard = keyboards.createAddressKeyboard(user.addresses);
            await this.editMessage(ctx, message, keyboard);
        } else {
            // אין כתובות שמורות - בקש כתובת חדשה
            session.awaitingInput = 'address';
            await this.editMessage(ctx, `📍 נהדר! כמעט סיימנו...

אנא שלח לי את הכתובת למשלוח:
(רחוב, מספר בית, עיר)

💡 טיפ: הכתובת תישמר למשלוחים הבאים`);
        }
    }
    
    async handleSelectAddress(ctx) {
        const addressIndex = parseInt(ctx.match[1]);
        const user = await User.findOne({ userId: ctx.from.id.toString() });
        
        if (!user || !user.addresses[addressIndex]) {
            return await ctx.answerCbQuery('❌ כתובת לא נמצאה');
        }
        
        const session = sessionManager.getSession(ctx.from.id);
        const address = user.addresses[addressIndex];
        
        session.currentOrder = {
            address: `${address.street}, ${address.city}`,
            addressData: address
        };
        
        // מעבר לבקשת טלפון
        session.awaitingInput = 'phone';
        await this.editMessage(ctx, `📞 כתובת נבחרה: ${session.currentOrder.address}

עכשיו אנא שלח לי את מספר הטלפון שלך:
(לצורך תיאום המשלוח)`);
    }
    
    async createOrder(ctx, session) {
        try {
            const orderNumber = this.generateOrderNumber();
            const user = await User.findOne({ userId: ctx.from.id.toString() });
            
            // חישוב סכומים
            const subtotal = session.cart.reduce((sum, item) => sum + item.subtotal, 0);
            const deliveryFee = parseInt(process.env.DELIVERY_FEE || 15);
            
            // יצירת ההזמנה
            const order = new Order({
                userId: ctx.from.id.toString(),
                userName: ctx.from.first_name,
                orderNumber: orderNumber,
                items: session.cart.map(item => ({
                    name: item.name,
                    price: item.price,
                    quantity: item.quantity,
                    category: item.category,
                    notes: item.notes,
                    emoji: item.emoji,
                    subtotal: item.subtotal
                })),
                subtotal: subtotal,
                deliveryFee: deliveryFee,
                totalAmount: subtotal + deliveryFee,
                deliveryAddress: {
                    street: session.currentOrder.address,
                    instructions: session.currentOrder.instructions || ''
                },
                userPhone: session.currentOrder.phone,
                estimatedDelivery: new Date(Date.now() + 45 * 60 * 1000) // 45 דקות
            });
            
            await order.save();
            
            // עדכון סטטיסטיקות משתמש
            if (user) {
                await user.updateStats(order.totalAmount);
                
                // הוספת נקודות נאמנות (1 נקודה לכל 5₪)
                user.loyaltyPoints += Math.floor(order.totalAmount / 5);
                await user.save();
            }
            
            // ניקוי הסשן
            session.cart = [];
            session.currentOrder = null;
            session.awaitingInput = null;
            
            // שליחת הודעת אישור
            await this.sendOrderConfirmation(ctx, order, user);
            
            console.log(`✅ הזמנה חדשה: ${orderNumber} - ${ctx.from.first_name} - ${this.formatPrice(order.totalAmount)}`);
            
        } catch (error) {
            console.error('❌ שגיאה ביצירת הזמנה:', error);
            await ctx.reply(
                '😞 מצטערים, היתה שגיאה בעיבוד ההזמנה. אנא נסה שוב מאוחר יותר.',
                keyboards.mainMenuKeyboard
            );
        }
    }
    
    async sendOrderConfirmation(ctx, order, user) {
        const estimatedTime = order.estimatedDelivery.toLocaleTimeString('he-IL', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const confirmationMessage = `🎉 הזמנה בוצעה בהצלחה!

📋 **מספר הזמנה: ${order.orderNumber}**
📍 כתובת: ${order.deliveryAddress.street}
📞 טלפון: ${order.userPhone}
💰 סה"כ: ${this.formatPrice(order.totalAmount)}
🕐 זמן אספקה משוער: ${estimatedTime}

${user?.loyaltyPoints ? `💎 נקודות נאמנות: ${user.loyaltyPoints}` : ''}

✅ ההזמנה התקבלה במטבח ואנחנו מתחילים להכין!
📱 תקבל עדכונים על סטטוס ההזמנה

תודה שבחרת בנו! 🙏`;

        await ctx.reply(confirmationMessage, keyboards.mainMenuKeyboard);
        
        // הודעה נוספת עם פרטי המעקב
        const trackingKeyboard = keyboards.createOrderDetailsKeyboard(order._id, order.status);
        await ctx.reply(
            `🔍 מעקב הזמנה ${order.orderNumber}:\n\n⏳ סטטוס נוכחי: ממתינה לאישור\n📞 לשאלות: ${process.env.RESTAURANT_PHONE}`,
            trackingKeyboard
        );
    }
    
    // =================================
    // 🔧 פונקציות עזר
    // =================================
    
    generateOrderNumber() {
        return 'ORD' + Date.now().toString(36).toUpperCase();
    }
    
    formatPrice(price) {
        return `₪${price}`;
    }
    
    async editMessage(ctx, text, keyboard) {
        try {
            await ctx.editMessageText(text, { 
                parse_mode: 'Markdown',
                ...keyboard 
            });
        } catch (error) {
            // אם העריכה נכשלה, שלח הודעה חדשה
            if (error.description?.includes('message is not modified')) {
                return;
            }
            await ctx.reply(text, { 
                parse_mode: 'Markdown',
                ...keyboard 
            });
        }
    }
    
    async updateUserFavorites(userId, itemName, category) {
        try {
            const user = await User.findOne({ userId: userId.toString() });
            if (user) {
                await user.addFavoriteItem(itemName, category);
            }
        } catch (error) {
            console.error('❌ שגיאה בעדכון מועדפים:', error);
        }
    }
    
    // =================================
    // 💬 טיפול בהודעות טקסט
    // =================================
    
    async handleTextMessage(ctx) {
        const session = sessionManager.getSession(ctx.from.id);
        const text = ctx.message.text.trim();
        
        // התעלמות מפקודות
        if (text.startsWith('/')) {
            return;
        }
        
        switch (session.awaitingInput) {
            case 'address':
                session.currentOrder = { address: text };
                session.awaitingInput = 'phone';
                
                await ctx.reply(`📞 תודה! 

עכשיו אנא שלח לי את מספר הטלפון שלך:
(לצורך תיאום המשלוח)`);
                break;
                
            case 'phone':
                // ולידציה בסיסית לטלפון
                if (!/^[0-9\-\+\s\(\)]+$/.test(text)) {
                    await ctx.reply('❌ אנא הכנס מספר טלפון תקין (ספרות בלבד)');
                    return;
                }
                
                session.currentOrder.phone = text;
                session.awaitingInput = null;
                
                // יצירת ההזמנה
                await this.createOrder(ctx, session);
                break;
                
            case 'feedback':
                await this.handleFeedbackMessage(ctx, text);
                break;
                
            default:
                // הודעה כללית - הצגת תפריט
                await ctx.reply(
                    '👋 שלום! אני בוט הזמנות אוטומטי.\n\nאנא השתמש בכפתורים למטה לניווט 🔽',
                    keyboards.mainMenuKeyboard
                );
        }
    }
    
    async handleFeedbackMessage(ctx, text) {
        try {
            // שמירת המשוב במסד הנתונים או שליחה למנהלים
            console.log(`📝 משוב מ-${ctx.from.first_name}: ${text}`);
            
            sessionManager.getSession(ctx.from.id).awaitingInput = null;
            
            await ctx.reply(
                '🙏 תודה רבה על המשוב!\n\nהערותיך חשובות לנו ויעזרו לנו להשתפר.',
                keyboards.mainMenuKeyboard
            );
        } catch (error) {
            console.error('❌ שגיאה בטיפול במשוב:', error);
        }
    }
    
    // =================================
    // 📊 פונקציות מידע וסטטיסטיקות
    // =================================
    
    async handleMyOrders(ctx) {
        try {
            const orders = await Order.find({ 
                userId: ctx.from.id.toString() 
            }).sort({ createdAt: -1 }).limit(5);
            
            if (orders.length === 0) {
                await this.editMessage(ctx, 
                    '📋 עדיין לא ביצעת הזמנות\n\nבואו נתחיל! 🛒',
                    keyboards.emptyCartKeyboard
                );
                return;
            }
            
            let message = '📋 **ההזמנות שלך:**\n\n';
            
            orders.forEach(order => {
                const statusEmoji = this.getStatusEmoji(order.status);
                const date = order.createdAt.toLocaleDateString('he-IL');
                
                message += `${statusEmoji} **${order.orderNumber}**\n`;
                message += `📅 ${date} | ${this.formatPrice(order.totalAmount)}\n`;
                message += `📊 ${this.getStatusText(order.status)}\n\n`;
            });
            
            await this.editMessage(ctx, message, keyboards.myOrdersKeyboard);
            
        } catch (error) {
            console.error('❌ שגיאה בטעינת הזמנות:', error);
            await ctx.answerCbQuery('❌ שגיאה בטעינת ההזמנות');
        }
    }
    
    getStatusEmoji(status) {
        const emojis = {
            'pending': '⏳',
            'confirmed': '✅', 
            'preparing': '👨‍🍳',
            'ready': '🍽️',
            'out_delivery': '🚚',
            'delivered': '✅',
            'cancelled': '❌'
        };
        return emojis[status] || '📋';
    }
    
    getStatusText(status) {
        const texts = {
            'pending': 'ממתינה לאישור',
            'confirmed': 'אושרה - בהכנה',
            'preparing': 'מוכנת במטבח',
            'ready': 'מוכנה למשלוח',
            'out_delivery': 'יצאה למשלוח',
            'delivered': 'נמסרה בהצלחה',
            'cancelled': 'בוטלה'
        };
        return texts[status] || 'לא ידוע';
    }
    
    // =================================
    // 🔄 חזרה לתפריט ראשי
    // =================================
    
    async handleBackToMain(ctx) {
        await this.editMessage(ctx, 
            `🏠 **תפריט ראשי** - ${process.env.RESTAURANT_NAME}\n\nבחר פעולה:`,
            keyboards.mainMenuKeyboard
        );
    }
}

// =================================
// 📤 Export
// =================================

module.exports = {
    BotController,
    sessionManager
};
