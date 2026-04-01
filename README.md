# AI-Ring-Chat

A distributed, decentralized UDP chat application using a ring topology.

## Why This Project?

This project exists primarily to **explore and test the capabilities of AI agentic systems** (specifically OpenWork) in developing a complex, multi-file software project from scratch.

The goal is to evaluate how well an AI system can:
- Understand and translate complex specifications into working code
- Maintain consistency across multiple files following the Model/View/Control (MVC) paradigm
- Handle distributed systems concepts (peer-to-peer networking, fault tolerance, consensus)
- Create a well-structured, testable architecture
- Produce documentation that accurately reflects the implementation

The application itself implements a **daisy-chain UDP chat** with a **ring topology** — a classic distributed systems pattern. While not novel, it provides an excellent testbed for evaluating AI development capabilities because it requires:

1. **Network protocol design** — Defining message formats and state machines
2. **Distributed algorithms** — Membership, failure detection, recovery
3. **MVC architecture** — Separating concerns across multiple components
4. **Testing complexity** — Simulating multiple nodes locally

---

## Overview

AI-Ring-Chat is a peer-to-peer chat application where each client is a **node** in a **ring**. There is **no central server** — all nodes are equal participants.

```
     ┌─────────────────────────────────────┐
     │                                     │
     ▼                                     │
  [Node A] ─────── UDP ───────► [Node B]  │
     ▲                           │        │
     │                           ▼        │
     │                      [Node C]      │
     │                           ▲        │
     └───────────────────────────┘        │
              (ring closes)               │
```

### Key Characteristics

- **Decentralized**: No server required; any node can join if it knows at least one existing node
- **Distributed**: Each node maintains only local state (itself and its neighbor)
- **Fault-tolerant**: Built-in failure detection and ring recovery mechanisms
- **Asynchronous**: UDP-based communication with configurable timeouts

---

## Architecture

The application follows the **Model/View/Control (MVC)** paradigm:

```
ai-ring-chat/
├── model/
│   ├── node.py          # Core node state and logic
│   ├── message.py       # Message types and parsing
│   └── ring_state.py    # Ring topology state management
├── view/
│   └── console.py       # Console-based user interface
├── control/
│   ├── network.py       # UDP send/receive handling
│   └── protocol.py      # Connection, exit, heartbeat protocols
├── main.py              # Entry point
├── config.py            # Configuration constants
└── README.md
```

### Components

| Component | Responsibility |
|-----------|---------------|
| **Model** | Core data structures, node state, ring topology, message definitions |
| **View** | User interface (console output, display formatting) |
| **Control** | Network I/O, protocol handlers, user command processing |

---

## Network Protocol

### Node Identity

Each node is identified by:
- `address:port` — e.g., `127.0.0.1:5000`
- All nodes use the **same port** for the protocol (allows testing with different addresses locally)

### Ring Structure

Each node maintains:
- `self` — Its own `address:port`
- `next` — The `address:port` of the next node in the ring

### Message Types

| Type | Format | Description |
|------|--------|-------------|
| **Join** | `node self_address:port` | New node joining the ring |
| **Exit** | `exit self_address:port next_address:port` | Node gracefully leaving |
| **Echo** | `echo self_address:port` | Liveness/heartbeat check |
| **Echo Response** | `echo_resp target_address:port origin_address:port` | Response to echo |
| **First** | `first requester_address:port` | Recovery when predecessor fails |
| **Public Text** | `text message_content` | Broadcast message to all nodes |
| **Private Text** | `user target_address:port message_content` | Direct message to specific node |
| **Restore** | `restore broken_address:port new_next_address:port` | Ring repair (double ring) |

### Connection Protocol (Node Join)

1. New node `N` knows existing node `X`'s `address:port`
2. `N` sends `node N_address:port` to `X`
3. `X` receives the message, records `N` as its `next`
4. `X` replies (or the message propagates) so `N` knows `X`'s address
5. `N` sets its `next` to whatever was `X`'s previous `next`

**Result**: `N` is inserted between `X` and `X`'s former `next`

```
Before: [X] ──► [Y]
After:  [X] ──► [N] ──► [Y]
```

### Exit Protocol (Graceful Leave)

1. Exiting node `E` sends `exit E_address:port next_address:port`
2. Message propagates around the ring
3. When message reaches node `P` where `P.next == E`:
   - `P` replaces `P.next` with `E.next`
   - Ring is restored

### Failure Detection & Recovery

Since UDP has no built-in reliability, we need explicit failure detection.

#### Single Ring Recovery (Echo Protocol)

1. **Heartbeat**: Each node periodically sends `echo self_address:port` to its `next`
2. If the `echo_resp` doesn't arrive within a timeout, `next` is considered failed
3. **Recovery**: Node sends `first self_address:port` forward
4. When this reaches the node that knew the failed `next`, it updates its `next` to the sender of `first`

#### Double Ring Recovery (Restore Protocol)

With two rings (clockwise and counter-clockwise):
1. Detect failure via missing heartbeat
2. Send `restore broken_address:port new_next_address:port` backwards
3. Each node updates its backward pointer

### Message Propagation Rules

#### Public Messages (`text`)
- Propagates to `next`
- **Stops** when it returns to the original sender (no loops)
- Each node logs it and caches by message ID

#### Private Messages (`user target_address:port`)
- Propagates to `next`
- **Stops** when it reaches the `target`
- Target logs it; intermediate nodes ignore content
- Does not propagate further after delivery

#### Cache & Deduplication
- Each message has a unique ID (sender + sequence number)
- Nodes cache recent message IDs
- If a message ID is already seen, it is **not** propagated again
- This handles both sender failure and message loops

---

## Usage

### Starting a Node

```bash
python main.py --address 127.0.0.1 --port 5000 --join 127.0.0.1:5001
```

Parameters:
- `--address` — Local bind address (default: 127.0.0.1)
- `--port` — Local port (required)
- `--join` — Existing node to join (optional; omit for first node)

### Commands (Interactive)

Once running, type commands in the console:

| Command | Description |
|---------|-------------|
| `send Hello everyone!` | Send public message |
| `send @127.0.0.1:5001 Hello!` | Send private message |
| `status` | Show current node and next node |
| `log` | Show recent messages |
| `quit` | Gracefully exit the ring |
| `help` | Show available commands |

---

## Technical Notes

### Why UDP?

UDP is connectionless and simpler for experimentation. Trade-offs:
- ✅ No connection overhead
- ✅ Natural broadcast/multicast potential
- ❌ No reliability — must implement our own acknowledgment
- ❌ No ordering — must implement our own sequencing

### Port Configuration

For production: All nodes should use the **same port** on different machines.

For local testing: Use different ports since `127.0.0.1` is the same address:
```bash
# Terminal 1
python main.py --address 127.0.0.1 --port 5000

# Terminal 2
python main.py --address 127.0.0.1 --port 5001 --join 127.0.0.1:5000

# Terminal 3
python main.py --address 127.0.0.1 --port 5002 --join 127.0.0.1:5000
```

### Future Enhancements

- [ ] **Cryptographic addressing**: Replace address-based targeting with public key fingerprints
- [ ] **Double ring**: Bidirectional message passing for faster propagation and easier recovery
- [ ] **Persistence**: Store message log to disk
- [ ] **GUI**: Web-based or desktop interface
- [ ] **Unit tests**: Comprehensive testing of protocol handlers
- [ ] **Integration tests**: Multi-node simulation

---

## Development Notes

This project is being developed with AI assistance to evaluate:
1. Specification comprehension and translation to code
2. Consistency across MVC components
3. Handling of edge cases in distributed protocols
4. Code quality and testability

---

*In omnia solacium*
