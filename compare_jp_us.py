"""Compare the JP disc's ELF layout against the US function map (config/funcmap.csv).

Answers: is the JP executable the same code layout (same function start addresses),
a constant shift, or a different build?
"""
import sys, os, struct, csv, collections

REPO = r"C:\Users\nb\Desktop\gow-src-upstream"
sys.path.insert(0, os.path.join(REPO, "tools", "disc"))
import discfs

ISO = r"C:\Users\nb\Desktop\gow-native-pc-2.0.0\zs.iso"
FUNCMAP = os.path.join(REPO, "engine", "runtime", "config", "funcmap.csv")

disc = discfs.open_disc(ISO)
elf_name = discfs.boot_elf_name(disc.read("SYSTEM.CNF"))
elf = disc.read(elf_name)

# --- ELF32 parse ---
(e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize,
 e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", elf, 16)
print(f"ELF: type={e_type} machine={e_machine} entry=0x{e_entry:08X} shnum={e_shnum} shstrndx={e_shstrndx}")

sh = []
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    (name, typ, flags, addr, offset, size, link, info, align, entsize) = struct.unpack_from("<IIIIIIIIII", elf, off)
    sh.append(dict(name=name, type=typ, flags=flags, addr=addr, offset=offset, size=size, link=link, entsize=entsize))
strtab_off = sh[e_shstrndx]["offset"]
def sname(n):
    end = elf.index(b"\0", strtab_off + n)
    return elf[strtab_off + n:end].decode("latin1")
sections = {sname(s["name"]): s for s in sh}
print("sections:", ", ".join(sorted(sections.keys())))

text = sections.get(".text")
print(f".text vaddr=0x{text['addr']:08X} size=0x{text['size']:X} ({text['size']} bytes)")

# --- symbol table ---
syms = []
for secname in (".symtab", ".dynsym"):
    sec = sections.get(secname)
    if not sec:
        continue
    strt = sh[sec["link"]]["offset"]
    n = sec["size"] // (sec["entsize"] or 16)
    for i in range(n):
        off = sec["offset"] + i * sec["entsize"]
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from("<IIIBBH", elf, off)
        if st_info >> 4 != 2:  # STT_FUNC
            continue
        end = elf.index(b"\0", strt + st_name)
        name = elf[strt + st_name:end].decode("latin1")
        if st_value and st_shndx:
            syms.append((st_value, st_size, name, secname))
    print(f"{secname}: {len(syms)} FUNC symbols")

syms.sort()
addrs = sorted({s[0] for s in syms})
print(f"unique FUNC start addresses: {len(addrs)}")

# --- US funcmap ---
us = []
with open(FUNCMAP, newline="", encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        us.append((int(row["Start"], 16), int(row["Size"]), row["Name"]))
us_addrs = sorted(a for a, _, _ in us)
print(f"US funcmap functions: {len(us)}")

# --- compare ---
us_set = set(us_addrs)
jp_set = set(addrs)
common = us_set & jp_set
print(f"exact address overlap: {len(common)} / {len(us_set)} US  ({100*len(common)/len(us_set):.1f}%)")

# constant-delta test: try every plausible shift by matching sorted order
best = None
for delta in range(-0x20000, 0x20001, 4):
    hits = sum(1 for a in us_addrs if (a + delta) in jp_set)
    if best is None or hits > best[1]:
        best = (delta, hits)
print(f"best constant shift: {best[0]:#x} matching {best[1]} of {len(us_addrs)} US functions "
      f"({100*best[1]/len(us_addrs):.1f}%)")

# where do the US stub addresses land?
tmpl = os.path.join(REPO, "engine", "runtime", "config", "recomp.template.toml")
import re
stubs = re.findall(r'"([^"]+)@(0x[0-9A-Fa-f]+)"', open(tmpl, encoding="utf-8").read())
in_jp = sum(1 for _, a in stubs if int(a, 16) in jp_set)
print(f"US stub addresses present in JP symbol set: {in_jp}/{len(stubs)}")
missing = [(n, a) for n, a in stubs if int(a, 16) not in jp_set][:10]
print("first missing stubs:", missing)

# sample of JP symbols for eyeballing
print("JP sample symbols:", [(f"0x{a:08X}", n) for a, _, n, _ in syms[:8]])
print("JP symbols in stub range (0x0026xxxx):",
      [(f"0x{a:08X}", n) for a, _, n, _ in syms if 0x00260000 <= a <= 0x00290000][:10])
