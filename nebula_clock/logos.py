"""Optional Nerd Font distro glyphs with simple text fallbacks."""

LOGOS = {
    "arch": ("", "ARCH"),
    "debian": ("", "DEB"),
    "ubuntu": ("", "UBU"),
    "mint": ("", "MINT"),
    "fedora": ("", "FED"),
    "gentoo": ("", "GENTOO"),
    "void": ("", "VOID"),
    "opensuse": ("", "SUSE"),
    "nixos": ("", "NIX"),
    "manjaro": ("", "MANJARO"),
    "kali": ("", "KALI"),
    "pop_os": ("", "POP!_OS"),
    "alpine": ("", "ALPINE"),
    "raspios": ("", "RASPBIAN"),
    "steamOS": ("", "STEAMOS"),
}


def get_logo(name: str, custom: str = "") -> str:
    if name == "custom":
        return custom or "LINUX"
    return LOGOS.get(name, ("●", name.replace("_", " ").upper()))[0]


def get_logo_fallback(name: str, custom: str = "") -> str:
    if name == "custom":
        return custom or "LINUX"
    return LOGOS.get(name, ("●", name.replace("_", " ").upper()))[1]
