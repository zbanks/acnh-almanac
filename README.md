AC:NH Almanac
=============

Calculate the best time to go fishing in AC:NH.

The goal of this project is to use the fish appearance rates from the game to calculate...

- The best time/place to catch a certain fish (or set of fishes)
- The expected value (in bells) from fishing at a certain time/place
- Are there certain fish sizes that should be ignored? (at certain times/places?)
- etc.

Data Source
-----------

This project is heavily based on data from [CylindricalEarth](https://github.com/Treeki/CylindricalEarth) from Treeki.

Everything in `data/` is based heavily on that repository.

### BCSV Column Headers

In the BCSV ("Binary CSV") files from the AC:NH image, each column is identified by a 4-byte integer which is derived from the column name. It's presumed to be a CRC32 hash.

As far as I know, we don't yet know how to map these hashes back to the original column name. Even looking at the disassembly, it looks like the column names were hashed at compile time, so there's no guarnatee that the original column names exist as strings in the resulting binary. There are about 1100 unique column names across all BCSV files.

I've tried computing the CRC32 of random string lists to look for matches against the hashes we have: I tried `strings` of all files in `exefs` (~423k unique), and `/usr/share/dict/words` (~99k), but didn't get any hits. I also tried some brute-forcing of UTF-8 strings ~6 bytes or fewer but didn't see anything promising.

What _did_ work is exploiting the linearity of CRC32: Treeki had named some of the columns already, and I was able to find columns that had a small edit distance.

- `0x1d790df7` = `apr1923`
- `0xada9eb19` = `aug1923`
- `(0x1d790df7 ^ 0xada9eb19)` = `0xb0d0e6ee`, which equals `CRC32([5, 21] + [0] * 9) ^ CRC32([0] * 11)`
    - XORing `apr` with `[0, 5, 21]` yields `aug`.
    - From this we can tell that the columns almost certainly have "apr" and "aug" in them
        - This alone doesn't tell us which one is which
        - We cannot infer anything about case, they could be "Apr"/"Aug" or "APR"/"AUG" etc.
        - We know that the column has 9 more bytes after the "Apr" that completely match

Searching for bit edits was promising.

- The months all showed up as expected.
- `may1617` and `may1719` have a bit edit of `0x03` in the 7th byte from the end (and same for `jan1617`, etc.)
- The columns named `nw`, `n1`, etc. by Treeki also matched with each other, and furthermore can infer that the columns are capitalized & zero indexed.
    - `nw` is actually `...NW...`, `n1` is actually  a`...N0...` etc.
    - We can determine that they all have a common 19-character suffix
- `CalendarEventParam.bcsv` has two huge clusters of column names that are all nearly dentical (~1 bit similarity) -- probably numeric?

I've included an updated `data/bcsv_constants.py` with the addtional column names that I've identified.
