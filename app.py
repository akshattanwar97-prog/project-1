# streamlit_app.py
import streamlit as st
import hashlib, json, time
from dataclasses import dataclass, asdict
from typing import List, Dict

# ----- Minimal blockchain (inspired by classic tutorials) ----- 
# Blocks link via previous hash; Proof-of-Work requires leading zeros. [web:21]

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def hash_block_header(b: Dict) -> str:
    header = json.dumps(
        {"index": b["index"], "ts": b["ts"], "prev": b["prev"], "nonce": b["nonce"], "entries": b["entries"]},
        sort_keys=True, separators=(",", ":")
    )
    return sha256_hex(header)

DIFFICULTY_ZEROS = 3  # small for demo speed; raise to 4+ for harder mining [web:21]

@dataclass
class Block:
    index: int
    ts: int
    prev: str
    entries: List[Dict]
    nonce: int = 0

    def to_dict(self) -> Dict:
        return {"index": self.index, "ts": self.ts, "prev": self.prev, "entries": self.entries, "nonce": self.nonce}

    def hash(self) -> str:
        return hash_block_header(self.to_dict())

def mine_block(block: Block, zeros: int = DIFFICULTY_ZEROS) -> str:
    target = "0" * zeros
    block.nonce = 0
    while True:
        h = block.hash()
        if h.startswith(target):
            return h
        block.nonce += 1
        # keep timestamp fresh occasionally (optional)
        if block.nonce % 100000 == 0:
            block.ts = int(time.time())

def valid_chain(chain: List[Block]) -> bool:
    for i, b in enumerate(chain):
        h = b.hash()
        if i == 0:
            if b.prev != "0"*64:
                return False
            if not h.startswith("0"*2):  # easier genesis [web:21]
                return False
        else:
            if b.prev != chain[i-1].hash():
                return False
            if not h.startswith("0"*DIFFICULTY_ZEROS):
                return False
    return True

def make_genesis() -> Block:
    g = Block(index=0, ts=int(time.time()), prev="0"*64, entries=[{"author":"system","text":"genesis","ts":int(time.time())}])
    # mine lightly for quick start
    target = "0"*2
    g.nonce = 0
    while True:
        if g.hash().startswith(target):
            return g
        g.nonce += 1

# ----- Streamlit UI (super minimal) ----- 
# Quick start: st.title, inputs, buttons, and a list/timeline. [web:29][web:26]

st.set_page_config(page_title="Simplest Blockchain Diary", page_icon="📘", layout="centered")

@st.cache_resource
def init_state():
    chain: List[Block] = [make_genesis()]
    pending: List[Dict] = []
    return {"chain": chain, "pending": pending}

S = init_state()

st.title("📘 Simplest Blockchain Diary")
st.caption("Add notes → mine a block → notes become tamper‑evident via hashes + Proof‑of‑Work.")  # concept from classic minimal tutorials [web:21]

# Input
author = st.text_input("Name/ID", value="Student")  # basic widget pattern [web:26]
text = st.text_area("Today’s note", placeholder="Today I learned about Blockchain...")  # basic widget pattern [web:34]

c1, c2 = st.columns(2)
with c1:
    if st.button("Add to pending"):
        if text.strip():
            S["pending"].append({"author": author.strip() or "Student", "text": text.strip(), "ts": int(time.time())})
            st.success("Added to pending.")
        else:
            st.error("Write something first.")

with c2:
    if st.button("⛏️ Mine block"):
        if not S["pending"]:
            st.warning("No pending entries.")
        else:
            prev_hash = S["chain"][-1].hash()
            blk = Block(index=len(S["chain"]), ts=int(time.time()), prev=prev_hash, entries=S["pending"].copy())
            mine_block(blk)
            S["chain"].append(blk)
            S["pending"].clear()
            st.success(f"Mined block #{blk.index}")

st.markdown("---")
st.subheader("Pending entries")
if S["pending"]:
    for e in S["pending"]:
        st.markdown(f"- {e['author']} @ {e['ts']}: {e['text']}")
else:
    st.write("(none)")

st.markdown("---")
st.subheader("Timeline (newest first)")
valid = valid_chain(S["chain"])
st.info(f"Chain valid: {valid}")

for b in reversed(S["chain"]):
    st.write(f"Block #{b.index} • hash {b.hash()[:12]}…")
    with st.expander("Details"):
        st.json({
            "index": b.index,
            "timestamp": b.ts,
            "prev_hash": b.prev,
            "hash": b.hash(),
            "nonce": b.nonce,
            "entries": b.entries
        })
