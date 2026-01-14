import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import base64


try:
    url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("SYSTEM_ERROR: Secure credentials missing in Streamlit Secrets.")

st.set_page_config(page_title="ReconX Intelligence", page_icon="🛡️", layout="wide")


st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .status-bar { background: #161b22; border: 1px solid #30363d; padding: 12px 20px; border-radius: 6px; margin-bottom: 20px; display: flex; justify-content: space-between; }
    .shop-card { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; text-align: center; height: 100%; }
    .price { color: #58a6ff; font-size: 22px; font-weight: bold; }
    .log-box { background: #010409; border: 1px solid #30363d; padding: 10px; margin-top: 5px; border-radius: 4px; font-size: 13px; color: #8b949e; }
    .stButton>button { border-radius: 6px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)


if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ ReconX Intelligence Platform")
    t1, t2 = st.tabs(["🔐 SYSTEM AUTH", "📝 REQUEST ACCESS"])
    with t1:
        e = st.text_input("CORPORATE EMAIL")
        
        p = st.text_input("PASSWORD", type="password") 
        if st.button("AUTHORIZE ACCESS"):
            try:
                auth = supabase.auth.sign_in_with_password({"email": e, "password": p})
                st.session_state.user = auth.user
                st.rerun()
            except: st.error("Authentication Failed.")
    with t2:
        ne = st.text_input("REGISTRATION EMAIL")
        nu = st.text_input("ASSIGNED USERNAME")
        np = st.text_input("PASSWORD", type="password")
        if st.button("INITIALIZE PROFILE"):
            try:
                res = supabase.auth.sign_up({"email": ne, "password": np})
                if res.user:
                    supabase.table("profiles").insert({"id": res.user.id, "username": nu, "rank": "USER", "credits": 10}).execute()
                    st.success("Account initialized.")
            except: st.error("Registration Error.")

else:
   
    profile = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    with st.sidebar:
        st.subheader("📁 SESSION ANALYST")
        st.caption(f"AGENT: {profile['username']} | RANK: {profile['rank']}")
        st.divider()
        menu = st.radio("NAVIGATION", ["Intelligence Core", "Session Logs", "Licensing & Credits", "Admin Control" if profile['rank'] == 'ROOT' else None])
        st.divider()
        if st.button("TERMINATE SESSION"):
            st.session_state.user = None
            st.rerun()

    
    if menu == "Licensing & Credits":
        st.title("💳 Service Licenses")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="shop-card"><h3>BASIC</h3><div class="price">Free</div><p>10 Credits / session<br>Standard Analysis</p></div>', unsafe_allow_html=True)
            st.button("Active Tier", disabled=True)
        with c2:
            st.markdown('<div class="shop-card"><h3>ENTERPRISE</h3><div class="price">$29.99/mo</div><p>Unlimited Credits<br>High-Priority Support</p></div>', unsafe_allow_html=True)
            if st.button("Upgrade Now"): st.info("Contact sales@reconx.ai")

    elif menu == "Session Logs":
        st.title("📜 Investigation Archives")
        if "messages" in st.session_state:
            for i in range(0, len(st.session_state.messages), 2):
                st.markdown(f"**Query:** {st.session_state.messages[i]['content']}")
                st.markdown(f'<div class="log-box">{st.session_state.messages[i+1]["content"][:250]}...</div>', unsafe_allow_html=True)
                st.divider()

    elif menu == "Admin Control" and profile['rank'] == 'ROOT':
        st.title("⚙️ ROOT_MANAGEMENT")
        users = supabase.table("profiles").select("*").execute().data
        st.table(users)

    else:
       
        st.markdown(f'<div class="status-bar"><span>SYSTEM_STATUS: SECURE</span><span>CREDITS: {profile["credits"] if profile["rank"] != "ROOT" else "INF"}</span></div>', unsafe_allow_html=True)
        
        cols = st.columns(4)
        cmd = None
        if cols[0].button("🌐 NETWORK"): cmd = "Perform network scan for: "
        if cols[1].button("📱 MOBILE"): cmd = "Mobile data lookup for: "
        if cols[2].button("👤 IDENTITY"): cmd = "Digital footprint for: "
        if cols[3].button("📍 GEOSPATIAL"): cmd = "Geographic analysis for: "

        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Enter analysis target..."):
            if profile['rank'] != 'ROOT' and profile['credits'] <= 0:
                st.warning("Insufficient credits.")
            else:
                full_q = (cmd or "") + prompt
                st.session_state.messages.append({"role": "user", "content": full_q})
                with st.chat_message("user"): st.markdown(full_q)
                
                with st.chat_message("assistant"):
                    
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": "You are ReconX Intelligence. Professional OSINT assistant. If the user speaks French, reply in French."}] + st.session_state.messages
                    )
                    ans = res.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    if profile['rank'] != 'ROOT':
                        supabase.table("profiles").update({"credits": profile['credits'] - 1}).eq("id", profile['id']).execute()
                    st.rerun()
