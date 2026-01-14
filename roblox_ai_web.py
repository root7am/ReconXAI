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
    st.error("ERREUR : Secrets manquants (SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY)")


st.set_page_config(page_title="ReconXAI - Kali Terminal", page_icon="🕵️‍♂️", layout="wide")


def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def sign_in(email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except:
        return None

def sign_up(email, password, username):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({
                "id": res.user.id, 
                "username": username, 
                "rank": "USER", 
                "credits": 10
            }).execute()
            return True
    except Exception as e:
        st.error(f"Erreur inscription: {e}")
        return False


st.markdown("""
    <style>
    .stApp { background-color: #0f111a; color: #a9b1d6; font-family: 'Fira Code', monospace; }
    .kali-panel { 
        background: #1a1b26; border: 1px solid #3b4261; padding: 15px; 
        border-radius: 4px; border-top: 3px solid #7aa2f7; margin-bottom: 20px;
    }
    .stButton>button { 
        width: 100%; border: 1px solid #3b4261; background: #16161e; color: #7aa2f7; 
        border-radius: 2px; text-transform: uppercase; font-size: 0.8rem;
    }
    .stButton>button:hover { border-color: #7aa2f7; color: #bb9af7; }
    .stChatMessage { background-color: #1a1b26 !important; border: 1px solid #3b4261 !important; }
    code { color: #9ece6a !important; background: #24283b !important; }
    </style>
    """, unsafe_allow_html=True)


if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    
    st.title("🐉 ReconXAI - Authentification")
    t1, t2 = st.tabs(["Connexion", "Création de compte"])
    
    with t1:
        e = st.text_input("Email")
        p = st.text_input("Mot de passe", type="password")
        if st.button("LOGIN"):
            auth = sign_in(e, p)
            if auth:
                st.session_state.user = auth.user
                st.rerun()
                
    with t2:
        ne = st.text_input("Email (Vérification requise)")
        nu = st.text_input("Pseudo OSINT")
        np = st.text_input("Mot de passe ", type="password")
        if st.button("REGISTER"):
            if sign_up(ne, np, nu):
                st.success("Vérifie tes emails !")
else:
    
    profile = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    
    with st.sidebar:
        st.image("https://www.kali.org/images/kali-logo.svg", width=180)
        st.markdown(f"**USER:** `{profile['username']}`")
        st.markdown(f"**RANK:** `{profile['rank']}`")
        
        menu = st.radio("SUDO MENU", ["Terminal OSINT", "Admin Panel" if profile['rank'] == 'ROOT' else None])
        
        st.divider()
        st.subheader("📷 Optical Scanner")
        uploaded_file = st.file_uploader("Upload Capture (Metadata/Reverse)", type=["png", "jpg", "jpeg"])
        
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()

    
    if menu == "Admin Panel" and profile['rank'] == 'ROOT':
        st.title("🛰️ Control Center")
        users = supabase.table("profiles").select("*").execute().data
        for u in users:
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"ID: {u['username']}")
            new_r = c2.selectbox("Rank", ["USER", "PREMIUM", "ROOT"], key=u['id'], index=["USER", "PREMIUM", "ROOT"].index(u['rank']))
            if c3.button("Update", key=f"btn_{u['id']}"):
                supabase.table("profiles").update({"rank": new_r}).eq("id", u['id']).execute()
                st.rerun()

    
    else:
        st.markdown(f"""
            <div class="kali-panel">
                <span style="color:#7aa2f7;">root@reconxai</span>:<span style="color:#bb9af7;">~#</span> 
                Credits: <span style="color:#9ece6a;">{profile['credits'] if profile['rank'] != 'ROOT' else '∞'}</span>
            </div>
        """, unsafe_allow_html=True)
        
        
        cols = st.columns(4)
        p_ready = ""
        if cols[0].button("🌐 IP/WHOIS"): p_ready = "Effectue un scan profond sur l'IP/Domaine : "
        if cols[1].button("📱 MOBILE"): p_ready = "Analyse OSINT du numéro de téléphone : "
        if cols[2].button("🕵️‍♂️ SHERLOCK"): p_ready = "Recherche le pseudonyme sur les réseaux : "
        if cols[3].button("📍 GEO-INT"): p_ready = "Analyse de géolocalisation pour : "

        
        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        
        if user_input := st.chat_input("Exécuter une commande..."):
            if profile['rank'] != 'ROOT' and profile['credits'] <= 0:
                st.error("ACCÈS REFUSÉ : Crédits épuisés.")
            else:
                prompt = p_ready + user_input
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Analyse en cours..."):
                        
                        model = "llama-3.2-11b-vision-preview" if uploaded_file else "llama-3.3-70b-versatile"
                        
                        if uploaded_file:
                            b64_img = encode_image(uploaded_file)
                            content = [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                            ]
                        else:
                            content = prompt

                        
                        res = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "system", "content": """Tu es le terminal ReconXAI.
                            Expert en investigation numérique (OSINT), Cybersécurité et Forensics.
                            - Réponds de façon technique et froide.
                            - Utilise des tableaux pour les données.
                            - Donne des commandes réelles (Nmap, Sherlock, Whois)."""}] + 
                            [{"role": "user", "content": content}]
                        )
                        
                        ans = res.choices[0].message.content
                        st.markdown(ans)
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                        
                        
                        if profile['rank'] != 'ROOT':
                            supabase.table("profiles").update({"credits": profile['credits'] - 1}).eq("id", profile['id']).execute()
                        st.rerun()
