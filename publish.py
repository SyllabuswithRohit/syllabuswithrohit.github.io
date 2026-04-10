import os
import json
import time
import subprocess

print("=========================================")
print("🚀 SyllabusWithRohit - Auto Publisher")
print("=========================================")

# 1. Draft File Check
draft_file = "draft.txt"
if not os.path.exists(draft_file):
    print("❌ Error: 'draft.txt' file nahi mili. Pehle usme apna text paste karein.")
    exit()

with open(draft_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

if not content:
    print("❌ Error: 'draft.txt' khali hai. Text paste kijiye.")
    exit()

# 2. Book Details
title = input("📚 Kitab ka Title: ")
author = input("✍️ Original Writer ka naam: ")
category = input("🏷️ Category (eg. Philosophy, History): ")

filename = title.lower().replace(" ", "_") + ".html"
filepath = f"books/{filename}"

# 3. Kindle-Style HTML Generator
paragraphs = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])

book_html = f"""<!DOCTYPE html>
<html lang="hi" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | SyllabusWithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config={{darkMode:'class',theme:{{extend:{{colors:{{paper:'#fdfbf7',ink:'#1a1a1a',sepia:'#f4ecd8',darkPaper:'#121212',darkInk:'#d1d1d1'}},fontFamily:{{kindle:['Lora','serif']}}}}}}}}</script>
    <style>
        #pb {{ position:fixed; top:0; left:0; height:4px; background:#8b5a2b; width:0%; z-index:100; transition: width 0.2s; }}
        article p {{ hyphens:auto; margin-bottom: 2rem; font-size: 21px; line-height: 1.8; text-align: justify; }}
        article p:first-of-type::first-letter {{ float:left; font-size:4rem; line-height:1; padding-right:12px; font-weight:bold; color: #8b5a2b; }}
    </style>
</head>
<body class="bg-paper text-ink dark:bg-darkPaper dark:text-darkInk font-kindle transition-colors duration-500">
    <div id="pb"></div>
    <nav class="sticky top-0 w-full bg-paper/90 dark:bg-darkPaper/90 backdrop-blur-md z-40 border-b border-ink/5">
        <div class="max-w-3xl mx-auto px-6 py-4 flex justify-between items-center text-xs uppercase tracking-widest font-sans font-bold">
            <a href="../index.html" class="opacity-60 hover:opacity-100 hover:text-[#8b5a2b] transition-colors">← Back to Library</a>
            <div class="flex space-x-4">
                <button onclick="setTheme('light')" class="hover:text-[#8b5a2b]">Light</button>
                <button onclick="setTheme('sepia')" class="text-[#8b5a2b]">Sepia</button>
                <button onclick="setTheme('dark')" class="hover:text-[#8b5a2b]">Dark</button>
            </div>
        </div>
    </nav>
    <main class="max-w-[700px] mx-auto px-6 pt-20 pb-32">
        <header class="mb-16 text-center">
            <div class="text-sm font-sans uppercase tracking-widest text-[#8b5a2b] font-bold mb-4">{category}</div>
            <h1 class="text-4xl md:text-5xl font-bold mb-4 leading-tight italic">{title}</h1>
            <p class="text-lg opacity-70 italic mb-8">By {author}</p>
            <div class="h-1 w-16 bg-[#8b5a2b]/30 mx-auto"></div>
        </header>
        <article class="selection:bg-sepia selection:text-ink">{paragraphs}</article>
    </main>
    <script>
        window.onscroll = () => {{ document.getElementById("pb").style.width = ((document.documentElement.scrollTop)/(document.documentElement.scrollHeight-document.documentElement.clientHeight)*100)+"%"; }};
        function setTheme(t) {{
            const root = document.documentElement;
            root.classList.remove('dark', 'sepia');
            if (t === 'dark') root.classList.add('dark');
            else if (t === 'sepia') document.body.style.backgroundColor = '#f4ecd8';
            else document.body.style.backgroundColor = '';
            localStorage.setItem('theme', t);
        }}
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)
print(f"✅ Page Created: {filename}")

# 4. Update Library Index
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

library.append({"title": title, "author": author, "category": category, "link": f"books/{filename}"})
with open(library_file, 'w', encoding='utf-8') as f: json.dump(library, f, indent=4)

cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="group relative flex flex-col justify-between bg-white dark:bg-[#1a1a1a] border border-ink/5 dark:border-darkInk/10 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-[#8b5a2b] scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></div>
        <div>
            <span class="text-xs font-bold uppercase tracking-widest text-[#8b5a2b] mb-3 block font-sans">{book['category']}</span>
            <h3 class="text-2xl font-bold italic mb-2 leading-snug">{book['title']}</h3>
            <p class="text-sm opacity-70 italic font-sans">{book['author']}</p>
        </div>
        <div class="mt-8 flex items-center text-sm font-sans font-bold opacity-70 group-hover:text-[#8b5a2b] group-hover:opacity-100 transition-colors">
            <span>Read Book</span><span class="ml-2 group-hover:translate-x-1 transition-transform">→</span>
        </div>
    </a>"""

index_html = f"""<!DOCTYPE html><html lang="hi" class="scroll-smooth"><head><meta charset="UTF-8"><title>Library | SyllabusWithRohit</title><script src="https://cdn.tailwindcss.com"></script><script>tailwind.config={{darkMode:'class',theme:{{extend:{{colors:{{paper:'#fdfbf7',ink:'#1a1a1a',darkPaper:'#121212',darkInk:'#d1d1d1'}},fontFamily:{{kindle:['Lora','serif']}}}}}}}}</script></head><body class="bg-paper text-ink dark:bg-[#0a0a0a] dark:text-darkInk font-serif transition-colors duration-500"><nav class="w-full bg-paper/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-ink/5 sticky top-0 z-50"><div class="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center"><div class="text-xl font-bold italic font-sans uppercase tracking-widest">Syllabus<span class="text-[#8b5a2b]">With</span>Rohit</div></div></nav><header class="max-w-6xl mx-auto px-6 py-24"><h1 class="text-5xl md:text-7xl font-bold italic mb-6 leading-tight">Gyan Sabke <span class="text-[#8b5a2b]">Liye.</span></h1><p class="text-xl opacity-70 max-w-lg leading-relaxed">Bhari kitabein, aasaan Hinglish mein. Aapki apni digital library.</p></header><main class="max-w-6xl mx-auto px-6 pb-32"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{cards}</div></main></body></html>"""

with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)
print("✅ Homepage Updated!")

# 5. Clear Draft & Push to GitHub
with open(draft_file, 'w', encoding='utf-8') as f: f.write("")

print("⏳ Pushing to GitHub... Please wait.")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", f"Added book: {title}"], check=True)
subprocess.run(["git", "push"], check=True)

print("🌟 BINGO! Check your website after 1 minute.")
