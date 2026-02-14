"""Groq API client with mock fallback when no API key is set."""
import json
import os
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS, TEMPERATURE, TIMEOUT


def _mock_recommendations(skin_tone: str, gender: str) -> dict:
    """Generate structured mock recommendations matching expected API response format."""
    g = gender.lower()
    is_female = g == "female"
    base = {
        "formal": {
            "tops": "White tailored shirt" if not is_female else "Cream blouse with subtle sheen",
            "bottoms": "Navy tailored trousers" if not is_female else "High-waist pencil skirt in charcoal",
            "shoes": "Oxford shoes in black" if not is_female else "Closed-toe pumps in nude",
        },
        "business": {
            "tops": "Light blue dress shirt" if not is_female else "Soft pink silk blouse",
            "bottoms": "Charcoal grey chinos" if not is_female else "Tailored wide-leg trousers",
            "shoes": "Brown leather loafers" if not is_female else "Block heels in tan",
        },
        "casual": {
            "tops": "Earth-tone henley" if not is_female else "Mustard yellow relaxed tee",
            "bottoms": "Dark wash jeans" if not is_female else "High-waist mom jeans",
            "shoes": "White sneakers" if not is_female else "Minimalist white sneakers",
        },
        "party": {
            "tops": "Black fitted shirt" if not is_female else "Emerald green wrap top",
            "bottoms": "Slim black trousers" if not is_female else "Black high-waist palazzo",
            "shoes": "Leather ankle boots" if not is_female else "Strappy heels in gold",
        },
    }
    # Color palette suggestions by skin tone
    palettes = {
        "Fair": {"primary": "Navy & White", "secondary": "Soft Pink & Lavender", "accent": "Coral & Gold"},
        "Medium": {"primary": "Burgundy & Olive", "secondary": "Camel & Cream", "accent": "Teal & Copper"},
        "Olive": {"primary": "Forest Green & Terracotta", "secondary": "Warm Beige & Brown", "accent": "Amber & Rust"},
        "Deep": {"primary": "Royal Blue & Black", "secondary": "Mustard & Bronze", "accent": "Electric Blue & Gold"},
    }
    palette = palettes.get(skin_tone, palettes["Medium"])
    # Curated Indian retailer search links (skin tone + gender relevant)
    q = "formal wear" if is_female else "formal shirts"
    shopping_links = {
        "Amazon.in": f"https://www.amazon.in/s?k={q.replace(' ', '+')}",
        "Myntra": f"https://www.myntra.com/{q.replace(' ', '-')}",
        "Zara": "https://www.zara.com/in/",
    }
    return {
        "dress_codes": base,
        "hairstyle": {
            "suggestion": "Sleek low bun with soft face-framing layers" if is_female else "Clean side part with trimmed sides",
            "maintenance_tips": "Use heat protectant; trim every 6–8 weeks; hydrate with light serum.",
        },
        "accessories": {
            "earrings": "Small gold hoops or studs" if is_female else "Minimal studs (if preferred)",
            "necklaces": "Delicate chain with pendant" if is_female else "Subtle chain or none",
            "bracelets": "Thin leather or metal cuff" if is_female else "Classic watch only",
            "watches": "Minimal leather-strap watch in silver or gold",
        },
        "color_palette": palette,
        "reasoning": f"Recommendations are tailored for {skin_tone} skin tone and {gender} presentation. "
        f"Colors chosen complement {skin_tone} undertones: {palette['primary']} as base, "
        f"{palette['secondary']} for balance, and {palette['accent']} for pops. "
        "Outfit combinations suit Indian climate and occasions from office to parties.",
        "shopping_links": shopping_links,
    }


def get_recommendations(skin_tone: str, gender: str, rgb: list) -> dict:
    """
    Fetch fashion recommendations. Uses Groq API if GROQ_API_KEY is set,
    otherwise returns mock data. Returns same structure in both cases.
    """
    if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
        return _mock_recommendations(skin_tone, gender)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        prompt = f"""You are a fashion stylist. Based on:
- Skin tone: {skin_tone}
- Gender: {gender}
- Approximate face region RGB: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}

Respond with a single valid JSON object (no markdown, no code block) containing exactly these keys:
- "dress_codes": object with keys "formal", "business", "casual", "party". Each value is an object with "tops", "bottoms", "shoes".
- "hairstyle": object with "suggestion" and "maintenance_tips".
- "accessories": object with "earrings", "necklaces", "bracelets", "watches".
- "color_palette": object with "primary", "secondary", "accent".
- "reasoning": string explaining why these recommendations match the skin tone.

Keep recommendations specific to Indian retailers (Amazon.in, Myntra, Zara) where relevant. Be concise."""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            timeout=TIMEOUT,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code block if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        out = json.loads(text)
        if "shopping_links" not in out:
            out["shopping_links"] = {
                "Amazon.in": "https://www.amazon.in/s?k=fashion",
                "Myntra": "https://www.myntra.com/",
                "Zara": "https://www.zara.com/in/",
            }
        return out
    except Exception:
        return _mock_recommendations(skin_tone, gender)
