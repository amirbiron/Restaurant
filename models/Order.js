// 🗄️ מודלים לבסיס הנתונים - מסעדה
// Built for MongoDB Atlas with Mongoose

const mongoose = require('mongoose');

// =================================
// 📋 סכמת הזמנה מתקדמת
// =================================

const orderItemSchema = new mongoose.Schema({
    name: {
        type: String,
        required: true,
        trim: true
    },
    price: {
        type: Number,
        required: true,
        min: 0
    },
    quantity: {
        type: Number,
        required: true,
        min: 1,
        max: 50
    },
    category: {
        type: String,
        enum: ['starters', 'mains', 'drinks', 'desserts'],
        required: true
    },
    notes: {
        type: String,
        maxlength: 200,
        trim: true
    },
    emoji: String,
    subtotal: {
        type: Number,
        required: true,
        min: 0
    }
});

// חישוב אוטומטי של subtotal
orderItemSchema.pre('save', function() {
    this.subtotal = this.price * this.quantity;
});

const orderSchema = new mongoose.Schema({
    // פרטי הזמנה בסיסיים
    orderNumber: {
        type: String,
        unique: true,
        required: true,
        uppercase: true
    },
    
    // פרטי לקוח
    userId: {
        type: String,
        required: true,
        index: true
    },
    userName: {
        type: String,
        required: true,
        trim: true
    },
    userPhone: {
        type: String,
        required: true,
        match: /^[0-9\-\+\s\(\)]+$/
    },
    
    // פריטי ההזמנה
    items: {
        type: [orderItemSchema],
        required: true,
        validate: {
            validator: function(items) {
                return items && items.length > 0;
            },
            message: 'ההזמנה חייבת לכלול לפחות פריט אחד'
        }
    },
    
    // פרטים כלכליים
    subtotal: {
        type: Number,
        required: true,
        min: 0
    },
    deliveryFee: {
        type: Number,
        default: 15,
        min: 0
    },
    discount: {
        type: Number,
        default: 0,
        min: 0
    },
    totalAmount: {
        type: Number,
        required: true,
        min: 0
    },
    
    // פרטי משלוח
    deliveryAddress: {
        street: {
            type: String,
            required: true,
            trim: true
        },
        building: String,
        apartment: String,
        city: {
            type: String,
            default: 'תל אביב',
            trim: true
        },
        instructions: {
            type: String,
            maxlength: 300
        },
        coordinates: {
            lat: Number,
            lng: Number
        }
    },
    
    // זמנים
    createdAt: {
        type: Date,
        default: Date.now,
        index: true
    },
    estimatedDelivery: {
        type: Date,
        required: true
    },
    actualDelivery: Date,
    
    // סטטוס ההזמנה
    status: {
        type: String,
        enum: [
            'pending',      // ממתינה לאישור
            'confirmed',    // אושרה - מתחילים להכין
            'preparing',    // בהכנה במטבח
            'ready',        // מוכנה למשלוח
            'out_delivery', // יצאה למשלוח
            'delivered',    // נמסרה
            'cancelled'     // בוטלה
        ],
        default: 'pending',
        index: true
    },
    
    statusHistory: [{
        status: String,
        timestamp: {
            type: Date,
            default: Date.now
        },
        note: String
    }],
    
    // פרטים נוספים
    paymentMethod: {
        type: String,
        enum: ['cash', 'card', 'online'],
        default: 'cash'
    },
    
    isPaid: {
        type: Boolean,
        default: false
    },
    
    customerNotes: {
        type: String,
        maxlength: 500
    },
    
    kitchenNotes: {
        type: String,
        maxlength: 300
    },
    
    // דירוג ומשוב
    rating: {
        type: Number,
        min: 1,
        max: 5
    },
    
    feedback: {
        type: String,
        maxlength: 1000
    },
    
    // מטא דאטה
    source: {
        type: String,
        enum: ['telegram', 'web', 'phone', 'walk_in'],
        default: 'telegram'
    },
    
    isTest: {
        type: Boolean,
        default: false
    }
}, {
    timestamps: true,
    collection: 'orders'
});

// =================================
// 🧮 Middleware לחישובים אוטומטיים
// =================================

// חישוב סכומים לפני שמירה
orderSchema.pre('save', function() {
    // חישוב subtotal
    this.subtotal = this.items.reduce((sum, item) => {
        return sum + (item.price * item.quantity);
    }, 0);
    
    // חישוב סה"כ
    this.totalAmount = this.subtotal + this.deliveryFee - this.discount;
    
    // הוספת רשומה להיסטוריית סטטוס
    if (this.isModified('status')) {
        this.statusHistory.push({
            status: this.status,
            timestamp: new Date()
        });
    }
    
    // חישוב זמן אספקה משוער (אם לא הוגדר)
    if (!this.estimatedDelivery) {
        const prepTime = this.items.length * 5; // 5 דקות לפריט
        const deliveryTime = 30; // 30 דקות משלוח
        this.estimatedDelivery = new Date(Date.now() + (prepTime + deliveryTime) * 60 * 1000);
    }
});

// =================================
// 📊 Methods
// =================================

// קבלת זמן הכנה משוער
orderSchema.methods.getPreparationTime = function() {
    const baseTime = 15; // זמן בסיס
    const itemTime = this.items.length * 3; // 3 דקות לפריט
    return baseTime + itemTime;
};

// בדיקה אם ההזמנה מאוחרת
orderSchema.methods.isLate = function() {
    if (this.status === 'delivered') return false;
    return new Date() > this.estimatedDelivery;
};

// עדכון סטטוס עם הערה
orderSchema.methods.updateStatus = function(newStatus, note = '') {
    this.status = newStatus;
    this.statusHistory.push({
        status: newStatus,
        timestamp: new Date(),
        note: note
    });
    
    // אם נמסרה - עדכן זמן מסירה בפועל
    if (newStatus === 'delivered') {
        this.actualDelivery = new Date();
    }
    
    return this.save();
};

// קבלת משך זמן ההזמנה
orderSchema.methods.getDuration = function() {
    const end = this.actualDelivery || new Date();
    return Math.round((end - this.createdAt) / (1000 * 60)); // בדקות
};

// =================================
// 🔍 Statics (שיטות סטטיות)
// =================================

// קבלת הזמנות פעילות
orderSchema.statics.getActiveOrders = function() {
    return this.find({
        status: { $in: ['pending', 'confirmed', 'preparing', 'ready', 'out_delivery'] }
    }).sort({ createdAt: -1 });
};

// סטטיסטיקות יומיות
orderSchema.statics.getDailyStats = function(date = new Date()) {
    const startOfDay = new Date(date);
    startOfDay.setHours(0, 0, 0, 0);
    
    const endOfDay = new Date(date);
    endOfDay.setHours(23, 59, 59, 999);
    
    return this.aggregate([
        {
            $match: {
                createdAt: { $gte: startOfDay, $lte: endOfDay },
                status: { $ne: 'cancelled' }
            }
        },
        {
            $group: {
                _id: null,
                totalOrders: { $sum: 1 },
                totalRevenue: { $sum: '$totalAmount' },
                avgOrderValue: { $avg: '$totalAmount' },
                deliveredOrders: {
                    $sum: { $cond: [{ $eq: ['$status', 'delivered'] }, 1, 0] }
                }
            }
        }
    ]);
};

// חיפוש הזמנות לפי מספר טלפון
orderSchema.statics.findByPhone = function(phone) {
    return this.find({ userPhone: phone }).sort({ createdAt: -1 });
};

// =================================
// 📈 Indexes לביצועים
// =================================

orderSchema.index({ userId: 1, createdAt: -1 });
orderSchema.index({ status: 1, createdAt: -1 });
orderSchema.index({ orderNumber: 1 }, { unique: true });
orderSchema.index({ createdAt: -1 });
orderSchema.index({ userPhone: 1 });
orderSchema.index({ 'deliveryAddress.city': 1 });

// =================================
// 👤 סכמת משתמש מתקדמת
// =================================

const userSchema = new mongoose.Schema({
    userId: {
        type: String,
        unique: true,
        required: true,
        index: true
    },
    
    // פרטים אישיים
    firstName: {
        type: String,
        required: true,
        trim: true
    },
    lastName: {
        type: String,
        trim: true
    },
    username: {
        type: String,
        trim: true
    },
    
    // פרטי קשר
    phone: {
        type: String,
        match: /^[0-9\-\+\s\(\)]+$/
    },
    email: {
        type: String,
        lowercase: true,
        trim: true
    },
    
    // כתובות
    addresses: [{
        name: String, // בית, עבודה וכו'
        street: String,
        building: String,
        apartment: String,
        city: String,
        instructions: String,
        isDefault: { type: Boolean, default: false }
    }],
    
    // העדפות
    preferences: {
        language: {
            type: String,
            enum: ['he', 'en', 'ar'],
            default: 'he'
        },
        notifications: {
            orderUpdates: { type: Boolean, default: true },
            promotions: { type: Boolean, default: true },
            newItems: { type: Boolean, default: false }
        },
        dietaryRestrictions: [String] // kosher, vegan, etc.
    },
    
    // סטטיסטיקות
    totalOrders: {
        type: Number,
        default: 0,
        min: 0
    },
    totalSpent: {
        type: Number,
        default: 0,
        min: 0
    },
    avgOrderValue: {
        type: Number,
        default: 0,
        min: 0
    },
    lastOrder: Date,
    
    // פריטים מועדפים
    favoriteItems: [{
        name: String,
        category: String,
        orderCount: { type: Number, default: 1 }
    }],
    
    // מצב חשבון
    isActive: {
        type: Boolean,
        default: true
    },
    isBlocked: {
        type: Boolean,
        default: false
    },
    blockReason: String,
    
    // לקוח VIP
    isVip: {
        type: Boolean,
        default: false
    },
    vipSince: Date,
    loyaltyPoints: {
        type: Number,
        default: 0,
        min: 0
    },
    
    // מטא דאטה
    source: {
        type: String,
        enum: ['telegram', 'web', 'referral'],
        default: 'telegram'
    },
    referralCode: String,
    referredBy: String
}, {
    timestamps: true,
    collection: 'users'
});

// Methods למשתמש
userSchema.methods.addFavoriteItem = function(itemName, category) {
    const existing = this.favoriteItems.find(item => item.name === itemName);
    if (existing) {
        existing.orderCount++;
    } else {
        this.favoriteItems.push({ name: itemName, category, orderCount: 1 });
    }
    return this.save();
};

userSchema.methods.updateStats = function(orderAmount) {
    this.totalOrders++;
    this.totalSpent += orderAmount;
    this.avgOrderValue = this.totalSpent / this.totalOrders;
    this.lastOrder = new Date();
    
    // בדיקה לVIP (לאחר 10 הזמנות או 500₪)
    if (this.totalOrders >= 10 || this.totalSpent >= 500) {
        this.isVip = true;
        if (!this.vipSince) {
            this.vipSince = new Date();
        }
    }
    
    return this.save();
};

// Indexes למשתמש
userSchema.index({ userId: 1 }, { unique: true });
userSchema.index({ phone: 1 });
userSchema.index({ isVip: 1 });
userSchema.index({ totalOrders: -1 });

// =================================
// 📤 Export Models
// =================================

const Order = mongoose.model('Order', orderSchema);
const User = mongoose.model('User', userSchema);

module.exports = {
    Order,
    User,
    orderSchema,
    userSchema
};
