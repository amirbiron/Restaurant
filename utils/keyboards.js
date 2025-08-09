// ⌨️ מקלדות אינטראקטיביות לבוט טלגרם מסעדה
// Built with Telegraf 4.16.3 - 2025

const { Markup } = require('telegraf');

// =================================
// 🏠 מקלדת תפריט ראשי
// =================================

const mainMenuKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🍽️ תפריט המסעדה', 'show_menu')],
    [
        Markup.button.callback('🛒 עגלת קניות', 'show_cart'),
        Markup.button.callback('📋 ההזמנות שלי', 'my_orders')
    ],
    [
        Markup.button.callback('📞 צור קשר', 'contact'),
        Markup.button.callback('ℹ️ מידע על המסעדה', 'restaurant_info')
    ],
    [
        Markup.button.callback('⭐ דירוג ומשוב', 'feedback'),
        Markup.button.callback('🎁 הטבות וקופונים', 'promotions')
    ]
]);

// =================================
// 📖 מקלדות תפריט אוכל
// =================================

const menuCategoriesKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🥗 מנות פתיחה', 'category_starters')],
    [Markup.button.callback('🍽️ מנות עיקריות', 'category_mains')],
    [Markup.button.callback('🥤 משקאות', 'category_drinks')],
    [Markup.button.callback('🍰 קינוחים', 'category_desserts')],
    [Markup.button.callback('🔥 המומלצים שלנו', 'category_specials')],
    [Markup.button.callback('🔙 חזרה לתפריט הראשי', 'back_to_main')]
]);

// =================================
// 🛒 מקלדות עגלת קניות
// =================================

const emptyCartKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🍽️ לתפריט', 'show_menu')],
    [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
]);

function createCartKeyboard(itemCount = 0) {
    const buttons = [];
    
    if (itemCount > 0) {
        buttons.push([Markup.button.callback('✏️ ערוך עגלה', 'edit_cart')]);
        buttons.push([Markup.button.callback('🗑️ רוקן עגלה', 'clear_cart')]);
        buttons.push([Markup.button.callback('✅ המשך להזמנה', 'proceed_order')]);
    }
    
    buttons.push([Markup.button.callback('🍽️ המשך קניות', 'show_menu')]);
    buttons.push([Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]);
    
    return Markup.inlineKeyboard(buttons);
}

// =================================
// 🏪 יצירת מקלדת פריטים לפי קטגוריה
// =================================

function createItemsKeyboard(category, items, page = 1, itemsPerPage = 5) {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageItems = items.slice(startIndex, endIndex);
    
    const buttons = [];
    
    // כפתורי פריטים
    pageItems.forEach((item, index) => {
        const actualIndex = startIndex + index;
        buttons.push([
            Markup.button.callback(
                `➕ ${item.emoji} ${item.name} - ₪${item.price}`,
                `add_${category}_${actualIndex}`
            )
        ]);
    });
    
    // כפתורי ניווט בעמודים
    const totalPages = Math.ceil(items.length / itemsPerPage);
    if (totalPages > 1) {
        const navigationButtons = [];
        
        if (page > 1) {
            navigationButtons.push(
                Markup.button.callback('⬅️ הקודם', `page_${category}_${page - 1}`)
            );
        }
        
        navigationButtons.push(
            Markup.button.callback(`📄 ${page}/${totalPages}`, 'page_info')
        );
        
        if (page < totalPages) {
            navigationButtons.push(
                Markup.button.callback('הבא ➡️', `page_${category}_${page + 1}`)
            );
        }
        
        buttons.push(navigationButtons);
    }
    
    // כפתורי חזרה
    buttons.push([Markup.button.callback('🔙 חזרה לקטגוריות', 'show_menu')]);
    
    return Markup.inlineKeyboard(buttons);
}

// =================================
// 🛍️ מקלדת פעולות על פריט
// =================================

function createItemActionKeyboard(category, itemIndex, quantity = 1) {
    return Markup.inlineKeyboard([
        [
            Markup.button.callback('➖', `decrease_${category}_${itemIndex}`),
            Markup.button.callback(`${quantity}`, 'quantity_display'),
            Markup.button.callback('➕', `increase_${category}_${itemIndex}`)
        ],
        [Markup.button.callback('🗑️ הסר מהעגלה', `remove_${category}_${itemIndex}`)],
        [Markup.button.callback('💬 הוסף הערה', `note_${category}_${itemIndex}`)],
        [Markup.button.callback('🔙 חזרה לעגלה', 'show_cart')]
    ]);
}

// =================================
// 📋 מקלדת הזמנות
// =================================

const myOrdersKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('📊 הזמנות פעילות', 'active_orders')],
    [Markup.button.callback('📚 היסטוריית הזמנות', 'order_history')],
    [Markup.button.callback('🔄 הזמן שוב', 'reorder_last')],
    [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
]);

function createOrderDetailsKeyboard(orderId, status) {
    const buttons = [];
    
    if (status === 'pending') {
        buttons.push([Markup.button.callback('❌ בטל הזמנה', `cancel_order_${orderId}`)]);
    }
    
    if (['delivered', 'cancelled'].includes(status)) {
        buttons.push([Markup.button.callback('🔄 הזמן שוב', `reorder_${orderId}`)]);
        buttons.push([Markup.button.callback('⭐ דרג הזמנה', `rate_order_${orderId}`)]);
    }
    
    buttons.push([Markup.button.callback('📞 צור קשר', 'contact')]);
    buttons.push([Markup.button.callback('🔙 ההזמנות שלי', 'my_orders')]);
    
    return Markup.inlineKeyboard(buttons);
}

// =================================
// 📞 מקלדת יצירת קשר
// =================================

const contactKeyboard = Markup.inlineKeyboard([
    [Markup.button.url('📞 התקשר עכשיו', `tel:${process.env.RESTAURANT_PHONE || '03-1234567'}`)],
    [Markup.button.url('📍 נווט למסעדה', 'https://maps.google.com/?q=' + encodeURIComponent(process.env.RESTAURANT_ADDRESS || 'תל אביב'))],
    [Markup.button.callback('💬 שלח הודעה', 'send_message')],
    [Markup.button.callback('❓ שאלות נפוצות', 'faq')],
    [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
]);

// =================================
// 📍 מקלדת בחירת כתובת
// =================================

function createAddressKeyboard(addresses = []) {
    const buttons = [];
    
    // כתובות שמורות
    addresses.forEach((address, index) => {
        const label = address.name || `${address.street}, ${address.city}`;
        buttons.push([
            Markup.button.callback(`📍 ${label}`, `select_address_${index}`)
        ]);
    });
    
    // כתובת חדשה
    buttons.push([Markup.button.callback('➕ הוסף כתובת חדשה', 'new_address')]);
    buttons.push([Markup.button.callback('🔙 חזרה לעגלה', 'show_cart')]);
    
    return Markup.inlineKeyboard(buttons);
}

// =================================
// 💳 מקלדת אמצעי תשלום
// =================================

const paymentMethodKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('💵 מזומן בעת המסירה', 'payment_cash')],
    [Markup.button.callback('💳 כרטיס אשראי', 'payment_card')],
    [Markup.button.callback('📱 ביט / פייבוקס', 'payment_digital')],
    [Markup.button.callback('🔙 חזרה', 'proceed_order')]
]);

// =================================
// ⭐ מקלדת דירוג
// =================================

function createRatingKeyboard(orderId) {
    return Markup.inlineKeyboard([
        [
            Markup.button.callback('⭐', `rate_${orderId}_1`),
            Markup.button.callback('⭐⭐', `rate_${orderId}_2`),
            Markup.button.callback('⭐⭐⭐', `rate_${orderId}_3`),
            Markup.button.callback('⭐⭐⭐⭐', `rate_${orderId}_4`),
            Markup.button.callback('⭐⭐⭐⭐⭐', `rate_${orderId}_5`)
        ],
        [Markup.button.callback('🔙 חזרה', 'my_orders')]
    ]);
}

// =================================
// 🎁 מקלדת קופונים והטבות
// =================================

const promotionsKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🎫 הכנס קוד קופון', 'enter_coupon')],
    [Markup.button.callback('🎁 הטבות VIP', 'vip_benefits')],
    [Markup.button.callback('👥 הזמן חבר וקבל הנחה', 'referral')],
    [Markup.button.callback('📅 מבצעי השבוע', 'weekly_deals')],
    [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
]);

// =================================
// ❓ מקלדת שאלות נפוצות
// =================================

const faqKeyboard = Markup.inlineKeyboard([
    [Markup.button.callback('🕐 זמני משלוח', 'faq_delivery_times')],
    [Markup.button.callback('💰 דמי משלוח', 'faq_delivery_fees')],
    [Markup.button.callback('🔄 מדיניות החזרות', 'faq_returns')],
    [Markup.button.callback('🥗 מידע תזונתי', 'faq_nutrition')],
    [Markup.button.callback('📞 צור קשר', 'contact')],
    [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
]);

// =================================
// 🔧 פונקציות עזר למקלדות
// =================================

function createConfirmationKeyboard(action, data = '') {
    return Markup.inlineKeyboard([
        [
            Markup.button.callback('✅ אישור', `confirm_${action}_${data}`),
            Markup.button.callback('❌ ביטול', `cancel_${action}`)
        ]
    ]);
}

function createYesNoKeyboard(action) {
    return Markup.inlineKeyboard([
        [
            Markup.button.callback('כן ✅', `yes_${action}`),
            Markup.button.callback('לא ❌', `no_${action}`)
        ]
    ]);
}

// מקלדת מספרים לכמות
function createQuantityKeyboard(category, itemIndex, currentQuantity = 1) {
    const buttons = [];
    
    // שורה ראשונה: 1-5
    buttons.push([
        ...Array.from({length: 5}, (_, i) => 
            Markup.button.callback(
                currentQuantity === i + 1 ? `[${i + 1}]` : `${i + 1}`,
                `quantity_${category}_${itemIndex}_${i + 1}`
            )
        )
    ]);
    
    // שורה שנייה: 6-10
    buttons.push([
        ...Array.from({length: 5}, (_, i) => 
            Markup.button.callback(
                currentQuantity === i + 6 ? `[${i + 6}]` : `${i + 6}`,
                `quantity_${category}_${itemIndex}_${i + 6}`
            )
        )
    ]);
    
    buttons.push([Markup.button.callback('🔙 חזרה', `item_${category}_${itemIndex}`)]);
    
    return Markup.inlineKeyboard(buttons);
}

// =================================
// 🏪 מקלדות מותאמות למסעדה
// =================================

// מקלדת שעות פעילות
function createBusinessHoursKeyboard() {
    return Markup.inlineKeyboard([
        [Markup.button.callback('🕐 שעות היום', 'hours_today')],
        [Markup.button.callback('📅 שעות השבוע', 'hours_week')],
        [Markup.button.callback('🎉 שעות חגים', 'hours_holidays')],
        [Markup.button.callback('🔙 מידע על המסעדה', 'restaurant_info')]
    ]);
}

// מקלדת תפריט מיוחד לVIP
function createVipKeyboard() {
    return Markup.inlineKeyboard([
        [Markup.button.callback('👑 תפריט VIP', 'vip_menu')],
        [Markup.button.callback('🎁 הטבות בלעדיות', 'vip_exclusive')],
        [Markup.button.callback('📞 קו VIP', 'vip_support')],
        [Markup.button.callback('🔙 תפריט ראשי', 'back_to_main')]
    ]);
}

// =================================
// 📤 Export כל המקלדות
// =================================

module.exports = {
    // מקלדות בסיסיות
    mainMenuKeyboard,
    menuCategoriesKeyboard,
    emptyCartKeyboard,
    contactKeyboard,
    myOrdersKeyboard,
    paymentMethodKeyboard,
    promotionsKeyboard,
    faqKeyboard,
    
    // פונקציות יצירת מקלדות דינמיות
    createCartKeyboard,
    createItemsKeyboard,
    createItemActionKeyboard,
    createOrderDetailsKeyboard,
    createAddressKeyboard,
    createRatingKeyboard,
    createConfirmationKeyboard,
    createYesNoKeyboard,
    createQuantityKeyboard,
    createBusinessHoursKeyboard,
    createVipKeyboard,
    
    // קבועים למקלדות
    KEYBOARDS: {
        MAIN_MENU: 'main_menu',
        MENU_CATEGORIES: 'menu_categories',
        CART: 'cart',
        ORDERS: 'orders',
        CONTACT: 'contact',
        PAYMENT: 'payment',
        RATING: 'rating',
        PROMOTIONS: 'promotions',
        FAQ: 'faq'
    }
};
