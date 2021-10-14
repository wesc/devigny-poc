"""Tool to hash strings to a point on the secp256r1 curve.

"""

import hashlib

import click
from Crypto.PublicKey import ECC
from Crypto.Math._IntegerGMP import IntegerGMP

import impl


@click.command()
@click.argument("s", type=str, required=True)
def nums(s):
    # secp256r1 constants
    a = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC
    b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
    p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF

    inc = 0
    while True:
        inc += 1

        # construct a NUMS string and map it to a point on the curve
        NUMS = hashlib.sha256(f"{s}/{inc}".encode("utf-8"))
        x = int(NUMS.hexdigest(), 16)
        x = IntegerGMP(x) % p

        # ecc curve is of the form y**2 = x**3 + a*x + b
        rhs = x ** 3 + x * a + b
        try:
            y = rhs.sqrt(modulus=p)
        except ValueError:
            continue

        lhs = y ** 2
        if lhs % p == rhs % p:
            try:
                point = ECC.EccPoint(x, y, curve="secp256r1")
                break
            except ValueError:
                continue

    click.echo(impl.point_to_b58(point))


if __name__ == "__main__":
    nums()
