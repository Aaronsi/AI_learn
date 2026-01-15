# Release Checklist

## Pre-Release Checklist

### 1. Code Quality ✅
- [ ] All tests passing
  ```bash
  npm run test
  cd src-tauri && cargo test
  ```
- [ ] No linting errors
  ```bash
  npm run lint
  npm run type-check
  cd src-tauri && cargo clippy -- -D warnings
  ```
- [ ] Code formatted
  ```bash
  cd src-tauri && cargo fmt --check
  ```

### 2. Documentation ✅
- [ ] README.md updated with latest features
- [ ] CHANGELOG.md updated with version changes
- [ ] API documentation up to date
- [ ] User guides reviewed
- [ ] Installation instructions tested

### 3. Version Bump 🔢
- [ ] Update version in `package.json`
- [ ] Update version in `src-tauri/Cargo.toml`
- [ ] Update version in `src-tauri/tauri.conf.json`
- [ ] Create version tag: `git tag v0.1.0`

### 4. Testing 🧪

#### Unit Tests
- [ ] TypeScript tests pass (100% coverage target)
- [ ] Rust tests pass (70%+ coverage target)

#### Integration Tests
- [ ] Audio capture works
- [ ] Transcription service connects
- [ ] Text injection functions
- [ ] Hot keys respond
- [ ] System tray menu works

#### Platform Testing

**macOS**
- [ ] Build succeeds on macOS 13+
- [ ] DMG installer works
- [ ] App launches successfully
- [ ] Permissions requested properly (Microphone, Accessibility)
- [ ] Global hotkey works in Safari
- [ ] Global hotkey works in Chrome
- [ ] Global hotkey works in VS Code
- [ ] Text injection works in all apps
- [ ] System tray icon displays correctly
- [ ] Chinese menu displays correctly

**Windows**
- [ ] Build succeeds on Windows 11
- [ ] MSI installer works
- [ ] App launches successfully
- [ ] Global hotkey works in Edge
- [ ] Global hotkey works in Chrome
- [ ] Global hotkey works in VS Code
- [ ] Text injection works with UI Automation
- [ ] Text injection works with clipboard fallback
- [ ] System tray icon displays correctly

**Linux**
- [ ] Build succeeds on Ubuntu 22.04
- [ ] DEB package installs correctly
- [ ] AppImage runs correctly
- [ ] Global hotkey works in Firefox
- [ ] Global hotkey works in VS Code
- [ ] Clipboard fallback works (X11)
- [ ] Clipboard fallback works (Wayland)
- [ ] System tray icon displays correctly

### 5. Performance Validation 📊
- [ ] Memory usage < 150MB
- [ ] CPU usage < 5% when idle
- [ ] Audio latency < 150ms
- [ ] Transcription latency < 200ms
- [ ] Startup time < 2s
- [ ] No memory leaks (10 minute test)

### 6. Security Review 🔒
- [ ] No hardcoded API keys
- [ ] API keys stored securely
- [ ] No unsafe Rust code
- [ ] Dependencies audited
  ```bash
  npm audit
  cargo audit
  ```
- [ ] Privacy policy reviewed

## Build Process

### 1. Clean Build
```bash
# Clean previous builds
npm run clean
rm -rf src-tauri/target/release

# Fresh install
rm -rf node_modules
npm install
```

### 2. Run Tests
```bash
# All tests must pass
npm run test
cd src-tauri && cargo test
```

### 3. Build for Each Platform

#### macOS (x86_64 + ARM64)
```bash
npm run tauri:build -- --target universal-apple-darwin
```
Outputs:
- `src-tauri/target/universal-apple-darwin/release/bundle/dmg/RAFlow_0.1.0_universal.dmg`

#### Windows (x86_64)
```bash
npm run tauri:build -- --target x86_64-pc-windows-msvc
```
Outputs:
- `src-tauri/target/x86_64-pc-windows-msvc/release/bundle/msi/RAFlow_0.1.0_x64.msi`

#### Linux (x86_64)
```bash
npm run tauri:build -- --target x86_64-unknown-linux-gnu
```
Outputs:
- `src-tauri/target/x86_64-unknown-linux-gnu/release/bundle/deb/raflow_0.1.0_amd64.deb`
- `src-tauri/target/x86_64-unknown-linux-gnu/release/bundle/appimage/raflow_0.1.0_amd64.AppImage`

### 4. Code Signing (Optional but Recommended)

#### macOS
```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" \
  "src-tauri/target/universal-apple-darwin/release/bundle/dmg/RAFlow.app"

# Notarize (required for macOS 10.15+)
xcrun notarytool submit RAFlow_0.1.0_universal.dmg \
  --apple-id your@email.com \
  --password xxxx-xxxx-xxxx-xxxx \
  --team-id XXXXXXXXXX \
  --wait
```

#### Windows
```bash
# Sign with signtool
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com \
  RAFlow_0.1.0_x64.msi
```

## Release Process

### 1. Create GitHub Release
- [ ] Go to GitHub repository
- [ ] Click "Create a new release"
- [ ] Tag: `v0.1.0`
- [ ] Title: `RAFlow v0.1.0 - Initial Release`
- [ ] Description: Copy from CHANGELOG.md

### 2. Upload Artifacts
Upload the following files:
- [ ] `RAFlow_0.1.0_universal.dmg` (macOS)
- [ ] `RAFlow_0.1.0_x64.msi` (Windows)
- [ ] `raflow_0.1.0_amd64.deb` (Linux DEB)
- [ ] `raflow_0.1.0_amd64.AppImage` (Linux AppImage)
- [ ] `checksums.txt` (SHA256 hashes)

### 3. Generate Checksums
```bash
# Create checksums file
cd dist
sha256sum * > checksums.txt
```

### 4. Release Notes Template
```markdown
# RAFlow v0.1.0 - Initial Release

## 🎉 First Public Release

RAFlow is a real-time speech-to-text tool that runs at system level, powered by ElevenLabs Scribe v2 API.

## ✨ Features

- 🎤 Real-time transcription with 150ms latency
- ⌨️ Global hotkeys for hands-free operation
- 🎯 Smart text injection with focus detection
- 📋 Clipboard fallback when direct injection fails
- 🌐 Support for 90+ languages
- 🔧 Technical term correction (90+ terms)
- 🔄 Self-correction detection
- 💻 Cross-platform (macOS, Windows, Linux)
- 🪶 Lightweight (< 150MB memory, < 5% CPU)
- 🔒 Privacy-first (direct connection to ElevenLabs)

## 📦 Download

- **macOS** (Universal): [RAFlow_0.1.0_universal.dmg](link)
- **Windows** (x64): [RAFlow_0.1.0_x64.msi](link)
- **Linux** (DEB): [raflow_0.1.0_amd64.deb](link)
- **Linux** (AppImage): [raflow_0.1.0_amd64.AppImage](link)

## 🔐 Verification

Verify downloads with SHA256 checksums:
[checksums.txt](link)

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [User Guide](docs/user-guide.md)
- [FAQ](docs/faq.md)

## 🐛 Known Issues

- None reported yet

## 🙏 Acknowledgments

Thanks to all contributors and testers!

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.
```

### 5. Publish Release
- [ ] Set as "Latest release"
- [ ] Click "Publish release"

## Post-Release

### 1. Announcements 📢
- [ ] Tweet announcement
- [ ] Post on Reddit (r/programming, r/rust, etc.)
- [ ] Post on Hacker News
- [ ] Update project website
- [ ] Email newsletter subscribers

### 2. Package Managers

#### Homebrew (macOS)
- [ ] Create Homebrew formula
- [ ] Submit PR to homebrew-cask
```ruby
cask "raflow" do
  version "0.1.0"
  sha256 "..."

  url "https://github.com/yourusername/raflow/releases/download/v#{version}/RAFlow_#{version}_universal.dmg"
  name "RAFlow"
  desc "Real-time speech-to-text tool"
  homepage "https://raflow.app/"

  app "RAFlow.app"
end
```

#### Winget (Windows)
- [ ] Create winget manifest
- [ ] Submit PR to winget-pkgs

#### AUR (Arch Linux)
- [ ] Create PKGBUILD
- [ ] Submit to AUR

### 3. Monitor 📊
- [ ] Watch for issues on GitHub
- [ ] Monitor download statistics
- [ ] Check crash reports (if telemetry enabled)
- [ ] Respond to user feedback

### 4. Update Documentation Site
- [ ] Update homepage with download links
- [ ] Add to changelog page
- [ ] Update version numbers

## Rollback Plan 🔄

If critical issues are found:

1. **Immediate**:
   - Mark release as "Pre-release"
   - Add warning to release notes
   - Pin issue to repository

2. **Fix**:
   - Create hotfix branch
   - Fix critical issues
   - Test thoroughly
   - Release patch version (v0.1.1)

3. **Communicate**:
   - Update release notes
   - Notify users via channels
   - Post status updates

## Version Numbers

Follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Examples:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New feature
- `1.0.0` - First stable release

## Automation (Future)

Consider automating:
- [ ] CI/CD pipeline for builds
- [ ] Automatic changelog generation
- [ ] Automatic version bumping
- [ ] Automatic release creation
- [ ] Automatic artifact uploads

## Resources

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [GitHub Releases Guide](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
