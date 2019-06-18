import os, mmap, sys

class PiSearch:

    seq_thres = 4

    def __init__(self):
        self.pi_file = os.open('pi1m.4.bin', os.O_RDONLY)
        self.pi_map = mmap.mmap(self.pi_file, 0, access=mmap.ACCESS_READ)
        self.num_digits = self.pi_map.size()
        self.idx_file = os.open('pi1m.4.idx', os.O_RDONLY)
        self.idx_map = mmap.mmap(self.idx_file, 0, access=mmap.ACCESS_READ)
    
    def digit_at(self, pos):
        b = self.pi_map[int(pos/2)]
        if pos & 0x01 == 1:
            return b & 0x0f
        return b >> 4

    def get_digits(self, start, length):

        if start >= self.num_digits:
            return ""

        end = start + length

        if end >= self.num_digits:
            end = self.num_digits - 1

        res = ""
        for i in range(end - start):
            res += str(self.digit_at(start + i)) + '0'

        return res

    def compare(self, start, searchbytes):
        skl = len(searchbytes)
        def_ = 0

        if skl + start >= self.num_digits:
            skl = self.num_digits - start
            def_ = -1

        for i in range(skl):
            da = self.digit_at(start + i)

            if da < searchbytes[i]:
                return -1
            elif da > searchbytes[i]:
                return 1

        return def_        

    def seqsearch3(self, start, searchbytes):

        max_pos = self.num_digits - len(searchbytes)
        doub = searchbytes[0] << 4 | searchbytes[1]
        doub2 = searchbytes[1] << 4 | searchbytes[2]

        position = start

        if position & 1 == 0:
            b = self.pi_map[int(position/2)]

            if b == doub and self.compare(position, searchbytes) == 0:
                return True, position, 0

            position += 1

        while position < max_pos:
            b = self.pi_map[int((position+1)/2)]

            if b == doub2 and self.compare(position, searchbytes) == 0:
                return True, position, 0

            if b == doub and self.compare(position+1, searchbytes) == 0:
                return True, position + 1, 0


            position += 2

        return False, 0, 0

    def seqsearch2(self, start, searchbytes):

        max_pos = self.num_digits - len(searchbytes)
        position = start

        while position < max_pos:

            if self.digit_at(position) == searchbytes[0]:

                if len(searchbytes) == 1 or self.digit_at(position+1) == searchbytes[1]:
                    return True, position, 0

            position += 1
        
        return False, 0, 0

    def idx_at(self, pos):
        i = pos * 4
        return int.from_bytes(self.idx_map[i:i+4], byteorder='little')

    @classmethod
    def binary_search(cls, n, f):
        i, j = 0, n
        while i < j:
            h = int((i + j) / 2)
            if f(h) == False:
                i = h + 1
            else:
                j = h
        return i

    def idxrange(self, searchbytes):
        def f(i):
            return self.compare(self.idx_at(i), searchbytes) >= 0

        start = self.binary_search(self.num_digits, f)

        def g(i):
            return self.compare(self.idx_at(i + start), searchbytes) != 0
        end = self.binary_search(self.num_digits - start, g)
        return start, end

    def count_byte_key(self, searchbytes):
        start, end = self.idxrange(searchbytes)
        return end - start

    def search_key_to_bytes(self, key):
        keys = [int(i) for i in key]
        searchbytes = bytearray(keys)
        return searchbytes

    def count(self, searchkey):
        return self.count_byte_key(self.search_key_to_bytes(searchkey))

    def idx_search(self, start, searchbytes):
        found_start, found_end = self.idxrange(searchbytes)
        n_mathes = (found_end - found_start)

        best = sys.maxsize

        for i in range(n_mathes):
            pos = self.idx_at(i + found_start)
            if pos >= start and pos < best:
                best = pos
        
        if best != sys.maxsize:
            return True, best, n_mathes

        return False, 0, 0

    def search(self, start, searchkey):

        querylen = len(searchkey)

        if querylen == 0:
            return False, 0, 0

        searchbytes = self.search_key_to_bytes(searchkey)

        if querylen <= self.seq_thres:
            n_mathes = self.count_byte_key(searchbytes)

        if querylen <= 2:
            found, position, _ = self.seqsearch2(start, searchbytes)

        elif querylen <= self.seq_thres:
            found, position, _ = self.seqsearch3(start, searchbytes)
        
        else:
            found, position, n_mathes = self.idx_search(start, searchbytes)

        return found, position, n_mathes


if __name__ == "__main__":
    a = PiSearch()
    b = a.search(0,"16101")
    print(b)
