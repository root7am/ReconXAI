import streamlit as st
from groq import Groq
import datetime
import base64


st.set_page_config(page_title="RECON API - Terminal", page_icon="🕵️‍♂️", layout="wide")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "full_history" not in st.session_state:
    st.session_state.full_history = []
if "credits" not in st.session_state:
    st.session_state.credits = 5


def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')


st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* Header avec Avatar Custom */
    .credit-header {
        background: rgba(15, 15, 15, 0.95);
        border: 1px solid #1f1f1f;
        padding: 15px 25px; border-radius: 12px;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 25px; border-left: 5px solid #ff4b4b;
    }
    .user-avatar { width: 55px; height: 55px; border-radius: 50%; border: 2px solid #ff4b4b; object-fit: cover; }
    .credit-amount { color: #ff4b4b; font-weight: bold; font-size: 1.3rem; }
    
    /* Boutique plein écran */
    .shop-container {
        background: #0d0d0d; border: 1px solid #ff4b4b;
        padding: 40px; border-radius: 15px; text-align: center;
        margin: 50px auto; max-width: 800px;
    }
    .shop-card {
        background: #151515; border: 1px solid #333;
        padding: 20px; border-radius: 10px; margin: 10px;
        display: inline-block; width: 280px; vertical-align: top;
    }
    
    /* Sidebar et Logs */
    .log-title { color: #ff4b4b; font-weight: bold; margin-top: 25px; border-bottom: 1px solid #1f1f1f; padding-bottom: 5px; }
    .stChatMessage { background-color: #0d0d0d !important; border: 1px solid #1a1a1a !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY manquante dans les Secrets.")


with st.sidebar:
    st.title("📡 RECON HUB")
    
    
    access_code = st.text_input("Saisir code d'accès :", type="password")
    if access_code == "OWNER_RECON_2026":
        rank, user_name, credits_val = "OWNER", "RECON_ROOT", "∞"
    else:
        rank, user_name, credits_val = "FREE", "CIVILIAN", str(st.session_state.credits)

   
    st.markdown('<div class="log-title">📸 ANALYSE IMAGE</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload une capture (Bug/Script)", type=["png", "jpg", "jpeg"])

    
    st.markdown('<div class="log-title">📜 LOGS DE SESSION</div>', unsafe_allow_html=True)
    if not st.session_state.full_history:
        st.caption("Aucune archive.")
    else:
        for log in reversed(st.session_state.full_history):
            with st.expander(f"🕒 {log['time']} | {log['query']}"):
                st.code(log['code'], language="lua")

    st.divider()
    if st.button("🗑️ RESET SESSION"):
        st.session_state.messages = []
        st.rerun()


custom_avatar = "https://cdn-icons-png.flaticon.com/512/6033/6033716.png" # Image Meta Custom
st.markdown(f"""
    <div class="credit-header">
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="{custom_avatar}" class="user-avatar">
            <div>
                <div style="font-weight: bold; font-size: 1.1rem;">{user_name}</div>
                <div style="color:#ff4b4b; font-size:0.75rem; border:1px solid #ff4b4b; padding:1px 6px; border-radius:4px; display:inline-block;">{rank} ACCESS</div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size: 0.7rem; color: #666;">RESSOURCES</div>
            <div class="credit-amount">{credits_val}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if rank == "FREE" and st.session_state.credits <= 0:
    st.markdown("""
        <div class="shop-container">
            <h2 style="color:#ff4b4b;">OFFLINE - CRÉDITS ÉPUISÉS</h2>
            <p>Upgrade ton rang pour continuer à utiliser RECON API.</p>
            <div class="shop-card">
                <h3>💠 PREMIUM</h3>
                <div style="color:#ff4b4b; font-size:1.8rem; font-weight:bold;">4.99€</div>
                <p style="font-size:0.8rem; color:#aaa;">• 500 Crédits / mois<br>• Accès Vision Prioritaire<br>• Modèles avancés</p>
                <button style="width:100%; border-radius:5px; border:none; background:#ff4b4b; color:white; padding:10px;">S'abonner</button>
            </div>
            <div class="shop-card">
                <h3 style="color:#ff4b4b;">👑 OWNER</h3>
                <div style="color:#ff4b4b; font-size:1.8rem; font-weight:bold;">14.99€</div>
                <p style="font-size:0.8rem; color:#aaa;">• Crédits ILLIMITÉS<br>• Accès à vie<br>• Support technique</p>
                <button style="width:100%; border-radius:5px; border:none; background:#ff4b4b; color:white; padding:10px;">Acheter</button>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    # Affichage de la discussion
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    
    if prompt := st.chat_input("Initialisation de la commande..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("SCANNING..."):
                try:
                    # Choix du modèle (Vision ou Texte)
                    if uploaded_file:
                        base64_image = encode_image(uploaded_file)
                        model_choice = "llama-3.2-11b-vision-preview"
                        user_content = [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    else:
                        model_choice = "llama-3.3-70b-versatile"
                        user_content = prompt

                    completion = client.chat.completions.create(
                        model=model_choice,
                        messages=[{"role": "system", "content": "Tu es ReconAI. Expert Roblox Luau. Réponds en Luau technique."}] + 
                                 [{"role": "user", "content": user_content}]
                    )
                    
                    full_response = completion.choices[0].message.content
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # Sauvegarde logs et crédits
                    st.session_state.full_history.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "query": "Vision" if uploaded_file else prompt[:20],
                        "code": full_response
                    })
                    
                    if rank == "FREE":
                        st.session_state.credits -= 1
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"SYSTEM ERROR: {e}")
