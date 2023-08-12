
import pytest

from vulcan.hamt import SVector

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
