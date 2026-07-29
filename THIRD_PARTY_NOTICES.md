# Third-party notices

## remote-bridge-hub

- Project: `xxb26553663-star/remote-bridge-hub`
- Source: <https://github.com/xxb26553663-star/remote-bridge-hub>
- Reference revision: `8a93f321ac71a602300c6cd77f7256fa4b63068e`
- License: GNU General Public License v3.0 only (`GPL-3.0-only`)

The Xiaomi RC003 ATVV UUIDs, microphone command behavior, IMA/DVI ADPCM decoding
order, capability parsing, and HID usage mapping are protocol references for this
Windows client. The client does not include upstream customer data or commercial
branding.

## open-voice-bridge Windows implementation

- Project: `nijez/open-voice-bridge`
- Source: <https://github.com/nijez/open-voice-bridge>
- License: GNU General Public License v3.0 only (`GPL-3.0-only`)

The Windows RC003 implementation in `apps/windows/rc003` is adapted from the
upstream Windows client. Attribution and the changes made in this repository
are summarized in `apps/windows/rc003/ATTRIBUTION.md`.

## RC003 product photo

The RC003 product photo bundled as `RC003-remote-photo.png` was supplied by the user on 2026-07-17 for the physical-button mapping interface. It is preserved at its original 508 x 1030 aspect ratio. Copyright and trademark rights in the photo and depicted products remain with their respective owners; the GPL-3.0-only license for the program does not grant additional rights to this image or the Xiaomi marks.

## VB-CABLE

- Project: `VB-Audio VB-CABLE`
- Source: <https://vb-audio.com/Cable/>
- Package used by the optional Windows helper: `VBCABLE_Driver_Pack45.zip`
- License: VB-Audio Donationware / the vendor's own terms; it is not GPL code

The Windows client does not modify, re-license, silently install, or select
VB-CABLE as the Windows default device. Audio is written only to the endpoint explicitly selected by the user; the client never changes the Windows system default input/output device. The optional bundle contains only the free Basic package, not the paid A+B/C+D products. The build helper
`apps/windows/rc003/build/fetch-vb-cable.ps1` downloads and hash-verifies the
official package only as an explicit build step. At runtime, installation is
available only after an explicit user click and a real Windows UAC prompt; the
Remote Mic process never runs with administrator privileges and never reports a driver install as successful merely because a process was launched.
