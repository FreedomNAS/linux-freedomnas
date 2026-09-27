# linux-freedomnas

The FreedomNAS kernel for the Arch and Artix editions: Arch's `linux-lts`
with the OpenZFS modules built into the same package, the way Proxmox ships
its kernels.

A NAS whose `zfs.ko` is built by DKMS on the machine stops booting the first
time that build fails. Here the kernel, the ZFS modules and the matching
userspace are compiled together from pinned sources, so an update brings all
of them or none.

| Package | Contents |
|---------|----------|
| `linux-freedomnas` | kernel and modules, ZFS in `extra/zfs`; conflicts with `zfs-dkms` |
| `linux-freedomnas-headers` | headers for building out-of-tree modules |
| `zfs-utils-freedomnas` | OpenZFS userspace and dracut module at the exact version in the kernel; provides `zfs-utils` |

The kernel package depends on `zfs-utils-freedomnas` of its own version and
release (split packages of one build share them), so pacman never pairs a
kernel with a different userspace. Init scripts are not in
`zfs-utils-freedomnas`: they come from each init system's package
(`zfs-openrc`, `zfs-dinit`, ...).

## Following upstream

The kernel parts follow `archlinux/packaging/packages/linux-lts` (taken at
6.18.54-1, commit b51edfc8); the docs package is dropped. Following an Arch
update means taking its `pkgver`, patches, `config.x86_64` and checksums.
A new OpenZFS release means `_zfsver` and its checksum; the tarballs are
checked against the release key of Tony Hutter
(`4F3BA9AB6D1F8D683DC2DFB56AD860EED4598027`, in `keys/pgp/`).

## Building and publishing

The build and upload scripts live in
[freedomnas-arch](https://codeberg.org/FreedomNAS/freedomnas-arch), next to
the other Arch packages, and take this checkout as a path:

```sh
../freedomnas-arch/bin/build.sh ../linux-freedomnas           # about 45 minutes
../freedomnas-arch/bin/build.sh ../linux-freedomnas -- -R     # repackage only
```

freedomnas-arch's workflow clones this repository and rebuilds the kernel
only when its version is not in the registry yet.

## License

GPL-2.0-or-later: the GNU General Public License, version 2 or (at your
option) any later version. The text of version 2 is in `LICENSE`. The
packages built from here keep the licenses of the kernel and of OpenZFS.
