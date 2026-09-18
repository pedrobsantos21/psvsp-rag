"""Interface web. Uso: uv run streamlit run app.py"""
import hmac
import os
import urllib.error

import anthropic
import streamlit as st

# Streamlit Cloud entrega segredos via st.secrets; chat.py espera env vars
os.environ.update({k: v for k, v in st.secrets.items() if isinstance(v, str)})

from psvsp.chat import responder  # noqa: E402  (precisa do env acima)

st.set_page_config(page_title="PSV-SP RAG", page_icon="🚦")
st.title("PSV-SP RAG")

# ponytail: senha única compartilhada; trocar por st.login (Google/OIDC) se precisar de usuários individuais
if not st.session_state.get("ok"):
    senha = st.text_input("Senha", type="password")
    if senha and hmac.compare_digest(senha, st.secrets["SENHA"]):
        st.session_state.ok = True
        st.rerun()
    if senha:
        st.error("Senha incorreta")
    st.stop()

hist = st.session_state.setdefault("hist", [])  # histórico da API
chat = st.session_state.setdefault("chat", [])  # (role, texto, sqls) para exibir

if st.sidebar.button("Limpar conversa"):
    hist.clear(); chat.clear()

for role, texto, sqls in chat:
    with st.chat_message(role):
        st.markdown(texto)
        for s in sqls:
            with st.expander("SQL"):
                st.code(s, language="sql")

if q := st.chat_input("Pergunte sobre o plano"):
    st.chat_message("user").markdown(q)
    sqls: list[str] = []
    n = len(hist)
    with st.chat_message("assistant"), st.spinner("Pensando..."):
        try:
            resp = responder(q, hist, sqls.append)
        except (anthropic.APIError, urllib.error.HTTPError, OSError) as e:
            del hist[n:]
            resp = f"erro: {e}"
    chat += [("user", q, []), ("assistant", resp, sqls)]
    st.rerun()
