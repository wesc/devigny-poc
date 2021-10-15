# Devigny Proof of Concept

Devigny is a decentralized identity linking protocol, inspired by the
[Bluesky Satellite contest](https://blueskyweb.org/satellite). Devigny
binds a user's accounts together using zero knowledge proofs such that
such links are impossible to forge and are only revealed if a user
desires to do so. It derives its operation from the practice of
placing public key fingerprints in owned accounts, but adds additional
security features.

## Protcol

1. The user generates a secret key, sk.
2. The user generates a signature for each account to link. Signatures
   are derived from sk and are called claims.
3. The user publishes the claims to each account.
4. The user publishes any number of proof books for any subset of
   accounts they wish to reveal. Proof books contain ZK proofs that
   claims are derived from the same sk.
5. A verifier gets the user's proof book and checks that the included
   claims are all derived from sk.

"user" and "verfier" in this context are analogous to DID "subjects"
and "verifiers" respectively. Unlike standard DIDs, there is no
issuer.

## `devigny` Setup

The `devigny` tool is a protocol proof of concept.

To install, create a Python virtualenv and install the necessary
packages:

```
$ python3 -m virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ ./devigny
```

In order to verify Twitter accounts, you'll need to set environment
variables to a Twitter API key:

```
export TWITTER_API_KEY=xxx
export TWITTER_API_SECRET_KEY=yyy
```

## Verifier Demo

`devigny` understands how to fetch data using a few fetch schemes:
IPFS, HTTP(S), and TWITTER.

To verify that the IPFS file
`bafkreih5qw4covu756swv47qgivrbdawhcnhpdefly6ehf6mgvrq4ah6qm`, Twitter
profile @weschow, and website / git repo
https://github.com/wesc/devigny-poc are controlled by a single user,
run:

```
$ ./devigny verify ipfs://bafkreiaqst7ppesyewoui6fkv5fprh74ly6lv5vramagekvylwfudhioji ipfs://bafkreih5qw4covu756swv47qgivrbdawhcnhpdefly6ehf6mgvrq4ah6qm twitter://weschow https://github.com/wesc/devigny-poc
ipfs://bafkreih5qw4covu756swv47qgivrbdawhcnhpdefly6ehf6mgvrq4ah6qm -- OK
twitter://weschow -- OK
https://github.com/wesc/devigny-poc -- OK
```

Where the first argument,
`ipfs://bafkreiaqst7ppesyewoui6fkv5fprh74ly6lv5vramagekvylwfudhioji`,
is the location of that user's proof book. From the output, you can
see that the check succeeded for all supplied accounts. The check
fails when run against an unclaimed Twitter account:

```
$ ./devigny verify ipfs://bafkreiaqst7ppesyewoui6fkv5fprh74ly6lv5vramagekvylwfudhioji twitter://jack
twitter://jack -- FAIL, proof of claim CE3va4sKE575MrntLhgnTM9eBpsg861WPkeH5pWgSSpe,e6F8b8Ypo5GZ9K2ozQB4CNSC4gLbR8W6DHuHsZFQoWU must be valid
```

The check also fails when run against an imposter account. For
example, @yesdefwes is most certainly not @weschow, despite [claiming
to be](https://twitter.com/yesdefwes/status/1449131650605068290):

```
$ ./devigny verify ipfs://bafkreiaqst7ppesyewoui6fkv5fprh74ly6lv5vramagekvylwfudhioji twitter://yesdefwes
twitter://yesdefwes -- FAIL, proof of claim CE3va4sKE575MrntLhgnTM9eBpsg861WPkeH5pWgSSpe,e6F8b8Ypo5GZ9K2ozQB4CNSC4gLbR8W6DHuHsZFQoWU must be valid
```

A _public_ proof book contains the linked accounts URIs, and so can be
checked:

```
$ ./devigny verify ipfs://bafkreiaqst7ppesyewoui6fkv5fprh74ly6lv5vramagekvylwfudhioji
https://github.com/wesc/devigny-poc -- OK
ipfs://bafkreih5qw4covu756swv47qgivrbdawhcnhpdefly6ehf6mgvrq4ah6qm -- OK
twitter://weschow -- OK
```

## Claims

A user first creates a secret key config:

```
$ ./devigny init
generating new secret key into config.yaml
```

The user then creates a claim:

```
$ ./devigny make-claim
claim: 8dXMQxHDbaYvgUnkNSaaLFdag3Sm8SejSnqSEhbM8Wnu,ERnnbuGtJnTs5aMbqqDrR4HiuKu4X55dbgJMJGpEgWY
```

The claim needs to be bound to a URI which uniquely specifies an
account or piece of content. First, place the signature anywhere on
the page:

```
devigny:[N]:8dXMQxHDbaYvgUnkNSaaLFdag3Sm8SejSnqSEhbM8Wnu,ERnnbuGtJnTs5aMbqqDrR4HiuKu4X55dbgJMJGpEgWY
```

The `devigny:` prefix allows the verifier to easily extract a
signature. `[N]` should be set to `0` for the current signature format
and can be used to allow for upgrades.

Then, bind the claim to the URI:

```
$ ./devigny bind-claim 8dXMQxHDbaYvgUnkNSaaLFdag3Sm8SejSnqSEhbM8Wnu,ERnnbuGtJnTs5aMbqqDrR4HiuKu4X55dbgJMJGpEgWY https://demo.com/
```

## Proof Book

To generate a proof book:

```
$ ./devigny prove-claims > proofs.yaml
```

(optionally with `--public` to make a public proof book)

The user should then publish `proofs.yaml` in any appropriate way, eg
to IPFS, a personal website, a publicly maintained directory,
blockchain, etc.

## Fetch Schemes

A fetch scheme is a method for taking a URI and fetching content where
`devigny` expects to find either a proof book or a claim signature. In
the case of IPFS or HTTP(S) this is straightforward: simply retrieve
the content and look for the `devigny:` prefix. For IPFS, the
`devigny` proof of concept tool relies on the ipfs.io gateway, which
can sometimes be slow to resolve.

The Twitter fetch scheme is more involved. A natural place to put the
signature is the bio field, however this leaves little space for a
real bio since the signature is ~100 characters long. Instead, the
user publishes the signature in a tweet, and the Twitter fetch
protocol searches for the user's most recent tweet with a `devigny:`
prefix. See [this
tweet](https://twitter.com/weschow/status/1448973030244425768) for an
example.

## Theory of Operation

A Devigny claim is a Pedersen commitment to a secret key. A proof book
consists of:

1. root commitment
2. proof of knowledge of the root secret key
3. series of ZK proofs that claims are commitments to the same secret
   key as the root.

To defend against impersonation, Devigny utilizes a specific form of
challenge when generating the non-interactive proofs. See
[theory](theory.md) for details.

## Authorship

Wes Chow (Twitter @weschow) authored this readme and all the code in
this repo, and here is the claim:
devigny:0:81grahS5rhRWyqopWdjjWi9iZEBMQRw1gtiXCQgKaJo3,HXswf5yJyztiW4TSfsh8VN3nS5Bjfe4jTi4DCUUmDTgg
