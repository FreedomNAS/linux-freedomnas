pkgbase=linux-freedomnas
pkgver=6.18.54
pkgrel=1
_zfsver=2.4.4
pkgdesc='FreedomNAS LTS Linux with OpenZFS'
url='https://codeberg.org/FreedomNAS'
arch=(
  x86_64
)
makedepends=(
  bc
  binutils
  cpio
  gettext
  glibc
  libelf
  libgcc
  openssl
  pahole
  perl
  python
  rust
  rust-bindgen
  rust-src
  tar
  xxhash
  xz
  zlib
  zstd

  libaio
  libtirpc
  pam
  util-linux-libs
)
options=(
  !debug
  !strip
)
_srcname=linux-$pkgver
_zfssrc=zfs-$_zfsver
source=(
  https://cdn.kernel.org/pub/linux/kernel/v${pkgver%%.*}.x/${_srcname}.tar.{xz,sign}
  https://github.com/openzfs/zfs/releases/download/zfs-$_zfsver/$_zfssrc.tar.gz{,.asc}
  0001-add-sysctl-to-allow-disabling-unprivileged-CLONE_NEW.patch
  0002-drm-amdgpu-avoid-memory-allocation-in-the-critical-c.patch
  0003-drm-amdgpu-use-GFP_ATOMIC-instead-of-NOWAIT-in-the-c.patch
)
source_x86_64=(config.x86_64)
validpgpkeys=(
  ABAF11C65A2970B130ABE3C479BE3E4300411886
  647F28654894E3BD457199BE38DBBDC86092693E
  4F3BA9AB6D1F8D683DC2DFB56AD860EED4598027
)
sha256sums=('9df30b02dd8102bbd0be52556288ef6889ddbe7f1ddb96fbf847d0becf3eacac'
            'SKIP'
            '2a3c70d55a37cc71618a95a60e81ad66530201eb118d37741dc92efcf848c8b1'
            'SKIP'
            '0bb3b4cda53db35c10e0a34defb5f52f3c91895d7b4a9f93b3f40f5401a71e02'
            '70d54dfde13e52ea1109c4222a987a29ada68feec35dca9ce4afd6f7977e8740'
            '44caa7c6a79055539f16ab118bece58934cdf93557643a50017634366c864b91')
sha256sums_x86_64=('aef082c1ee2484304a180fc6e8b320f7c93b27843a5deb74e1a92fe32d1dd86c')

export KBUILD_BUILD_HOST=freedomnas
export KBUILD_BUILD_USER=$pkgbase
export KBUILD_BUILD_TIMESTAMP="$(date -Ru${SOURCE_DATE_EPOCH:+d @$SOURCE_DATE_EPOCH})"

prepare() {
  cd $_srcname

  echo "Setting version..."
  echo "-$pkgrel" > localversion.10-pkgrel
  echo "${pkgbase#linux}" > localversion.20-pkgname

  local src
  for src in "${source[@]}"; do
    src="${src%%::*}"
    src="${src##*/}"
    src="${src%.zst}"
    [[ $src = *.patch ]] || continue
    echo "Applying patch $src..."
    patch -Np1 < "../$src"
  done

  echo "Setting config..."
  cp ../config.$CARCH .config
  make olddefconfig
  diff -u ../config.$CARCH .config || :

  make -s kernelrelease > version
  echo "Prepared $pkgbase version $(<version)"
}

build() {
  cd $_srcname
  make all
  make -C tools/bpf/bpftool vmlinux.h feature-clang-bpf-co-re=1

  cd "$srcdir/$_zfssrc"
  ./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --sbindir=/usr/bin \
    --libdir=/usr/lib \
    --libexecdir=/usr/lib \
    --datadir=/usr/share \
    --includedir=/usr/include \
    --with-udevdir=/usr/lib/udev \
    --with-mounthelperdir=/usr/bin \
    --with-dracutdir=/usr/lib/dracut \
    --with-config=all \
    --with-linux="$srcdir/$_srcname" \
    --with-linux-obj="$srcdir/$_srcname"
  make
}

_package() {
  pkgdesc="The $pkgdesc kernel and modules, ZFS included"
  license=(
    'Apache-2.0 OR MIT'
    'BSD-2-Clause OR GPL-2.0-or-later'
    BSD-3-Clause
    'BSD-3-Clause OR GPL-2.0-only'
    'BSD-3-Clause OR GPL-2.0-or-later'
    BSD-3-Clause-Clear
    CDDL-1.0
    GPL-1.0-or-later
    'GPL-1.0-or-later OR BSD-3-Clause'
    GPL-2.0-only
    'GPL-2.0-only OR Apache-2.0'
    'GPL-2.0-only OR BSD-2-Clause'
    'GPL-2.0-only OR BSD-3-Clause'
    'GPL-2.0-only OR CDDL-1.0'
    'GPL-2.0-only OR Linux-OpenIB'
    'GPL-2.0-only OR MIT'
    'GPL-2.0-only OR MPL-1.1'
    'GPL-2.0-only OR X11'
    'GPL-2.0-only WITH Linux-syscall-note'
    GPL-2.0-or-later
    'GPL-2.0-or-later OR BSD-2-Clause'
    'GPL-2.0-or-later OR BSD-3-Clause'
    'GPL-2.0-or-later OR MIT'
    'GPL-2.0-or-later OR X11'
    'GPL-2.0-or-later WITH GCC-exception-2.0'
    ISC
    LGPL-2.0-or-later
    'LGPL-2.1-only'
    'LGPL-2.1-only OR BSD-2-Clause'
    LGPL-2.1-or-later
    MIT
    MPL-1.1
    X11
    Zlib
  )
  depends=(
    coreutils
    initramfs
    kmod
    "zfs-utils-freedomnas=$pkgver-$pkgrel"
  )
  optdepends=(
    "$pkgbase-headers: headers and scripts for building modules"
    'linux-firmware: firmware images needed for some devices'
    'wireless-regdb: to set the correct wireless channels of your country'
  )
  provides=(
    KSMBD-MODULE
    NTSYNC-MODULE
    VIRTUALBOX-GUEST-MODULES
    WIREGUARD-MODULE
    "ZFS-MODULE=$_zfsver"
    "SPL-MODULE=$_zfsver"
  )
  conflicts=(
    zfs-dkms
    zfs-dkms-git
  )

  cd $_srcname
  local kernver="$(<version)"
  local modulesdir="$pkgdir/usr/lib/modules/$kernver"

  echo "Installing boot image..."
  install -Dm644 "$(make -s image_name)" "$modulesdir/vmlinuz"
  echo "$pkgbase" | install -Dm644 /dev/stdin "$modulesdir/pkgbase"

  echo "Installing modules..."
  ZSTD_CLEVEL=19 make INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 \
    DEPMOD=/doesnt/exist modules_install

  echo "Installing ZFS modules..."
  make -C "$srcdir/$_zfssrc/module" \
    KERNELRELEASE="$kernver" \
    INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_DIR=extra/zfs INSTALL_MOD_STRIP=1 \
    DEPMOD=/doesnt/exist \
    modules_install
  find "$modulesdir/extra" -name '*.ko' -exec zstd -q -19 --rm {} +

  rm -f "$modulesdir"/build

  install -vDm 644 LICENSES/deprecated/{GPL-1.0,ISC,Linux-OpenIB,X11,Zlib} -t "$pkgdir/usr/share/licenses/$pkgname/"
  install -vDm 644 LICENSES/preferred/{BSD,MIT}* -t "$pkgdir/usr/share/licenses/$pkgname/"
  install -vDm 644 LICENSES/exceptions/* -t "$pkgdir/usr/share/licenses/$pkgname/"
  install -vDm 644 "$srcdir/$_zfssrc/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/OpenZFS-CDDL-1.0"
}

_package-headers() {
  pkgdesc="Headers and scripts for building modules for the $pkgdesc kernel"
  license=(
    BSD-3-Clause
    'BSD-3-Clause OR GPL-2.0-only'
    GPL-1.0-or-later
    'GPL-1.0-or-later WITH Linux-syscall-note'
    GPL-2.0-only
    'GPL-2.0-only OR Apache-2.0'
    'GPL-2.0-only OR BSD-2-Clause'
    'GPL-2.0-only OR BSD-3-Clause'
    'GPL-2.0-only OR CDDL-1.0'
    'GPL-2.0-only OR Linux-OpenIB'
    'GPL-2.0-only OR Linux-OpenIB OR BSD-2-Clause'
    'GPL-2.0-only OR MIT'
    'GPL-2.0-only OR MPL-1.1'
    'GPL-2.0-only OR X11'
    'GPL-2.0-only WITH Linux-syscall-note'
    '(GPL-2.0-only WITH Linux-syscall-note) AND MIT'
    '(GPL-2.0-only WITH Linux-syscall-note) OR BSD-2-Clause'
    '(GPL-2.0-only WITH Linux-syscall-note) OR BSD-3-Clause'
    '(GPL-2.0-only WITH Linux-syscall-note) OR CDDL-1.0'
    '(GPL-2.0-only WITH Linux-syscall-note) OR Linux-OpenIB'
    '(GPL-2.0-only WITH Linux-syscall-note) OR MIT'
    GPL-2.0-or-later
    'GPL-2.0-or-later OR BSD-2-Clause'
    'GPL-2.0-or-later OR BSD-3-Clause'
    'GPL-2.0-or-later OR MIT'
    'GPL-2.0-or-later WITH Linux-syscall-note'
    '(GPL-2.0-or-later WITH Linux-syscall-note) OR BSD-3-Clause'
    '(GPL-2.0-or-later WITH Linux-syscall-note) OR MIT'
    'LGPL-2.0-or-later OR BSD-2-Clause'
    'LGPL-2.0-or-later WITH Linux-syscall-note'
    ISC
    'LGPL-2.0-or-later WITH Linux-syscall-note'
    'LGPL-2.0-or-later OR BSD-2-Clause'
    LGPL-2.1-only
    'LGPL-2.1-only OR BSD-2-Clause'
    'LGPL-2.1-only OR MIT'
    'LGPL-2.1-only WITH Linux-syscall-note'
    LGPL-2.1-or-later
    'LGPL-2.1-or-later OR BSD-2-Clause'
    'LGPL-2.1-or-later WITH Linux-syscall-note'
    MIT
    Zlib
  )
  depends=(
    binutils
    glibc
    libelf
    libgcc
    openssl
    pahole
    xxhash
    zlib
    zstd
  )
  provides=(LINUX-HEADERS)

  cd $_srcname
  local builddir="$pkgdir/usr/lib/modules/$(<version)/build"

  local karch
  case $CARCH in
    x86_64) karch=x86 ;;
    *) echo "Unknown CARCH $CARCH"; exit 1 ;;
  esac

  echo "Installing build files..."
  install -Dt "$builddir" -m644 .config Makefile Module.symvers System.map \
    localversion.* version vmlinux tools/bpf/bpftool/vmlinux.h
  install -Dt "$builddir/kernel" -m644 kernel/Makefile
  install -Dt "$builddir/arch/$karch" -m644 arch/$karch/Makefile
  cp -t "$builddir" -a scripts
  ln -srt "$builddir" "$builddir/scripts/gdb/vmlinux-gdb.py"

  if [[ $(scripts/config -s CONFIG_HAVE_STACK_VALIDATION) = y ]]; then
    install -Dt "$builddir/tools/objtool" tools/objtool/objtool
  fi

  if [[ $(scripts/config -s CONFIG_DEBUG_INFO_BTF_MODULES) = y ]]; then
    install -Dt "$builddir/tools/bpf/resolve_btfids" tools/bpf/resolve_btfids/resolve_btfids
  fi

  echo "Installing headers..."
  cp -t "$builddir" -a include
  cp -t "$builddir/arch/$karch" -a arch/$karch/include
  install -Dt "$builddir/arch/$karch/kernel" -m644 arch/$karch/kernel/asm-offsets.s

  install -Dt "$builddir/drivers/md" -m644 drivers/md/*.h
  install -Dt "$builddir/net/mac80211" -m644 net/mac80211/*.h
  install -Dt "$builddir/drivers/media/i2c" -m644 drivers/media/i2c/msp3400-driver.h
  install -Dt "$builddir/drivers/media/usb/dvb-usb" -m644 drivers/media/usb/dvb-usb/*.h
  install -Dt "$builddir/drivers/media/dvb-frontends" -m644 drivers/media/dvb-frontends/*.h
  install -Dt "$builddir/drivers/media/tuners" -m644 drivers/media/tuners/*.h
  install -Dt "$builddir/drivers/iio/common/hid-sensors" -m644 drivers/iio/common/hid-sensors/*.h

  echo "Installing KConfig files..."
  find . -name 'Kconfig*' -exec install -Dm644 {} "$builddir/{}" \;

  if [[ $(scripts/config -s CONFIG_RUST) = y ]]; then
    echo "Installing Rust files..."
    install -Dt "$builddir/rust" -m644 rust/*.rmeta
    install -Dt "$builddir/rust" rust/*.so
  fi

  echo "Installing unstripped VDSO..."
  make INSTALL_MOD_PATH="$pkgdir/usr" vdso_install \
    link=

  echo "Removing unneeded architectures..."
  local arch
  for arch in "$builddir"/arch/*/; do
    [[ $arch = */$karch/ ]] && continue
    echo "Removing $(basename "$arch")"
    rm -r "$arch"
  done

  echo "Removing documentation..."
  rm -r "$builddir/Documentation"

  echo "Removing broken symlinks..."
  find -L "$builddir" -type l -printf 'Removing %P\n' -delete

  echo "Removing loose objects..."
  find "$builddir" -type f -name '*.o' -printf 'Removing %P\n' -delete

  echo "Stripping build tools..."
  local file
  while read -rd '' file; do
    case "$(file -Sib "$file")" in
      application/x-sharedlib\;*)      strip -v $STRIP_SHARED "$file" ;;
      application/x-archive\;*)        strip -v $STRIP_STATIC "$file" ;;
      application/x-executable\;*)     strip -v $STRIP_BINARIES "$file" ;;
      application/x-pie-executable\;*) strip -v $STRIP_SHARED "$file" ;;
    esac
  done < <(find "$builddir" -type f -perm -u+x ! -name vmlinux -print0)

  echo "Stripping vmlinux..."
  strip -v $STRIP_STATIC "$builddir/vmlinux"

  echo "Adding symlink..."
  mkdir -p "$pkgdir/usr/src"
  ln -sr "$builddir" "$pkgdir/usr/src/$pkgbase"

  install -vDm 644 LICENSES/deprecated/{ISC,Linux-OpenIB,X11,Zlib} -t "$pkgdir/usr/share/licenses/$pkgname/"
  install -vDm 644 LICENSES/preferred/{BSD*,MIT} -t "$pkgdir/usr/share/licenses/$pkgname/"
  install -vDm 644 LICENSES/exceptions/* -t "$pkgdir/usr/share/licenses/$pkgname/"
}

package_zfs-utils-freedomnas() {
  pkgdesc="OpenZFS userspace utilities, the exact version built into $pkgbase"
  license=(CDDL-1.0)
  depends=(
    glibc
    libaio
    libtirpc
    openssl
    pam
    util-linux-libs
    zlib
  )
  optdepends=(
    'python: arcstat, arc_summary and dbufstat'
    'dracut: the zfs dracut module for a ZFS root'
  )
  provides=("zfs-utils=$_zfsver")
  conflicts=(zfs-utils zfs-utils-git)
  backup=(etc/default/zfs etc/zfs/zed.d/zed.rc)

  cd "$srcdir/$_zfssrc"
  make DESTDIR="$pkgdir" install

  rm -rf "${pkgdir:?}/lib" "${pkgdir:?}/usr/lib/modules" "${pkgdir:?}/usr/src"
  rm -rf "${pkgdir:?}/etc/init.d" "${pkgdir:?}/etc/conf.d" \
    "${pkgdir:?}/usr/share/initramfs-tools" "${pkgdir:?}/usr/lib/initcpio"
  rm -rf "${pkgdir:?}/usr/share/zfs/zfs-tests" "${pkgdir:?}/usr/share/zfs/runfiles" \
    "${pkgdir:?}/usr/share/zfs/test-runner" "${pkgdir:?}/usr/bin/raidz_test"

  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}

pkgname=(
  "$pkgbase"
  "$pkgbase-headers"
  zfs-utils-freedomnas
)
for _p in "$pkgbase" "$pkgbase-headers"; do
  eval "package_$_p() {
    $(declare -f "_package${_p#$pkgbase}")
    _package${_p#$pkgbase}
  }"
done

