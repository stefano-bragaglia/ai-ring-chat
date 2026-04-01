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
│   ├── nodes.py         # Node data model (address, next, address_book, message_log)
│   └── message.py      # Message types and parsing
├── view/
│   └── console.py       # Console-based user interface
├── control/
│   ├── network.py       # UDP send/receive handling
│   └── protocol.py      # Connection, exit, heartbeat protocols
├── main.py              # Entry point
└── README.md
```

### Components

| Component | Responsibility |
|-----------|---------------|
| **Model** | Nodes data model, ring topology state, message definitions |
| **View** | User interface (console output, display formatting) |
| **Control** | Network I/O, protocol handlers, user command processing |

---

## Network Protocol

The protocol is implemented in `control/protocol.py` with static methods that handle each message type. The `Node` class in `model/nodes.py` leads the interaction - it listens for messages and delegates handling to protocol methods.

### Protocol Methods

Each message type has a corresponding handler method:

| Method | Description |
|--------|-------------|
| `handle_join(node, message)` | Set node's next to sender, propagate JOIN |
| `handle_exit(node, message)` | Remove exiting node from ring, propagate |
| `handle_ping(node, message)` | Record PING timestamp, respond with ECHO |
| `handle_echo(node, message)` | Record ECHO timestamp, update node state |
| `handle_next(node, message)` | If `is_head()`, set next to sender; else propagate |
| `handle_text(node, message)` | Log payload, propagate if not duplicate |
| `handle_user(node, message)` | Deliver to target or propagate |

### Head/Tail Detection

Each node tracks timestamps:
- `last_ping_received` - timestamp of last PING received
- `last_echo_received` - timestamp of last ECHO received

Node determines its state:
- **Head**: Sending PINGs but not receiving ECHOs (next node failed)
- **Tail**: Not receiving PINGs (predecessor failed)
- **Normal**: Receiving both PINGs and ECHOs

### Message Propagation

- TEXT messages propagate to all nodes (stop if payload already in log)
- USER messages propagate until target is reached
- Control messages (JOIN, EXIT, PING, ECHO, NEXT) propagate as needed

### Network Layer

Low-level UDP sending is handled by `control/network.py`:
- `send(address, port, message)` - send message to endpoint
- `receive(socket)` - receive incoming messages

---

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
| **JOIN** | `JOIN address:port` | New node joining the ring |
| **EXIT** | `EXIT address:port next_address:port` | Node gracefully leaving |
| **PING** | `PING address:port` | Liveness/heartbeat check |
| **ECHO** | `ECHO address:port` | Response to PING |
| **NEXT** | `NEXT address:port` | Recovery when predecessor fails (tail → head) |
| **TEXT** | `TEXT message_content` | Broadcast message to all nodes |
| **USER** | `USER target_address:port message_content` | Direct message to specific node |

**Note:** Every message contains the sender's address. Nodes build a local address book as messages propagate through the ring, enabling private messaging to any known node.

### Connection Protocol (Node Join)

1. New node `N` knows existing node `X`'s `address:port`
2. `N` sends `JOIN N_address:port` to `X`
3. `X` receives the message, records `N` as its `next`
4. `X` replies (or the message propagates) so `N` knows `X`'s address
5. `N` sets its `next` to whatever was `X`'s previous `next`

**Result**: `N` is inserted between `X` and `X`'s former `next`

```
Before: [X] ──► [Y]
After:  [X] ──► [N] ──► [Y]
```

### Exit Protocol (Graceful Leave)

1. Exiting node `E` sends `EXIT E_address:port next_address:port`
2. Message propagates around the ring
3. When message reaches node `P` where `P.next == E`:
   - `P` replaces `P.next` with `E.next`
   - Ring is restored

### Failure Detection & Recovery

Since UDP has no built-in reliability, we need explicit failure detection.

#### Single Ring Recovery (PING/ECHO Protocol)

1. **Heartbeat**: Each node periodically sends `PING address:port` to its `next`
2. If the `ECHO` doesn't arrive within a timeout, `next` is considered failed
3. **Recovery (Tail → Head)**:
   - Node that stops receiving PINGs knows it became the **tail**
   - Tail sends `NEXT address:port` forward (propagates around ring)
   - Node that was sending PINGs but not receiving ECHOs knows it became the **head** (its PINGs to next are failing)
   - Head updates its `next` to the address in the NEXT message
   - Ring is restored

```
    [Head] ──► [Failing Node] ──► [Tail]
        │                           │
        │  (PINGs not ECHOed)      │  (no PINGs received)
        ▼                           ▼
    Becomes head               Sends NEXT
                                    │
                                    ▼
                            NEXT propagates → Head updates next
```

### Message Propagation Rules

#### Public Messages (`text`)
- Propagates to `next`
- **Stops** when it returns to the original sender (no loops)
- Each node logs it and caches by message ID

#### Private Messages (`USER target_address:port`)
- Propagates to `next`
- **Stops** when it reaches the `target`
- Target logs it; intermediate nodes ignore content
- Does not propagate further after delivery

#### Cache & Deduplication
- Each node maintains a `message_log` of recent payloads
- When a message is received, if its payload is already in the log, it is **not** propagated again
- This handles both sender failure and message loops
- Log entries are stored with timestamps for potential cleanup

---

## Usage

### Command Line Arguments

```bash
# Start a new ring (first node) in normal mode
python -m ai_ring_chat

# Join an existing ring (normal mode) - port 57782 is appended automatically
python -m ai_ring_chat --join 192.168.1.100

# Test mode with local port
python -m ai_ring_chat --self 9000

# Test mode: join another test node (both are ports)
python -m ai_ring_chat --self 9000 --join 9001
```

### Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--self PORT` | `-s` | Test mode: run locally on specified port (> 1024). Address is 127.0.0.1 |
| `--join TARGET` | `-j` | Target to join. In normal mode: IPv4 address (port 57782 appended). In test mode: port (address is 127.0.0.1) |

### Notes

- **Normal mode**: Local address auto-detected, `--join` expects IPv4 address (e.g., `192.168.1.100`)
- **Test mode**: Both `--self` and `--join` are ports, address is always `127.0.0.1`
- **Default port**: 57782 (well-known port for the protocol)
- **Test mode ports**: Must be > 1024 (privileged port threshold)

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
- [ ] **Persistence**: Store message log to disk
- [ ] **GUI**: Web-based or desktop interface
- [ ] **Integration tests**: Multi-node simulation

---

## Development Notes

This project is being developed with AI assistance to evaluate:
1. Specification comprehension and translation to code
2. Consistency across MVC components
3. Handling of edge cases in distributed protocols
4. Code quality and testability

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| **Tests** | 118 passed |
| **Coverage** | 99% overall (main.py: 99%, message.py: 99%, nodes.py: 96%, protocol.py: 100%) |
| **Complexity** | Average A (2.21) |

### Code Complexity by Function

| Function | Grade | Score |
|----------|-------|-------|
| `parse_message` | A | 5 |
| `handle_user` | A | 5 |
| `parse_port` | A | 4 |
| `Node.add_to_address_book` | A | 4 |
| `_process_exit` | A | 4 |
| `Address` | A | 4 |
| `Address.parse` | A | 4 |
| `handle_next` | A | 4 |
| `handle_text` | A | 4 |
| `get_ipv4_address` | A | 3 |
| `parse_join_target` | A | 3 |
| `parse_args` | A | 3 |
| `main` | A | 3 |
| `Node` | A | 2 |
| `Node.is_head` | A | 3 |
| `Node.next_address_str` | A | 3 |
| `Message` | A | 3 |
| `handle_join` | A | 3 |
| `handle_exit` | A | 3 |
| `_extract_target` | A | 3 |
| `is_valid_ipv4` | A | 2 |
| `NodeConfig` | A | 1 |
| `MessageType` | A | 1 |

---

*In omnia solacium*
