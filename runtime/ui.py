#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import matplotlib.figure as mpl_fig
import pandas as pd


from engine.ai_engine import generate_code
from engine.code_executor import execute_code
from engine.conversation_gate import classify_followup
from engine.question_rewriter import rewrite_question
from engine.conversation_logger import log_event
from engine.verbalizer import verbalize_result
from engine.result_router import route_result


from audio_recorder_streamlit import audio_recorder
import tempfile
import hashlib
import os
import io
import json


from openai import OpenAI


# =========================================================
# CSS
# =========================================================

def apply_theme_css(theme_color: str | None = None):
    css = """
    <style>
      .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1rem !important;
      }

      textarea {
        font-size: 1.05rem !important;
        min-height: 70px !important;
        height: 70px !important;
      }

      .stpyplot {
        max-height: 520px !important;
        overflow-y: auto !important;
      }

      .streamlit-expanderContent {
        max-height: 550px !important;
        overflow-y: auto !important;
      }

      .answer-box {
        font-size: 2rem !important;
        line-height: 1.5 !important;
        padding: 1rem 1.2rem;
        background: #fff6f8;
        border-left: 5px solid #7a0019;
        border-radius: 6px;
        margin-top: 1rem;
      }

      .debug-box {
        background: #f3f3f3;
        border-left: 4px solid #999;
        padding: 0.8rem 1rem;
        margin-top: 1rem;
        font-size: 0.95rem;
        color: #333;
      }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    if theme_color:
        st.markdown(
            f"""
            <style>
              .answer-box {{
                color: {theme_color} !important;
                border-left-color: {theme_color} !important;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# In[ ]:


# =========================================================
# Main UI
# =========================================================

def render_app_ui(cfg: dict, df, prompt: str, app_path: str):
    # =========================================================
    # BACK BUTTON – vissza a nyitóoldalra
    # =========================================================
    
    title = cfg.get("app", {}).get("name", "Talk to Your Data")
    
    col1, col2 = st.columns([1,10])
    
    with col1:
        if st.button("⬅️", key="back_button", help="Vissza az alkalmazásokhoz"):
            st.session_state.pop("selected_app", None)
            st.session_state.pop("base_question", None)
            st.session_state.pop("history_questions", None)
            st.session_state.pop("question_input", None)
            st.session_state.pop("last_audio_hash", None)
            st.rerun()
    
    with col2:
        st.title(title)
    
    
    ui_cfg = cfg.get("ui", {})
    ai_cfg = cfg.get("ai", {})

    apply_theme_css(ui_cfg.get("theme_color"))

    # =====================================================
    # HISTORY BETÖLTÉS (csak egyszer)
    # =====================================================

    if "history_questions" not in st.session_state:

        history_questions = []
        seen_questions = set()

        log_path = os.path.join(app_path, "logs", "conversation_logs.jsonl")

        # --- 1. Log fájl beolvasása: utolsó 5 NEW kérdés ---
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
        
                # a legutolsókból indulunk (gyorsabb és biztosan "utolsó 5")
                for line in reversed(lines):
                    try:
                        record = json.loads(line.strip())
        
                        if record.get("event") != "question_run":
                            continue
                        if (record.get("gate_decision") or "").upper() != "NEW":
                            continue
        
                        q = (record.get("final_question") or "").strip()
                        if not q:
                            continue
        
                        if q not in seen_questions:
                            history_questions.append(q)
                            seen_questions.add(q)
        
                        if len(history_questions) >= 8:
                            break
        
                    except:
                        continue
        
            except:
                pass
        

        # --- 2. Ha kevesebb mint 5 kérdés, demo fallback ---
        if len(history_questions) < 5:

            demo_path = os.path.join(app_path, "demo_questions.json")

            if os.path.exists(demo_path):
                try:
                    with open(demo_path, "r", encoding="utf-8") as f:
                        demo_data = json.load(f)
                        demo_questions = demo_data.get("questions", [])
                        history_questions = [
                            q.strip() for q in demo_questions
                            if isinstance(q, str) and q.strip()
                        ]

                except:
                    history_questions = []

        # Legfrissebb felül (ha logból jött)
#        history_questions = list(reversed(history_questions))

        st.session_state["history_questions"] = history_questions

    

    
    desc = cfg.get("app", {}).get("description")
    if desc:
        st.caption(desc)

    # Conversation memory
    if "base_question" not in st.session_state:
        st.session_state["base_question"] = None
    if "last_audio_hash" not in st.session_state:
        st.session_state["last_audio_hash"] = None
    


    # Layout
    show_code_panel = bool(ui_cfg.get("show_code_panel", True))
    if show_code_panel:
        col_left, col_right = st.columns([1, 1])
    else:
        col_left, col_right = st.columns([1, 1])

    # =====================================================
    # JOBB OLDAL – HISTORY PANEL
    # =====================================================
    
    with col_right:
    
        st.markdown("###  Korábbi kérdések")
    
        history_questions = st.session_state.get("history_questions", [])
    
        if history_questions:
    
            for idx, q in enumerate(history_questions):
    
                # rövidítés, ha túl hosszú
#                display_text = q if len(q) <= 100 else q[:100] + "..."
    
                if st.button(q, key=f"history_{idx}", use_container_width=True, type="secondary"):
                    st.session_state["question_input"] = q
                    st.rerun()

    
        else:
            st.markdown("_Még nincsenek korábbi kérdések._")

    
    with col_left:
        # 🎙️ Hangbemondás
        audio_bytes = audio_recorder(
            recording_color="#ff3333",
            neutral_color="#cccccc",
            icon_name="microphone",
            icon_size="2x",
        )

        if audio_bytes:
            audio_hash = hashlib.md5(audio_bytes).hexdigest()

            if audio_hash != st.session_state["last_audio_hash"]:
                st.session_state["last_audio_hash"] = audio_hash

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                    with open(tmp_path, "rb") as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    file=audio_file,
                                    model="whisper-1",
                                    language="hu",
                                    response_format="text",
                                    temperature=0,
                                    prompt=(
                                        "Magyar piackutatási és adatelemzési kérdések: "
                                        "gyorsétterem, csokoládé, százalék, darabszám, "
                                        "nők, férfiak, budapestiek."
                                    ),
                                )

                    st.session_state["question_input"] = transcript

                finally:
                    os.remove(tmp_path)

        if "question_input" not in st.session_state:
            st.session_state["question_input"] = ""

    
        question = st.text_area(
            "Írd be a kérdést:",
            key="question_input",
            placeholder="",
        )




        btn_col, spinner_col = st.columns([1, 3])
        with btn_col:
            run_clicked = st.button("Futtatás")
        
        with spinner_col:
            spinner_placeholder = st.empty()
        
        result_placeholder = st.empty()



    # =====================================================
    # Run
    # =====================================================


    if run_clicked and question.strip():

        prev = st.session_state.get("base_question")
    
        try:
            with spinner_placeholder.container():
                with st.spinner("⏳ Az elemzés folyamatban!"):
                    # 1) Gate
                    if prev:
                        decision = classify_followup(prev, question)
                    else:
                        decision = "NEW"
    
                    log_event(
                        app_dir=app_path,
                        data={
                            "event": "gate_decision",
                            "previous_question": prev,
                            "user_input": question,
                            "gate_decision": decision,
                            "app_name": cfg.get("app", {}).get("name"),
                        }
                    )
    
                    # 2) UNCLEAR → nincs üresjárat, azonnali üzenet + KILÉPÉS
                    if decision == "UNCLEAR":
                        result_placeholder.warning(
                            "❗️Ezt így nem értem biztosan. Írd át pontosabban, vagy adj meg több részletet."
                        )
                        return
    
                    # 3) FOLLOWUP → rewrite
                    rewritten_question = None
    
                    if decision == "FOLLOWUP" and prev:
                        rewritten_question = rewrite_question(
                            prev,
                            question,
                            model=ai_cfg.get("model", "gpt-4.1"),
                        )
                        final_question = (rewritten_question or "").strip()
    
                        if not final_question:
                            result_placeholder.warning(
                                "❗️Nem sikerült a follow-up kérdést egyértelműsíteni. Írd le kicsit bővebben."
                            )
                            return
                    else:
                        final_question = question.strip()
    
                    # 4) Codegen + log + futtatás
                    model = ai_cfg.get("model", "gpt-4.1")
                    temperature = ai_cfg.get("temperature", 0.0)
    
                    code = generate_code(
                        user_question=final_question,
                        system_prompt=prompt,
                        model=model,
                        temperature=temperature,
                        )
    
                    log_event(
                        app_dir=app_path,
                        data={
                            "event": "question_run",
                            "previous_question": prev,
                            "user_input": question,
                            "gate_decision": decision,
                            "rewritten_question": rewritten_question,
                            "final_question": final_question,
                            "app_name": cfg.get("app", {}).get("name"),
                            "generated_code": code,
                        },
                    )
    
                    result = execute_code(code, df)
                    routed = route_result(result)
    
                    if routed.kind == "figure":
                        result_placeholder.pyplot(routed.figure)
    
                    elif routed.kind == "table":
                        df_out = routed.data.copy().reset_index(drop=True)
                        result_placeholder.dataframe(df_out, use_container_width=True)
    
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df_out.to_excel(writer, index=False, sheet_name="Eredmeny")
    
                        st.download_button(
                            label="📥 Letöltés Excel formátumban",
                            data=output.getvalue(),
                            file_name="eredmeny.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
    
                    else:
                        pretty_text = verbalize_result(
                            question=final_question,
                            result=routed.data,
                            model=ai_cfg.get("model", "gpt-4.1"),
                            temperature=0.2,
                        )
                        result_placeholder.markdown(
                            f"<div class='answer-box'>{pretty_text}</div>",
                            unsafe_allow_html=True,
                        )
    
                    # 5) base_question
                    st.session_state["base_question"] = final_question
    
                    # 6) history
                    if decision == "NEW":
                        if "history_questions" in st.session_state:
                            fq = (final_question or "").strip()
                            if fq and fq not in st.session_state["history_questions"]:
                                st.session_state["history_questions"].insert(0, fq)
                            # tartsuk max 5 elemre
                            st.session_state["history_questions"] = st.session_state["history_questions"][:8]
    
        except Exception as e:
            result_placeholder.error(str(e))
    
        finally:
            spinner_placeholder.empty()




