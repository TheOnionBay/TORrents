*Notes:*

- This is TOR on top of HTTP
- All members of the network listen on port 5000 (peers, nodes and tracker)

# Terms definitions

* *Symmetric key*: a 128-bits key used for AES encryption/decryption.
* *Assymetric key*: a 1024-bits key used for RSA encryption/decryption.

# Starting the tunnel

A peer A selects three nodes X, Y, Z among those in the node pool and
starts by building a circuit. A sends a message to X. X gets the following
POST HTTP message:

```json
{
    "CID": "35ce8f75-6b57-4824-8597-dd756c75a9c5",
    "payload": <encrypted data>
}
```

where CID stands for CircuitID and is a randomly generated UUIDv4 (it
is globally unique). Since X has not seen this CID before, it will
decrypt the payload with its private key, assuming the payload is the encrypted session
key that will be used in future communications with this
CircuitID.  Once it has this, the request handler returns HTTP code 200 to say OK.

The CircuitID (CID) will identify this link (the edge from A to X),
and the node can already put together 3 related elements:

`<InIP, InCID, SessKey>`

Where `InIP` is the IP address of A, `InCID` is
`35ce8f75-6b57-4824-8597-dd756c75a9c5`, and `SessKey` in the symmetric key.

The symmetric key that's asymmetrically encrypted in the payload is a
128-bit key such as:

`62E45FA2AA90DA900007FE59C88FDAEC`

This key can be generated in Python easily.

Instead of a key, we could very well send key material (a seed) so the
node generates the key on its own with a key derivation function. It's
basically the same, so we will send the key directly to simplify
things.

At this point we have done a simplified version of TLS, in which we
used public key cryptography to exchange a symmetric key.

# Extending the tunnel

Client A then sends the following message to node X, encrypting the
payload with the previously shared session key:

```json
{
    "CID": "35ce8f75-6b57-4824-8597-dd756c75a9c5", <-- CID for link A - X
    "payload": <encrypted data>
}
```

Now, node X knows about this CID and does the usual relay operation. 2
possibilities here: node X does have an outbound CID and IP for the
received CID OR not. If it does have an outbound CID and IP, simply
decrypt payload, and build a new message such as:

```json
{
    "CID": <outbound CID>,
    "payload": <decrypted data>
}
```

and pass it on to the outbound IP of that CID.

If it does not have an outbound CID however, this could mean we are
extending the tunnel, and we do not know
exactly where to go. We interpret payload differently. In `<decrypted
data>` we should find the IP where we want to relay the message. It is
in fact another JSON object and has this structure:

```json
{
    "to": <IP of Y>,
    "relay": <encrypted data>
}
```

So we know we have to connect to Y. We generate a new CID for that
new connection. Then, we can build a new object to send like this:

```json
{
    "CID": "e9ca363d-c386-415d-9c13-127e0ca0b673", <-- CID for link X - Y
    "payload": <encrypted data>
}
```

where the encrypted data in "relay" is copied in "payload".

When Y receives this message, it interprets it just like how X
interpreted its first message coming from A.

The idea is to send the same "CREATE TUNNEL" message so node Y does
not know at what position it is on the chain. Payload is encrypted
with node Y's public key and it contains the session key shared
between client A and Y.

Node X now keeps in its data structure 5 things in relation:

`<InIP, InCID, SessKey, OutIP, OutCID>`

where `OutIP` is the IP address of Y, and `OutCID` is
`e9ca363d-c386-415d-9c13-127e0ca0b673`.

So whenever it receives something with a header CID in InCID or OutCID
it knows where to relay the message.

The same thing is done with the third node to create the tunnel.

As you may notice, we are modeling stateful multiplexed TLS secured
TCP connections (actual implementation of the node network in TOR)
with the data structure in each node that relates inbound IP's, CID's,
SessKey with outbound IP's, CID's.

## Connecting the tracker

When client A has the 3 session keys in its possesion it has to send a
final connection message to the tracker. The exit node Z will get a
message with a CID for which it has no OutCID (nor any InCID). This message is
intended for the tracker. It will decrypt the payload with its private
assymetric key as described before and
check the `to:` field and relay the message. As when extending the
tunnel, the node Z will create a new CID for the connection between
Z and the tracker.
The payload of the message is the list of files the client will share
to the torrent network.

# Onion Rounting after Tunnel is Established

The tracker always gets messages in plaintext. This is the TOR way and the
simplest way. No encryption after the exit nodes.

When a client sends a message to the tracker, the message is encrypted
by the client with the three symmetric keys of the three nodes X, Y and Z.
Each node decrypts the message and relay to the next (thus it is plaintext
between Z and the tracker). When the tracker responds, the message is also 
plaintext between the tracker and Z. Z encrypts the message with its
symmetric key and send to Y. Y encrypts with its symmetric key, and so on.
When the client receives a message, it always decrypts it with its
three symmetric keys.


# Client - Tracker Protocol

## From Client to Tracker
The client can send three types of message to the tracker. These
JSON structures are carried in the payload transmitted through the
nodes.

### List of available files
This describes what files a client is ready to share, and is as follow:
```
{
    "type": "ls",
    "files": ["titanic", "privateryan", "shawshank"]
}
```
### File Request
A client can request a file to the tracker.

```json
{
    "type": "request",
    "file": "borat"
}
```

### Send a file chunk
A client can send a chunk of a file after the tracker
asked it to do so.

```json
{
    "type": "file_chunk",
    "chunk_idx": <index of the chunk in the file> 
    "data": <bytes data>
}
```
The exact format of this message is described later.

## From Tracker to Client
A tracker can send one type of message to the client

### Asking for file sharing
The tracker can send a request to a client to share a file.
```json
{
    "type": "request",
    "file": "borat"
}
```
The redirection of the file messages to the requesting client 
is done **by the tracker** with control messages to the exit nodes,
the client just has to send `"file_chunk"` messages to its tunnel.

## From Tracker to Exit Node - Control messages

Nodes can at any point receive control messages from the tracker.

How do they differentiate between messages intended for them and
messages that have to go back to the client ?

The CID used by the tracker will be "control". As in:

```json
{
    "CID": "control",
    "payload": {
        ...
    }
}
```


# Client

The client will show an HTML page with an input to type in the file
wanted. Since it is also a Flask server, it can receive the tracker
requests and files from other peers.
