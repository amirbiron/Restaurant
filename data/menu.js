// 🍽️ תפריט המסעדה המלא - דאטה מובנית ונגישה
// עם פונקציות עזר ומערכת חיפוש

// =================================
// 📋 קטגוריות ופריטים
// =================================

const menuCategories = {
    starters: {
        name: '🥗 מנות פתיחה',
        description: 'מנות קלות לפתיחת הארוחה',
        items: [
            {
                id: 'hummus_classic',
                name: 'חומוס קלאסי',
                description: 'חומוס קרמי עם טחינה, ביצה קשה ופטרוזיליה',
                price: 18,
                emoji: '🧄',
                category: 'starters',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 5,
                calories: 250,
                ingredients: ['חומוס', 'טחינה', 'לימון', 'שמן זית', 'פטרוזיליה'],
                allergens: ['שומשום'],
                spiceLevel: 0,
                popular: true
            },
            {
                id: 'israeli_salad',
                name: 'סלט ישראלי',
                description: 'עגבניות, מלפפון, בצל ופטרוזיליה בחיתוך עדין',
                price: 22,
                emoji: '🥗',
                category: 'starters',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 10,
                calories: 80,
                ingredients: ['עגבניות', 'מלפפון', 'בצל', 'פטרוזיליה', 'לימון'],
                allergens: [],
                spiceLevel: 0
            },
            {
                id: 'falafel_plate',
                name: 'פלאפל (8 יח\')',
                description: 'כדורי פלאפל פריכים מבצק חומוס עם רוטב טחינה',
                price: 25,
                emoji: '🧆',
                category: 'starters',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: false,
                prepTime: 12,
                calories: 380,
                ingredients: ['חומוס', 'פטרוזיליה', 'כוסברה', 'בצל', 'שום'],
                allergens: ['גלוטן', 'שומשום'],
                spiceLevel: 1
            },
            {
                id: 'antipasti',
                name: 'אנטיפסטי מעורב',
                description: 'זיתים, גבינות, עגבניות מיובשות וקרקרים',
                price: 35,
                emoji: '🫒',
                category: 'starters',
                isVegetarian: true,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 8,
                calories: 420,
                ingredients: ['זיתים', 'גבינת עזים', 'עגבניות מיובשות', 'קרקרים'],
                allergens: ['גלוטן', 'חלב'],
                spiceLevel: 0
            },
            {
                id: 'soup_day',
                name: 'מרק היום',
                description: 'מרק טרי מוכן יומיומית (בירור טלפוני)',
                price: 20,
                emoji: '🍲',
                category: 'starters',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 3,
                calories: 150,
                ingredients: ['משתנה לפי היום'],
                allergens: ['עשוי להכיל גלוטן/חלב'],
                spiceLevel: 0
            }
        ]
    },
    
    mains: {
        name: '🍽️ מנות עיקריות',
        description: 'המנות המשביעות והטעימות שלנו',
        items: [
            {
                id: 'shawarma_laffa',
                name: 'שווארמה בלאפה',
                description: 'שווארמה עוף או טלה בלאפה עם סלטים וטחינה',
                price: 35,
                emoji: '🌯',
                category: 'mains',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 15,
                calories: 680,
                ingredients: ['לאפה', 'בשר עוף/טלה', 'סלטים', 'טחינה', 'פיקלס'],
                allergens: ['גלוטן', 'שומשום'],
                spiceLevel: 2,
                popular: true,
                options: ['עוף', 'טלה', 'מעורב']
            },
            {
                id: 'burger_classic',
                name: 'המבורגר קלאסי + צ\'יפס',
                description: 'המבורגר 200 גרם עם ירקות טריים וציפס ביתי',
                price: 45,
                emoji: '🍔',
                category: 'mains',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 20,
                calories: 850,
                ingredients: ['בשר בקר', 'לחמנייה', 'עגבנייה', 'חסה', 'בצל', 'ציפס'],
                allergens: ['גלוטן'],
                spiceLevel: 1,
                popular: true
            },
            {
                id: 'pizza_margherita',
                name: 'פיצה מרגריטה',
                description: 'פיצה איטלקית עם רוטב עגבניות, מוצרלה ובזיליקום',
                price: 52,
                emoji: '🍕',
                category: 'mains',
                isVegetarian: true,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 25,
                calories: 720,
                ingredients: ['בצק פיצה', 'רוטב עגבניות', 'מוצרלה', 'בזיליקום'],
                allergens: ['גלוטן', 'חלב'],
                spiceLevel: 0,
                size: 'אישית (30 ס"מ)'
            },
            {
                id: 'schnitzel_meal',
                name: 'שניצל + תוספות',
                description: 'שניצל עוף פריך עם פירה, אורז או צ\'יפס',
                price: 48,
                emoji: '🍗',
                category: 'mains',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 18,
                calories: 780,
                ingredients: ['חזה עוף', 'פירורי לחם', 'ביצה', 'קמח'],
                allergens: ['גלוטן', 'ביצים'],
                spiceLevel: 0,
                options: ['פירה', 'אורז', 'צ\'יפס']
            },
            {
                id: 'fish_grilled',
                name: 'דג ים צלוי',
                description: 'פילה דג טרי צלוי עם ירקות אדים ואורז',
                price: 58,
                emoji: '🐟',
                category: 'mains',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: true,
                prepTime: 22,
                calories: 520,
                ingredients: ['פילה דג ים', 'ירקות עונתיים', 'אורז', 'לימון'],
                allergens: ['דגים'],
                spiceLevel: 1
            },
            {
                id: 'pasta_carbonara',
                name: 'פסטה קרבונרה',
                description: 'פסטה פטוצ\'יני ברוטב קרם עם בייקון ופרמזן',
                price: 42,
                emoji: '🍝',
                category: 'mains',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 16,
                calories: 680,
                ingredients: ['פסטה', 'בייקון', 'קרם', 'פרמזן', 'ביצה'],
                allergens: ['גלוטן', 'חלב', 'ביצים'],
                spiceLevel: 0
            }
        ]
    },
    
    drinks: {
        name: '🥤 משקאות',
        description: 'משקאות קרים וחמים למשב כל הצמא',
        items: [
            {
                id: 'cola_can',
                name: 'קוקה קולה',
                description: 'פחית 330 מ"ל קרה',
                price: 8,
                emoji: '🥤',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 1,
                calories: 140,
                ingredients: ['מים מוגזים', 'סוכר', 'תמצית קולה'],
                allergens: [],
                spiceLevel: 0,
                temperature: 'קר',
                size: '330 מ"ל'
            },
            {
                id: 'orange_juice',
                name: 'מיץ תפוזים טבעי',
                description: 'מיץ תפוזים טרי סחוט',
                price: 12,
                emoji: '🧃',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 3,
                calories: 110,
                ingredients: ['תפוזים טריים'],
                allergens: [],
                spiceLevel: 0,
                temperature: 'קר',
                size: '250 מ"ל'
            },
            {
                id: 'coffee_black',
                name: 'קפה שחור',
                description: 'קפה איכותי חם וארומטי',
                price: 10,
                emoji: '☕',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 5,
                calories: 5,
                ingredients: ['פולי קפה', 'מים'],
                allergens: [],
                spiceLevel: 0,
                temperature: 'חם',
                caffeine: true
            },
            {
                id: 'beer_goldstar',
                name: 'בירה גולדסטאר',
                description: 'בירה ישראלית 500 מ"ל',
                price: 18,
                emoji: '🍺',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: false,
                prepTime: 1,
                calories: 210,
                ingredients: ['מים', 'לתת', 'כשות'],
                allergens: ['גלוטן'],
                spiceLevel: 0,
                temperature: 'קר',
                size: '500 מ"ל',
                alcohol: true,
                minAge: 18
            },
            {
                id: 'lemonade',
                name: 'לימונדה ביתית',
                description: 'לימונדה טרייה עם נענע ופריכות לימון',
                price: 14,
                emoji: '🍋',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 5,
                calories: 95,
                ingredients: ['לימון', 'סוכר', 'מים', 'נענע', 'קרח'],
                allergens: [],
                spiceLevel: 0,
                temperature: 'קר'
            },
            {
                id: 'tea_mint',
                name: 'תה נענע',
                description: 'תה נענע חם ומרגיע',
                price: 8,
                emoji: '🍵',
                category: 'drinks',
                isVegetarian: true,
                isVegan: true,
                isGlutenFree: true,
                prepTime: 7,
                calories: 0,
                ingredients: ['עלי נענע', 'מים חמים'],
                allergens: [],
                spiceLevel: 0,
                temperature: 'חם'
            }
        ]
    },
    
    desserts: {
        name: '🍰 קינוחים',
        description: 'קינוחים מתוקים לסיום מושלם',
        items: [
            {
                id: 'tiramisu',
                name: 'טירמיסו איטלקי',
                description: 'קינוח שכבות עם קרם מסקרפונה וקפה',
                price: 28,
                emoji: '🍰',
                category: 'desserts',
                isVegetarian: true,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 5,
                calories: 450,
                ingredients: ['מסקרפונה', 'ביצים', 'סוכר', 'קפה', 'ליידי פינגרס'],
                allergens: ['חלב', 'ביצים', 'גלוטן'],
                spiceLevel: 0,
                popular: true
            },
            {
                id: 'chocolate_souffle',
                name: 'סופלה שוקולד',
                description: 'סופלה שוקולד חמה עם גלידת וניל',
                price: 32,
                emoji: '🍫',
                category: 'desserts',
                isVegetarian: true,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 20,
                calories: 520,
                ingredients: ['שוקולד מריר', 'ביצים', 'סוכר', 'קמח', 'חמאה'],
                allergens: ['חלב', 'ביצים', 'גלוטן'],
                spiceLevel: 0,
                temperature: 'חם'
            },
            {
                id: 'ice_cream',
                name: 'גלידה (3 כדורים)',
                description: 'בחירה מטעמים: וניל, שוקולד, תות',
                price: 18,
                emoji: '🍨',
                category: 'desserts',
                isVegetarian: true,
                isVegan: false,
                isGlutenFree: true,
                prepTime: 3,
                calories: 280,
                ingredients: ['חלב', 'קרם', 'סוכר', 'טעמים טבעיים'],
                allergens: ['חלב'],
                spiceLevel: 0,
                temperature: 'קר',
                options: ['וניל', 'שוקולד', 'תות', 'פיסטוק']
            }
        ]
    },
    
    specials: {
        name: '🔥 המומלצים שלנו',
        description: 'המנות המיוחדות והפופולריות ביותר',
        items: [
            {
                id: 'chef_special',
                name: 'מנת השף המיוחדת',
                description: 'מנה מיוחדת משתנה שבועית - בירור טלפוני',
                price: 65,
                emoji: '👨‍🍳',
                category: 'specials',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 30,
                calories: 0, // משתנה
                ingredients: ['משתנה שבועית'],
                allergens: ['בירור טלפוני'],
                spiceLevel: 0,
                popular: true,
                limited: true
            },
            {
                id: 'combo_family',
                name: 'קומבו משפחתי',
                description: 'שווארמה + המבורגר + פיצה + 4 משקאות + קינוח',
                price: 120,
                emoji: '👨‍👩‍👧‍👦',
                category: 'specials',
                isVegetarian: false,
                isVegan: false,
                isGlutenFree: false,
                prepTime: 25,
                calories: 2800,
                ingredients: ['ראה מנות נפרדות'],
                allergens: ['גלוטן', 'חלב', 'ביצים'],
                spiceLevel: 1,
                servings: 4,
                popular: true,
                discount: 25 // הנחה של 25₪
            }
        ]
    }
};

// =================================
// 🏷️ תגיות ומאפיינים מיוחדים
// =================================

const specialTags = {
    popular: '🔥 פופולרי',
    new: '🆕 חדש',
    vegan: '🌱 טבעוני',
    vegetarian: '🥬 צמחוני',
    glutenFree: '🚫 ללא גלוטן',
    spicy: '🌶️ חריף',
    healthy: '💪 בריא',
    kids: '👶 לילדים',
    alcohol: '🔞 +18'
};

// =================================
// 📊 פונקציות עזר
// =================================

class MenuManager {
    constructor() {
        this.categories = menuCategories;
        this.cache = new Map();
    }
    
    // קבלת כל הקטגוריות
    getAllCategories() {
        return Object.keys(this.categories);
    }
    
    // קבלת שם קטגוריה
    getCategoryName(categoryId) {
        return this.categories[categoryId]?.name || 'קטגוריה לא ידועה';
    }
    
    // קבלת פריטי קטגוריה
    getCategory(categoryId) {
        return this.categories[categoryId]?.items || [];
    }
    
    // קבלת פריט ספציפי
    getItem(categoryId, itemIndex) {
        const items = this.getCategory(categoryId);
        return items[itemIndex] || null;
    }
    
    // קבלת פריט לפי ID
    getItemById(itemId) {
        for (const category of Object.values(this.categories)) {
            const item = category.items.find(item => item.id === itemId);
            if (item) return item;
        }
        return null;
    }
    
    // חיפוש פריטים
    search(query, filters = {}) {
        const results = [];
        const searchTerm = query.toLowerCase();
        
        for (const [categoryId, category] of Object.entries(this.categories)) {
            for (const item of category.items) {
                // חיפוש טקסט
                const matchesText = 
                    item.name.toLowerCase().includes(searchTerm) ||
                    item.description.toLowerCase().includes(searchTerm) ||
                    item.ingredients.some(ing => ing.toLowerCase().includes(searchTerm));
                
                if (!matchesText) continue;
                
                // פילטרים
                let matchesFilters = true;
                
                if (filters.vegetarian && !item.isVegetarian) matchesFilters = false;
                if (filters.vegan && !item.isVegan) matchesFilters = false;
                if (filters.glutenFree && !item.isGlutenFree) matchesFilters = false;
                if (filters.maxPrice && item.price > filters.maxPrice) matchesFilters = false;
                if (filters.minPrice && item.price < filters.minPrice) matchesFilters = false;
                if (filters.category && categoryId !== filters.category) matchesFilters = false;
                
                if (matchesFilters) {
                    results.push({
                        ...item,
                        categoryId,
                        categoryName: category.name
                    });
                }
            }
        }
        
        return results;
    }
    
    // קבלת פריטים פופולריים
    getPopularItems(limit = 5) {
        const popular = [];
        
        for (const [categoryId, category] of Object.entries(this.categories)) {
            for (const item of category.items) {
                if (item.popular) {
                    popular.push({
                        ...item,
                        categoryId,
                        categoryName: category.name
                    });
                }
            }
        }
        
        return popular.slice(0, limit);
    }
    
    // קבלת פריטים לפי טווח מחירים
    getItemsByPriceRange(min, max) {
        const results = [];
        
        for (const [categoryId, category] of Object.entries(this.categories)) {
            for (const item of category.items) {
                if (item.price >= min && item.price <= max) {
                    results.push({
                        ...item,
                        categoryId,
                        categoryName: category.name
                    });
                }
            }
        }
        
        return results.sort((a, b) => a.price - b.price);
    }
    
    // קבלת פריטים צמחוניים/טבעוניים
    getVegetarianItems(veganOnly = false) {
        const results = [];
        
        for (const [categoryId, category] of Object.entries(this.categories)) {
            for (const item of category.items) {
                const isValid = veganOnly ? item.isVegan : item.isVegetarian;
                if (isValid) {
                    results.push({
                        ...item,
                        categoryId,
                        categoryName: category.name
                    });
                }
            }
        }
        
        return results;
    }
    
    // סטטיסטיקות תפריט
    getMenuStats() {
        let totalItems = 0;
        let totalVegetarian = 0;
        let totalVegan = 0;
        let totalGlutenFree = 0;
        let avgPrice = 0;
        let priceSum = 0;
        
        for (const category of Object.values(this.categories)) {
            for (const item of category.items) {
                totalItems++;
                priceSum += item.price;
                if (item.isVegetarian) totalVegetarian++;
                if (item.isVegan) totalVegan++;
                if (item.isGlutenFree) totalGlutenFree++;
            }
        }
        
        avgPrice = Math.round(priceSum / totalItems);
        
        return {
            totalItems,
            totalCategories: Object.keys(this.categories).length,
            totalVegetarian,
            totalVegan,
            totalGlutenFree,
            avgPrice,
            priceRange: {
                min: Math.min(...this.getAllItems().map(item => item.price)),
                max: Math.max(...this.getAllItems().map(item => item.price))
            }
        };
    }
    
    // קבלת כל הפריטים
    getAllItems() {
        const allItems = [];
        
        for (const [categoryId, category] of Object.entries(this.categories)) {
            for (const item of category.items) {
                allItems.push({
                    ...item,
                    categoryId,
                    categoryName: category.name
                });
            }
        }
        
        return allItems;
    }
    
    // המלצות לפי העדפות משתמש
    getRecommendations(userPreferences = {}) {
        const allItems = this.getAllItems();
        let scored = [];
        
        for (const item of allItems) {
            let score = 0;
            
            // ניקוד בסיסי
            if (item.popular) score += 3;
            if (item.price <= 30) score += 2; // פריטים זולים יותר
            
            // ניקוד לפי העדפות
            if (userPreferences.vegetarian && item.isVegetarian) score += 5;
            if (userPreferences.vegan && item.isVegan) score += 5;
            if (userPreferences.glutenFree && item.isGlutenFree) score += 3;
            if (userPreferences.spicy && item.spiceLevel > 1) score += 2;
            if (userPreferences.healthy && item.calories < 400) score += 2;
            
            // העדפות קטגוריה
            if (userPreferences.favoriteCategories?.includes(item.categoryId)) {
                score += 3;
            }
            
            scored.push({ ...item, score });
        }
        
        return scored
            .sort((a, b) => b.score - a.score)
            .slice(0, 6);
    }
    
    // פורמט מחיר
    formatPrice(price) {
        return `₪${price}`;
    }
    
    // יצירת תגיות לפריט
    getItemTags(item) {
        const tags = [];
        
        if (item.popular) tags.push(specialTags.popular);
        if (item.isVegan) tags.push(specialTags.vegan);
        else if (item.isVegetarian) tags.push(specialTags.vegetarian);
        if (item.isGlutenFree) tags.push(specialTags.glutenFree);
        if (item.spiceLevel > 2) tags.push(specialTags.spicy);
        if (item.alcohol) tags.push(specialTags.alcohol);
        if (item.calories < 300) tags.push(specialTags.healthy);
        
        return tags;
    }
}

// =================================
// 📤 Export
// =================================

const menuManager = new MenuManager();

module.exports = {
    menuCategories,
    specialTags,
    menuManager,
    
    // פונקציות קיצור
    getCategory: (categoryId) => menuManager.getCategory(categoryId),
    getItem: (categoryId, itemIndex) => menuManager.getItem(categoryId, itemIndex),
    getCategoryName: (categoryId) => menuManager.getCategoryName(categoryId),
    search: (query, filters) => menuManager.search(query, filters),
    getPopularItems: (limit) => menuManager.getPopularItems(limit),
    getRecommendations: (preferences) => menuManager.getRecommendations(preferences)
};
