import streamlit as st
from engine.app_registry import list_apps
from runtime.app_runner import run_app


def run_app_selector():
    st.set_page_config(layout="wide")

    # Ha már fut egy app → mutassunk "Vissza" gombot, és csak utána futtassuk az appot
    if st.session_state.get("selected_app"):
        top = st.container()
        with top:
            left, right = st.columns([1, 6])
            with left:
                if st.button("⬅️ Vissza", use_container_width=True):
                    # kötelező: kiválasztott app törlése
                    st.session_state.pop("selected_app", None)

                    # opcionális: app-hoz kötődő state-ek takarítása (ha kell)
                    st.session_state.pop("base_question", None)
                    st.session_state.pop("history_questions", None)
                    st.session_state.pop("question_input", None)
                    st.session_state.pop("last_audio_hash", None)

                    st.rerun()

        run_app(st.session_state["selected_app"])
        return

    # ---- App selector UI ----
    st.title("Beszélgess az adataiddal!")

    apps = list_apps("apps")
    if not apps:
        st.error("Nincsenek elérhető appok az apps/ könyvtárban.")
        return

    st.markdown("### Válassz egy alkalmazást")

    options = {app["name"]: app for app in apps}
    selected_name = st.selectbox("Elérhető alkalmazások", list(options.keys()))
    selected_app = options[selected_name]

    if st.button("Indítás"):
        st.session_state["selected_app"] = selected_app["path"]
        st.rerun()