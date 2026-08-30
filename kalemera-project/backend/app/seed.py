import asyncio
import os
import sys
from PIL import Image, ImageDraw

# Add app directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import AsyncSessionLocal, engine, Base
from app.models import User, UserRole, Category, Product, ProductVariant
from app.security import get_password_hash


from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

def create_compressed_placeholder(filename: str, label: str, bg_color: str) -> str:
    """Generates a compressed placeholder image using Pillow if directory is writable."""
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            img = Image.new("RGB", (400, 300), color=bg_color)
            draw = ImageDraw.Draw(img)
            draw.text((20, 130), label, fill="white")
            img.save(file_path, "JPEG", quality=75, optimize=True)
    except Exception:
        pass

    return f"/uploads/{filename}"


CATEGORIES_TO_SEED = [
    "Pizza",
    "Crepe",
    "Burgers",
    "Meals",
    "Salads",
    "Rice & Pasta",
    "Chicken Sandwiches",
    "Meat Sandwiches",
    "Sauces",
    "Potato",
    "Drinks",
    "Market"
]

# Products List
PRODUCTS_DATA = [
            # ==== 1. PIZZA (16 items) ====
            {
                "name": "Margherita Pizza - مارجريتا",
                "description": "صلصة كالميرا المميزة، جبنة موتزاريلا، زعتر / Kalmera special sauce, mozzarella cheese, oregano.",
                "price": 0.0,
                "stock": 50,
                "category": "Pizza",
                "img_filename": "pizza_margherita.jpg",
                "img_label": "Margherita Pizza",
                "img_color": "#D32F2F",
                "variants": [("S", 110.0), ("L", 130.0)]
            },
            {
                "name": "Crispy Pizza - كرسبي",
                "description": "قطع الدجاج المقرمش، فلفل، زيتون، موتزاريلا / Crispy chicken pieces, pepper, olives, mozzarella.",
                "price": 0.0,
                "stock": 40,
                "category": "Pizza",
                "img_filename": "pizza_crispy.jpg",
                "img_label": "Crispy Pizza",
                "img_color": "#FF9800",
                "variants": [("S", 140.0), ("L", 180.0)]
            },
            {
                "name": "Vegetables Pizza - خضار",
                "description": "طماطم، فلفل أخضر، زيتون، بصل، مشروم، موتزاريلا / Tomatoes, green pepper, olives, onion, mushroom, mozzarella.",
                "price": 0.0,
                "stock": 45,
                "category": "Pizza",
                "img_filename": "pizza_veg.jpg",
                "img_label": "Veg Pizza",
                "img_color": "#4CAF50",
                "variants": [("S", 115.0), ("L", 150.0)]
            },
            {
                "name": "Mushroom Pizza - مشروم",
                "description": "مشروم فريش، صلصة، جبنة موتزاريلا / Fresh mushroom, tomato sauce, mozzarella cheese.",
                "price": 0.0,
                "stock": 35,
                "category": "Pizza",
                "img_filename": "pizza_mushroom.jpg",
                "img_label": "Mushroom Pizza",
                "img_color": "#795548",
                "variants": [("S", 130.0), ("L", 170.0)]
            },
            {
                "name": "Chicken Pizza - فراخ",
                "description": "قطع فراخ متبلة، صلصة، جبنة موتزاريلا / Marinated chicken chunks, sauce, mozzarella.",
                "price": 0.0,
                "stock": 30,
                "category": "Pizza",
                "img_filename": "pizza_chicken.jpg",
                "img_label": "Chicken Pizza",
                "img_color": "#FFC107",
                "variants": [("S", 140.0), ("L", 180.0)]
            },
            {
                "name": "BBQ Chicken Pizza - بركيو",
                "description": "قطع فراخ، صوص باربيكيو، موتزاريلا / Chicken pieces, BBQ sauce, mozzarella.",
                "price": 0.0,
                "stock": 30,
                "category": "Pizza",
                "img_filename": "pizza_bbq.jpg",
                "img_label": "BBQ Pizza",
                "img_color": "#D84315",
                "variants": [("S", 145.0), ("L", 185.0)]
            },
            {
                "name": "Shrimp Pizza - جمبري",
                "description": "جمبري وسط متبل بخلطة كالميرا، موتزاريلا / Shrimp seasoned with Kalmera spices, mozzarella.",
                "price": 0.0,
                "stock": 20,
                "category": "Pizza",
                "img_filename": "pizza_shrimp.jpg",
                "img_label": "Shrimp Pizza",
                "img_color": "#FF5722",
                "variants": [("S", 200.0), ("L", 300.0)]
            },
            {
                "name": "Chicken Ranch Pizza - تشيكن رانش",
                "description": "قطع فراخ، صوص رانش كريمي، موتزاريلا / Chicken pieces, creamy Ranch sauce, mozzarella.",
                "price": 0.0,
                "stock": 30,
                "category": "Pizza",
                "img_filename": "pizza_ranch.jpg",
                "img_label": "Ranch Pizza",
                "img_color": "#0097A7",
                "variants": [("S", 145.0), ("L", 185.0)]
            },
            {
                "name": "Pastrami Pizza - بسطرمة",
                "description": "بسطرمة ممتازة، فلفل، زيتون، موتزاريلا / Premium pastrami, peppers, olives, mozzarella.",
                "price": 0.0,
                "stock": 25,
                "category": "Pizza",
                "img_filename": "pizza_pastrami.jpg",
                "img_label": "Pastrami Pizza",
                "img_color": "#880E4F",
                "variants": [("S", 160.0), ("L", 200.0)]
            },
            {
                "name": "Mix Cheese Pizza - ميكس جبن",
                "description": "موتزاريلا، شيدر، رومي، كيري / Mozzarella, cheddar, roumy, kiri cheese mix.",
                "price": 0.0,
                "stock": 35,
                "category": "Pizza",
                "img_filename": "pizza_mixcheese.jpg",
                "img_label": "Mix Cheese",
                "img_color": "#FFD54F",
                "variants": [("S", 140.0), ("L", 180.0)]
            },
            {
                "name": "Four Seasons Pizza - فورسيزون",
                "description": "أربعة أقسام متنوعة من إضافات كالميرا المميزة / Four sections with distinct toppings.",
                "price": 0.0,
                "stock": 30,
                "category": "Pizza",
                "img_filename": "pizza_fourseasons.jpg",
                "img_label": "Four Seasons",
                "img_color": "#689F38",
                "variants": [("S", 160.0), ("L", 200.0)]
            },
            {
                "name": "Kalmera Pizza - كالميرا",
                "description": "خلطة كالميرا الخاصة من اللحوم والخضار والجبن / Special Kalmera mix of meats, veggies, cheese.",
                "price": 0.0,
                "stock": 25,
                "category": "Pizza",
                "img_filename": "pizza_kalmera.jpg",
                "img_label": "Kalmera Pizza",
                "img_color": "#795548",
                "variants": [("S", 160.0), ("L", 200.0)]
            },
            {
                "name": "Tuna Pizza - تونة",
                "description": "قطع تونة مفتتة، بصل، فلفل، زيتون، موتزاريلا / Tuna chunks, onions, peppers, olives, mozzarella.",
                "price": 0.0,
                "stock": 25,
                "category": "Pizza",
                "img_filename": "pizza_tuna.jpg",
                "img_label": "Tuna Pizza",
                "img_color": "#00ACC1",
                "variants": [("S", 180.0), ("L", 200.0)]
            },
            {
                "name": "Shish Tawook Pizza - شيش طاوق",
                "description": "قطع شيش طاووق مشوي، فلفل، زيتون، موتزاريلا / Grilled shish tawook chunks, olives, mozzarella.",
                "price": 0.0,
                "stock": 30,
                "category": "Pizza",
                "img_filename": "pizza_shish.jpg",
                "img_label": "Shish Pizza",
                "img_color": "#E65100",
                "variants": [("S", 145.0), ("L", 185.0)]
            },
            {
                "name": "Hot Dog Pizza - هوت دوج",
                "description": "قطع هوت دوج فرانكفورتر، خضروات، موتزاريلا / Frankfurter hot dog chunks, veggies, mozzarella.",
                "price": 0.0,
                "stock": 35,
                "category": "Pizza",
                "img_filename": "pizza_hotdog.jpg",
                "img_label": "Hot Dog Pizza",
                "img_color": "#BF360C",
                "variants": [("S", 134.0), ("L", 170.0)]
            },
            {
                "name": "Sausage Pizza - سجق",
                "description": "سجق بلدي متبل بخلطة كالميرا، موتزاريلا / Traditional seasoned sausage, mozzarella.",
                "price": 0.0,
                "stock": 35,
                "category": "Pizza",
                "img_filename": "pizza_sausage.jpg",
                "img_label": "Sausage Pizza",
                "img_color": "#3E2723",
                "variants": [("S", 130.0), ("L", 170.0)]
            },

            # ==== 2. CREPE (12 items) ====
            {
                "name": "Potato Crepe - بطاطس",
                "description": "بطاطس مقرمشة، كاتشب، مايونيز، موتزاريلا / Crispy potatoes, ketchup, mayonnaise, mozzarella.",
                "price": 70.0,
                "stock": 60,
                "category": "Crepe",
                "img_filename": "crepe_potato.jpg",
                "img_label": "Potato Crepe",
                "img_color": "#FFEB3B"
            },
            {
                "name": "Shawarma Crepe - شاورمة",
                "description": "شاورما دجاج أو لحم مع التومية والموتزاريلا / Chicken or beef shawarma, garlic dip, mozzarella.",
                "price": 120.0,
                "stock": 40,
                "category": "Crepe",
                "img_filename": "crepe_shawarma.jpg",
                "img_label": "Shawarma Crepe",
                "img_color": "#F57C00"
            },
            {
                "name": "Pane Crepe - بانية",
                "description": "قطع فراخ بانيه مقرمشة، كاتشب، مايونيز، موتزاريلا / Crispy chicken pane chunks, mozzarella.",
                "price": 110.0,
                "stock": 40,
                "category": "Crepe",
                "img_filename": "crepe_pane.jpg",
                "img_label": "Pane Crepe",
                "img_color": "#FFB300"
            },
            {
                "name": "Cordon Bleu Crepe - كوردن بلو",
                "description": "كوردن بلو دجاج غني بجبن الموتزاريلا / Chicken cordon bleu, mozzarella, sauces.",
                "price": 120.0,
                "stock": 35,
                "category": "Crepe",
                "img_filename": "crepe_cordon.jpg",
                "img_label": "Cordon Bleu Crepe",
                "img_color": "#FF5722"
            },
            {
                "name": "Crispy Crepe - كرسبي",
                "description": "قطع دجاج مقرمش مميز مع الجبن والبطاطس / Crispy chicken chunks, cheese, sauces.",
                "price": 110.0,
                "stock": 50,
                "category": "Crepe",
                "img_filename": "crepe_crispy.jpg",
                "img_label": "Crispy Crepe",
                "img_color": "#FF9800"
            },
            {
                "name": "Shish Tawook Crepe - شيش طاوق",
                "description": "قطع شيش طاووق مشوي، فلفل ألوان، موتزاريلا / Grilled shish tawook, bell peppers, mozzarella.",
                "price": 120.0,
                "stock": 40,
                "category": "Crepe",
                "img_filename": "crepe_shish.jpg",
                "img_label": "Shish Crepe",
                "img_color": "#FB8C00"
            },
            {
                "name": "Fajita Crepe - فاهيتا",
                "description": "قطع فراخ فاهيتا، بصل، فلفل ألوان، موتزاريلا / Chicken fajita mix, peppers, onions, mozzarella.",
                "price": 120.0,
                "stock": 35,
                "category": "Crepe",
                "img_filename": "crepe_fajita.jpg",
                "img_label": "Fajita Crepe",
                "img_color": "#F4511E"
            },
            {
                "name": "Burger Crepe - برجر",
                "description": "قطع برجر لحم بلدي، كاتشب، مايونيز، موتزاريلا / Beef burger patty chunks, sauces, mozzarella.",
                "price": 110.0,
                "stock": 40,
                "category": "Crepe",
                "img_filename": "crepe_burger.jpg",
                "img_label": "Burger Crepe",
                "img_color": "#4E342E"
            },
            {
                "name": "Hot Dog Crepe - هوت دوج",
                "description": "قطع هوت دوج، كاتشب، مايونيز، موتزاريلا / Frankfurter hot dog chunks, mozzarella.",
                "price": 110.0,
                "stock": 45,
                "category": "Crepe",
                "img_filename": "crepe_hotdog.jpg",
                "img_label": "Hot Dog Crepe",
                "img_color": "#D84315"
            },
            {
                "name": "Mix Cheese Crepe - ميكس جبن",
                "description": "تشكيلة من الجبن السائحة اللذيذة / Selected melted cheese mix.",
                "price": 110.0,
                "stock": 50,
                "category": "Crepe",
                "img_filename": "crepe_mixcheese.jpg",
                "img_label": "Mix Cheese Crepe",
                "img_color": "#FDD835"
            },
            {
                "name": "Mix Chicken Crepe - ميكس تشكين",
                "description": "بانيه، كرسبي، شيش، زنجر، موتزاريلا / Pane, crispy, shish, zinger chicken mix, mozzarella.",
                "price": 130.0,
                "stock": 35,
                "category": "Crepe",
                "img_filename": "crepe_mixchicken.jpg",
                "img_label": "Mix Chicken Crepe",
                "img_color": "#FFA000"
            },
            {
                "name": "Mix Meat Crepe - ميكس لحوم",
                "description": "برجر، هوت دوج، سجق بلدي، موتزاريلا / Burger, hot dog, sausage mix, mozzarella.",
                "price": 130.0,
                "stock": 35,
                "category": "Crepe",
                "img_filename": "crepe_mixmeat.jpg",
                "img_label": "Mix Meat Crepe",
                "img_color": "#5D4037"
            },

            # ==== 3. BURGERS (2 items) ====
            {
                "name": "Jumbo Burger 225g - برجر جامبو ٢٢٥ جم",
                "description": "برجر لحم بلدي مشوي، طماطم، خس، خيار مخلل، صوص بيج تيستي / Grilled premium beef patty, tomato, lettuce, pickles, Big Tasty sauce.",
                "price": 120.0,
                "stock": 35,
                "category": "Burgers",
                "img_filename": "sand_burger_jumbo.jpg",
                "img_label": "Jumbo Burger",
                "img_color": "#3E2723"
            },
            {
                "name": "Jumbo Burger 125g - برجر جامبو ١٢٥ جم",
                "description": "برجر لحم بلدي مشوي صغير / Small grilled premium beef patty.",
                "price": 90.0,
                "stock": 35,
                "category": "Burgers",
                "img_filename": "sand_burger_small.jpg",
                "img_label": "Small Burger",
                "img_color": "#4E342E"
            },

            # ==== 4. CHICKEN SANDWICHES (13 items) ====
            {
                "name": "Grilled Chicken Sandwich - تشيكن جريل",
                "description": "صدور دجاج مشوية متبلة، خس، خيار مخلل، تومية / Marinated grilled chicken breast, lettuce, pickles, garlic sauce.",
                "price": 90.0,
                "stock": 40,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_grilled_chicken.jpg",
                "img_label": "Grilled Chicken",
                "img_color": "#FFC107"
            },
            {
                "name": "Cordon Bleu Chicken Sandwich - كوردن بلو",
                "description": "رول دجاج محشي جبنة ولحم مدخن مقرمش / Stuffed chicken breast roll with cheese and smoked meat.",
                "price": 120.0,
                "stock": 30,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_cordon.jpg",
                "img_label": "Cordon Bleu Sandwich",
                "img_color": "#FF7043"
            },
            {
                "name": "Chicken Pane Sandwich - تشيكن بانية",
                "description": "صدور دجاج بانيه مقرمشة، خس، كاتشب، مايونيز / Crispy chicken pane, lettuce, ketchup, mayo.",
                "price": 95.0,
                "stock": 45,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_pane.jpg",
                "img_label": "Chicken Pane",
                "img_color": "#FFB300"
            },
            {
                "name": "Chicken Fajita Sandwich - تشيكن فاهيتا",
                "description": "قطع فراخ فاهيتا، بصل، فلفل ألوان، بهارات فاهيتا / Chicken fajita chunks, peppers, onions, fajita seasoning.",
                "price": 95.0,
                "stock": 40,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_fajita.jpg",
                "img_label": "Chicken Fajita",
                "img_color": "#FF5722"
            },
            {
                "name": "Chicken Crispy Sandwich - تشيكن كرسبي",
                "description": "قطع صدور دجاج كرسبي حارة ومقرمشة / Spicy crispy chicken strips, lettuce, mayo.",
                "price": 95.0,
                "stock": 50,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_crispy.jpg",
                "img_label": "Chicken Crispy",
                "img_color": "#FFA000"
            },
            {
                "name": "Shish Tawook Sandwich - شيش طاوق",
                "description": "شيش طاووق مشوي على الفحم، فلفل ألوان، تومية / Charcoal-grilled shish tawook, bell peppers, garlic sauce.",
                "price": 100.0,
                "stock": 45,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_shish.jpg",
                "img_label": "Shish Sandwich",
                "img_color": "#F57C00"
            },
            {
                "name": "Crispy + Fries Sandwich - كرسبي + بطاطس",
                "description": "صدور دجاج كرسبي مقرمشة مع بطاطس مقلية داخل الساندوتش / Crispy chicken strips with French fries inside.",
                "price": 110.0,
                "stock": 40,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_crispy_fries.jpg",
                "img_label": "Crispy + Fries",
                "img_color": "#FBC02D"
            },
            {
                "name": "Chicken Roll Sandwich - تشيكن رول",
                "description": "دجاج مفروم رول محشي خضروات وجبن / Ground chicken roll stuffed with veggies and cheese.",
                "price": 100.0,
                "stock": 30,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_roll.jpg",
                "img_label": "Chicken Roll",
                "img_color": "#FFCC80"
            },
            {
                "name": "Smoked Chicken Sandwich - فراخ مدخن",
                "description": "شرائح دجاج مدخن، جبنة شيدر، خس، مايونيز / Smoked chicken slices, cheddar, lettuce, mayo.",
                "price": 90.0,
                "stock": 35,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_smoked.jpg",
                "img_label": "Smoked Chicken",
                "img_color": "#EF6C00"
            },
            {
                "name": "Chicken Mushroom Sandwich - تشيكن مشروم",
                "description": "صدور دجاج بصوص المشروم الكريمي الغني / Chicken breast topped with rich creamy mushroom sauce.",
                "price": 100.0,
                "stock": 35,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_mushroom_chicken.jpg",
                "img_label": "Chicken Mushroom",
                "img_color": "#8D6E63"
            },
            {
                "name": "Chicken Shawarma Sandwich - شاورمة فراخ",
                "description": "شاورما دجاج متبلة بخلطة كالميرا، خيار مخلل، تومية / Seasoned chicken shawarma, pickles, garlic sauce.",
                "price": 95.0,
                "stock": 50,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_ch_shawarma.jpg",
                "img_label": "Chicken Shawarma",
                "img_color": "#FFA726"
            },
            {
                "name": "Italian Chicken Sandwich - تشيكن إيطاليين",
                "description": "صدور دجاج، جبنة موتزاريلا سايحة، صوص إيطالي مميز / Chicken breast, melted mozzarella, special Italian sauce.",
                "price": 110.0,
                "stock": 30,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_italian.jpg",
                "img_label": "Italian Chicken",
                "img_color": "#388E3C"
            },
            {
                "name": "Chicken Zinger Sandwich - تشيكن زنجر",
                "description": "صدور دجاج حارة مقرمشة، خس، مايونيز، شيدر / Spicy crispy chicken breast, lettuce, mayo, cheddar cheese.",
                "price": 120.0,
                "stock": 50,
                "category": "Chicken Sandwiches",
                "img_filename": "sand_zinger.jpg",
                "img_label": "Zinger Sandwich",
                "img_color": "#E65100"
            },

            # ==== 5. MEAT SANDWICHES (6 items) ====
            {
                "name": "Barma Meat Sandwich - لحوم برمة",
                "description": "قطع لحم مفروم متبل ومطبوخ على الطريقة الخاصة / Seasoned minced beef cooked in special traditional style.",
                "price": 70.0,
                "stock": 45,
                "category": "Meat Sandwiches",
                "img_filename": "sand_barma.jpg",
                "img_label": "Barma Meat",
                "img_color": "#4E342E"
            },
            {
                "name": "Alexandrian Liver Sandwich - كبدة إسكندراني",
                "description": "كبدة بلدي مشوحة مع الفلفل الحار والليمون والبهارات / Spiced Alexandrian-style beef liver with chili and lemon.",
                "price": 70.0,
                "stock": 60,
                "category": "Meat Sandwiches",
                "img_filename": "sand_liver.jpg",
                "img_label": "Liver Sandwich",
                "img_color": "#5D4037"
            },
            {
                "name": "Baladi Sausage Sandwich - سجق بلدي",
                "description": "سجق بلدي مشوح مع البصل والفلفل والطماطم والبهارات / Stir-fried traditional sausage with peppers and onions.",
                "price": 70.0,
                "stock": 50,
                "category": "Meat Sandwiches",
                "img_filename": "sand_sausage.jpg",
                "img_label": "Baladi Sausage",
                "img_color": "#8D6E63"
            },
            {
                "name": "Kofta Sandwich - كفتة",
                "description": "أصابع كفتة لحم بلدي مشوية على الفحم مع البقدونس والطحينة / Charcoal-grilled beef kofta with parsley and tahini.",
                "price": 90.0,
                "stock": 45,
                "category": "Meat Sandwiches",
                "img_filename": "sand_kofta.jpg",
                "img_label": "Kofta Sandwich",
                "img_color": "#3E2723"
            },
            {
                "name": "Hot Dog Sandwich - هوت دوج",
                "description": "هوت دوج مشوي مع البصل والفلفل وصوص الكاتشب والمايونيز / Grilled hot dog with peppers, onions, ketchup, mayo.",
                "price": 90.0,
                "stock": 50,
                "category": "Meat Sandwiches",
                "img_filename": "sand_hotdog.jpg",
                "img_label": "Hot Dog Sandwich",
                "img_color": "#D84315"
            },
            {
                "name": "Mix Liver Sandwich - ميكس كبدة",
                "description": "تشكيلة كبدة بلدي مع السجق والبهارات / Special mix of beef liver and traditional sausage.",
                "price": 80.0,
                "stock": 40,
                "category": "Meat Sandwiches",
                "img_filename": "sand_mix_liver.jpg",
                "img_label": "Mix Liver",
                "img_color": "#5D4037"
            },

            # ==== 6. MEALS (12 items) ====
            {
                "name": "Quarter Chicken Meal - ربع فرخة",
                "description": "ربع فرخة مشوية على الفحم، تقدم مع: أرز + عيش + طحينة + بطاطس / Charcoal-grilled quarter chicken, served with: rice, bread, tahini, fries.",
                "price": 135.0,
                "stock": 30,
                "category": "Meals",
                "img_filename": "meal_q_chicken.jpg",
                "img_label": "Quarter Chicken",
                "img_color": "#FF5722"
            },
            {
                "name": "Half Chicken Meal - نص فرخة",
                "description": "نصف فرخة مشوية على الفحم، تقدم مع: أرز + عيش + طحينة + بطاطس / Charcoal-grilled half chicken, served with: rice, bread, tahini, fries.",
                "price": 200.0,
                "stock": 25,
                "category": "Meals",
                "img_filename": "meal_h_chicken.jpg",
                "img_label": "Half Chicken",
                "img_color": "#E64A19"
            },
            {
                "name": "Quarter Kofta Meal - ربع كفتة",
                "description": "ربع كيلو كفتة بلدي مشوية، تقدم مع: أرز + عيش + طحينة + بطاطس / Quarter kg grilled kofta, served with: rice, bread, tahini, fries.",
                "price": 160.0,
                "stock": 25,
                "category": "Meals",
                "img_filename": "meal_q_kofta.jpg",
                "img_label": "Quarter Kofta",
                "img_color": "#4E342E"
            },
            {
                "name": "Half Kofta Meal - نص كفتة",
                "description": "نصف كيلو كفتة بلدي مشوية، تقدم مع: أرز + عيش + طحينة + بطاطس / Half kg grilled kofta, served with: rice, bread, tahini, fries.",
                "price": 220.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_h_kofta.jpg",
                "img_label": "Half Kofta Meal",
                "img_color": "#3E2723"
            },
            {
                "name": "Mix Quarter Kofta + Quarter Chicken Meal - ميكس ربع كفتة + ربع فرخة",
                "description": "وجبة مشويات مشكلة ربع كفتة وربع فرخة، تقدم مع: أرز + عيش + طحينة + بطاطس / Mix grill of quarter kofta and quarter chicken, with sides.",
                "price": 200.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_mix_q.jpg",
                "img_label": "Mix Q Meal",
                "img_color": "#795548"
            },
            {
                "name": "Mix Grill Meal - ميكس جريل",
                "description": "كفتة، شيش طاووق، ربع فرخة، تقدم مع: أرز + عيش + طحينة + بطاطس / Kofta, shish tawook, quarter chicken, served with: rice, bread, tahini, fries.",
                "price": 250.0,
                "stock": 15,
                "category": "Meals",
                "img_filename": "meal_mix_grill.jpg",
                "img_label": "Mix Grill",
                "img_color": "#3E2723"
            },
            {
                "name": "Shish Tawook Meal - شيش طاوق",
                "description": "وجبة شيش طاووق مشوي، تقدم مع: أرز + عيش + طحينة + بطاطس / Grilled shish tawook meal, served with: rice, bread, tahini, fries.",
                "price": 200.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_shish.jpg",
                "img_label": "Shish Meal",
                "img_color": "#FB8C00"
            },
            {
                "name": "Cordon Bleu Meal - كوردن بلو",
                "description": "وجبة كوردن بلو دجاج مقرمش محشي جبن، تقدم مع: أرز + عيش + طحينة + بطاطس / Chicken cordon bleu meal, served with: rice, bread, tahini, fries.",
                "price": 200.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_cordon.jpg",
                "img_label": "Cordon Bleu Meal",
                "img_color": "#FF7043"
            },
            {
                "name": "Zinger Meal - زنجر",
                "description": "وجبة صدور دجاج زنجر حارة مقرمشة، تقدم مع: أرز + عيش + طحينة + بطاطس / Spicy crispy chicken zinger meal, served with: rice, bread, tahini, fries.",
                "price": 200.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_zinger.jpg",
                "img_label": "Zinger Meal",
                "img_color": "#E65100"
            },
            {
                "name": "Crispy Chicken Meal - كرسبي",
                "description": "وجبة استربس دجاج مقرمش، تقدم مع: أرز + عيش + طحينة + بطاطس / Crispy chicken strips meal, served with: rice, bread, tahini, fries.",
                "price": 220.0,
                "stock": 15,
                "category": "Meals",
                "img_filename": "meal_crispy.jpg",
                "img_label": "Crispy Meal",
                "img_color": "#FFA000"
            },
            {
                "name": "Chicken Pane Meal - بانية",
                "description": "وجبة صدور دجاج بانيه مقرمشة، تقدم مع: أرز + عيش + طحينة + بطاطس / Crispy chicken pane meal, served with: rice, bread, tahini, fries.",
                "price": 200.0,
                "stock": 20,
                "category": "Meals",
                "img_filename": "meal_pane.jpg",
                "img_label": "Pane Meal",
                "img_color": "#FFC107"
            },
            {
                "name": "Meat Casserole Meal - طاجن لحمة",
                "description": "طاجن لحمة بالبصل في الفرن، يقدم مع: أرز + عيش + طحينة + بطاطس / Baked beef casserole with onions, served with: rice, bread, tahini, fries.",
                "price": 250.0,
                "stock": 15,
                "category": "Meals",
                "img_filename": "meal_tajin.jpg",
                "img_label": "Tajin Meal",
                "img_color": "#4E342E"
            },

            # ==== 7. RICE & PASTA (16 items) ====
            {
                "name": "Rizo Rice - ريزو",
                "description": "أرز ريزو مبهر مع قطع الاستربس المقرمشة والقصة الحارة / Spiced rizo rice with crispy chicken strips and spicy sauce.",
                "price": 130.0,
                "stock": 40,
                "category": "Rice & Pasta",
                "img_filename": "rice_rizo.jpg",
                "img_label": "Rizo Rice",
                "img_color": "#FF8F00"
            },
            {
                "name": "Shawarma Rice - أرز شاورمة",
                "description": "أرز كالميرا الأصفر المغطى بشاورما الدجاج أو اللحم والصلصة / Yellow rice topped with chicken or beef shawarma and sauce.",
                "price": 120.0,
                "stock": 40,
                "category": "Rice & Pasta",
                "img_filename": "rice_shawarma.jpg",
                "img_label": "Shawarma Rice",
                "img_color": "#FB8C00"
            },
            {
                "name": "Bechamel Pasta - مكرونة بشاميل",
                "description": "مكرونة فرن باللحمة المفرومة والباشميل الغني / Baked pasta with minced beef and rich white bechamel sauce.",
                "price": 80.0,
                "stock": 45,
                "category": "Rice & Pasta",
                "img_filename": "pasta_bechamel.jpg",
                "img_label": "Bechamel Pasta",
                "img_color": "#FFE082"
            },
            {
                "name": "Crispy Chicken Pasta - مكرونة كرسبي",
                "description": "مكرونة بالوايت صوص وقطع الدجاج الكرسبي المقرمش / Pasta with white sauce and crispy chicken chunks.",
                "price": 120.0,
                "stock": 30,
                "category": "Rice & Pasta",
                "img_filename": "pasta_crispy.jpg",
                "img_label": "Crispy Pasta",
                "img_color": "#FFA000"
            },
            {
                "name": "Shawarma Pasta - مكرونة شاورمة",
                "description": "مكرونة بصوص الوايت أو الريد مغطاة بشاورما الدجاج / Pasta topped with savory chicken shawarma.",
                "price": 120.0,
                "stock": 35,
                "category": "Rice & Pasta",
                "img_filename": "pasta_shawarma.jpg",
                "img_label": "Shawarma Pasta",
                "img_color": "#FB8C00"
            },
            {
                "name": "White Sauce Pasta - مكرونة وايت صوص",
                "description": "مكرونة كلاسيكية بصوص الكريمة الأبيض الغني والجبن / Classic pasta in rich creamy white sauce.",
                "price": 120.0,
                "stock": 40,
                "category": "Rice & Pasta",
                "img_filename": "pasta_whitesauce.jpg",
                "img_label": "White Sauce Pasta",
                "img_color": "#FFF9C4"
            },
            {
                "name": "Shish Tawook Pasta - مكرونة شيش",
                "description": "مكرونة بالوايت صوص مع قطع الشيش طاووق المشوية / White sauce pasta with grilled shish tawook chunks.",
                "price": 130.0,
                "stock": 30,
                "category": "Rice & Pasta",
                "img_filename": "pasta_shish.jpg",
                "img_label": "Shish Pasta",
                "img_color": "#F57C00"
            },
            {
                "name": "Hot Dog Pasta - مكرونة هوت دوج",
                "description": "مكرونة بصوص الطماطم أو الوايت مع قطع الهوت دوج / Pasta with frankfurter hot dog chunks.",
                "price": 110.0,
                "stock": 35,
                "category": "Rice & Pasta",
                "img_filename": "pasta_hotdog.jpg",
                "img_label": "Hot Dog Pasta",
                "img_color": "#D84315"
            },
            {
                "name": "Negresco Pasta - مكرونة نجرسكو",
                "description": "مكرونة فرن بالوايت صوص، قطع دجاج، مشروم، موتزاريلا / Baked pasta with white sauce, chicken, mushroom, mozzarella.",
                "price": 120.0,
                "stock": 25,
                "category": "Rice & Pasta",
                "img_filename": "pasta_negresco.jpg",
                "img_label": "Negresco",
                "img_color": "#FFE082"
            },
            {
                "name": "Fajita Pasta - مكرونة فاهيتا",
                "description": "مكرونة ببهارات الفاهيتا مع صدور دجاج مشوحة وفلفل / Spiced fajita pasta with chicken chunks and peppers.",
                "price": 130.0,
                "stock": 30,
                "category": "Rice & Pasta",
                "img_filename": "pasta_fajita.jpg",
                "img_label": "Fajita Pasta",
                "img_color": "#E64A19"
            },
            {
                "name": "Sausage Pasta - مكرونة سجق",
                "description": "مكرونة متبلة مع قطع السجق البلدي المشوح / Savory pasta with stir-fried traditional sausage.",
                "price": 100.0,
                "stock": 35,
                "category": "Rice & Pasta",
                "img_filename": "pasta_sausage.jpg",
                "img_label": "Sausage Pasta",
                "img_color": "#3E2723"
            },
            {
                "name": "Kofta Pasta - مكرونة كفتة",
                "description": "مكرونة حمراء تقدم مع أصابع كفتة بلدي مشوية / Red sauce pasta served with grilled beef kofta.",
                "price": 110.0,
                "stock": 35,
                "category": "Rice & Pasta",
                "img_filename": "pasta_kofta.jpg",
                "img_label": "Kofta Pasta",
                "img_color": "#4E342E"
            },
            {
                "name": "Liver Pasta - مكرونة كبدة",
                "description": "مكرونة متبلة بصوص كالميرا مغطاة بكبدة إسكندراني / Spiced pasta topped with Alexandrian beef liver.",
                "price": 100.0,
                "stock": 40,
                "category": "Rice & Pasta",
                "img_filename": "pasta_liver.jpg",
                "img_label": "Liver Pasta",
                "img_color": "#5D4037"
            },
            {
                "name": "Zinger Pasta - مكرونة زنجر",
                "description": "مكرونة بصوص الجبنة والوايت صوص مع زنجر حار / White sauce pasta with spicy chicken zinger.",
                "price": 120.0,
                "stock": 30,
                "category": "Rice & Pasta",
                "img_filename": "pasta_zinger.jpg",
                "img_label": "Zinger Pasta",
                "img_color": "#E65100"
            },
            {
                "name": "Cordon Bleu Pasta - مكرونة كوردن بلو",
                "description": "مكرونة بالوايت صوص الغني مغطاة بقطع كوردن بلو دجاج / Rich white sauce pasta topped with cordon bleu.",
                "price": 130.0,
                "stock": 30,
                "category": "Rice & Pasta",
                "img_filename": "pasta_cordon.jpg",
                "img_label": "Cordon Bleu Pasta",
                "img_color": "#FF7043"
            },
            {
                "name": "Shawarma Fatteh - فتة شاورمة",
                "description": "فتة أرز كلاسيكية مع عيش مقرمش وتومية وشاورما دجاج / Yellow rice fatteh with crispy bread, garlic, chicken shawarma.",
                "price": 130.0,
                "stock": 35,
                "category": "Rice & Pasta",
                "img_filename": "fatteh_shawarma.jpg",
                "img_label": "Shawarma Fatteh",
                "img_color": "#FFA726"
            },

            # ==== 8. SALADS (6 items) ====
            {
                "name": "Tahini Salad - طحينة",
                "description": "طحينة بيضاء بلدي مع الليمون والبهارات / Authentic white sesame paste with lemon and spices.",
                "price": 20.0,
                "stock": 100,
                "category": "Salads",
                "img_filename": "salad_tahini.jpg",
                "img_label": "Tahini",
                "img_color": "#F5F5DC"
            },
            {
                "name": "Tomato Salad - طماطم",
                "description": "طماطم متبلة بالثوم والخل والبهارات والليمون / Spiced tomatoes seasoned with garlic, vinegar, lemon.",
                "price": 20.0,
                "stock": 100,
                "category": "Salads",
                "img_filename": "salad_tomato.jpg",
                "img_label": "Tomato Salad",
                "img_color": "#EF5350"
            },
            {
                "name": "Pickles - مخلل",
                "description": "تشكيلة مخللات كالميرا المشكلة اللذيذة / Assorted traditional pickled vegetables.",
                "price": 20.0,
                "stock": 150,
                "category": "Salads",
                "img_filename": "salad_pickles.jpg",
                "img_label": "Pickles",
                "img_color": "#4CAF50"
            },
            {
                "name": "Garlic Dip - ثومية",
                "description": "صلصة ثومية كريمية شهية على طريقة كالميرا / Rich creamy traditional garlic dip sauce.",
                "price": 20.0,
                "stock": 120,
                "category": "Salads",
                "img_filename": "salad_garlic.jpg",
                "img_label": "Garlic Dip",
                "img_color": "#ECEFF1"
            },
            {
                "name": "Coleslaw Salad - كول سلو",
                "description": "كرنب مقطع، جزر، دريسنج كالميرا الحلو المميز / Shredded cabbage, carrots, sweet Kalmera dressing.",
                "price": 40.0,
                "stock": 50,
                "category": "Salads",
                "img_filename": "salad_coleslaw.jpg",
                "img_label": "Coleslaw",
                "img_color": "#E8F5E9"
            },
            {
                "name": "Caesar Salad - سيزر سالاد",
                "description": "خس كابوتشا، قطع دجاج مشوي، كروتون، دريسنج سيزر / Lettuce, grilled chicken chunks, croutons, Caesar dressing.",
                "price": 80.0,
                "stock": 30,
                "category": "Salads",
                "img_filename": "salad_caesar.jpg",
                "img_label": "Caesar Salad",
                "img_color": "#81C784"
            },

            # ==== 9. SAUCES (7 items) ====
            {
                "name": "Mozzarella Sauce - جبنة موتزاريلا",
                "description": "صوص جبنة موتزاريلا غني ودافيء / Rich warm melted mozzarella cheese sauce.",
                "price": 30.0,
                "stock": 100,
                "category": "Sauces",
                "img_filename": "sauce_mozzarella.jpg",
                "img_label": "Mozzarella Sauce",
                "img_color": "#FFFDE7"
            },
            {
                "name": "Cheddar Cheese Sauce - جبنة شيدر",
                "description": "صوص جبنة شيدر ذهبي دافيء ولذيذ / Smooth melted golden cheddar cheese sauce.",
                "price": 30.0,
                "stock": 100,
                "category": "Sauces",
                "img_filename": "sauce_cheddar.jpg",
                "img_label": "Cheddar Sauce",
                "img_color": "#FFD54F"
            },
            {
                "name": "Ranch Sauce - رانش",
                "description": "صوص رانش كريمي بالثوم والأعشاب / Creamy herb and garlic Ranch sauce.",
                "price": 30.0,
                "stock": 120,
                "category": "Sauces",
                "img_filename": "sauce_ranch.jpg",
                "img_label": "Ranch Sauce",
                "img_color": "#F5F5F5"
            },
            {
                "name": "BBQ Sauce - باربيكيو",
                "description": "صوص باربيكيو مدخن غني وحلو / Rich smoky sweet BBQ sauce.",
                "price": 20.0,
                "stock": 150,
                "category": "Sauces",
                "img_filename": "sauce_bbq.jpg",
                "img_label": "BBQ Sauce",
                "img_color": "#BF360C"
            },
            {
                "name": "Big Tasty Sauce - بيج تيستي",
                "description": "الصوص المدخن الشهير المميز للبرجر / Famous rich smoky burger sauce.",
                "price": 30.0,
                "stock": 150,
                "category": "Sauces",
                "img_filename": "sauce_bigtasty.jpg",
                "img_label": "Big Tasty Sauce",
                "img_color": "#FFCC80"
            },
            {
                "name": "Garlic Sauce - ثومية",
                "description": "صلصة ثومية كريمية إضافية / Extra portion of rich garlic sauce.",
                "price": 20.0,
                "stock": 100,
                "category": "Sauces",
                "img_filename": "sauce_garlic.jpg",
                "img_label": "Garlic Sauce",
                "img_color": "#ECEFF1"
            },
            {
                "name": "Mayonnaise Sauce - مايونيز",
                "description": "صوص مايونيز كريمي كلاسيكي / Classic rich creamy mayonnaise sauce.",
                "price": 20.0,
                "stock": 150,
                "category": "Sauces",
                "img_filename": "sauce_mayo.jpg",
                "img_label": "Mayonnaise",
                "img_color": "#FAFAFA"
            },

            # ==== 10. POTATO (4 items) ====
            {
                "name": "Fries Sandwich - ساندوتش بطاطس",
                "description": "بطاطس محمرة مقرمشة في خبز سوري مع الكاتشب والمايونيز / Crispy French fries in Syrian bread with sauces.",
                "price": 40.0,
                "stock": 60,
                "category": "Potato",
                "img_filename": "potato_sand.jpg",
                "img_label": "Fries Sandwich",
                "img_color": "#FFF59D"
            },
            {
                "name": "Cheese Fries Sandwich - ساندوتش بطاطس جبنة",
                "description": "بطاطس محمرة مع صوص الجبن الشيدر الدافئ في خبز سوري / French fries with warm cheddar cheese sauce in Syrian bread.",
                "price": 50.0,
                "stock": 60,
                "category": "Potato",
                "img_filename": "potato_cheese_sand.jpg",
                "img_label": "Cheese Fries Sand",
                "img_color": "#FFE082"
            },
            {
                "name": "Fries Packet - باكت بطاطس",
                "description": "عبوة بطاطس محمرة مقرمشة ومتبلة / Packet of crispy seasoned French fries.",
                "price": 40.0,
                "stock": 80,
                "category": "Potato",
                "img_filename": "potato_fries.jpg",
                "img_label": "Fries Packet",
                "img_color": "#FFF59D"
            },
            {
                "name": "Cheese Fries Packet - باكت بطاطس جبنة",
                "description": "باكت بطاطس محمرة مقرمشة مغطاة بصوص الشيدر الدافئ / Crispy fries smothered in hot cheddar cheese sauce.",
                "price": 50.0,
                "stock": 80,
                "category": "Potato",
                "img_filename": "potato_cheese.jpg",
                "img_label": "Cheese Fries",
                "img_color": "#FBC02D"
            }
        ]

async def seed_initial_data_if_empty(session: AsyncSession):
    """Safely seeds default categories, products, and default users if categories table is empty."""
    result = await session.execute(select(func.count()).select_from(Category))
    cat_count = result.scalar() or 0
    if cat_count > 0:
        return  # Already populated

    # 1. Create Default Users if not exist
    admin_phone = "01000000001"
    customer_phone = "01000000002"

    admin_res = await session.execute(select(User).where(User.phone == admin_phone))
    if not admin_res.scalars().first():
        admin = User(
            phone=admin_phone,
            hashed_password=get_password_hash("admin123"),
            full_name="كالميرا أدمن / Kalmera Admin",
            role=UserRole.ADMIN,
        )
        session.add(admin)

    cust_res = await session.execute(select(User).where(User.phone == customer_phone))
    if not cust_res.scalars().first():
        customer = User(
            phone=customer_phone,
            hashed_password=get_password_hash("customer123"),
            full_name="عميل تجريبي / Demo Customer",
            role=UserRole.CUSTOMER,
        )
        session.add(customer)

    # 2. Create Categories
    category_records = {}
    for cat_name in CATEGORIES_TO_SEED:
        cat = Category(name=cat_name)
        session.add(cat)
        await session.flush()
        category_records[cat_name] = cat.id

    # 3. Create Products and Variants
    for prod in PRODUCTS_DATA:
        image_path = create_compressed_placeholder(
            prod["img_filename"], prod["img_label"], prod["img_color"]
        )

        full_name = prod["name"]
        name_ar, name_en = full_name, full_name
        if " - " in full_name:
            parts = full_name.split(" - ", 1)
            name_en = parts[0].strip()
            name_ar = parts[1].strip()

        full_desc = prod.get("description", "")
        desc_ar, desc_en = full_desc, full_desc
        if full_desc and " / " in full_desc:
            parts = full_desc.split(" / ", 1)
            desc_ar = parts[0].strip()
            desc_en = parts[1].strip()

        new_product = Product(
            name=name_ar,
            name_en=name_en,
            description=desc_ar or None,
            description_en=desc_en or None,
            price=prod["price"],
            stock=prod["stock"],
            category_id=category_records[prod["category"]],
            image_path=image_path,
        )

        if "variants" in prod:
            for size_name, size_price in prod["variants"]:
                new_product.variants.append(
                    ProductVariant(name=size_name, price=size_price)
                )

        session.add(new_product)

    await session.commit()
    print("Initial Kalmera menu data seeded successfully.")


async def seed_data():
    print("Re-creating database tables and seeding Kalmera menu...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_initial_data_if_empty(session)


if __name__ == "__main__":
    asyncio.run(seed_data())

