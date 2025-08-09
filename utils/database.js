// 🗄️ ניהול מסד נתונים וחיבורים - MongoDB Atlas
// עם פונקציות עזר, קאש וביצועים מתקדמים

const mongoose = require('mongoose');
const { Order, User } = require('../models/Order');

// =================================
// 🔌 ניהול חיבורים
// =================================

class DatabaseManager {
    constructor() {
        this.isConnected = false;
        this.connectionRetries = 0;
        this.maxRetries = 5;
        this.retryDelay = 5000; // 5 שניות
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 דקות
    }
    
    // חיבור למסד הנתונים
    async connect() {
        if (this.isConnected) {
            console.log('✅ כבר מחובר למסד הנתונים');
            return true;
        }
        
        try {
            const options = {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                serverSelectionTimeoutMS: 10000, // 10 שניות timeout
                heartbeatFrequencyMS: 2000, // בדיקת לב כל 2 שניות
                maxPoolSize: 10, // מקס 10 חיבורים בפול
                bufferCommands: false, // אל תשמור פקודות בבאפר אם אין חיבור
                bufferMaxEntries: 0
            };
            
            await mongoose.connect(process.env.MONGODB_URI, options);
            
            this.isConnected = true;
            this.connectionRetries = 0;
            
            console.log('✅ מחובר בהצלחה ל-MongoDB Atlas');
            this.setupEventHandlers();
            
            return true;
            
        } catch (error) {
            console.error('❌ שגיאה בחיבור למסד הנתונים:', error.message);
            
            this.connectionRetries++;
            if (this.connectionRetries < this.maxRetries) {
                console.log(`🔄 ינסיון ${this.connectionRetries}/${this.maxRetries} בעוד ${this.retryDelay / 1000} שניות...`);
                
                setTimeout(() => {
                    this.connect();
                }, this.retryDelay);
                
                return false;
            } else {
                console.error('💀 כשל בחיבור למסד הנתונים אחרי מספר ניסיונות');
                process.exit(1);
            }
        }
    }
    
    // הגדרת מאזינים לאירועים
    setupEventHandlers() {
        mongoose.connection.on('error', (error) => {
            console.error('❌ שגיאת חיבור:', error.message);
            this.isConnected = false;
        });
        
        mongoose.connection.on('disconnected', () => {
            console.warn('⚠️ החיבור למסד הנתונים נותק');
            this.isConnected = false;
            
            // ניסיון חיבור מחדש
            setTimeout(() => {
                console.log('🔄 מנסה להתחבר מחדש...');
                this.connect();
            }, this.retryDelay);
        });
        
        mongoose.connection.on('reconnected', () => {
            console.log('✅ התחבר מחדש למסד הנתונים');
            this.isConnected = true;
        });
    }
    
    // בדיקת חיבור
    async checkConnection() {
        try {
            await mongoose.connection.db.admin().ping();
            return true;
        } catch (error) {
            console.error('❌ מסד הנתונים לא זמין:', error.message);
            return false;
        }
    }
    
    // סגירת חיבור
    async disconnect() {
        try {
            await mongoose.disconnect();
            this.isConnected = false;
            console.log('👋 החיבור למסד הנתונים נסגר');
        } catch (error) {
            console.error('❌ שגיאה בסגירת החיבור:', error.message);
        }
    }
    
    // =================================
    // 🔄 מערכת Cache
    // =================================
    
    // שמירה בקאש
    setCache(key, data, customTimeout = null) {
        const timeout = customTimeout || this.cacheTimeout;
        const expiry = Date.now() + timeout;
        
        this.cache.set(key, {
            data: data,
            expiry: expiry
        });
        
        // ניקוי אוטומטי של קאש
        this.cleanExpiredCache();
    }
    
    // קבלה מהקאש
    getCache(key) {
        const cached = this.cache.get(key);
        
        if (!cached) return null;
        
        // בדיקה אם הקאש תקף
        if (Date.now() > cached.expiry) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.data;
    }
    
    // ניקוי קאש ישן
    cleanExpiredCache() {
        const now = Date.now();
        
        for (const [key, value] of this.cache.entries()) {
            if (now > value.expiry) {
                this.cache.delete(key);
            }
        }
    }
    
    // ריקון קאש
    clearCache() {
        this.cache.clear();
        console.log('🧹 קאש נוקה');
    }
    
    // =================================
    // 👤 פונקציות משתמשים
    // =================================
    
    async findUser(userId) {
        const cacheKey = `user_${userId}`;
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const user = await User.findOne({ userId: userId.toString() });
            
            if (user) {
                this.setCache(cacheKey, user, 10 * 60 * 1000); // 10 דקות
            }
            
            return user;
        } catch (error) {
            console.error('❌ שגיאה בחיפוש משתמש:', error);
            return null;
        }
    }
    
    async createUser(userData) {
        try {
            const user = new User(userData);
            await user.save();
            
            // עדכון קאש
            this.setCache(`user_${userData.userId}`, user);
            
            console.log(`✅ משתמש חדש נוצר: ${userData.firstName} (${userData.userId})`);
            return user;
        } catch (error) {
            console.error('❌ שגיאה ביצירת משתמש:', error);
            return null;
        }
    }
    
    async updateUser(userId, updateData) {
        try {
            const user = await User.findOneAndUpdate(
                { userId: userId.toString() },
                updateData,
                { new: true }
            );
            
            if (user) {
                // עדכון קאש
                this.setCache(`user_${userId}`, user);
            }
            
            return user;
        } catch (error) {
            console.error('❌ שגיאה בעדכון משתמש:', error);
            return null;
        }
    }
    
    // =================================
    // 📋 פונקציות הזמנות
    // =================================
    
    async createOrder(orderData) {
        try {
            const order = new Order(orderData);
            await order.save();
            
            console.log(`✅ הזמנה חדשה נוצרה: ${order.orderNumber}`);
            
            // עדכון סטטיסטיקות בקאש
            this.clearCache(); // ניקוי קאש כדי לעדכן סטטיסטיקות
            
            return order;
        } catch (error) {
            console.error('❌ שגיאה ביצירת הזמנה:', error);
            return null;
        }
    }
    
    async findOrderByNumber(orderNumber) {
        const cacheKey = `order_${orderNumber}`;
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const order = await Order.findOne({ orderNumber: orderNumber.toUpperCase() });
            
            if (order) {
                this.setCache(cacheKey, order, 30 * 60 * 1000); // 30 דקות
            }
            
            return order;
        } catch (error) {
            console.error('❌ שגיאה בחיפוש הזמנה:', error);
            return null;
        }
    }
    
    async getUserOrders(userId, limit = 10) {
        const cacheKey = `user_orders_${userId}`;
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const orders = await Order.find({ 
                userId: userId.toString() 
            })
            .sort({ createdAt: -1 })
            .limit(limit);
            
            this.setCache(cacheKey, orders, 5 * 60 * 1000); // 5 דקות
            
            return orders;
        } catch (error) {
            console.error('❌ שגיאה בקבלת הזמנות משתמש:', error);
            return [];
        }
    }
    
    async updateOrderStatus(orderId, newStatus, note = '') {
        try {
            const order = await Order.findById(orderId);
            
            if (!order) {
                throw new Error('הזמנה לא נמצאה');
            }
            
            await order.updateStatus(newStatus, note);
            
            // ניקוי קאש רלוונטי
            this.cache.delete(`order_${order.orderNumber}`);
            this.cache.delete(`user_orders_${order.userId}`);
            
            console.log(`✅ סטטוס הזמנה ${order.orderNumber} עודכן ל-${newStatus}`);
            
            return order;
        } catch (error) {
            console.error('❌ שגיאה בעדכון סטטוס הזמנה:', error);
            return null;
        }
    }
    
    // =================================
    // 📊 סטטיסטיקות ודוחות
    // =================================
    
    async getDailyStats(date = new Date()) {
        const cacheKey = `daily_stats_${date.toDateString()}`;
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const stats = await Order.getDailyStats(date);
            
            this.setCache(cacheKey, stats, 60 * 60 * 1000); // שעה
            
            return stats[0] || {
                totalOrders: 0,
                totalRevenue: 0,
                avgOrderValue: 0,
                deliveredOrders: 0
            };
        } catch (error) {
            console.error('❌ שגיאה בקבלת סטטיסטיקות יומיות:', error);
            return null;
        }
    }
    
    async getTopUsers(limit = 10) {
        const cacheKey = `top_users_${limit}`;
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const users = await User.find({ isActive: true })
                .sort({ totalSpent: -1 })
                .limit(limit)
                .select('firstName totalOrders totalSpent isVip');
            
            this.setCache(cacheKey, users, 30 * 60 * 1000); // 30 דקות
            
            return users;
        } catch (error) {
            console.error('❌ שגיאה בקבלת משתמשים מובילים:', error);
            return [];
        }
    }
    
    async getActiveOrders() {
        const cacheKey = 'active_orders';
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        try {
            const orders = await Order.getActiveOrders();
            
            this.setCache(cacheKey, orders, 2 * 60 * 1000); // 2 דקות
            
            return orders;
        } catch (error) {
            console.error('❌ שגיאה בקבלת הזמנות פעילות:', error);
            return [];
        }
    }
    
    // =================================
    // 🔧 פונקציות עזר כלליות
    // =================================
    
    // יצירת גיבוי מהיר
    async createBackup() {
        try {
            const timestamp = new Date().toISOString().split('T')[0];
            
            const orders = await Order.find({}).sort({ createdAt: -1 }).limit(1000);
            const users = await User.find({}).sort({ createdAt: -1 }).limit(1000);
            
            const backup = {
                timestamp: new Date().toISOString(),
                orders: orders,
                users: users,
                stats: await this.getDailyStats()
            };
            
            console.log(`💾 גיבוי נוצר: ${orders.length} הזמנות, ${users.length} משתמשים`);
            
            return backup;
        } catch (error) {
            console.error('❌ שגיאה ביצירת גיבוי:', error);
            return null;
        }
    }
    
    // ניקוי נתונים ישנים
    async cleanOldData(daysToKeep = 180) {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
            
            // מחיקת הזמנות ישנות ומבוטלות
            const result = await Order.deleteMany({
                createdAt: { $lt: cutoffDate },
                status: 'cancelled'
            });
            
            console.log(`🧹 נוקו ${result.deletedCount} הזמנות ישנות`);
            
            return result.deletedCount;
        } catch (error) {
            console.error('❌ שגיאה בניקוי נתונים:', error);
            return 0;
        }
    }
    
    // בדיקת תקינות מסד הנתונים
    async healthCheck() {
        try {
            const isConnected = await this.checkConnection();
            
            if (!isConnected) {
                return { status: 'error', message: 'אין חיבור למסד הנתונים' };
            }
            
            const ordersCount = await Order.countDocuments();
            const usersCount = await User.countDocuments();
            const activeOrdersCount = await Order.countDocuments({ 
                status: { $in: ['pending', 'confirmed', 'preparing', 'ready', 'out_delivery'] }
            });
            
            return {
                status: 'healthy',
                connection: isConnected,
                orders: ordersCount,
                users: usersCount,
                activeOrders: activeOrdersCount,
                cacheSize: this.cache.size,
                uptime: process.uptime()
            };
        } catch (error) {
            return { 
                status: 'error', 
                message: error.message 
            };
        }
    }
}

// =================================
// 📤 Export
// =================================

const dbManager = new DatabaseManager();

module.exports = {
    DatabaseManager,
    dbManager,
    
    // פונקציות קיצור
    connect: () => dbManager.connect(),
    disconnect: () => dbManager.disconnect(),
    checkConnection: () => dbManager.checkConnection(),
    
    // משתמשים
    findUser: (userId) => dbManager.findUser(userId),
    createUser: (userData) => dbManager.createUser(userData),
    updateUser: (userId, updateData) => dbManager.updateUser(userId, updateData),
    
    // הזמנות
    createOrder: (orderData) => dbManager.createOrder(orderData),
    findOrderByNumber: (orderNumber) => dbManager.findOrderByNumber(orderNumber),
    getUserOrders: (userId, limit) => dbManager.getUserOrders(userId, limit),
    updateOrderStatus: (orderId, status, note) => dbManager.updateOrderStatus(orderId, status, note),
    
    // סטטיסטיקות
    getDailyStats: (date) => dbManager.getDailyStats(date),
    getTopUsers: (limit) => dbManager.getTopUsers(limit),
    getActiveOrders: () => dbManager.getActiveOrders(),
    
    // תחזוקה
    createBackup: () => dbManager.createBackup(),
    cleanOldData: (days) => dbManager.cleanOldData(days),
    healthCheck: () => dbManager.healthCheck()
};
