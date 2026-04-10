import os
import json
import subprocess
import math
import re

print("=========================================")
print("💼 SyllabuswithRohit - V42.1 EXECUTIVE")
print("=========================================")

UPI_ID = "syllabuswithrohit@upi"
COFFEE_LINK = "https://buymeacoffee.com/SyllabuswithRohit"
YT_LINK = "https://www.youtube.com/@SyllabuswithRohit"

draft_file = "draft.txt"
if not os.path.exists(draft_file): open(draft_file, 'w').close()
with open(draft_file, 'r', encoding='utf-8') as f: content = f.read().strip()

shared_styles = """
    :root { --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; --font-size: 21px; --font-family: 'Lora', serif; }
    body.sepia { --bg: #f4ecd8; --text: #2c1e0f; --accent: #6f421a; }
    body.dark { --bg: #000000; --text: #e0e0e0; --accent: #555555; }
    body.red-mode { --bg: #000000; --text: #ff0000; --accent: #ff0000; }
    body { opacity: 1; transition: opacity 0.3s ease-out, background-color 0.4s, color 0.4s; background-color: var(--bg); color: var(--text); font-family: var(--font-family); overflow-x: hidden; }
    body.htmx-swapping { opacity: 0 !important; }
    
    .zen-nav { transition: transform 0.3s ease-in-out; }
    .zen-nav.hidden-nav { transform: translateY(-100%); }
    .hide-scrollbar::-webkit-scrollbar { display: none; }
    .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    
    /* V42: The Floating Dock Style */
    .dynamic-dock { position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%); background: rgba(20, 20, 20, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 40px; padding: 6px 12px; display: flex; align-items: center; gap: 8px; z-index: 999; box-shadow: 0 20px 40px rgba(0,0,0,0.3); transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s; }
    .dynamic-dock.hidden-dock { transform: translate(-50%, 150%); opacity: 0; pointer-events: none; }
    .dock-btn { background: transparent; color: #fff; border: none; border-radius: 50px; padding: 8px 12px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; font-family: sans-serif; display: flex; align-items: center; justify-content: center; opacity: 0.8; }
    .dock-btn:hover { opacity: 1; background: rgba(255,255,255,0.15); }
    .dock-divider { width: 1px; height: 18px; background: rgba(255,255,255,0.2); }
    
    /* Clean Top Nav Buttons */
    .top-btn { font-size: 10px; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; padding: 6px 12px; border-radius: 20px; background: transparent; border: 1px solid var(--accent); color: var(--text); cursor: pointer; transition: 0.2s; opacity: 0.6; }
    .top-btn:hover { opacity: 1; background: var(--text); color: var(--bg); }

    #scrollPercent { position: fixed; top: 0; left: 0; height: 3px; background: var(--accent); width: 0%; z-index: 100; transition: width 0.1s; }
    #timeRemaining { position: fixed; top: 15px; left: 50%; transform: translateX(-50%); font-size: 10px; font-weight: bold; font-family: sans-serif; letter-spacing: 2px; opacity: 0; transition: opacity 0.3s; z-index: 99; color: var(--text); background: var(--bg); padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.2); pointer-events: none;}
    
    article p { margin-bottom: 2.8rem; font-size: var(--font-size); line-height: 1.85; text-align: justify; transition: font-size 0.3s; }
    @media (max-width: 640px) { article p { line-height: 1.75; font-size: calc(var(--font-size) - 2px); } }
    .bionic-word b { font-weight: 800; opacity: 1; }
    .bionic-word { opacity: 0.85; }

    #selection-toolbar { display:none; position:absolute; background:#111; color:#fff; padding:8px; border-radius:12px; z-index:9999; box-shadow:0 10px 20px rgba(0,0,0,0.3); font-family:sans-serif; gap:6px; align-items:center;}
    .toolbar-btn { background:none; border:none; color:#fff; font-size:13px; font-weight:bold; cursor:pointer; padding:6px 12px; border-radius:6px; }
    .toolbar-btn:hover { background:rgba(255,255,255,0.1); }
    .toolbar-arrow { position:absolute; bottom:-6px; left:50%; transform:translateX(-50%); width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-top:6px solid #111; }
    
    #dictModal { display:none; position:fixed; bottom:30px; left:50%; transform:translateX(-50%); background:var(--bg); color:var(--text); border:2px solid var(--accent); padding:20px; border-radius:12px; z-index:10000; max-width:90%; width:400px; box-shadow:0 15px 30px rgba(0,0,0,0.2); font-family:sans-serif;}
    #supportModal { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-blur: 5px; }
    .modal-content { background:var(--bg); color:var(--text); padding:40px; border-radius:15px; max-width:380px; width:100%; text-align:center; border: 2px solid var(--accent); position:relative; }
    .close-btn { position:absolute; top:10px; right:20px; font-size:32px; color:var(--text); opacity:0.6; cursor:pointer; background:none; border:none; }

    #quoteGenModal { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:10000; align-items:center; justify-content:center; padding:20px; flex-direction:column; backdrop-blur: 10px;}
    #quoteCanvas { background: #1a1a1a; max-width: 100%; height: auto; box-shadow: 0 20px 50px rgba(0,0,0,0.5); border-radius: 12px; }
    .canvas-controls { margin-top: 20px; display: flex; gap: 10px; }
"""

def generate_book_html(book_title, book_author, book_category, book_time, paragraphs_html, filename, word_count):
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{book_title} | SyllabuswithRohit</title>
    <meta name="theme-color" content="#fdfbf7">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.11"></script>
    <style>{shared_styles}</style>
</head>
<body hx-boost="true">
    <div id="scrollPercent"></div>
    <div id="timeRemaining"></div>

    <div id="selection-toolbar">
        <button onclick="defineWord()" class="toolbar-btn">📖 Define</button>
        <button onclick="saveQuote('{filename}', '{book_title}')" class="toolbar-btn" style="color:#FFDD00;">📝 Save</button>
        <button onclick="openQuoteGenerator('{book_title}')" class="toolbar-btn" style="color:#00e676;">📸 Share</button>
        <div class="toolbar-arrow" id="toolbar-arrow"></div>
    </div>

    <div id="quoteGenModal">
        <button onclick="document.getElementById('quoteGenModal').style.display='none'" class="absolute top-4 right-6 text-3xl text-white opacity-60 hover:opacity-100">&times;</button>
        <canvas id="quoteCanvas" width="1080" height="1080"></canvas>
        <div class="canvas-controls">
            <button onclick="downloadQuote()" class="bg-white text-black px-6 py-3 rounded-full font-bold text-sm tracking-wider uppercase hover:bg-gray-200 transition">📥 Download</button>
            <button onclick="nativeShareImage()" id="nativeShareBtn" class="bg-[#00e676] text-black px-6 py-3 rounded-full font-bold text-sm tracking-wider uppercase hover:bg-[#00c853] transition hidden">📤 Share</button>
        </div>
    </div>

    <div id="dictModal"><button onclick="document.getElementById('dictModal').style.display='none'" class="absolute top-2 right-4 text-xl opacity-50">&times;</button><h3 id="dictWord" class="font-bold text-xl mb-2 italic"></h3><p id="dictDef" class="text-sm opacity-80 leading-relaxed"></p></div>

    <nav id="navbar" class="zen-nav flex justify-between items-center px-4 py-4 fixed w-full top-0 bg-transparent z-50 pointer-events-none">
        <a href="../index.html" class="top-btn pointer-events-auto" hx-target="body" style="background:var(--bg);">← Library</a>
        <button onclick="showModal()" class="top-btn pointer-events-auto" style="background:var(--bg);">Support</button>
    </nav>

    <div id="dock" class="dynamic-dock">
        <button onclick="toggleFullscreen()" class="dock-btn" title="Fullscreen">⛶</button>
        <div class="dock-divider"></div>
        <button id="audioBtn" onclick="toggleAudio()" class="dock-btn" title="Focus Audio">🎧</button>
        <button id="scrollBtn" onclick="toggleAutoScroll()" class="dock-btn" title="Auto Scroll">⏷</button>
        <button onclick="toggleBionic()" class="dock-btn" title="Speed Reading">⚡</button>
        <div class="dock-divider"></div>
        <button onclick="saveBookmark('{filename}', '{book_title}')" class="dock-btn" title="Save Bookmark">🔖</button>
        <button onclick="cycleFontFamily()" class="dock-btn" title="Change Font Style">T</button>
        <button onclick="cycleFontSize()" class="dock-btn" title="Change Size">Aa</button>
        <button onclick="cycleTheme()" class="dock-btn" title="Change Theme">🌓</button>
    </div>

    <main class="max-w-[680px] mx-auto px-6 pt-24 pb-32">
        <header class="text-center mb-16">
            <div class="text-[10px] tracking-[4px] uppercase font-bold opacity-50 mb-4">{book_category} • {book_time} MIN READ</div>
            <h1 class="text-4xl md:text-5xl font-bold italic mb-4 leading-tight">{book_title}</h1>
            <p class="text-lg opacity-60 italic">By {book_author}</p>
        </header>
        <article id="content" data-words="{word_count}" data-time="{book_time}">{paragraphs_html}</article>
    </main>

    <div id="supportModal">
        <div class="modal-content">
            <button onclick="closeModal()" class="close-btn">&times;</button>
            <h2 class="text-2xl font-bold mb-4 italic">Support</h2>
            <div style="background:white; padding:10px; border-radius:10px; display:inline-block; margin-bottom:20px; border: 2px solid var(--accent);"><img src="../qr.png" class="w-40 h-40 object-contain"></div>
            <p class="text-sm opacity-80 mb-6 font-sans">Aapka support mujhe aur books laane me madad karega.</p>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" style="background:var(--accent); color:var(--bg); padding:14px; border-radius:30px; display:block; font-size:12px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; text-decoration:none;">Pay via UPI App</a>
            <a href="{COFFEE_LINK}" target="_blank" style="background:#FFDD00; color:#000; padding:14px; border-radius:30px; display:block; font-size:12px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; text-decoration:none;">Buy me a Coffee</a>
        </div>
    </div>

    <script>
        (function() {{
            const totalMins = parseInt(document.getElementById('content').getAttribute('data-time'));
            let wordsRead = parseInt(localStorage.getItem('wordsRead') || 0); let articleWords = parseInt(document.getElementById('content').getAttribute('data-words')); let hasCounted = false;

            window.setTheme = function(t) {{ document.body.className = t; localStorage.setItem('theme', t); let colors = {{ 'light': '#fdfbf7', 'sepia': '#f4ecd8', 'dark': '#000000', 'red-mode': '#000000' }}; document.querySelector('meta[name="theme-color"]').setAttribute('content', colors[t]); }}
            setTheme(localStorage.getItem('theme') || 'light');
            window.cycleTheme = function() {{ const themes = ['light', 'sepia', 'dark', 'red-mode']; let curr = themes.indexOf(localStorage.getItem('theme')); window.setTheme(themes[(curr + 1) % themes.length]); }};
            
            let sizes = [18, 21, 24, 28]; let currentFont = parseInt(localStorage.getItem('fontSize')) || 21; document.documentElement.style.setProperty('--font-size', currentFont + 'px');
            window.cycleFontSize = function() {{ let curr = sizes.indexOf(currentFont) !== -1 ? sizes.indexOf(currentFont) : 1; currentFont = sizes[(curr + 1) % sizes.length]; document.documentElement.style.setProperty('--font-size', currentFont + 'px'); localStorage.setItem('fontSize', currentFont); }};
            
            const fonts = ["'Lora', serif", "'Inter', sans-serif", "monospace"]; let fontIdx = parseInt(localStorage.getItem('fontIdx') || 0); document.documentElement.style.setProperty('--font-family', fonts[fontIdx]);
            window.cycleFontFamily = function() {{ fontIdx = (fontIdx + 1) % fonts.length; document.documentElement.style.setProperty('--font-family', fonts[fontIdx]); localStorage.setItem('fontIdx', fontIdx); }}

            window.toggleFullscreen = function() {{ if (!document.fullscreenElement) {{ document.documentElement.requestFullscreen().catch(err => {{}}); }} else {{ if (document.exitFullscreen) {{ document.exitFullscreen(); }} }} }}

            const bookId = "pos_{filename}"; let savedPos = localStorage.getItem(bookId); if(savedPos) window.scrollTo({{top: savedPos, behavior: 'auto'}});

            let timer; let lastScrollTop = 0; 
            const navbar = document.getElementById('navbar'); const dock = document.getElementById('dock'); 
            const scrollBar = document.getElementById('scrollPercent'); const timeLabel = document.getElementById('timeRemaining');
            
            window.onscroll = () => {{
                const winScroll = document.documentElement.scrollTop || document.body.scrollTop; 
                const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
                let scrolled = (winScroll / height) * 100; if (scrolled < 0) scrolled = 0; if (scrolled > 100) scrolled = 100;
                
                scrollBar.style.width = scrolled + "%"; 
                
                let minsLeft = Math.max(1, Math.ceil(totalMins - (totalMins * (scrolled/100))));
                if(scrolled > 98) minsLeft = 0;
                timeLabel.innerText = minsLeft > 0 ? minsLeft + " mins left" : "Finished";
                timeLabel.style.opacity = "1";
                
                if (scrolled > 80 && !hasCounted) {{ localStorage.setItem('wordsRead', wordsRead + articleWords); hasCounted = true; }}
                
                if (winScroll > lastScrollTop && winScroll > 100) {{ navbar.classList.add('hidden-nav'); dock.classList.add('hidden-dock'); }} 
                else {{ navbar.classList.remove('hidden-nav'); dock.classList.remove('hidden-dock'); }}
                
                lastScrollTop = winScroll <= 0 ? 0 : winScroll; localStorage.setItem(bookId, winScroll);
                clearTimeout(timer); timer = setTimeout(() => {{ timeLabel.style.opacity = "0"; dock.classList.add('hidden-dock'); }}, 2500);
            }};

            document.addEventListener('mousemove', () => {{ dock.classList.remove('hidden-dock'); clearTimeout(timer); timer = setTimeout(() => dock.classList.add('hidden-dock'), 2500); }});
            document.addEventListener('touchstart', () => {{ dock.classList.remove('hidden-dock'); clearTimeout(timer); timer = setTimeout(() => dock.classList.add('hidden-dock'), 2500); }}, {{passive: true}});

            window.showModal = function() {{ document.getElementById('supportModal').style.display = 'flex'; }}
            window.closeModal = function() {{ document.getElementById('supportModal').style.display = 'none'; }}
            window.saveBookmark = function(id, title) {{ let marks = JSON.parse(localStorage.getItem('myBookmarks') || '[]'); if(!marks.find(b => b.id === id)) {{ marks.push({{id: id, title: title, link: "books/" + id + ".html"}}); localStorage.setItem('myBookmarks', JSON.stringify(marks)); alert("Book saved to your Library!"); }} else {{ alert("Already saved in your Library."); }} }}

            if(!window.hasSelectionListener) {{
                window.hasSelectionListener = true; const toolbar = document.getElementById('selection-toolbar'); const arrow = document.getElementById('toolbar-arrow');
                document.addEventListener('selectionchange', () => {{
                    const selection = window.getSelection(); window.selectedText = selection.toString().trim();
                    if(window.selectedText.length > 0 && window.selectedText.length < 350) {{
                        toolbar.style.display = 'flex'; const isTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
                        if(isTouch) {{ toolbar.style.position = 'fixed'; toolbar.style.bottom = '20px'; toolbar.style.top = 'auto'; toolbar.style.left = '50%'; toolbar.style.transform = 'translateX(-50%)'; arrow.style.display = 'none';
                        }} else {{ const rect = selection.getRangeAt(0).getBoundingClientRect(); toolbar.style.position = 'absolute'; toolbar.style.top = (window.scrollY + rect.top - 50) + 'px'; toolbar.style.left = (rect.left + (rect.width / 2) - (toolbar.offsetWidth / 2)) + 'px'; toolbar.style.transform = 'none'; arrow.style.display = 'block'; }}
                    }} else {{ toolbar.style.display = 'none'; }}
                }});
            }}

            window.saveQuote = function(bookId, bookTitle) {{
                if(!window.selectedText) return; let quotes = JSON.parse(localStorage.getItem('myQuotes') || '[]');
                quotes.push({{text: window.selectedText, book: bookTitle}}); localStorage.setItem('myQuotes', JSON.stringify(quotes));
                document.getElementById('selection-toolbar').style.display = 'none'; window.getSelection().removeAllRanges(); alert("Quote Saved to Notebook!");
            }};
            
            window.openQuoteGenerator = function(bookTitle) {{
                if(!window.selectedText) return;
                document.getElementById('selection-toolbar').style.display = 'none'; document.getElementById('quoteGenModal').style.display = 'flex';
                const canvas = document.getElementById('quoteCanvas'); const ctx = canvas.getContext('2d'); const theme = localStorage.getItem('theme') || 'light';
                const bgCol = theme === 'dark' || theme === 'red-mode' ? '#121212' : (theme === 'sepia' ? '#f4ecd8' : '#fdfbf7');
                const textCol = theme === 'dark' ? '#ffffff' : (theme === 'red-mode' ? '#ff0000' : '#1a1a1a');
                const accentCol = theme === 'red-mode' ? '#ff0000' : '#888888';
                
                ctx.fillStyle = bgCol; ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = textCol; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                ctx.font = 'italic 120px Lora, serif'; ctx.globalAlpha = 0.1; ctx.fillText('"', 100, 150); ctx.globalAlpha = 1.0;
                
                ctx.font = 'italic 52px Lora, serif'; const words = window.selectedText.split(' '); let line = ''; let y = 450 - (Math.min(window.selectedText.length / 50, 4) * 30); const maxWidth = 800;
                for(let n = 0; n < words.length; n++) {{ let testLine = line + words[n] + ' '; let metrics = ctx.measureText(testLine); if (metrics.width > maxWidth && n > 0) {{ ctx.fillText(line, canvas.width / 2, y); line = words[n] + ' '; y += 75; }} else {{ line = testLine; }} }}
                ctx.fillText(line, canvas.width / 2, y);
                
                /* ========================================================
                   BUG FIX: Using ${{bookTitle}} to prevent Python f-string crash 
                   ======================================================== */
                ctx.fillStyle = accentCol; ctx.font = 'bold 30px Inter, sans-serif'; ctx.fillText(`— ${{bookTitle}} —`, canvas.width / 2, y + 120);
                ctx.font = 'bold 22px Inter, sans-serif'; ctx.letterSpacing = '5px'; ctx.fillText('SYLLABUSWITHROHIT', canvas.width / 2, 1000);
                
                if (navigator.share && navigator.canShare) {{ document.getElementById('nativeShareBtn').style.display = 'block'; }} window.getSelection().removeAllRanges();
            }};

            window.downloadQuote = function() {{ const canvas = document.getElementById('quoteCanvas'); const link = document.createElement('a'); link.download = 'Syllabus_Quote.png'; link.href = canvas.toDataURL('image/png'); link.click(); }};
            window.nativeShareImage = async function() {{ const canvas = document.getElementById('quoteCanvas'); canvas.toBlob(async (blob) => {{ const file = new File([blob], 'quote.png', {{ type: 'image/png' }}); try {{ await navigator.share({{ title: 'SyllabuswithRohit Quote', files: [file] }}); }} catch(e) {{}} }}); }};
            window.defineWord = async function() {{ if(!window.selectedText || window.selectedText.includes(" ")) {{ alert("Please select a single word to define."); return; }} try {{ let res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + window.selectedText); let data = await res.json(); let def = data[0].meanings[0].definitions[0].definition; document.getElementById('dictWord').innerText = window.selectedText; document.getElementById('dictDef').innerText = def; document.getElementById('dictModal').style.display = 'block'; document.getElementById('selection-toolbar').style.display = 'none'; }} catch(e) {{ alert("Meaning not found for: " + window.selectedText); }} }};

            window.isBionic = false; 
            window.toggleBionic = function() {{ const contentDiv = document.getElementById('content'); if (window.isBionic) {{ location.reload(); }} else {{ let pTags = contentDiv.getElementsByTagName('p'); for (let p of pTags) {{ let html = p.innerHTML; p.innerHTML = html.replace(/(<[^>]+>)|([A-Za-z\u0900-\u097F]+)/g, function(match, tag, word) {{ if (tag) return tag; if (word.length <= 1) return word; let mid = Math.ceil(word.length / 2); return `<span class="bionic-word"><b>${{word.slice(0, mid)}}</b>${{word.slice(mid)}}</span>`; }}); }} window.isBionic = true; }} }};

            window.scrollInterval = null; window.isScrolling = false;
            window.toggleAutoScroll = function() {{ if(window.isScrolling) {{ clearInterval(window.scrollInterval); window.isScrolling = false; }} else {{ window.scrollInterval = setInterval(() => window.scrollBy(0, 1), 30); window.isScrolling = true; }} }};
            window.audioCtx = null; window.isPlaying = false;
            window.toggleAudio = function() {{ if(!window.audioCtx) {{ window.audioCtx = new (window.AudioContext || window.webkitAudioContext)(); let bufferSize = 2 * window.audioCtx.sampleRate, noiseBuffer = window.audioCtx.createBuffer(1, bufferSize, window.audioCtx.sampleRate), output = noiseBuffer.getChannelData(0); let lastOut = 0; for (let i = 0; i < bufferSize; i++) {{ let white = Math.random() * 2 - 1; output[i] = (lastOut + (0.02 * white)) / 1.02; lastOut = output[i]; output[i] *= 3.5; }} let brownNoise = window.audioCtx.createBufferSource(); brownNoise.buffer = noiseBuffer; brownNoise.loop = true; let noiseNode = window.audioCtx.createGain(); noiseNode.gain.value = 0.1; brownNoise.connect(noiseNode); noiseNode.connect(window.audioCtx.destination); brownNoise.start(0); }} if(window.isPlaying) {{ window.audioCtx.suspend(); window.isPlaying = false; }} else {{ window.audioCtx.resume(); window.isPlaying = true; }} }};
        }})();
    </script>
</body>
</html>"""

# --- BULK UPDATE LIBRARY ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

for b in library:
    old_filepath = b['link']
    if os.path.exists(old_filepath):
        with open(old_filepath, 'r', encoding='utf-8') as old_f: old_html = old_f.read()
        article_match = re.search(r'<article[^>]*>(.*?)</article>', old_html, re.DOTALL)
        if article_match:
            old_paras = article_match.group(1)
            b_word_count = len(re.sub(r'<[^>]+>', '', old_paras).split())
            b_filename = old_filepath.split('/')[-1].replace('.html', '')
            new_html = generate_book_html(b['title'], b['author'], b['category'], b.get('time', 5), old_paras, b_filename, b_word_count)
            with open(old_filepath, 'w', encoding='utf-8') as new_f: new_f.write(new_html)

if content:
    word_count = len(content.split())
    reading_time = math.ceil(word_count / 200)
    title = input("📚 Nayi Kitab ka Title: ")
    author = input("✍️ Original Writer: ")
    category = input("🏷️ Category: ")
    filename = title.lower().replace(" ", "_")
    filepath = f"books/{filename}.html"
    paras = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])
    new_html = generate_book_html(title, author, category, reading_time, paras, filename, word_count)
    with open(filepath, 'w', encoding='utf-8') as f: f.write(new_html)
    
    new_book = {"title": title, "author": author, "category": category, "link": filepath, "time": reading_time, "words": word_count}
    if not any(b['title'] == title for b in library): library.append(new_book)
    else:
        for idx, b in enumerate(library):
            if b['title'] == title: library[idx] = new_book

with open(library_file, "w", encoding='utf-8') as f: json.dump(library, f, indent=4)

# --- GENERATE HOMEPAGE ---
cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" hx-target="body" class="organic-hover book-card group p-8 border-l-[10px] flex flex-col justify-between min-h-[250px] relative overflow-hidden" style="background:var(--bg); border-color:var(--accent); border-top:1px solid rgba(128,128,128,0.2); border-right:1px solid rgba(128,128,128,0.2); border-bottom:1px solid rgba(128,128,128,0.2); box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 4px;">
        <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-[var(--text)] to-transparent opacity-[0.03] rounded-bl-full pointer-events-none"></div>
        <div>
            <span class="text-[9px] font-bold tracking-[3px] opacity-50 mb-4 block uppercase font-sans">{book['category']} • {book.get('time', 5)} MIN</span>
            <h3 class="book-title text-2xl font-bold italic leading-tight mb-2" style="color:var(--text);">{book['title']}</h3>
            <p class="text-sm opacity-70 italic" style="color:var(--text);">{book['author']}</p>
        </div>
        <div class="text-[10px] font-bold tracking-[2px] uppercase mt-6 group-hover:translate-x-2 transition-transform duration-300" style="color:var(--text);">Read Book →</div>
    </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Library | SyllabuswithRohit</title>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#fdfbf7">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.11"></script>
    <style>{shared_styles}</style>
</head>
<body hx-boost="true">
    <nav class="flex justify-between items-center px-4 py-4 sticky top-0 bg-transparent z-50 pointer-events-none">
        <div class="top-btn font-sans uppercase opacity-80 pointer-events-auto" style="background:var(--bg); border:none;">LIBRARY</div>
        <button onclick="showModal()" class="top-btn pointer-events-auto" style="background:var(--bg);">SUPPORT</button>
    </nav>
    <main class="max-w-6xl mx-auto px-6 py-8">
        <div class="text-center mb-12">
            <div class="ambient-aura mx-auto mb-6"><img src="myprofile.jpg" class="w-24 h-24 rounded-full object-cover relative z-10 shadow-xl" style="border: 3px solid var(--accent);"></div>
            <div class="flex flex-col md:flex-row justify-center items-center gap-6 mb-10"><h1 class="shimmer-text text-4xl md:text-5xl font-bold italic tracking-tight">SyllabuswithRohit</h1></div>
            <div class="flex justify-center gap-4 mb-10">
                <button onclick="exportData()" class="text-[11px] font-bold tracking-[1px] uppercase opacity-60 hover:opacity-100 border border-current px-4 py-2 rounded-full transition-opacity hover:-translate-y-1">☁️ Backup</button>
                <label class="text-[11px] font-bold tracking-[1px] uppercase opacity-60 hover:opacity-100 border border-current px-4 py-2 rounded-full cursor-pointer transition-opacity hover:-translate-y-1">📥 Restore<input type="file" accept=".json" onchange="importData(event)" class="hidden"></label>
            </div>
        </div>

        <div class="max-w-md mx-auto mb-16 relative"><input type="text" id="searchBox" onkeyup="filterBooks()" placeholder="Search books..." class="w-full px-6 py-4 rounded-full border-2 text-sm font-sans focus:outline-none transition-colors" style="background:transparent; border-color:var(--accent); color:var(--text);"></div>
        
        <div id="bookmarks-section" class="mb-12 hidden"><h2 class="text-xs font-bold tracking-[3px] uppercase opacity-50 mb-6 font-sans">🔖 Your Bookmarks</h2><div id="bookmarks-container" class="flex gap-4 overflow-x-auto pb-4 hide-scrollbar"></div></div>
        
        <div id="notebook-section" class="mb-16 hidden"><h2 class="text-xs font-bold tracking-[3px] uppercase opacity-50 mb-6 font-sans">📝 My Notebook</h2><div id="quotes-container" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div></div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" id="bookGrid">{cards}</div>
    </main>

    <div id="supportModal"><div class="modal-content"><button onclick="closeModal()" class="close-btn">&times;</button><h2 class="text-2xl font-bold mb-4 italic">Support</h2><div style="background:white; padding:10px; border-radius:10px; display:inline-block; margin-bottom:20px; border: 2px solid var(--accent);"><img src="qr.png" class="w-40 h-40 object-contain"></div><p class="text-sm opacity-80 mb-6 font-sans">Aapka support mujhe aur books laane me madad karega.</p><a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" class="theme-btn-primary" style="background:var(--accent); color:var(--bg); padding:14px; border-radius:30px; display:block; font-size:12px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; text-decoration:none;">Pay via UPI App</a><a href="{COFFEE_LINK}" target="_blank" style="background:#FFDD00; color:#000; padding:14px; border-radius:30px; display:block; font-size:12px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; text-decoration:none;">Buy me a Coffee</a></div></div>

    <script>
        (function() {{
            window.setTheme = function(t) {{ document.body.className = t; localStorage.setItem('theme', t); let colors = {{ 'light': '#fdfbf7', 'sepia': '#f4ecd8', 'dark': '#000000', 'red-mode': '#000000' }}; document.querySelector('meta[name="theme-color"]').setAttribute('content', colors[t]); }}
            setTheme(localStorage.getItem('theme') || 'light');
            window.showModal = function() {{ document.getElementById('supportModal').style.display = 'flex'; }}
            window.closeModal = function() {{ document.getElementById('supportModal').style.display = 'none'; }}
            
            window.filterBooks = function() {{ let input = document.getElementById('searchBox').value.toLowerCase(); let cards = document.getElementsByClassName('book-card'); for (let i = 0; i < cards.length; i++) {{ let title = cards[i].querySelector('.book-title').innerText.toLowerCase(); if (title.indexOf(input) > -1) cards[i].style.display = 'flex'; else cards[i].style.display = 'none'; }} }}
            
            let marks = JSON.parse(localStorage.getItem('myBookmarks') || '[]');
            if(marks.length > 0) {{ document.getElementById('bookmarks-section').classList.remove('hidden'); let container = document.getElementById('bookmarks-container'); marks.forEach(m => {{ container.innerHTML += `<a href="${{m.link}}" hx-target="body" class="organic-hover shrink-0 w-64 p-6 border-l-[6px] transition-transform hover:-translate-y-1" style="background:var(--bg); border-color:var(--accent); border-top:1px solid rgba(128,128,128,0.2); border-right:1px solid rgba(128,128,128,0.2); border-bottom:1px solid rgba(128,128,128,0.2);"><h3 class="font-bold italic text-lg" style="color:var(--text);">${{m.title}}</h3><p class="text-[9px] uppercase tracking-[2px] mt-4 opacity-50" style="color:var(--text);">Resume →</p></a>`; }}); }}

            let quotes = JSON.parse(localStorage.getItem('myQuotes') || '[]');
            if(quotes.length > 0) {{ document.getElementById('notebook-section').classList.remove('hidden'); let qContainer = document.getElementById('quotes-container'); quotes.forEach(q => {{ qContainer.innerHTML += `<div class="p-6 rounded-lg organic-hover" style="background:var(--bg); border:1px solid rgba(128,128,128,0.2);"><p class="italic opacity-80 mb-3" style="color:var(--text);">"${{q.text}}"</p><p class="text-[10px] font-bold tracking-[2px] uppercase opacity-50" style="color:var(--text);">- ${{q.book}}</p></div>`; }}); }}

            window.exportData = function() {{ const data = {{ myBookmarks: localStorage.getItem('myBookmarks'), myQuotes: localStorage.getItem('myQuotes') }}; const blob = new Blob([JSON.stringify(data)], {{type: 'application/json'}}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'SyllabusWithRohit_Backup.json'; a.click(); }};
            window.importData = function(event) {{ const file = event.target.files[0]; if (file) {{ const reader = new FileReader(); reader.onload = function(e) {{ try {{ const data = JSON.parse(e.target.result); if(data.myBookmarks) localStorage.setItem('myBookmarks', data.myBookmarks); if(data.myQuotes) localStorage.setItem('myQuotes', data.myQuotes); alert('Data Restored! Refreshing...'); location.reload(); }} catch(err) {{ alert('Invalid Backup File.'); }} }}; reader.readAsText(file); }} }};

            if('serviceWorker' in navigator) {{ navigator.serviceWorker.register('sw.js'); }}
        }})();
    </script>
</body>
</html>"""
with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "V42.1 Executive Fix: Corrected python f-string variable escape in canvas generation"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 EXECUTIVE FLAWLESS LIVE! Python bug has been permanently squashed.")
