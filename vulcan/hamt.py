

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

