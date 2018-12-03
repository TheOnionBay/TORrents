*Notes:*

- This is TOR on top of HTTP
- All members of the network listen on port 5000 (peers, nodes and tracker)

# Installation
Install **python3** and **pipenv** on your machine, then on the root of the project run:
```bash
     pipenv install
     pipenv shell
```
This is will install all python dependencies and activate the project's virtual environment.
#Usage
##Option 1 - LAN
Firstly, run the tracker:
```bash
    python3 tracker.py
```

Then, you will need to run at least three nodes.
<ip\> : the public ip of the current machine.
```bash
     python3 node.py <ip>
```

And finally, the client.
<lof\> : path to a *.json file containing the files. Examples can be found on the /client folder.

```bash
     python3 client.py <lof>
```
##Option 2 - Online
You can also try TheOnionBay online on the following links:
###Tracker
http://theonionbay.club/

###Nodes
http://node1.theonionbay.club/
http://node2.theonionbay.club/
http://node3.theonionbay.club/
http://node4.theonionbay.club/
http://node5.theonionbay.club/
http://node6.theonionbay.club/

###Clients
http://alice.theonionbay.club/
http://bob.theonionbay.club/

The server is synchronized with the github repository.

# Terms and definitions

* *Symmetric key*: a 128-bits key used for AES encryption/decryption.
* *Assymetric key*: a 1024-bits key used for RSA encryption/decryption.
* *Upstream*: Direction from client to tracker.
* *Downstream*: Direction from tracker to client.

In the next sections we will talk about fields having names such as UpID,
DownCID, etc... In these names, Up and Down stand for *upstream* and
*downstream*, therefore referring to the connection towards the tracker or
towards the client, respectively.

# Onion Routing

## Creating the tunnel

A peer A selects three nodes X, Y, Z among those in the node pool and starts by
building a circuit. For that, A will send a message that will create the whole
circuit at once. Broadly speaking, the message is sent to X, but it contains a payload
that is forwarded to Y, and subsequently another payload is forwarded to Z.

The message is sent by POST HTTP, and is as follow:

```json
{
    "CID": "35ce8f75-6b57-4824-8597-dd756c75a9c5",
    "aes_key": "<encrypted AES key for X>",
    "payload": "<encrypted data>"
}
```

where CID stands for CircuitID and is a randomly generated UUIDv4 (it is
globally unique). The field `aes_key` is the session key (16 bytes, for example
`62E45FA2AA90DA900007FE59C88FDAEC`) that is shared between A and X, encrypted
with RSA, so that only X can decrypt it (once encrypted with RSA, the key is 128
bytes long). The field `payload` is encrypted with the AES key, and contains the
data for extending the tunnel.

Instead of a key, we could very well send key material (a seed) so the node
generates the key on its own with a key derivation function. It's basically the
same, so we will send the key directly to simplify things.

The decrypted payload should be interpreted as a JSON object, and has the
following structure:

```json
{
    "to": "<IP of Y>",
    "aes_key": "<encrypted AES key for Y>",
    "relay": "<encrypted data>"
}
```

The field `to` contains the IP address of the next node, where X will forward
the message. In order to do that, X will first generate a new CID for the
communication between X and Y, let's say this new CID is
`e9ca363d-c386-415d-9c13-127e0ca0b673`. The fields `aes_key` and `relay` are
destined to Y and are encrypted so that only Y can read it.

Now, X has five pieces of data about its connection to A and the next hop, Y:

`<DownIP, DownCID, SessKey, UpIP, UpCID>`

Where `DownIP` is the IP address of A, `DownCID` is the CID between A and X (
`35ce8f75-6b57-4824-8597-dd756c75a9c5`), `SessKey` is the AES symmetric key between A and X
(`62E45FA2AA90DA900007FE59C88FDAEC`), `UpIP` is the IP of Y, and
`UpCID` is the CID between X and Y (`e9ca363d-c386-415d-9c13-127e0ca0b673`).

X will put all this data in its Relay table  so later on when it receives a
message whose CID is in DownCID or UpCID it knows where to relay the message,
and it knows the session key to encrypt/decrypt the payload.

X can now forward the tunnel creation message to Y. It will create a new message
for Y, such as

```json
{
    "CID": "e9ca363d-c386-415d-9c13-127e0ca0b673",
    "aes_key": "<encrypted AES key for Y>",
    "payload": "<encrypted data>"
}
```

where `aes_key` and `payload` are just copied from the message shown above.

When Y receives this message, the procedure is exactly the same as what X did,
since the message Y receives contains the same fields  as what X received from
A (note that the AES key that Y receives is shared between A and Y). Now, Y
forwards the tunnel creation message to Z in the same way. The only difference
for Z is that there is no longer a "aes_key" field for the tracker, since the
messages are plaintext between the exit node Z and the tracker.

As you may notice, we are modelling stateful multiplexed TLS secured TCP
connections (actual implementation of the node network in TOR) with the data
structure in each node that relates inbound IP's, CID's, SessKey with outbound
IP's, CID's.

## Connecting the tracker

The final payload that Z forwards to the tracker is actually a list describing
which files A can share on the torrent network. The tracker responds by
giving the list of all files made available by the other users of the network.

## Message Once the Tunnel is Established

The tracker always gets messages in plaintext. This is the TOR way and the
simplest way. No encryption after the exit nodes.

When a client sends a message to the tracker, the payload is encrypted by the
client with the three symmetric keys of the three nodes X, Y and Z. Each node
decrypts the payload and relay to the next (thus it is plaintext between Z and
the tracker). When the tracker responds, the message is also plaintext between
the tracker and Z. Z encrypts the payload with its symmetric key and send to Y.
Y encrypts with its symmetric key, and so on. When the client receives a
message, it always decrypts the payload with its three symmetric keys.

# Data Structures in a Node

A node contains three tables in memory to forward messages: the *Relay Table*,
the *Upstream File Sharing Table* and the *Downstream File Sharing Table*.

## Relay Table
The relay table is filled as described in the
previous section, when a node receives for the first time a message from an
unknown CID, or the first time a message is relayed for a given CID.
Its fields are

| DownIP | DownCID | SessKey | UpIP | UpCID |
| ---- | ----- | ------- | ----- | ------ |
| | | | | | |

Where DownIP is the IP address of the previous node downstream, DownCID is the
CID of the connection to the previous node downstream, SessKey is a symmetric
key shared with the client all the way downstream, UpIP is the IP of the next
node upstream, and UpCID is the CID of the connection to the next node.

## Upstream File Sharing Table
This table is filled when a node is responsible for transmitting a file coming
from its client to another client through a bridge. Each file sharing have an
unique ID, named a *File Sharing ID*, or *FSID* for short. The File Sharing
Table is as follow

| BridgeCID | BridgeIP | FSID |
| ----- | ---- | ---- |
| | | |

This tells the node where to forward a file message that arrives with a given
FSID.

## Downstream File Sharing Table
This table is filled when a node is going to receive a file coming from  another
node through a bridge. The DownCID is one of the downstream connections that the
node has already, and BridgeCID is the CID that the node at the other side of
the bridge is using to connect to this node (CID9 in the image below). To get
the correct downstream ID and SessKey to forward a file message, the Relay Table
should be indexed with DownCID.

| DownCID | BridgeCID |
| ----- | ---- |
| | |

# File Sharing Protocol

## Messages sent by the client
The client can send three types of messages. These JSON structures are carried
in the payload transmitted through the nodes.

* *List of available files*:

This describes what files a client is ready to share, and is as follow:
```json
{
    "type": "ls",
    "files": ["titanic", "privateryan", "shawshank"]
}
```
As described before, this message is the first one transmitted by the client
to the tracker.

* *File Request*:

A client can request a file to the tracker.

```json
{
    "type": "request",
    "file": "borat"
}
```

* *Send a file chunk*:

A client can send a the content of a file after the tracker asked it to do so.

```json
{
    "type": "file",
    "file": "<name of the file>",
    "data": "<content of the file>",
    "FSID": "<FSID>"
}
```
The FSID field is a number uniquely identifying the file sharing process, and is
explained below. It is also important to include the name of the file, so that
the target client knows what file it received.

## Messages sent by the tracker
A tracker can send three types of messages. But since they are a bit more
complicated than the messages sent by clients, we will rather describe
chronologically the process of file sharing from the point of view of the
tracker.

*A note on control messages:*

Nodes can at any point receive control messages from the tracker. How do they
differentiate between messages intended for them and messages that have to go
back to the client ? The URL on which the message is sent is appended by
`control/`, for example `http://node1.theonionbay.club:5000/control/`.

* *Bridge creation*:

Assume the following setting:
![](schematic.png?raw=true)
Two clients, C1 and C2, are connected to the tracker, and we gave a name to the
CircuitID of each link between nodes. Suppose C1 sends to the tracker a request
to the tracker for a file named *Dikkenek.avi* that C2 can provide. We will
describe *how the bridge between Z2 and Z1 is established*. How the actual file
is transmitted is described later. The procedure is as follow:

1) The tracker assigns a *File Sharing ID* (FSID) to this file sharing
operation. This is a number,  taken from a counter incremented at each file
request. Let's name this number `FSID1`.
2) The tracker creates a new CircuitID that will be used in the link to bridge
Z2 to Z1. Let's name this new CID `CID9`.
3) The tracker sends a *control message* to Z2, instructing it to add a new
entry to its *Upstream File Sharing Table* to properly redirect the file to Z1.
The message being sent is

```json
{
    "type": "make_bridge",
    "bridge_CID": "<CID9>",
    "to": "<IP of Z1>",
    "FSID": "<FSID1>"
}
```
Note that this is the only message where the field `"CID"` is not used. In this
case, the FSID is sufficient to indicate to Z2 which messages should be
redirected to the bridge, it is independent from its link to the tracker.

Upon receiving this message, Z2 creates an entry in its Upstream File Sharing Table:

| BridgeCID | BridgeIP    | FSID  |
| ------ | -------- | ----- |
| `CID9`   | `IP of Z1` | `FSID1` |

So whenever a file message labelled with `FSID1` arrives to Z2, it knows where
to forward the message, and which CID to put in the message.

The situation is now looking like that:

![](schematic_bridge.png?raw=true)

4) The tracker sends *control message* to Z1, instructing it to add a new entry
to its *Downstream File Sharing Table*. This will allow the file coming from Z2
to be properly redirected to Y1 and ultimately to C1. This control message is

```json
{
    "CID": "<CID4>",
    "type": "receive_bridge",
    "bridge_CID": "<CID9>"
}
```

In order to find the downstream link to which redirect file messages from the
bridge, Z1 executes a lookup in its Relay table in the UpCID column with the CID
it shares with the tracker (`CID4`). The matching DownCID and DownIP (which are
`CID3` and the IP of Y in our example) indicate where to forward file messages.

Z1 can fill the Downstream File Sharing Table with that information:

| DownCID | BridgeCID |
| ----- | ---- |
| `<CID3>` | `<CID9>` |

We do not store the DownIP or the SessKey here, as this would be redundant with
the data in the Relay table.

* *File sharing instruction*:

1) Now that the bridge is established between Z2 and Z1, the tracker sends a
request message to C2, instructing it to share its file name *Dikkenek.avi*,
by using the File Sharing ID `FSID1`. The payload of the message is

```json
{
    "type": "request",
    "file": "Dikkenek.avi",
    "FSID": "<FSID1>",
}
```

2) Upon receiving this request, the message has been encrypted three times by
the three nodes (Z2, Y2 and X2). C2 decrypts the message, fetch the file and
send the file sharing message to its tunnel through X2. This message is
encrypted three times. The payload is as described in the previous section:

```json
{
    "type": "file",
    "file": "Dikkenek.avi",
    "data": "<content of the file>",
    "FSID": "<FSID>"
}
```

3) When the message arrives to Z2, Z2 removes the last layer of encryption and
sees that this is a file sharing message (the payload is now plaintext).
Therefore, Z2 does a lookup in its Upstream File Sharing Table by using the FSID
contained in the message. This tells Z2 that the file should be transmitted to
Z1 with CID `CID9`.

4) Z2 forwards the file message to Z1 (through the bridge):
```json
{
    "CID": "<CID9>",
    "payload": {
        "type": "file",
        "file": "Dikkenek.avi",
        "data": "<content of the file>"
    }
}
```
At this points, the FSID is no longer needed, so it is not transmitted any more.

5) Upon receiving the message from Z2, Z1 does a table lookup in the Downstream
File Sharing Table, and finds `CID9` in the column BridgeCID. The matching
DownCID is `CID3`. Z1 can therefore look at the Relay Table to find the IP and
SessKey associated to `CID3`, and finds the IP of Y1, and `K_Z1` for the
symmetric key. Z1 therefore has every needed information to encrypt and send the
message back to C1 through Y1.

6) The message arrives back, encrypted three times to C1. C1 decrypts the three
layers, and finds the file message
```json
{
    "type": "file",
    "file": "Dikkenek.avi",
    "data": "<content of the file>"
}
```
Et voilà.

# Client

The client will show an HTML page with an input to type in the file
wanted. Since it is also a Flask server, it can receive the tracker
requests and files from other peers.
