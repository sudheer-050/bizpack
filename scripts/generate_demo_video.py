import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_font(name, size):
    windir = os.environ.get("WINDIR", "C:\\Windows")
    font_path = os.path.join(windir, "Fonts", name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def create_frames():
    WIDTH, HEIGHT = 1280, 720
    FPS = 24
    TOTAL_FRAMES = 336  # 14 seconds
    
    # Fonts
    font_title = get_font("segoeuib.ttf", 26)
    font_sub = get_font("segoeui.ttf", 16)
    font_code = get_font("consola.ttf", 18)
    font_code_bold = get_font("consolab.ttf", 18)
    font_code_sm = get_font("consola.ttf", 15)
    font_hero = get_font("segoeuib.ttf", 42)
    font_hero_sub = get_font("segoeui.ttf", 22)
    
    # Colors
    BG = (13, 17, 23)
    WIN_BG = (22, 27, 34)
    WIN_BORDER = (48, 54, 61)
    CYAN = (88, 166, 255)
    GREEN = (63, 185, 80)
    AMBER = (210, 153, 34)
    RED = (248, 81, 73)
    GRAY = (139, 148, 158)
    WHITE = (230, 237, 243)
    PURPLE = (188, 140, 255)

    frames_dir = os.path.join("scripts", "temp_frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    existing_frames = len([f for f in os.listdir(frames_dir) if f.endswith(".png")])
    if existing_frames >= TOTAL_FRAMES:
        print(f"Reusing {existing_frames} pre-generated frames...")
    else:
        print("Generating 336 frames...")
        for i in range(TOTAL_FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)
        
        # Scene 5: Outro (Frame 270 - 335)
        if i >= 270:
            # Hero card
            draw.rectangle([100, 100, 1180, 620], fill=WIN_BG, outline=CYAN, width=2)
            
            # Glowing title
            draw.text((WIDTH//2, 180), "⚡ BIZPACK", font=font_hero, fill=CYAN, anchor="mm")
            draw.text((WIDTH//2, 235), "The Intelligent Business Data Engine for Python", font=font_hero_sub, fill=WHITE, anchor="mm")
            
            # Key highlights
            features = [
                "✔  Zero-Friction Spreadsheet Cleaning in 1 Line",
                "✔  Accurate Multi-Currency Standardization (USD, EUR, GBP, INR)",
                "✔  Two-Tier Date Disambiguation (0% Dropped NaT Rows)",
                "✔  Pythonic Business Math: xlookup, pareto (80/20), growth, run-rate",
                "✔  Zero Heavy Dependencies (Pure Pandas + NumPy)"
            ]
            y_f = 295
            for feat in features:
                draw.text((WIDTH//2, y_f), feat, font=font_sub, fill=(200, 210, 220), anchor="mm")
                y_f += 32
                
            # Install pill
            pill_rect = [WIDTH//2 - 220, 485, WIDTH//2 + 220, 545]
            draw.rectangle(pill_rect, fill=(30, 40, 55), outline=GREEN, width=2)
            draw.text((WIDTH//2, 515), "$ pip install bizpack", font=font_title, fill=GREEN, anchor="mm")
            
            draw.text((WIDTH//2, 580), "github.com/sudheer-050/bizpack  •  MIT Licensed", font=font_sub, fill=GRAY, anchor="mm")
            
            img.save(os.path.join(frames_dir, f"frame_{i:04d}.png"))
            continue

        # Common Window Frame for Scenes 1 - 4
        # Outer glow/border
        draw.rectangle([80, 60, 1200, 660], fill=WIN_BG, outline=WIN_BORDER, width=1)
        
        # Window Titlebar
        draw.rectangle([80, 60, 1200, 105], fill=(30, 36, 44))
        # Traffic lights
        draw.ellipse([100, 77, 114, 91], fill=(255, 95, 86))
        draw.ellipse([124, 77, 138, 91], fill=(255, 189, 46))
        draw.ellipse([148, 77, 162, 91], fill=(39, 201, 63))
        
        # Window Title
        draw.text((WIDTH//2, 84), "bizpack — bash — 120x35", font=font_sub, fill=GRAY, anchor="mm")
        
        # Dynamic Top Header above window
        if i < 70:
            header_text = "🚨 THE PROBLEM: Dirty Multi-Currency Corporate Spreadsheets"
            header_col = RED
        elif i < 140:
            header_text = "⚡ THE SOLUTION: 1 Line to Clean & Standardize Everything"
            header_col = CYAN
        elif i < 200:
            header_text = "🌍 SMART AUTOMATION: Multi-Currency & Date Disambiguation"
            header_col = AMBER
        else:
            header_text = "✨ THE RESULT: Pristine, Audit-Ready Financial Data"
            header_col = GREEN
            
        draw.text((WIDTH//2, 35), header_text, font=font_title, fill=header_col, anchor="mm")

        # SCENE 1: Dirty Data (0 <= i < 70)
        if i < 70:
            draw.text((110, 125), "$ cat quarterly_sales_raw.csv", font=font_code, fill=WHITE)
            
            table_lines = [
                ("  Customer Name / Account  , Order Date , Gross Revenue  , Margin % , Notes ", GRAY),
                ("-----------------------------------------------------------------------------", WIN_BORDER),
                ("  Acme Corp / 00124        , 25/03/2024 , ₹ 1,49,670.67  , 33.3%    , Standard ", WHITE),
                ("  Wayne Ent / 00235        , 03/25/2024 , ($ 12,865.27)  , (9.8%)   , Deficit  ", WHITE),
                ("  Massive Dynamic / 00280  , 14.12.2024 , £ 5,306.25     , 22.0%    , High VIP ", WHITE),
                ("  Globex Corp / 00945      , 05/09/2024 , € 41.392,35    , 17.5%    , Europe   ", WHITE),
                ("  Hooli Inc / 00234        , 05/09/2024 , $ 59,426.74    , 51.8%    , Renew    ", WHITE),
                ("  Grand Total              ,            , $ 243,901.00   , 36.0%    ,          ", AMBER),
            ]
            
            y = 165
            for line_text, col in table_lines:
                draw.text((110, y), line_text, font=font_code_sm, fill=col)
                y += 26
                
            # Error Callout Box
            draw.rectangle([110, 395, 1170, 520], fill=(35, 20, 25), outline=RED, width=1)
            draw.text((130, 415), "⚠️ SILENT FINANCIAL DISASTERS WITH RAW PANDAS:", font=font_title, fill=RED)
            draw.text((130, 450), "• Naive regex strips '$', '€', '₹' and sums raw numbers -> $100 + ₹8900 = $9,000 (2,800% ERROR!)", font=font_sub, fill=WHITE)
            draw.text((130, 475), "• 05/09/2024 in India (Sept 5) vs US (May 9) -> pd.to_datetime drops rows to NaT or inverts months!", font=font_sub, fill=WHITE)
            draw.text((130, 500), "• Accounting parentheses ($12,865) turn into positive +12865 -> Loss becomes profit!", font=font_sub, fill=WHITE)
            
            # Bottom hint
            draw.text((110, 620), "[BizPack] Press Enter to run automated repair...", font=font_code, fill=GRAY)

        # SCENE 2: Clean Code (70 <= i < 140)
        elif i < 140:
            draw.text((110, 125), "$ python", font=font_code, fill=WHITE)
            draw.text((110, 160), ">>> import bizpack as bp", font=font_code, fill=CYAN)
            
            # Typing effect
            full_cmd = "clean_df = bp.clean_file('quarterly_sales_raw.csv')"
            chars_to_show = min(len(full_cmd), int((i - 75) * 1.5))
            current_typed = full_cmd[:chars_to_show]
            cursor = "█" if (i // 6) % 2 == 0 else ""
            draw.text((110, 195), f">>> {current_typed}{cursor}", font=font_code, fill=WHITE)
            
            if i >= 110:
                draw.rectangle([110, 250, 1170, 480], fill=(20, 30, 40), outline=CYAN, width=1)
                draw.text((135, 275), "[BizPack Engine Initialized]", font=font_title, fill=CYAN)
                draw.text((135, 315), "• Scanning column headers and removing special characters...", font=font_code_sm, fill=WHITE)
                draw.text((135, 345), "• Inspecting multi-currency entries across 100 rows...", font=font_code_sm, fill=WHITE)
                draw.text((135, 375), "• Activating Two-Tier Hierarchical Date Engine...", font=font_code_sm, fill=WHITE)
                draw.text((135, 405), "• Identifying ID columns to protect leading zeros...", font=font_code_sm, fill=WHITE)
                draw.text((135, 435), "• Status: Ready for standardization.", font=font_code_sm, fill=GREEN)

        # SCENE 3: Interactive Prompt & Conversion (140 <= i < 200)
        elif i < 200:
            draw.text((110, 125), ">>> clean_df = bp.clean_file('quarterly_sales_raw.csv')", font=font_code, fill=WHITE)
            
            # Interactive prompt box
            draw.rectangle([110, 165, 1170, 315], fill=(30, 25, 15), outline=AMBER, width=2)
            draw.text((130, 185), "[BizPack Alert] 🌍 Multiple currencies detected in 'gross_revenue': [EUR, GBP, INR, USD]", font=font_code_bold, fill=AMBER)
            draw.text((130, 215), "To prevent multi-million ledger errors, BizPack standardizes all amounts into 1 currency.", font=font_sub, fill=WHITE)
            
            choice_text = "Which currency would you like to convert into? [Default: USD]: "
            if i >= 165:
                choice_text += "USD"
            cursor = "█" if (i // 6) % 2 == 0 and i < 175 else ""
            draw.text((130, 255), f"{choice_text}{cursor}", font=font_code, fill=CYAN)
            
            if i >= 175:
                draw.text((130, 285), "-> Standardizing 100 rows to USD (rates: EUR=1.087, GBP=1.282, INR=0.0119)", font=font_code_sm, fill=GREEN)

            # Processing steps
            if i >= 170:
                steps = [
                    ("[1/4] ✔ Two-Tier Date Engine: Deducing DD/MM vs MM/DD (0% NaT dropped)", GREEN),
                    ("[2/4] ✔ Multi-Currency: Converted 100 rows using real-time FX rates", GREEN),
                    ("[3/4] ✔ Types & Accounting: ($12,865) -> -12865.27 | '00124' preserved", GREEN),
                    ("[4/4] ✔ Sheet Hygiene: Removed 'Grand Total' footer & archived to attrs", GREEN),
                ]
                y_s = 345
                max_step = min(len(steps), (i - 170) // 7 + 1)
                for s_idx in range(max_step):
                    txt, col = steps[s_idx]
                    draw.text((130, y_s), txt, font=font_code_sm, fill=col)
                    y_s += 28

        # SCENE 4: Pristine Output & Math (200 <= i < 270)
        else:
            draw.text((110, 125), ">>> print(clean_df.head(5))", font=font_code, fill=WHITE)
            
            clean_lines = [
                ("  customer_name    account_num  order_date   gross_revenue  margin_pct  notes       ", CYAN),
                ("--------------------------------------------------------------------------------", WIN_BORDER),
                ("  Acme Corp        '00124'      2024-03-25        1781.08       0.333   Standard    ", WHITE),
                ("  Wayne Ent        '00235'      2024-03-25      -12865.27      -0.098   Deficit     ", WHITE),
                ("  Massive Dynamic  '00280'      2024-12-14        6802.61       0.220   High VIP    ", WHITE),
                ("  Globex Corp      '00945'      2024-09-05        1397.28       0.175   Europe      ", WHITE),
                ("  Hooli Inc        '00234'      2024-05-09       59426.74       0.518   Renew       ", WHITE),
            ]
            y = 160
            for line_text, col in clean_lines:
                draw.text((110, y), line_text, font=font_code_sm, fill=col)
                y += 24
                
            # Success badge
            draw.text((110, 350), "✔ [BizPack Success] 100 rows cleaned in 24 ms. Zero dropped rows.", font=font_code_bold, fill=GREEN)
            
            # Pythonic Business formulas cards
            draw.rectangle([110, 390, 1170, 520], fill=(20, 30, 42), outline=CYAN, width=1)
            draw.text((130, 405), "⚡ BUILT-IN VECTORIZED BUSINESS FORMULAS:", font=font_title, fill=CYAN)
            draw.text((130, 440), ">>> df['tier'] = bp.xlookup(df['sku'], cat['sku'], cat['tier'])  # Fast exact match", font=font_code_sm, fill=WHITE)
            draw.text((130, 465), ">>> pareto = bp.pareto(df, 'customer', 'revenue')                  # 80/20 Rule", font=font_code_sm, fill=WHITE)
            draw.text((130, 490), ">>> growth = bp.growth(df, 'order_date', 'revenue', freq='M')      # MoM/YoY Deltas", font=font_code_sm, fill=WHITE)
            
            draw.text((110, 620), "Next: Boardroom export with `bp.format_for_display(clean_df)`", font=font_code, fill=GRAY)

        img.save(os.path.join(frames_dir, f"frame_{i:04d}.png"))
        if (i + 1) % 50 == 0 or i == TOTAL_FRAMES - 1:
            print(f"Generated {i + 1} / {TOTAL_FRAMES} frames...")

    print("All frames generated. Compiling video with ffmpeg...")
    
    # Compile MP4
    mp4_path = os.path.join("assets", "bizpack_demo.mp4")
    cmd_mp4 = [
        "ffmpeg", "-y",
        "-framerate", "24",
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        mp4_path
    ]
    subprocess.run(cmd_mp4, check=True)
    print(f"✔ Generated MP4: {mp4_path}")

    # Compile animated GIF (scaled to 800px width for fast loading on GitHub)
    gif_path = os.path.join("assets", "demo.gif")
    cmd_gif = [
        "ffmpeg", "-y",
        "-framerate", "16",
        "-i", os.path.join(frames_dir, "frame_%04d.png"),
        "-vf", "fps=16,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
        gif_path
    ]
    subprocess.run(cmd_gif, check=True)
    print(f"✔ Generated GIF: {gif_path}")

    # Clean up temp frames
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    print("✔ Cleaned up temporary frames.")

if __name__ == "__main__":
    create_frames()
