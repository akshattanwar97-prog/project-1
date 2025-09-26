# streamlit_app.py
import streamlit as st
import hashlib, json, time
from dataclasses import dataclass
from typing import List, Dict

# --- Minimal blockchain primitives ---
def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def header_hash(index: int, ts: int, prev: str, nonce: int, entry: Dict) -> str:
    # Single-entry per block; deterministic JSON
    payload = json.dumps(
        {"index": index, "ts": ts, "prev": prev, "nonce": nonce, "entry": entry},
        sort_keys=True, separators=(",", ":")
    )
    return sha256_hex(payload)

DIFFICULTY_ZEROS = 3  # adjust for demo speed vs. PoW strength

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
    # Fallback: relax difficulty by 1 to ensure completion on slow hardware
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
    # Light PoW for genesis
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

# --- Streamlit UI (immediate entry -> block) ---
st.set_page_config(page_title="Blockchain Diary (Instant)", page_icon="📘", layout="centered")  # basic app pattern [web:29]

# Session state for stable, per-user state [web:47]
if "chain" not in st.session_state:
    st.session_state.chain = [make_genesis()]

st.title("📘 Blockchain Diary (Instant)")
st.caption("Type a note and click Add — it mines a new block immediately. No pending queue; each entry is its own block for a clear timeline.")  # simple UX guidance [web:29]

with st.sidebar:
    st.subheader("Settings")
    dz = st.number_input("Difficulty (leading zeros)", 1, 6, DIFFICULTY_ZEROS, 1)  # simple control [web:29]
    if st.button("Validate chain"):
        st.success(f"Chain valid: {valid_chain(st.session_state.chain)}")

col1, col2 = st.columns([2,1])
with col1:
    author = st.text_input("Name/ID", value="Student", key="author_in")  # widget pattern [web:29]
    text = st.text_area("Today’s entry", placeholder="Today I learned about Blockchain...", height=120, key="text_in")  # widget pattern [web:29]
    if st.button("Add (mine a new block)", type="primary"):
        if text.strip():
            prev_hash = st.session_state.chain[-1].hash()
            entry = {"author": (author or "Student").strip(), "text": text.strip(), "ts": int(time.time())}
            blk = Block(index=len(st.session_state.chain), ts=int(time.time()), prev=prev_hash, entry=entry)
            mine(blk, zeros=dz)  # single-entry block mined immediately [web:21]
            st.session_state.chain.append(blk)
            st.success(f"Added block #{blk.index}")
            # clear input after successful add
            st.session_state.text_in = ""
        else:
            st.error("Please write something before adding.")
with col2:
    ok = valid_chain(st.session_state.chain)
    st.metric("Chain valid", "Yes" if ok else "No")  # simple, visible status [web:29]

st.markdown("---")
st.subheader("Timeline (newest first)")
for b in reversed(st.session_state.chain):
    st.write(f"Block #{b.index} • hash {b.hash()[:12]}…")  # clear, per-entry visibility [web:29]
    with st.expander("Details"):
        st.json({
            "index": b.index,
            "timestamp": b.ts,
            "prev_hash": b.prev,
            "hash": b.hash(),
            "nonce": b.nonce,
            "entry": b.entry
        })
