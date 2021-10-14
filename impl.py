import sys
import hashlib

import base58
from Crypto import Random
from Crypto.PublicKey import ECC


CURVE = "secp256r1"


def str_to_sha256(s: str):
    """Generate a 256 bit integer hash of an arbitrary string."""

    return int.from_bytes(hashlib.sha256(s.encode("utf-8")).digest(), "big")


def int_to_b58(i):
    return base58.b58encode_int(i).decode("ascii")


def int_from_b58(i):
    return base58.b58decode_int(i)


def point_from_ints(P):
    return ECC.EccPoint(x=P[0], y=P[1], curve=CURVE)


def point_to_ints(P):
    return [int(P.x), int(P.y)]


def point_to_b58(P):
    """Return b58 encoded P."""

    data = [
        int_to_b58(int(P.x)),
        int_to_b58(int(P.y)),
    ]
    return ",".join(data)


def point_from_b58(b):
    """Return b58 decoded P."""

    x, y = [int_from_b58(t) for t in b.split(",")]
    return ECC.EccPoint(x=x, y=y, curve=CURVE)


class Params:
    def __init__(self, G=None, H=None):
        self.order = 256
        if G is None:
            self.G = ECC.generate(curve=CURVE).pointQ
        else:
            self.G = G

        if H is None:
            self.H = ECC.generate(curve=CURVE).pointQ
        else:
            self.H = H

    @staticmethod
    def from_dict(G, H):
        return Params(point_from_b58(G), point_from_b58(H))

    def random(self):
        return Random.random.getrandbits(self.order)


class Commitment:
    def __init__(self, params, x=None, r=None):
        self.params = params
        self.H = params.H
        self.G = params.G

        if x is None:
            self.x = self.params.random()
        else:
            self.x = x

        if r is None:
            self.r = self.params.random()
        else:
            self.r = r

        self.Z = self.r * self.H + self.x * self.G

    def to_dict(self):
        return {
            "G": point_to_b58(self.G),
            "H": point_to_b58(self.H),
            "x": int_to_b58(self.x),
            "r": int_to_b58(self.r),
            "Z": point_to_b58(self.Z),
        }

    @staticmethod
    def from_dict(data):
        params = Params.from_dict(data["G"], data["H"])
        return Commitment(params, x=int_from_b58(data["x"]), r=int_from_b58(data["r"]))

    def __str__(self):
        G = point_to_b58(self.G)
        H = point_to_b58(self.H)
        return f"G={G} H={H} x={self.x} r={self.r}"

    def __repr__(self):
        return str(self)

    def pk_opening(self, binding=""):
        """Proof of knowledge of opening.

        Supplying a binding generates a proof that checks out only if
        the verifier also knows the binding.

        """

        t1 = self.params.random()
        t2 = self.params.random()
        T = Commitment(self.params, x=t1, r=t2)

        challenge = f"{self.Z.x}/{self.Z.y}/{T.Z.x}/{T.Z.y}/{binding}"
        c = str_to_sha256(challenge)

        s1 = t1 + c * self.x
        s2 = t2 + c * self.r

        return {
            "G": point_to_b58(self.G),
            "H": point_to_b58(self.H),
            "Z": point_to_b58(self.Z),
            "T": point_to_b58(T.Z),
            "s1": int_to_b58(s1),
            "s2": int_to_b58(s2),
        }

    @staticmethod
    def verify_pk_opening(G, H, Z, T, s1, s2, binding=""):
        """Verifies a pk of opening.

        A proof with a binding will only check out if the same binding
        parameter is supplied.

        """

        G = point_from_b58(G)
        H = point_from_b58(H)
        Z = point_from_b58(Z)
        T = point_from_b58(T)
        s1 = int_from_b58(s1)
        s2 = int_from_b58(s2)

        challenge = f"{Z.x}/{Z.y}/{T.x}/{T.y}/{binding}"
        c = str_to_sha256(challenge)

        LHS = s1 * G + s2 * H
        RHS = T + c * Z

        return LHS == RHS

    def zk_x_eq(self, other, binding=""):
        """Make a ZK proof of x equality.

        Supplying a binding generates a proof that only checks out if
        the verifier knows the binding.

        """

        t1 = self.params.random()
        t2 = self.params.random()
        t3 = self.params.random()

        TP = Commitment(self.params, x=t1, r=t2)
        TQ = Commitment(other.params, x=t1, r=t3)

        challenge = f"{self.Z.x}/{self.Z.y}/{TP.Z.x}/{TP.Z.y}/{other.Z.x}/{other.Z.y}/{TQ.Z.x}/{TQ.Z.y}/{binding}"
        c = str_to_sha256(challenge)

        s1 = t1 + c * self.x
        s2 = t2 + c * self.r
        s3 = t3 + c * other.r

        return {
            "PG": point_to_b58(self.G),
            "PH": point_to_b58(self.H),
            "P": point_to_b58(self.Z),
            "QG": point_to_b58(other.G),
            "QH": point_to_b58(other.H),
            "Q": point_to_b58(other.Z),
            "TP": point_to_b58(TP.Z),
            "TQ": point_to_b58(TQ.Z),
            "s1": int_to_b58(s1),
            "s2": int_to_b58(s2),
            "s3": int_to_b58(s3),
        }

    @staticmethod
    def verify_x_eq(PG, PH, P, QG, QH, Q, TP, TQ, s1, s2, s3, binding=""):
        """Verify zero knowledge proof of x equality.

        A proof with a binding will only check out if the same binding
        parameter is supplied.

        """

        PG = point_from_b58(PG)
        PH = point_from_b58(PH)
        P = point_from_b58(P)
        QG = point_from_b58(QG)
        QH = point_from_b58(QH)
        Q = point_from_b58(Q)
        TP = point_from_b58(TP)
        TQ = point_from_b58(TQ)
        s1 = int_from_b58(s1)
        s2 = int_from_b58(s2)
        s3 = int_from_b58(s3)

        challenge = f"{P.x}/{P.y}/{TP.x}/{TP.y}/{Q.x}/{Q.y}/{TQ.x}/{TQ.y}/{binding}"
        c = str_to_sha256(challenge)

        P_check = s1 * PG + s2 * PH == TP + c * P
        Q_check = s1 * QG + s3 * QH == TQ + c * Q
        return P_check and Q_check
