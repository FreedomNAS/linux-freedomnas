#!/usr/bin/env python3
"""
follow-lts.py [--apply] [--work DIR]

Keep PKGBUILD on the newest Linux LTS that OpenZFS supports, with our
config and patches.

- Point releases of the series PKGBUILD is on come from kernel.org's
  releases.json, as soon as they are out.
- OpenZFS follows its newest stable release whose META Linux-Maximum covers
  the series.
- A newer LTS series is taken only when that OpenZFS supports it and Arch's
  linux-lts already moved to it.
- While Arch's linux-lts is on the same series, its config.x86_64 and
  patches are ours too (config.freedomnas stays, merged over it at build
  time); a change of theirs alone gives a new pkgrel.

Every tarball is checked against its PGP signature (keys/pgp) before its
sha256 is written, and every patch must apply to the new sources: anything
that fails leaves PKGBUILD untouched and exits 1. Without --apply it only
prints what it would do. Exit 0 with "up to date" when nothing is newer.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKGBUILD = ROOT / "PKGBUILD"
KEYS = ROOT / "keys" / "pgp"
RELEASES = "https://www.kernel.org/releases.json"
ZFS_RELEASES = "https://api.github.com/repos/openzfs/zfs/releases?per_page=30"
ZFS_META = "https://raw.githubusercontent.com/openzfs/zfs/{tag}/META"
KERNEL_TAR = "https://cdn.kernel.org/pub/linux/kernel/v{major}.x/linux-{version}.tar.{ext}"
ZFS_TAR = "https://github.com/openzfs/zfs/releases/download/zfs-{version}/zfs-{version}.tar.gz{ext}"
ARCH = "https://gitlab.archlinux.org/archlinux/packaging/packages/linux-lts/-/raw/main/{name}"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "linux-freedomnas follow-lts"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def download(url: str, target: Path) -> Path:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "follow-lts"}),
                                timeout=600) as response, open(target, "wb") as f:
        shutil.copyfileobj(response, f)
    return target


def series(version: str) -> tuple:
    return tuple(int(p) for p in version.split(".")[:2])


def numbers(version: str) -> tuple:
    return tuple(int(p) for p in version.split("."))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def variable(text: str, name: str) -> str:
    return re.search(rf"^{name}=(\S+)$", text, re.M).group(1)


def longterm() -> list:
    releases = json.loads(fetch(RELEASES))["releases"]
    return [r["version"] for r in releases if r["moniker"] == "longterm" and not r.get("iseol")]


def zfs_choice() -> tuple:
    """The newest stable OpenZFS and the newest kernel series it supports."""
    tags = [r["tag_name"] for r in json.loads(fetch(ZFS_RELEASES))
            if not r["prerelease"] and not r["draft"] and re.fullmatch(r"zfs-\d+\.\d+\.\d+", r["tag_name"])]
    newest = max(tags, key=lambda t: numbers(t[4:]))
    meta = fetch(ZFS_META.format(tag=newest)).decode()
    maximum = re.search(r"^Linux-Maximum:\s*(\S+)", meta, re.M).group(1)
    return newest[4:], series(maximum)


def arch_files() -> dict:
    """Arch linux-lts: its pkgver, patches (name -> text) and config.x86_64."""
    pkgbuild = fetch(ARCH.format(name="PKGBUILD")).decode()
    names = re.findall(r"^\s*(\S+\.patch)\s*$", pkgbuild, re.M)
    return {"pkgver": variable(pkgbuild, "pkgver"),
            "patches": {name: fetch(ARCH.format(name=name)).decode() for name in names},
            "config": fetch(ARCH.format(name="config.x86_64")).decode()}


def gpg_verify(work: Path, signature: Path, data_cmd: list) -> None:
    home = Path(tempfile.mkdtemp(prefix="gnupg.", dir=work))
    home.chmod(0o700)
    keyring = home / "keys.gpg"
    for key in sorted(KEYS.glob("*.asc")):
        subprocess.run(["gpg", "--homedir", str(home), "--batch", "--quiet", "--no-default-keyring",
                        "--keyring", str(keyring), "--import", str(key)], check=True,
                       stderr=subprocess.DEVNULL)
    producer = subprocess.Popen(data_cmd, stdout=subprocess.PIPE)
    verify = subprocess.run(["gpgv", "--keyring", str(keyring), str(signature), "-"],
                            stdin=producer.stdout, capture_output=True, text=True)
    producer.stdout.close()
    producer.wait()
    if verify.returncode != 0 or producer.returncode != 0:
        raise SystemExit(f"bad signature for {signature.name}: {verify.stderr.strip()}")


def patches_apply(work: Path, tarball: Path, version: str, patches: list) -> None:
    subprocess.run(["tar", "-xf", str(tarball), "-C", str(work)], check=True)
    tree = work / f"linux-{version}"
    for patch in patches:
        run = subprocess.run(["patch", "-Np1", "--dry-run", "-i", str(patch)], cwd=tree,
                             capture_output=True, text=True)
        if run.returncode != 0:
            raise SystemExit(f"{patch.name} does not apply to {version}:\n{run.stdout}{run.stderr}")
    shutil.rmtree(tree)


def sums_block(name: str, values: list) -> str:
    lines = [f"{name}=('{values[0]}'"] + [f"{' ' * (len(name) + 2)}'{v}'" for v in values[1:]]
    return "\n".join(lines) + ")"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--work", default=None)
    args = parser.parse_args()

    text = PKGBUILD.read_text()
    current, zfs_current, pkgrel = variable(text, "pkgver"), variable(text, "_zfsver"), int(variable(text, "pkgrel"))
    lts = longterm()
    zfs_version, zfs_max = zfs_choice()
    if numbers(zfs_version) < numbers(zfs_current):
        zfs_version = zfs_current

    target_series = series(current)
    arch = arch_files()
    newest = max((v for v in lts if series(v) <= zfs_max), key=numbers, default=current)
    if series(newest) > target_series:
        if series(arch["pkgver"]) == series(newest):
            target_series = series(newest)
        else:
            print(f"Linux {'.'.join(map(str, series(newest)))} is LTS, Arch's linux-lts is still at "
                  f"{arch['pkgver']}: staying on {'.'.join(map(str, target_series))}")
    if series(arch["pkgver"]) != target_series:
        arch = None
    in_series = [v for v in lts if series(v) == target_series]
    version = max(in_series, key=numbers) if in_series else current
    if numbers(version) < numbers(current):
        version = current

    ours = {n: (ROOT / n).read_text() for n in re.findall(r"^\s*(\S+\.patch)\s*$", text, re.M)}
    arch_differs = bool(arch) and (arch["patches"] != ours
                                   or arch["config"] != (ROOT / "config.x86_64").read_text())
    if version == current and zfs_version == zfs_current and not arch_differs:
        print(f"up to date: Linux {current}, OpenZFS {zfs_current}")
        return 0
    print(f"Linux {current} -> {version}, OpenZFS {zfs_current} -> {zfs_version}"
          + (f", config and patches of Arch's linux-lts {arch['pkgver']}" if arch_differs else ""))
    if not args.apply:
        return 0

    work = Path(args.work or tempfile.mkdtemp(prefix="follow-lts."))
    work.mkdir(parents=True, exist_ok=True)
    major = version.split(".")[0]
    kernel = download(KERNEL_TAR.format(major=major, version=version, ext="xz"), work / f"linux-{version}.tar.xz")
    sign = download(KERNEL_TAR.format(major=major, version=version, ext="sign"), work / f"linux-{version}.tar.sign")
    gpg_verify(work, sign, ["xz", "-dc", str(kernel)])
    zfs = download(ZFS_TAR.format(version=zfs_version, ext=""), work / f"zfs-{zfs_version}.tar.gz")
    asc = download(ZFS_TAR.format(version=zfs_version, ext=".asc"), work / f"zfs-{zfs_version}.tar.gz.asc")
    gpg_verify(work, asc, ["cat", str(zfs)])

    old_patches = list(ours)
    staged = work / "staged"
    staged.mkdir(exist_ok=True)
    if arch:
        patch_files = []
        for name, body in arch["patches"].items():
            (staged / name).write_text(body)
            patch_files.append(staged / name)
        (staged / "config.x86_64").write_text(arch["config"])
    else:
        patch_files = [ROOT / name for name in old_patches]
    patches_apply(work, kernel, version, patch_files)

    if arch:
        for name in old_patches:
            (ROOT / name).unlink()
        for path in patch_files:
            shutil.copy(path, ROOT / path.name)
        shutil.copy(staged / "config.x86_64", ROOT / "config.x86_64")
        block = "\n".join(f"  {p.name}" for p in patch_files)
        text = re.sub(r"(?m)^(\s*\S+\.patch\s*\n)+", block + "\n", text, count=1)
    names = [p.name for p in patch_files] if arch else old_patches
    sums = [sha256(kernel), "SKIP", sha256(zfs), "SKIP"] + [sha256(ROOT / n) for n in names] \
        + [sha256(ROOT / "config.freedomnas")]
    text = re.sub(r"(?ms)^sha256sums=\(.*?\)", sums_block("sha256sums", sums), text, count=1)
    text = re.sub(r"(?ms)^sha256sums_x86_64=\(.*?\)",
                  sums_block("sha256sums_x86_64", [sha256(ROOT / "config.x86_64")]), text, count=1)
    new_rel = 1 if version != current else pkgrel + 1
    text = re.sub(r"(?m)^pkgver=\S+$", f"pkgver={version}", text)
    text = re.sub(r"(?m)^pkgrel=\S+$", f"pkgrel={new_rel}", text)
    text = re.sub(r"(?m)^_zfsver=\S+$", f"_zfsver={zfs_version}", text)
    PKGBUILD.write_text(text)
    if not args.work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"PKGBUILD now on Linux {version}-{new_rel}, OpenZFS {zfs_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
