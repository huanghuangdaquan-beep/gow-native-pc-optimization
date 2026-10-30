"""Probe the JP disc's boot ELF: PCSX2 CRC + .text SHA-1, compared with the US profile."""
import sys, os, json
REPO = r"C:\Users\nb\Desktop\gow-src-upstream"
sys.path.insert(0, os.path.join(REPO, "tools", "disc"))
sys.path.insert(0, os.path.join(REPO, "tools", "pipeline"))
import discfs
import profile as profiles

iso = r"C:\Users\nb\Desktop\gow-native-pc-2.0.0\zs.iso"
disc = discfs.open_disc(iso)
print("boot elf:", discfs.boot_elf_name(disc.read("SYSTEM.CNF")))
elf_name = discfs.boot_elf_name(disc.read("SYSTEM.CNF"))
elf = disc.read(elf_name)
print("elf size:", len(elf))
print("pcsx2 crc:", discfs.pcsx2_crc(elf))
print("text sha1:", discfs.text_sha1(elf))
prof = [p for p in profiles.all_profiles() if p["id"] == "gow1"][0]
print("profile crc:", prof["executable"]["crc"])
print("profile text_sha1:", prof["executable"]["text_sha1"])
print("MATCH crc:", discfs.pcsx2_crc(elf) == prof["executable"]["crc"])
print("MATCH text:", discfs.text_sha1(elf) == prof["executable"]["text_sha1"])
# also: does the US ELF name exist on this disc?
print("has SCUS_973.99:", disc.has("SCUS_973.99"))
