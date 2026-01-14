import streamlit as st
from groq import Groq
from supabase import create_client, Client
import datetime
import base64


try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("ERREUR : Secrets (SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY) manquants.")

st.set_page_config(page_title="ReconX - Terminal", page_icon="📟", layout="wide")


def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def sign_in(email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except: return None


st.markdown("""
    <style>
    /* Fond total noir et police monospaced */
    .stApp { background-color: #000000; color: #00FF00; font-family: 'Consolas', 'Monaco', monospace; }
    
    /* Header Terminal */
    .terminal-header {
        background: #0a0a0a; border: 1px solid #1a1a1a;
        padding: 10px; border-radius: 2px; border-left: 3px solid #00FF00;
        margin-bottom: 20px; font-size: 0.9rem;
    }
    
    /* Input Chat */
    .stChatInputContainer { background-color: #050505 !important; border: 1px solid #1a1a1a !important; }
    
    /* Boutons style Terminal */
    .stButton>button { 
        width: 100%; border: 1px solid #1a1a1a; background: #000000; color: #00FF00; 
        border-radius: 0px; text-transform: uppercase; font-size: 0.75rem; height: 40px;
    }
    .stButton>button:hover { border-color: #00FF00; color: #00FF00; background: #050505; }
    
    /* Messages */
    .stChatMessage { background-color: #050505 !important; border: 1px solid #111 !important; border-radius: 0px !important; }
    code { color: #00FF00 !important; background: #0a0a0a !important; border: 1px solid #1a1a1a !important; }
    
    /* Sidebar sombre */
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #111; }
    </style>
    """, unsafe_allow_html=True)


if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("📟 RECON_X LOGIN")
    e = st.text_input("AUTH_EMAIL")
    p = st.text_input("AUTH_PWD", type="password")
    if st.button("> ACCESS_GRANTED"):
        auth = sign_in(e, p)
        if auth: 
            st.session_state.user = auth.user
            st.rerun()
else:
    
    profile = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    with st.sidebar:
        st.markdown(f"### 🖥️ SESSION_INFO")
        st.code(f"USER: {profile['username']}\nRANK: {profile['rank']}\nSTATUS: ONLINE")
        
        st.divider()
        menu = st.radio("CORE_MENU", ["Terminal", "Admin Panel" if profile['rank'] == 'ROOT' else None])
        uploaded_file = st.file_uploader("📥 OPTICAL_SCAN", type=["png", "jpg", "jpeg"])
        
        if st.button("> SHUTDOWN"):
            st.session_state.user = None
            st.rerun()

    if menu == "Admin Panel" and profile['rank'] == 'ROOT':
        st.title("🛰️ ROOT_CONTROL")
        users = supabase.table("profiles").select("*").execute().data
        for u in users:
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.code(u['username'])
            new_r = c2.selectbox("LVL", ["USER", "PREMIUM", "ROOT"], key=u['id'], index=["USER", "PREMIUM", "ROOT"].index(u['rank']))
            if c3.button("SAVE", key=f"b_{u['id']}"):
                supabase.table("profiles").update({"rank": new_r}).eq("id", u['id']).execute()
                st.rerun()

    else:
        
        st.markdown(f'<div class="terminal-header">root@reconx:~# credits:{profile["credits"] if profile["rank"] != "ROOT" else "INF"} status:connected</div>', unsafe_allow_html=True)
        
        
        cols = st.columns(4)
        btn_query = None
        if cols[0].button("[ NETWORK ]"): btn_query = "Scan IP/Domain: "
        if cols[1].button("[ MOBILE ]"): btn_query = "Phone OSINT: "
        if cols[2].button("[ SOCIAL ]"): btn_query = "Username search: "
        if cols[3].button("[ GEOLOC ]"): btn_query = "Geoloc analyse: "

       
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        
        user_input = st.chat_input("Command_prompt...")
        
        if btn_query or user_input:
            if profile['rank'] != 'ROOT' and profile['credits'] <= 0:
                st.error("OUT_OF_CREDITS")
            else:
                final_prompt = (btn_query or "") + (user_input or "")
                st.session_state.messages.append({"role": "user", "content": final_prompt})
                
                with st.chat_message("user"): st.markdown(final_prompt)

                with st.chat_message("assistant"):
                    
                    model = "llama-3.2-11b-vision-preview" if uploaded_file else "llama-3.3-70b-versatile"
                    
                    if uploaded_file:
                        content = [{"type": "text", "text": final_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(uploaded_file)}"}}]
                    else:
                        content = final_prompt

                    res = client.chat.completions.create(
                        model=model, 
                        messages=[{"role": "system", "content": "Tu es ReconX. Terminal pur. Réponses brutes, techniques, sans fioritures. Style hacking."}] + st.session_state.messages
                    )
                    
                    ans = res.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    if profile['rank'] != 'ROOT':
                        supabase.table("profiles").update({"credits": profile['credits'] - 1}).eq("id", profile['id']).execute()
                    st.rerun()
