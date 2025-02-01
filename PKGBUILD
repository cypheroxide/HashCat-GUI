# Maintainer: cypheroxide <cypheroxide.cyberservices@protonmail.com>
pkgname=hashcat-gui
pkgver=0.1.0
pkgrel=1
pkgdesc="A modern GUI interface for HashCat password cracker"
arch=('x86_64')
url="https://github.com/cypheroxide/hashbreaker"
license=('GPL3')
depends=(
'python'
'python-flask'
'python-werkzeug'
'python-psutil'
'python-pyqt5'
'python-pydantic'
'python-yaml'
'python-typing-extensions'
'hashcat'
)
makedepends=(
'python-pip'
'python-setuptools'
'python-wheel'
)
backup=('etc/hashcat-gui/config.yaml')
source=("$pkgname-$pkgver.tar.gz"
        "$pkgname.desktop"
        "$pkgname.service")
sha256sums=('SKIP'
        'SKIP'
        'SKIP')

prepare() {
cd "$pkgname-$pkgver"
python -m venv --system-site-packages "$srcdir/venv"
source "$srcdir/venv/bin/activate"
pip install -r requirements.txt
}

build() {
cd "$pkgname-$pkgver"
source "$srcdir/venv/bin/activate"
python setup.py build
}

package() {
cd "$pkgname-$pkgver"
source "$srcdir/venv/bin/activate"
python setup.py install --root="$pkgdir" --optimize=1 --skip-build

# Install application files
install -Dm755 src/main.py "$pkgdir/usr/bin/hashcat-gui"
install -Dm644 config.yaml "$pkgdir/etc/hashcat-gui/config.yaml"
install -Dm644 data/hash_types.txt "$pkgdir/usr/share/hashcat-gui/data/hash_types.txt"

# Install systemd service
install -Dm644 "$srcdir/$pkgname.service" "$pkgdir/usr/lib/systemd/user/hashcat-gui.service"

# Install desktop entry and icon
install -Dm644 "$srcdir/$pkgname.desktop" "$pkgdir/usr/share/applications/hashcat-gui.desktop"
install -Dm644 src/gui/images/icon.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/hashcat-gui.png"

# Create cache and log directories
install -dm755 "$pkgdir/var/cache/hashcat-gui"
install -dm755 "$pkgdir/var/log/hashcat-gui"

# Install documentation
install -Dm644 README.md "$pkgdir/usr/share/doc/hashcat-gui/README.md"
install -Dm644 CONTRIBUTING.md "$pkgdir/usr/share/doc/hashcat-gui/CONTRIBUTING.md"
install -Dm644 LICENSE "$pkgdir/usr/share/licenses/hashcat-gui/LICENSE"

# Set proper permissions
chmod 750 "$pkgdir/etc/hashcat-gui"
chmod 640 "$pkgdir/etc/hashcat-gui/config.yaml"
chmod 755 "$pkgdir/usr/bin/hashcat-gui"
}

