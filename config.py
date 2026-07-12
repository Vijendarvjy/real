"""
Static configuration: room types, default dimensions, design styles,
and per-room customization option sets. Kept separate from app logic
so new rooms/options can be added without touching UI or AI code.
"""

# Each room has: icon, default (L x W x H) in feet, and a list of
# customization fields. Each field is (key, label, type, options/range)
ROOM_CONFIG = {
    "Master Bedroom": {
        "icon": "🛏️",
        "default_dims": {"length": 14.0, "width": 12.0, "height": 10.0},
        "fields": {
            "bed_size": {
                "label": "Bed Size",
                "options": ["Queen", "King", "California King", "Double"],
            },
            "wardrobe_type": {
                "label": "Wardrobe Type",
                "options": ["Sliding Door", "Hinged Door", "Walk-in Closet", "Open Wardrobe"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Engineered Wood", "Laminate", "Vitrified Tile", "Carpet"],
            },
            "wall_finish": {
                "label": "Wall Finish",
                "options": ["Textured Paint", "Wallpaper (Accent Wall)", "Wood Paneling", "Plain Matte Paint"],
            },
            "lighting": {
                "label": "Lighting",
                "options": ["Cove Lighting", "Pendant Lights", "Recessed Spotlights", "Chandelier"],
            },
        },
    },
    "Kids Bedroom": {
        "icon": "🧸",
        "default_dims": {"length": 11.0, "width": 10.0, "height": 10.0},
        "fields": {
            "bed_size": {
                "label": "Bed Size",
                "options": ["Single", "Bunk Bed", "Trundle Bed", "Twin"],
            },
            "study_zone": {
                "label": "Study Zone",
                "options": ["Wall-mounted Desk", "Corner Study Table", "None"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Vinyl (Soft)", "Laminate", "Carpet Tiles"],
            },
            "theme": {
                "label": "Theme",
                "options": ["Space", "Jungle Safari", "Pastel Minimal", "Sports"],
            },
        },
    },
    "Living / Hall": {
        "icon": "🛋️",
        "default_dims": {"length": 20.0, "width": 15.0, "height": 10.0},
        "fields": {
            "seating_layout": {
                "label": "Seating Layout",
                "options": ["L-Shaped Sofa", "Straight Sofa + Chairs", "U-Shaped Sofa", "Modular Sectional"],
            },
            "tv_unit_style": {
                "label": "TV Unit Style",
                "options": ["Floating Wall-mounted", "Console with Storage", "Entertainment Wall Panel", "Corner Unit"],
            },
            "false_ceiling": {
                "label": "False Ceiling",
                "options": ["Full Gypsum Ceiling", "Perimeter Cove Ceiling", "None"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Italian Marble", "Vitrified Tile (Large Format)", "Engineered Wood"],
            },
            "color_palette": {
                "label": "Color Palette",
                "options": ["Warm Neutrals", "Cool Greys", "Earthy Tones", "Monochrome + Accent"],
            },
        },
    },
    "Kitchen": {
        "icon": "🍳",
        "default_dims": {"length": 12.0, "width": 9.0, "height": 9.5},
        "fields": {
            "layout": {
                "label": "Kitchen Layout",
                "options": ["L-Shaped", "Parallel / Galley", "U-Shaped", "Island"],
            },
            "countertop": {
                "label": "Countertop Material",
                "options": ["Granite", "Quartz", "Marble", "Concrete"],
            },
            "cabinet_finish": {
                "label": "Cabinet Finish",
                "options": ["High-Gloss Acrylic", "Matte Laminate", "Wood Veneer", "PU Paint"],
            },
            "backsplash": {
                "label": "Backsplash",
                "options": ["Ceramic Tile", "Glass Panel", "Natural Stone"],
            },
        },
    },
    "Doors": {
        "icon": "🚪",
        "default_dims": {"length": 3.0, "width": 0.2, "height": 7.0},
        "fields": {
            "door_type": {
                "label": "Door Type",
                "options": ["Flush Door", "Panel Door", "Sliding Glass Door", "French Door"],
            },
            "material": {
                "label": "Material",
                "options": ["Engineered Wood", "Solid Wood (Teak)", "UPVC", "Aluminium + Glass"],
            },
            "finish": {
                "label": "Finish",
                "options": ["Laminate", "Veneer + Polish", "Paint Finish"],
            },
        },
    },
    "Windows": {
        "icon": "🪟",
        "default_dims": {"length": 4.0, "width": 0.2, "height": 4.5},
        "fields": {
            "window_type": {
                "label": "Window Type",
                "options": ["Sliding", "Casement", "Fixed + Openable Combo", "Bay Window"],
            },
            "frame_material": {
                "label": "Frame Material",
                "options": ["UPVC", "Aluminium", "Wood"],
            },
            "glass_type": {
                "label": "Glass Type",
                "options": ["Clear Glass", "Tinted Glass", "Double Glazed (Insulated)", "Frosted"],
            },
            "treatment": {
                "label": "Window Treatment",
                "options": ["Roller Blinds", "Sheer Curtains", "Wooden Venetian Blinds", "None"],
            },
        },
    },
    "TV / Media Unit": {
        "icon": "📺",
        "default_dims": {"length": 8.0, "width": 1.5, "height": 6.0},
        "fields": {
            "unit_style": {
                "label": "Unit Style",
                "options": ["Wall-mounted Floating Panel", "Low Console Unit", "Wall-to-Wall Storage Wall"],
            },
            "material": {
                "label": "Material",
                "options": ["Wood Veneer + Laminate", "High-Gloss PU", "Matte Laminate + Stone Cladding"],
            },
            "backdrop": {
                "label": "TV Backdrop",
                "options": ["Textured Stone Panel", "Wood Slat Panel", "Fluted Panel + LED Strip", "Plain Paint"],
            },
        },
    },
    "Bathroom": {
        "icon": "🚿",
        "default_dims": {"length": 8.0, "width": 6.0, "height": 9.0},
        "fields": {
            "sanitaryware": {
                "label": "Sanitaryware Style",
                "options": ["Wall-hung", "Floor-mounted", "Premium Designer"],
            },
            "tiling": {
                "label": "Tiling",
                "options": ["Large Format Tiles", "Marble Look Tiles", "Mosaic Accent + Plain"],
            },
            "shower": {
                "label": "Shower Type",
                "options": ["Glass Enclosed Shower Cubicle", "Rain Shower (Open)", "Bathtub + Shower Combo"],
            },
        },
    },
}

DESIGN_STYLES = [
    "Modern Minimalist",
    "Contemporary",
    "Scandinavian",
    "Industrial",
    "Traditional Indian",
    "Mid-Century Modern",
    "Luxury Art Deco",
    "Japandi",
]

BUDGET_TIERS = ["Economy", "Standard", "Premium", "Luxury"]
