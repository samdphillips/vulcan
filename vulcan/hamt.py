

class SVector:
    is_leaf = False

    def __init__(self, mask, slots):
        mask = mask & ((1 << 64) - 1)
        n = mask.bit_count()
        if n != len(slots):
            raise Exception(f'mask ({n}) and number of slots ({len(slots)}) do not match')
        self.mask = mask
        self.slots = slots

    def has_child(self, i):
        m = 1 << i
        return self.mask & m != 0

    def child_index(self, i):
        # PRE: i is a valid index from the mask
        v = (1 << i) - 1
        return (self.mask & v).bit_count()

    def update(self, rm, am, add_slots):
        # XXX: validate masks
        nm0 = (self.mask & ~rm) | am
        size = nm0.bit_count()
        new_slots = [None] * size
        i = 0
        j = 0
        k = 0
        nm = nm0
        replace_m = nm & am & rm
        add_m = nm & am & ~rm
        copy_m = nm & ~am & ~rm
        remove_m = ~nm & ~am & rm

        while nm != 0:
            if replace_m & 1 == 1:
                i += 1
                new_slots[j] = add_slots[k]
                j += 1
                k += 1
            elif add_m & 1 == 1:
                new_slots[j] = add_slots[k]
                j += 1
                k += 1
            elif copy_m & 1 == 1:
                new_slots[j] = self.slots[i]
                i += 1
                j += 1
            elif remove_m & 1 == 1:
                i += 1

            nm = nm >> 1
            replace_m = replace_m >> 1
            add_m = add_m >> 1
            copy_m = copy_m >> 1
            remove_m = remove_m >> 1
        return SVector(nm0, new_slots)

    def __contains__(self, i):
        return self.has_child(i)

    def __getitem__(self, i):
        if self.has_child(i):
            j = self.child_index(i)
            return self.slots[j]
        else:
            return None


_BRANCH_FACTOR   = 16
_TRIE_MASK_WIDTH = 4
_TRIE_MASK       = 0xF
_COUNT_POS       = 0
_SUBTREE_POS     = 1
_KEY_POS         = _SUBTREE_POS + _BRANCH_FACTOR
_VALUE_POS       = _KEY_POS + _BRANCH_FACTOR

class Hamt:
    def __init__(self, root=None):
        if root is None:
            root = SVector(1, [0])
        self.root = root

    def count(self):
        return self.root[_COUNT_POS]

    def _find_insert(self, key, value, key_hash, node, depth):
        if key_hash == 0:
            raise Exception("out of hash bits")

        i = key_hash & _TRIE_MASK
        ti = _SUBTREE_POS + i
        if ti in node:
            changed, child = self._find_insert(key,
                                               value,
                                               key_hash >> _TRIE_MASK_WIDTH,
                                               node[ti],
                                               depth + 1)
            if changed:
                m = (1 << _COUNT_POS) | (1 << ti)
                return True, node.update(m, m, [node[_COUNT_POS] + 1, child])
            else:
                return False, node
        else:
            ki = _KEY_POS + i
            vi = _VALUE_POS + i
            if ki in node:
                # replace or split
                old_key = node[ki]
                if old_key == key:
                    old_value = node[vi]
                    if old_value == value:
                        # same key/value don't change
                        return False, node
                    # replace key/value
                    m = (1 << ki) | (1 << vi)
                    return True, node.update(m, m, [key, value])
                # split value
                old_key = node[ki]
                old_value = node[vi]
                old_hash = hash(old_key) & ((1 << 64) - 1)
                old_hash = old_hash >> ((depth + 1) * _TRIE_MASK_WIDTH)
                key_hash = key_hash >> _TRIE_MASK_WIDTH
                child = self.make_node2(old_key, old_value, old_hash,
                                        key, value, key_hash)
                rm = (1 << _COUNT_POS) | (1 << ki) | (1 << vi)
                am = (1 << _COUNT_POS) | (1 << ti)
                return True, node.update(rm, am, [node[_COUNT_POS] + 1, child])
            # insert key/value into node
            rm = 1 << _COUNT_POS
            am = (1 << _COUNT_POS) | (1 << ki) | (1 << vi)
            return True, node.update(rm, am, [node[_COUNT_POS] + 1, key, value])

    def make_node2(self, ak, av, ah, bk, bv, bh):
        ai = ah & _TRIE_MASK
        bi = bh & _TRIE_MASK
        if bi < ai:
            return self.make_node2(bk, bv, bh, ak, av, ah)
        elif bi == ai:
            child = self.make_node2(ak, av, ah >> _TRIE_MASK_WIDTH,
                                    bk, bv, bh >> _TRIE_MASK_WIDTH)
            ti = _SUBTREE_POS + ai
            m = (1 << _COUNT_POS) | (1 << ti)
            return SVector(m, [2, child])
        aki = _KEY_POS + ai
        bki = _KEY_POS + bi
        avi = _VALUE_POS + ai
        bvi = _VALUE_POS + bi
        m = ((1 << _COUNT_POS) |
             (1 << aki) | (1 << avi) |
             (1 << bki) | (1 << bvi))
        return SVector(m, [2, ak, bk, av, bv])

    def insert(self, key, value):
        key_hash = hash(key) & ((1 << 64) - 1)
        changed, next_root = self._find_insert(key, value, key_hash, self.root, 0)
        if changed:
            return Hamt(next_root)
        return self

    def lookup(self, key, fk, sk):
        key_hash = hash(key) & ((1 << 64) - 1)
        node = self.root
        i = key_hash & _TRIE_MASK
        ti = _SUBTREE_POS + i
        while ti in node:
            node = node[ti]
            key_hash = key_hash >> _TRIE_MASK_WIDTH
            if key_hash == 0:
                raise Exception("out of hash bits")
            i = key_hash & _TRIE_MASK
            ti = _SUBTREE_POS + i
        ki = _KEY_POS + i
        if ki in node:
            found_key = node[ki]
            if found_key == key:
                # node has the right key
                vi = _VALUE_POS + i
                return sk(found_key, node[vi])
        # node has the wrong key OR
        # node doesn't have key
        return fk()

    def _find_remove(self, key, key_hash, node):
        if key_hash == 0:
            raise Exception("out of hash bits")

        i = key_hash & _TRIE_MASK
        ti = _SUBTREE_POS + i
        if ti in node:
            changed, child = self._find_remove(key,
                                               key_hash >> _TRIE_MASK_WIDTH,
                                               node[ti])
            if changed:
                m = (1 << _COUNT_POS) | (1 << ti)
                if child is None:
                    # remove this child
                    if node[_COUNT_POS] == 1:
                        # no subtrees and no key/values
                        # remove entire node
                        return True, None
                    return True, node.update(m, 1 << _COUNT_POS, [node[_COUNT_POS] - 1])
                # swap child
                return True, node.update(m, m, [node[_COUNT_POS] - 1, child])
            return False, node

        ki = _KEY_POS + i
        if ki in node:
            if key == node[ki]:
                if node[_COUNT_POS] == 1:
                    # no subtrees and no key/values
                    # remove entire node
                    return True, None
                # remove key/value from node
                vi = _VALUE_POS + i
                rm = (1 << _COUNT_POS) | (1 << ki) | (1 << vi)
                am = (1 << _COUNT_POS)
                return True, node.update(rm, am, [node[_COUNT_POS] - 1])
            # no change: key doesn't match
        # no change: no key here
        return False, node

    def remove(self, key):
        key_hash = hash(key) & ((1 << 64) - 1)
        changed, next_root = self._find_remove(key, key_hash, self.root)
        if changed:
            return Hamt(next_root)
        return self
