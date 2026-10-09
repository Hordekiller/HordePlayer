Name:           hordeplayer
Version:        %{_hversion}
Release:        1%{?dist}
Summary:        Professional local video player powered by ffmpeg
License:        GPL-3.0-or-later
URL:            https://github.com/Hordekiller/HordePlayer
Source0:        %{name}-%{_hversion}.tar.gz
BuildArch:      noarch
AutoReqProv:    no
Requires:       python3
Recommends:     ffmpeg

%description
HordePlayer plays any video link or local file in a clean, modern web UI.
A small local ffmpeg server remuxes/transcodes MKV and AC3/E-AC3 audio
(common in Farsi-dubbed files) that browsers cannot decode, with optional
audio amplification and EBU R128 normalization.

%prep
%setup -q

%build
# nothing to compile (pure Python + HTML)

%install
rm -rf %{buildroot}
install -d %{buildroot}%{_datadir}/hordeplayer
cp -r app/. %{buildroot}%{_datadir}/hordeplayer/
find %{buildroot}%{_datadir}/hordeplayer -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || :
install -d %{buildroot}%{_bindir}
install -m0755 packaging/hordeplayer %{buildroot}%{_bindir}/hordeplayer
install -d %{buildroot}%{_datadir}/applications
install -m0644 packaging/hordeplayer.desktop %{buildroot}%{_datadir}/applications/hordeplayer.desktop
install -d %{buildroot}%{_datadir}/metainfo
install -m0644 packaging/hordeplayer.appdata.xml %{buildroot}%{_datadir}/metainfo/hordeplayer.appdata.xml
install -d %{buildroot}%{_datadir}/icons/hicolor/128x128/apps \
           %{buildroot}%{_datadir}/icons/hicolor/256x256/apps \
           %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
install -m0644 assets/hordeplayer-128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/hordeplayer.png
install -m0644 assets/hordeplayer-256.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/hordeplayer.png
install -m0644 assets/hordeplayer.png     %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/hordeplayer.png

%files
%license LICENSE
%doc README.md
%{_bindir}/hordeplayer
%{_datadir}/hordeplayer
%{_datadir}/applications/hordeplayer.desktop
%{_datadir}/metainfo/hordeplayer.appdata.xml
%{_datadir}/icons/hicolor/128x128/apps/hordeplayer.png
%{_datadir}/icons/hicolor/256x256/apps/hordeplayer.png
%{_datadir}/icons/hicolor/512x512/apps/hordeplayer.png

%changelog
* Fri Oct 09 2026 Hordekiller <Hordekiller@users.noreply.github.com> - 1.0.0-1
- Initial release
