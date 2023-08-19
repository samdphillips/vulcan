
import pytest

from vulcan.hamt import Hamt, SVector

class TestSVector:
    def test_bad_mask(self):
        with pytest.raises(Exception):
            SVector(0, [None])

    def test_has_child(self):
        sv0 = SVector(1, [None])
        assert sv0.has_child(0)
        assert not sv0.has_child(1)
        assert 0 in sv0
        assert 1 not in sv0

        sv1 = SVector(2, [None])
        assert not sv1.has_child(0)
        assert sv1.has_child(1)


    def test_child_index(self):
        assert SVector(1, [None]).child_index(0) == 0
        assert SVector(2, [None]).child_index(1) == 0
        assert SVector(3, [None] * 2).child_index(0) == 0
        assert SVector(3, [None] * 2).child_index(1) == 1

    def test_ref(self):
        assert SVector(3, [3,4])[0] == 3
        assert SVector(3, [3,4])[1] == 4
        assert SVector(3, [3,4])[2] == None
        assert SVector(4, [5])[0] == None
        assert SVector(4, [5])[1] == None
        assert SVector(4, [5])[2] == 5

    def test_update_empty_add(self):
        sv0 = SVector(0,[])
        sv1 = sv0.update(0, 1, [42])
        assert sv1.mask == 1
        assert sv1.slots == [42]

    def test_update_replace(self):
        sv0 = SVector(4,[3])
        sv1 = sv0.update(4,4,[42])
        assert sv1.mask == 4
        assert sv1.slots == [42]

    def test_update_copy(self):
        sv0 = SVector(3, [41,42])
        sv1 = sv0.update(0,0,[])
        assert sv0.mask == sv1.mask
        assert sv0.slots == sv1.slots

    def test_update_remove_empty(self):
        sv0 = SVector(1, [1])
        sv1 = sv0.update(1,0,[])
        assert sv1.mask == 0
        assert sv1.slots == []

    def test_update_remove_first(self):
        sv0 = SVector(3, [1,2])
        sv1 = sv0.update(1,0,[])
        assert sv1.mask == 2
        assert sv1.slots == [2]

    def test_update_shift(self):
        sv0 = SVector(3, [3, 4])
        sv1 = sv0.update(3, 6, [3, 4])
        assert sv1.mask == 6
        assert sv1.slots == [3, 4]

class O:
    def __init__(self, s, h):
        self.s = s
        self.h = h

    def __hash__(self):
        return (super().__hash__() << self.s) | self.h

class TestHamt:
    def setup(self):
        self.h0 = Hamt()
        self.ka = O(8, 0x00)
        self.kb = O(8, 0x01)
        self.kc = O(8, 0x10)
        self.kd = O(8, 0x20)

    def test_count(self):
        assert self.h0.count() == 0
        h1 = self.h0.insert(self.ka, 42)
        assert h1.count() == 1
        h2 = h1.insert(self.kb, 43)
        assert h2.count() == 2
        h3 = h2.remove(self.ka)
        assert h3.count() == 1
        h4 = h3.remove(self.kb)
        assert h4.count() == 0

    def test_insert_ref(self):
        h1 = self.h0.insert(self.ka, 42)
        h2 = h1.insert(self.kb, 43)
        assert self.h0.lookup(self.ka, lambda: None, lambda k,v: v) is None
        assert self.h0.lookup(self.kb, lambda: None, lambda k,v: v) is None

        assert h1.lookup(self.ka, lambda: None, lambda k,v: v) == 42
        assert h1.lookup(self.kb, lambda: None, lambda k,v: v) is None

        assert h2.lookup(self.ka, lambda: None, lambda k,v: v) == 42
        assert h2.lookup(self.kb, lambda: None, lambda k,v: v) == 43

    def test_insert_split(self):
        h1 = self.h0.insert(self.ka, 42)
        h2 = h1.insert(self.kc, 43)
        assert h2.count() == 2
        assert h2.lookup(self.ka, lambda: None, lambda k,v: v) == 42
        assert h2.lookup(self.kc, lambda: None, lambda k,v: v) == 43

    def test_insert_dup(self):
        h1 = self.h0.insert(self.ka, 42)
        h2 = h1.insert(self.ka, 42)
        assert h2.count() == 1
        assert h2.lookup(self.ka, lambda: None, lambda k,v: v) == 42

    def test_insert_replace(self):
        h1 = self.h0.insert(self.ka, 42)
        h2 = h1.insert(self.ka, 43)
        assert h2.count() == 1
        assert h2.lookup(self.ka, lambda: None, lambda k,v: v) == 43

    def test_insert_traverse(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kc, 1)
        h3 = h2.insert(self.kd, 2)
        assert h3.count() == 3
        assert h3.lookup(self.ka, lambda: None, lambda k,v: v) == 0
        assert h3.lookup(self.kc, lambda: None, lambda k,v: v) == 1
        assert h3.lookup(self.kd, lambda: None, lambda k,v: v) == 2

    def test_insert_split_swap(self):
        h1 = self.h0.insert(self.kc, 1)
        h2 = h1.insert(self.ka, 0)
        assert h2.count() == 2
        assert h2.lookup(self.ka, lambda: None, lambda k,v: v) == 0
        assert h2.lookup(self.kc, lambda: None, lambda k,v: v) == 1

    def test_insert_traverse_dup(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kc, 1)
        h3 = h2.insert(self.kc, 1)
        assert h3.count() == 2
        assert h3.lookup(self.ka, lambda: None, lambda k,v: v) == 0
        assert h3.lookup(self.kc, lambda: None, lambda k,v: v) == 1

    def test_insert_afewbitsmore(self):
        ka = O(8, 0)
        kb = O(8, 0)
        h1 = self.h0.insert(ka, 0)
        h2 = h1.insert(kb, 1)
        assert h2.count() == 2
        assert h2.lookup(ka, lambda: None, lambda k,v: v) == 0
        assert h2.lookup(kb, lambda: None, lambda k,v: v) == 1

    def test_remove_traverse(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kc, 1)
        h3 = h2.insert(self.kd, 2)
        h4 = h3.remove(self.ka)
        assert h4.count() == 2
        assert h4.lookup(self.ka, lambda: None, lambda k,v: v) is None
        assert h4.lookup(self.kc, lambda: None, lambda k,v: v) == 1
        assert h4.lookup(self.kd, lambda: None, lambda k,v: v) == 2

    def test_remove_all(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kb, 1)
        h3 = h2.remove(self.ka)
        h4 = h3.remove(self.kb)
        assert h4.count() == 0
        assert h4.lookup(self.ka, lambda: None, lambda k,v: v) is None
        assert h4.lookup(self.kb, lambda: None, lambda k,v: v) is None

    def test_remove_missing(self):
        h1 = self.h0.remove(self.ka)
        assert h1.count() == 0

    def test_remove_all_traverse(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kc, 1)
        h3 = h2.insert(self.kd, 2)
        h4 = h3.remove(self.ka)
        h5 = h4.remove(self.kd)
        h6 = h5.remove(self.kc)
        assert h6.count() == 0
        assert h6.lookup(self.ka, lambda: None, lambda k,v: v) is None
        assert h6.lookup(self.kc, lambda: None, lambda k,v: v) is None
        assert h6.lookup(self.kd, lambda: None, lambda k,v: v) is None

    def test_remove_traverse_keep(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kb, 1)
        h3 = h2.insert(self.kc, 2)
        h4 = h3.remove(self.ka)
        h5 = h4.remove(self.kc)
        assert h5.count() == 1
        assert h5.lookup(self.ka, lambda: None, lambda k,v: v) is None
        assert h5.lookup(self.kc, lambda: None, lambda k,v: v) is None
        assert h5.lookup(self.kb, lambda: None, lambda k,v: v) == 1

    def test_remove_traverse_missing(self):
        h1 = self.h0.insert(self.ka, 0)
        h2 = h1.insert(self.kb, 1)
        h3 = h2.insert(self.kc, 2)
        h4 = h3.remove(self.kd)
        assert h4.count() == 3
        assert h4.lookup(self.ka, lambda: None, lambda k,v: v) == 0
        assert h4.lookup(self.kb, lambda: None, lambda k,v: v) == 1
        assert h4.lookup(self.kc, lambda: None, lambda k,v: v) == 2
