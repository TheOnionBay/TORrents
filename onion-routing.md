*Notes:*

- This is TOR on top of HTTP
- All members of the network listen on port 5000 (peers, nodes and tracker)

# Terms definitions

* *Symmetric key*: a 128-bits key used for AES encryption/decryption.
* *Assymetric key*: a 1024-bits key used for RSA encryption/decryption.

# Onion Rounting

## Starting the tunnel

A peer A selects three nodes X, Y, Z among those in the node pool and starts by
building a circuit. A sends a message to X. X gets the following POST HTTP
message:

```json
{
    "CID": "35ce8f75-6b57-4824-8597-dd756c75a9c5",
    "payload": "<encrypted data>"
}
```

where CID stands for CircuitID and is a randomly generated UUIDv4 (it is
globally unique). Since X has not seen this CID before, it will decrypt the
payload with its private key, assuming the payload is the encrypted session key
that will be used in future communications with this CircuitID.  Once it has
this, the request handler returns HTTP code 200 to say OK.

The CircuitID (CID) will identify this link (the edge from A to X), and the node
can already put together 3 related elements:

`<DownIP, DownCID, SessKey>`

Where `DownIP` is the IP address of A, `DownCID` is
`35ce8f75-6b57-4824-8597-dd756c75a9c5`, and `SessKey` is the symmetric key.

The symmetric key that's asymmetrically encrypted in the payload is a 128-bit
key such as:

`62E45FA2AA90DA900007FE59C88FDAEC`

This key can be generated in Python easily.

Instead of a key, we could very well send key material (a seed) so the node
generates the key on its own with a key derivation function. It's basically the
same, so we will send the key directly to simplify things.

At this point we have done a simplified version of TLS, in which we used public
key cryptography to exchange a symmetric key.

## Extending the tunnel

Client A then sends the following message to node X, encrypting the payload with
the previously shared session key:

```json
{
    "CID": "35ce8f75-6b57-4824-8597-dd756c75a9c5", <-- CID for link A - X
    "payload": "<encrypted data>"
}
```

Now, node X knows about this CID and does the usual relay operation. 2
possibilities here: node X does have an outbound CID and IP for the received CID
OR not. If it does have an outbound CID and IP, simply decrypt payload, and
build a new message such as:

```json
{
    "CID": "<outbound CID>",
    "payload": "<decrypted data>"
}
```

and pass it on to the outbound IP of that CID.

If it does not have an outbound CID however, this could mean we are extending
the tunnel, and we do not know exactly where to go. We interpret payload
differently. In `<decrypted data>` we should find the IP where we want to relay
the message. It is in fact another JSON object and has this structure:

```json
{
    "to": "<IP of Y>",
    "relay": "<encrypted data>"
}
```

So we know we have to connect to Y. We generate a new CID for that new
connection. Then, we can build a new object to send like this:

```json
{
    "CID": "e9ca363d-c386-415d-9c13-127e0ca0b673", <-- CID for link X - Y
    "payload": "<encrypted data>"
}
```

where the encrypted data in "relay" is copied in "payload".

When Y receives this message, it interprets it just like how X interpreted its
first message coming from A.

The idea is to send the same "CREATE TUNNEL" message so node Y does not know at
what position it is on the chain. Payload is encrypted with node Y's public key
and it contains the session key shared between client A and Y.

Node X now keeps in its data structure 5 things in relation:

`<DownIP, DownCID, SessKey, UpIP, UpCID>`

where `UpIP` is the IP address of Y, and `UpCID` is
`e9ca363d-c386-415d-9c13-127e0ca0b673`.

So whenever it receives something with a header CID in DownCID or UpCID it knows
where to relay the message.

The same thing is done with the third node to create the tunnel.

As you may notice, we are modeling stateful multiplexed TLS secured TCP
connections (actual implementation of the node network in TOR) with the data
structure in each node that relates inbound IP's, CID's, SessKey with outbound
IP's, CID's.

## Connecting the tracker

When client A has the 3 session keys in its possesion it has to send a final
connection message to the tracker. The exit node Z will get a message with a CID
for which it has no UpCID (nor any DownCID). This message is intended for the
tracker. It will decrypt the payload with its private assymetric key as
described before and check the `to:` field and relay the message. As when
extending the tunnel, the node Z will create a new CID for the connection
between Z and the tracker. The payload of the message is the list of files the
client will share to the torrent network.

## Message Once the Tunnel is Established

The tracker always gets messages in plaintext. This is the TOR way and the
simplest way. No encryption after the exit nodes.

When a client sends a message to the tracker, the message is encrypted by the
client with the three symmetric keys of the three nodes X, Y and Z. Each node
decrypts the message and relay to the next (thus it is plaintext between Z and
the tracker). When the tracker responds, the message is also plaintext between
the tracker and Z. Z encrypts the message with its symmetric key and send to Y.
Y encrypts with its symmetric key, and so on. When the client receives a
message, it always decrypts it with its three symmetric keys.

# Data Structures in a Node

A node contains two tables in memory to forward messages: the *Relay Table* and
the *File Sharing Table*.

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

## File Sharing Table
This table is filled when a node is responsible for transmitting a file coming
from its client to another client through a bridge. Each file sharing have an
unique ID, named a *File Sharing ID*, or *FSID* for short. The File Sharing
Table is as follow

| UpCID | UpIP | FSID |
| ----- | ---- | ---- |
| | | |

This tells the node where to forward a file message that arrives with a given
FSID.


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
back to the client ? The CID used by the tracker will be "control". As in:

```json
{
    "CID": "control",
    ...
}
```

* *Bridge creation*:

Assume the following setting:
![](docs/schematic.png?raw=true)
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
entry to its *File Sharing Table* to properly redirect the file to Z1. The
message being sent is

```json
{
    "CID": "control",
    "type": "make_bridge",
    "bridge_CID": "<CID9>",
    "to": "<IP of Z1>",
    "FSID": "<FSID1>"
}
```

Upon receiving this message, Z2 creates an entry in its File Sharing Table:

| UpCID | UpIP    | FSID  |
| ------ | -------- | ----- |
| `CID9`   | `IP of Z1` | `FSID1` |

So whenever a file message labelled with `FSID1` arrives to Z2, it knows where
to forward the message, and which CID to put in the message.

The situation is now looking like that:

![](docs/schematic_bridge.png?raw=true)

4) The tracker sends *control message* to Z1, instructing it to add a
new entry to its relay table. This will allow the file coming from Z2 to be
properly redirected to Y1 and ultimately to C1. This control message is

```json
{
    "CID": "control",
    "type": "receive_bridge",
    "bridge_CID": "<CID9>",
    "from": "<IP of Z2>",
    "FSID": "<FSID1>"
}
```

When Z1 receives this message, there is already an entry in its relay table
about the link between C1 and the tracker. This entry is as follow

| DownIP | DownCID | SessKey | UpIP | UpCID |
| ---- | ----- | ------- | ----- | ------ |
| `IP of Y1` | `CID3` | `K_Z1` | `IP_T` | `CID4` |

Therefore the new entry to add required by the control message is mainly
a copy of this one, just replacing the UpIP and UpCID by those of the new
connection coming from Z2. The table is now

| DownIP | DownCID | SessKey | UpIP | UpCID |
| ---- | ----- | ------- | ----- | ------ |
| `IP of Y1` | `CID3` | `K_Z1` | `IP_T` | `CID4` |
| `IP of Y1` | `CID3` | `K_Z1` | `IP_Z2` | `CID9` |


* *File sharing instruction*:

1) Now that the bridge is established between Z2 and Z1, the tracker sends a
request message to C2, instructing it to share its file name *Dikkenek.avi*,
by using the File Sharing ID `FSID1`

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
encrypted three times. The innermost payload is as described in the previous
section:

```json
{
    "type": "file",
    "file": "Dikkenek.avi",
    "data": "<content of the file>",
    "FSID": "<FSID>"
}
```

3) When the message arrives to Z2, Z2 removes the last layer of encryption and
sees that this is a file sharing message (the message is now plaintext).
Therefore, Z2 does a lookup in its File Sharing Table by using the FSID
contained in the message. This tells Z2 that the file should be transmitted to
Z1 with CID `CID9`.

4) Z2 forwards the file message to Z1:
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
At this points, the FSID is no longer needed, so it is not transmitted anymore.

5) Upon receiving the message from Z2, Z1 does a table lookup in the Relay
Table, and finds `CID9` in the column UpCID. The matching DownIP is the IP of Y1,
the matching DownCID is `CID3` and the matching symmetric key is `K_Z1`. Z1
therefore has every needed information to encrypt and send the message back to
C1 through Y1.

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
