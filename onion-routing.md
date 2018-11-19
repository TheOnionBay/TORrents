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
message with a CID for which it has no OutCID. This message is
intended for the tracker. It will decrypt the payload as usual and
check the `to:` field and relay the message. The message can be foo,
or OK, or anything (even the list of files...).

We simply want Z (the exit node) to include the necessary information
in its data structure to relay messages to the tracker without looking
up a `to:` field. This is why the message can be anything and not an
extend instruction to exchange keys.

# Client - Tracker communication

The tracker always gets things in plaintext. This is the TOR way and the
simplest way.

Now the sending is straight-forward.

The client will send the list of files it has to tracker:

```
{
    "type": "ls",
    "files": ["titanic", "privateryan", "shawshank"]
}
```

another kind of message it can send:

```json
{
    "type": "request",
    "file": "borat"
}
```

This is obviously the kernel of the whole thing sent. It has to be
wrapped in successive layers of encryption (3).

# Tracker-nodes control messages

Nodes can at any point receive control messages from the tracker.

How do they differentiate between messages intended for them and
messages that have to go back to the client ?

The CID used by the tracker will be "control". As in:

```json
{
    "CID": "control",
    "payload": {
        "type": "bridge",
        "FromCID":
        ???
    }
}
```

# Client

The client will show an HTML page with an input to type in the file
wanted. Since it is also a Flask server, it can receive the tracker
requests and files from other peers.

So for a client to send a file to the network:

```json
{
    "type": "share",
    "file": "barbie"
}
```
