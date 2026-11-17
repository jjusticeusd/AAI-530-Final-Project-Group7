import streamlit as st
from dotenv import load_dotenv

from referee.backends import ask, available, backend
from referee.retrieve import load_chunks
from referee.ruling import rule

st.set_page_config(page_title="NCAA Football Referee")
AVATARS = {"user": ":material/sports_football:", "assistant": ":material/sports:"}


@st.cache_resource
def chunks():
    load_dotenv()
    return load_chunks()


@st.cache_data(ttl=60)
def labels():
    return available()


def new_chat():
    st.session_state.history = []


def penalty(ruling):
    if ruling.get("foul") is False:
        return None if ruling.get("type") == "rule" else "No foul"
    if not ruling.get("foul"):
        return None
    yards, spot = ruling.get("penalty_yards"), ruling.get("enforcement_spot")
    return ", ".join(
        [
            "Foul",
            *([f"{yards} yards"] if yards is not None else []),
            *([f"from the {spot}"] if spot else []),
        ]
    )


def show(result):
    ruling = result["ruling"]
    if ruling is None:
        raw = result["raw"]
        if "{" in raw and "}" not in raw[raw.find("{") :]:
            st.warning(
                "The answer was cut off before it finished. Try again or pick another model."
            )
        else:
            st.warning(
                "The model did not return a ruling in the expected format. Check the rulebook before relying on this."
            )
        st.markdown(result["raw"])
    else:
        st.markdown(f"**{ruling.get('call', '')}**")
        if line := penalty(ruling):
            st.markdown(line)
        if ruling.get("explanation"):
            st.markdown(ruling["explanation"])
        if ruling.get("quote"):
            st.markdown(f"> {ruling['quote']}")
        cited = [
            f"{r} (not in the retrieved rules)"
            if r in result["unverified"]
            else f"{r} (checked)"
            for r in ruling.get("rules") or []
        ]
        if cited:
            st.caption("Rules cited: " + "; ".join(cited))
        if mentioned := [
            u for u in result["unverified"] if u not in (ruling.get("rules") or [])
        ]:
            st.caption(
                "Also mentioned, but not in the retrieved rules: "
                + "; ".join(mentioned)
            )
        if not result["quote_found"]:
            st.caption("The quote was not found word for word in the retrieved rules.")
    if result["needs_review"]:
        st.warning(
            "Needs review: check this with the rulebook or an official.",
            icon=":material/flag:",
        )
    with st.expander("Retrieved rules"):
        for c in result["found"]:
            st.markdown(f"**{c['id']}** (p. {c['page']})")
            st.text(c["text"])


rules = chunks()
if "history" not in st.session_state:
    new_chat()
history = st.session_state.history

with st.sidebar:
    options = labels()
    label = st.selectbox("Model", options)
    st.button("New chat", on_click=new_chat)

st.title("NCAA Football Referee")
st.caption(
    "Answers come from the 2026 NCAA Football Rules book. This is a study aid, not an official ruling."
)
if not options:
    st.error("No model is set up. Add a key to .env or start Ollama, then reload.")
    st.stop()

for message in history:
    with st.chat_message(message["role"], avatar=AVATARS[message["role"]]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            show(message["result"])

if question := st.chat_input("Ask a rules question or describe a play"):
    history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(question)
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Checking the rulebook..."):
            send = backend(label)
            result = rule(
                rules,
                lambda m: ask(send, m),
                [{"role": m["role"], "content": m["content"]} for m in history],
            )
        if result["raw"] is None:
            history.pop()
            st.error("The referee is unavailable right now. Try again in a minute.")
        else:
            history.append(
                {"role": "assistant", "content": result["raw"], "result": result}
            )
            show(result)
