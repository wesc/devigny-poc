import unittest

from impl import Params, Commitment


class TestProof(unittest.TestCase):
    def test_pk_opening(self):
        params = Params()
        c1 = Commitment(params, x=123, r=111)
        proof = c1.pk_opening()
        self.assertTrue(Commitment.verify_pk_opening(**proof), "pk of opening failed")

        # fake a proof for a commitment that is otherwise the exact
        # same
        c2 = Commitment(params, x=123, r=111)
        proof["s1"] = c2.pk_opening()["s1"]
        self.assertFalse(Commitment.verify_pk_opening(**proof))

    def test_bound_pk_opening(self):
        params = Params()
        c1 = Commitment(params, x=123, r=111)
        proof = c1.pk_opening(binding="https://twitter.com/jack")
        self.assertTrue(
            Commitment.verify_pk_opening(**proof, binding="https://twitter.com/jack"),
            "bound pk of opening failed",
        )
        self.assertFalse(
            Commitment.verify_pk_opening(**proof),
            "bound pk of opening should failed",
        )

    def test_zk_x_eq(self):
        c1 = Commitment(Params(), x=222)
        c2 = Commitment(Params(), x=222)
        proof = c1.zk_x_eq(c2)
        self.assertTrue(Commitment.verify_x_eq(**proof))

        c1 = Commitment(Params(), x=222)
        c2 = Commitment(Params(), x=333)
        proof = c1.zk_x_eq(c2)
        self.assertFalse(Commitment.verify_x_eq(**proof))

    def test_bound_zk_x_eq(self):
        c1 = Commitment(Params(), x=222)
        c2 = Commitment(Params(), x=222)
        proof = c1.zk_x_eq(c2, binding="https://twitter.com/jack")
        self.assertTrue(
            Commitment.verify_x_eq(**proof, binding="https://twitter.com/jack")
        )
        self.assertFalse(Commitment.verify_x_eq(**proof))


if __name__ == "__main__":
    unittest.main()
