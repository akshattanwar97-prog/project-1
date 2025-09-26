# streamlit_app.py
import streamlit as st
import hashlib, json, time
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime  # + added for human-readable time

# --- Minimal blockchain primitives ---
def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def header_hash(index: int, ts: int, prev: str, nonce: int, entry: Dict) -> str:
    payload = json.dumps(
        {"index": index, "ts": ts, "prev": prev, "nonce": nonce, "entry": entry},
        sort_keys=True, separators=(",", ":")
    )
    return sha256_hex(payload)

DIFFICULTY_ZEROS = 3

@dataclass
class Block:
    index: int
    ts: int
    prev: str
    entry: Dict
    nonce: int = 0
    def hash(self) -> str:
        return header_hash(self.index, self.ts, self.prev, self.nonce, self.entry)

def mine(block: Block, zeros: int = DIFFICULTY_ZEROS, max_iters: int = 5_000_000) -> str:
    target = "0" * zeros
    iters = 0
    block.nonce = 0
    while iters < max_iters:
        h = block.hash()
        if h.startswith(target):
            return h
        block.nonce += 1
        iters += 1
        if block.nonce % 100_000 == 0:
            block.ts = int(time.time())
    target = "0" * max(zeros - 1, 1)
    while True:
        h = block.hash()
        if h.startswith(target):
            return h
        block.nonce += 1
        if block.nonce % 100_000 == 0:
            block.ts = int(time.time())

def make_genesis() -> Block:
    g = Block(index=0, ts=int(time.time()), prev="0"*64,
              entry={"author":"system","text":"genesis","ts":int(time.time())}, nonce=0)
    target = "0"*2
    while True:
        if g.hash().startswith(target):
            return g
        g.nonce += 1

def valid_chain(chain: List[Block]) -> bool:
    if not chain:
        return False
    for i, b in enumerate(chain):
        h = b.hash()
        if i == 0:
            if b.prev != "0"*64:
                return False
            if not h.startswith("0"*2):
                return False
        else:
            if b.prev != chain[i-1].hash():
                return False
            if not h.startswith("0"*DIFFICULTY_ZEROS):
                return False
    return True

# +++++++++++++++++++++++++ NEW: certificate HTML generator +++++++++++++++++++++++++
def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def certificate_html(block: Block) -> str:
    name = block.entry.get("author", "Student")
    note = block.entry.get("text", "")
    note_safe = note.replace("<", "&lt;").replace(">", "&gt;")
    created = format_ts(block.entry.get("ts", block.ts))
    bhash = block.hash()
    tmpl = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Certificate - Block {block.index}</title>
<style>
  @page {{ size: A4; margin: 25mm; }}
  body {{ font-family: Arial, sans-serif; color: #222; }}
  .card {{
    border: 2px solid #0f766e; padding: 24px; border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  h1 {{ color: #0f766e; margin-bottom: 0; }}
  .subtitle {{ color: #444; margin-top: 4px; }}
  .section {{ margin-top: 18px; }}
  .label {{ font-weight: 600; color: #374151; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; word-break: break-all; }}
  .note {{ white-space: pre-wrap; line-height: 1.4; background: #f9fafb; padding: 12px; border-radius: 8px; }}
  .footer {{ margin-top: 16px; font-size: 12px; color: #6b7280; }}
</style>
</head>
<body>
  <div class="card">
    <h1>Certificate of Entry</h1>
    <div class="subtitle">This document certifies a tamper‑evident diary entry recorded on a blockchain.</div>

    <div class="section"><span class="label">Student:</span> {name}</div>
    <div class="section"><span class="label">Created:</span> {created}</div>
    <div class="section"><span class="label">Block Index:</span> {block.index}</div>
    <div class="section"><span class="label">Block Hash:</span> <div class="mono">{bhash}</div></div>

    <div class="section"><span class="label">Entry:</span>
      <div class="note">{note_safe}</div>
    </div>

    <div class="footer">
      Previous Hash: <span class="mono">{block.prev}</span><br/>
      Nonce: <span class="mono">{block.nonce}</span>
    </div>
  </div>
</body>
</html>
"""
    return tmpl
# +++++++++++++++++++++++++ END NEW ++++++++++++++++++++++++++++++++++++++++++++++++

# --- Streamlit UI (immediate entry -> block) ---
st.set_page_config(page_title="Blockchain Diary (Instant)", page_icon="📘", layout="centered")

if "chain" not in st.session_state:
    st.session_state.chain = [make_genesis()]

st.title("📘 Blockchain Diary (Instant)")
st.caption("Type a note and click Add — it mines a new block immediately. No pending queue; each entry is its own block for a clear timeline.")

with st.sidebar:
    st.subheader("Settings")
    dz = st.number_input("Difficulty (leading zeros)", 1, 6, DIFFICULTY_ZEROS, 1)
    if st.button("Validate chain"):
        st.success(f"Chain valid: {valid_chain(st.session_state.chain)}")

col1, col2 = st.columns([2,1])
with col1:
    author = st.text_input("Name/ID", value="Student", key="author_in")
    text = st.text_area("Today’s entry", placeholder="Today I learned about Blockchain...", height=120, key="text_in")
    if st.button("Add (mine a new block)", type="primary"):
        if text.strip():
            prev_hash = st.session_state.chain[-1].hash()
            entry = {"author": (author or "Student").strip(), "text": text.strip(), "ts": int(time.time())}
            blk = Block(index=len(st.session_state.chain), ts=int(time.time()), prev=prev_hash, entry=entry)
            mine(blk, zeros=dz)
            st.session_state.chain.append(blk)
            st.success(f"Added block #{blk.index}")
            st.session_state.text_in = ""
        else:
            st.error("Please write something before adding.")
with col2:
    ok = valid_chain(st.session_state.chain)
    st.metric("Chain valid", "Yes" if ok else "No")

st.markdown("---")
st.subheader("Timeline (newest first)")
for b in reversed(st.session_state.chain):
    st.write(f"Block #{b.index} • hash {b.hash()[:12]}…")
    with st.expander("Details"):
        st.json({
            "index": b.index,
            "timestamp": b.ts,
            "prev_hash": b.prev,
            "hash": b.hash(),
            "nonce": b.nonce,
            "entry": b.entry
        })
        # +++++++++++++ NEW: per-block certificate download +++++++++++++
        cert_html = certificate_html(b)
        st.download_button(
            label="Download certificate (.html)",
            data=cert_html.encode("utf-8"),
            file_name=f"certificate_block_{b.index}.html",
            mime="text/html"
        )
        # Tip for printing to PDF
        st.caption("Open the downloaded .html and use the browser’s Print → Save as PDF for a polished PDF certificate.")
        # +++++++++++++ END NEW +++++++++++++++++++++++++++++++++++++++++
