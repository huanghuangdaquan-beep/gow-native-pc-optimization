@echo off
rem Dev launcher for the Japanese disc (SCAJ_973.99).
rem Settings measured on an i3-4170 with its Intel HD 4400; see
rem docs/research/gpu-performance-2026-10-30.md.
rem
rem Resolution: two independent knobs. The internal one is what costs GPU time.
rem   GOW_RENDER_HEIGHT=360   internal picture height in lines (448 = PS2 native, 360 = 0.80x, 240 = 0.54x,
rem                           720 = supersampled). This is the knob to turn down when the game stutters.
rem   GOW_WINDOW=1280x720     window (presentation) size. Leaving it unset makes the window the same height as
rem                           GOW_RENDER_HEIGHT in 16:9 (360 -> 640x360), which is a third of the frame rate on an
rem                           Intel HD 4400: presenting a 412x360 frame into 1280x720 costs host 20.6 Hz vs 32.7 Hz.
rem Or let the runtime pick: PS2X_GS_HW_SCALE=auto, then GOW_FPS_TARGET=60 and GOW_MIN_SCALE=0.5 bound it.
rem
rem GOW_VU1N_X64=1 is the in-process x86-64 VU1 JIT: vu time 2.3 s -> 0.16 s per 5 s, which is what leaves the
rem CPU free at a higher internal resolution.
rem GOW_POKE_SEMA=6 used to be needed to leave the boot screen: SifBindRpc left cd->hdr.sema_id at -1, so the
rem memory-card RPC never signalled a completion semaphore and the game waited forever. The semaphore is created at
rem bind time now, so the boot screen is left on its own; set GOW_POKE_SEMA=6 again only to compare against the old
rem behaviour (it fakes the handshake, and the game then runs with the memory card never answered).
setlocal

rem ---- quality ----
rem First argument = internal height in lines: "play-jpn.cmd 360" (or 240 / 448 / 720).
rem On the HD 4400 in the intro: 240 -> 59 fps, 360 -> 33 fps, 448 -> 32 fps (window follows the height).
set GOW_RENDER_HEIGHT=240
if not "%~1"=="" set GOW_RENDER_HEIGHT=%~1

set PS2X_GS_HW=1
set PS2X_GS_WORKER=1
set GOW_SCALER=bilinear
set GOW_VU1N_X64=1
rem set GOW_POKE_SEMA=6
rem GOW_OSD=1 draws "<rate> Hz  <w>x<h>" in the corner: if it is stuck on a still picture, this tells you whether
rem the window is presenting at all.
set GOW_OSD=1
rem set GOW_PERF_DIAG=1 to print the per-window time split on stderr
rem PS2X_GS_HW_SCALE=auto overrides the fixed height and adapts once per second

rem A previous run whose launcher was closed keeps running (closing the console does not end the game) and the next
rem one then fights it for the window and the GPU: end it first.
taskkill /F /IM ps2EntryRunner.exe >nul 2>&1

set RUNNER=C:\gbp-clang\ps2xRuntime\ps2EntryRunner.exe
if not exist "%RUNNER%" (
  echo Build it first: build.cmd -Stages build
  exit /b 1
)
"%RUNNER%" "%~dp0data\gow1\discs\jpn\SCAJ_973.99"
