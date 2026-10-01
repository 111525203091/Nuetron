from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Monster Juice Catalog Data
FLAVORS = [
    {
        "id": "mango-loco",
        "name": "MANGO LOCO",
        "tagline": "A Heavenly Blend of Exotic Juices",
        "description": "On the eve of October 31st, friends and family gather to celebrate Día de los Muertos. Marigolds, mysticism, and memories combine with food and drink to entice the departed to the party. Mango Loco is a heavenly blend of exotic juices certain to attract even the most stubborn spirit.",
        "juice_percentage": "16% Real Fruit Juice",
        "caffeine": "160 mg",
        "calories": "210 kcal",
        "flavor_profile": ["Exotic Mango", "Tropical Guava", "Citrus Spark"],
        "color_primary": "#ff5900",
        "color_secondary": "#00d2ff",
        "color_glow": "rgba(255, 89, 0, 0.45)",
        "badge": "FANS FAVORITE",
        "bg_gradient": "radial-gradient(circle at 50% 30%, rgba(255, 89, 0, 0.25) 0%, rgba(10, 11, 14, 0.95) 75%)"
    },
    {
        "id": "pipeline-punch",
        "name": "PIPELINE PUNCH",
        "tagline": "The Banzai Beast of the North Shore",
        "description": "Banzai Pipeline, the world's most famous wave on Oahu's legendary North Shore, comes alive for just a few brief months each winter. In honor of this epic force of nature, we created Pipeline Punch: the perfect mix of Hawaiian passionfruit, orange, and guava, Monsterized with our full energy blend.",
        "juice_percentage": "16% Real Hawaiian Blend",
        "caffeine": "160 mg",
        "calories": "200 kcal",
        "flavor_profile": ["Passionfruit", "Sweet Orange", "Velvet Guava"],
        "color_primary": "#ff007b",
        "color_secondary": "#ff9e00",
        "color_glow": "rgba(255, 0, 123, 0.45)",
        "badge": "COASTAL RUSH",
        "bg_gradient": "radial-gradient(circle at 50% 30%, rgba(255, 0, 123, 0.25) 0%, rgba(10, 11, 14, 0.95) 75%)"
    },
    {
        "id": "khaotic",
        "name": "KHAOTIC",
        "tagline": "Pure Citrus Carnage Re-Engineered",
        "description": "Back in 2005, the original Monster Juice shook up the game by combining great tasting real juice with energy drink functionality. Now we've updated the flavor and repackaged the design to create Khaotic: a reimagined citrus chaos that rips through your tastebuds with savage energy.",
        "juice_percentage": "10% Real Citrus Juice",
        "caffeine": "160 mg",
        "calories": "190 kcal",
        "flavor_profile": ["Electric Orange", "Tangy Mandarin", "Monster Blend"],
        "color_primary": "#ffaa00",
        "color_secondary": "#52ff00",
        "color_glow": "rgba(255, 170, 0, 0.45)",
        "badge": "RE-ENGINEERED CLASSIC",
        "bg_gradient": "radial-gradient(circle at 50% 30%, rgba(255, 170, 0, 0.25) 0%, rgba(10, 11, 14, 0.95) 75%)"
    },
    {
        "id": "pacific-punch",
        "name": "PACIFIC PUNCH",
        "tagline": "Old School Punch with Tattoo Soul",
        "description": "Not too sweet, not too heavy, but deep, bold, and fully loaded with genuine fruit character. Styled with authentic traditional sailor tattoo flash art, Pacific Punch delivers a retro tidal wave of fruit punch energy with relentless bite.",
        "juice_percentage": "12% Tropical Red Punch",
        "caffeine": "160 mg",
        "calories": "210 kcal",
        "flavor_profile": ["Dark Cherry", "Crimson Apple", "Pineapple Kick"],
        "color_primary": "#e60026",
        "color_secondary": "#ffd700",
        "color_glow": "rgba(230, 0, 38, 0.45)",
        "badge": "CLASSIC HIGH TIDE",
        "bg_gradient": "radial-gradient(circle at 50% 30%, rgba(230, 0, 38, 0.25) 0%, rgba(10, 11, 14, 0.95) 75%)"
    },
    {
        "id": "aussie-lemonade",
        "name": "AUSSIE LEMONADE",
        "tagline": "Land Down Under Exotic Citrus Storm",
        "description": "Inspired by the Land Down Under with over 10,000 beaches, the Great Barrier Reef, and home to some of the wildest terrain on Earth. Aussie Style Lemonade is Monster's twist on classic lemonade, striking the ultimate balance between tart, sweet, and pure citrus buzz.",
        "juice_percentage": "11% Meyer Lemon & Citrus",
        "caffeine": "160 mg",
        "calories": "180 kcal",
        "flavor_profile": ["Zesty Lemon", "Sub-Tropical Lime", "Crisp Fizz"],
        "color_primary": "#00e5ff",
        "color_secondary": "#ccff00",
        "color_glow": "rgba(0, 229, 255, 0.45)",
        "badge": "NEW DROP",
        "bg_gradient": "radial-gradient(circle at 50% 30%, rgba(0, 229, 255, 0.25) 0%, rgba(10, 11, 14, 0.95) 75%)"
    }
]

REVIEWS = [
    {
        "quote": "Mango Loco legitimately tastes like an actual tropical mango puree fused with the raw power of a lightning bolt.",
        "author": "Kai V., Pro BMX Rider",
        "stars": 5,
        "flavor": "Mango Loco"
    },
    {
        "quote": "Pipeline Punch in the morning before catching waves at sunrise is an absolute non-negotiable ritual.",
        "author": "Elena M., Surf Instructor",
        "stars": 5,
        "flavor": "Pipeline Punch"
    },
    {
        "quote": "The citrus bite of Khaotic keeps our entire esports team laser-locked during 14-hour tournament qualifiers.",
        "author": "Marcus 'Vortex' D., Competitive Gamer",
        "stars": 5,
        "flavor": "Khaotic"
    }
]

@app.route('/')
def home():
    return render_template('index.html', flavors=FLAVORS, reviews=REVIEWS)

@app.route('/api/flavors')
def get_flavors():
    return jsonify(FLAVORS)

@app.route('/api/claim-promo', methods=['POST'])
def claim_promo():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    flavor = data.get('flavor', 'Mango Loco')

    if not email or '@' not in email:
        return jsonify({"success": False, "message": "Please provide a valid email address."}), 400

    promo_code = f"BEAST-{flavor[:3].upper()}-99X"
    return jsonify({
        "success": True,
        "message": f"Beast VIP pass unlocked! Check your inbox ({email}) for your free can voucher.",
        "promo_code": promo_code,
        "discount": "FREE 16oz Can + 25% Off 12-Pack Case"
    })

@app.route('/api/find-stores', methods=['POST'])
def find_stores():
    data = request.get_json() or {}
    zip_code = data.get('zip_code', '90210').strip()
    
    # Mock realistic stores based on location
    stores = [
        {"name": "Speedway Extreme Depot", "address": f"104 Market Blvd, Zone {zip_code}", "distance": "0.4 miles", "stock": "High Stock - All Flavors"},
        {"name": "7-Eleven 24/7 Supercenter", "address": f"820 Grand Avenue, Zone {zip_code}", "distance": "0.9 miles", "stock": "Pipeline & Mango Loco Only"},
        {"name": "Target Express Cooler Section", "address": f"1450 Pacific Coast Hwy, Zone {zip_code}", "distance": "1.7 miles", "stock": "12-Pack Cases In Stock"},
        {"name": "GNC Live Well & Energy", "address": f"2100 Metro Mall, Suite 4, Zone {zip_code}", "distance": "2.3 miles", "stock": "Full Cold Vault Stocked"}
    ]
    return jsonify({"success": True, "zip_code": zip_code, "stores": stores})

if __name__ == '__main__':
    print("==================================================")
    print("⚡ MONSTER JUICE ADVERTISEMENT WEB APP ⚡")
    print("Running on http://127.0.0.1:5000")
    print("Press Ctrl+C to terminate.")
    print("==================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
