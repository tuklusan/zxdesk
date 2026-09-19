# Three-pass optimization report

Author: tuklusan

Source snapshot: `3def6b297fdd93f851a66c20d78ddab5d1703c4b`
Pinned optimizer rule set: upeep80 0.2.0
Files examined per pass: 37 assembly source files under `src/`

## Pass agreement

Each of the three passes reread the source from repository storage. All three passes saw the same source blob identities and produced the same consolidated totals.

| Pass | Candidates |
| --- | ---: |
| 1 | 60 |
| 2 | 60 |
| 3 | 60 |

No source edits were made by this analysis.

## Consolidated totals

| Rule | Count | Review note |
| --- | ---: | --- |
| dead-store-entry | 22 | Heuristic only. Highest false-positive risk, especially indirect stores. |
| relative-jump | 18 | Verify exact assembled byte range before changing JP to JR. |
| zero-a | 10 | Candidate `LD A,0` to `XOR A`; confirm flag requirements. |
| push-load-pop-unused | 8 | Review register and stack liveness around the whole sequence. |
| compare-zero | 1 | Candidate `CP 0` to `OR A`; confirm all flags, not only Z. |
| jump-thread | 1 | Redirect a jump through a jump-only target. |
| **Total** | **60** | |

## Candidates

### dead-store-entry — 22

These are analyzer candidates only. Do not remove an indirect store merely because the textual address is not read later.

- `src/calendar.inc:253` — `ld (CalLeapY),a`
- `src/calendar.inc:445` — `ld (hl),a`
- `src/calendar.inc:545` — `ld (CalRem),a`
- `src/clock.inc:145` — `ld (ClkFrac),a`
- `src/clock.inc:352` — `ld (hl),a`
- `src/commander.inc:244` — `ld (PrintInv),a`
- `src/commander.inc:298` — `ld (PrintInv),a`
- `src/dlgset.inc:142` — `ld (DlgResult),a`
- `src/zxdesk.asm:1472` — `ld (Ps2MaskA+1),a`
- `src/zxdesk.asm:1730` — `ld (PrintInv),a`
- `src/filemgr.inc:324` — `ld (NoteResult),a`
- `src/hittest.inc:58` — `ld (CtlDlg+3),a`
- `src/hittest.inc:71` — `ld (CtlDrop+3),a`
- `src/kbdtest.inc:21` — `ld (de),a`
- `src/note.inc:1094` — `ld (NoteTop),a`
- `src/note.inc:1264` — `ld (NoteResult),a`
- `src/panel.inc:500` — `ld (de),a`
- `src/bench3.asm:1172` — `ld (BStErr),a`
- `src/bench3.asm:1228` — `ld (BTpErr),a`
- `src/resize.inc:183` — `ld (RszWantH),a`
- `src/scroll.inc:91` — `ld (WinBarOn),a`
- `src/storage.inc:166` — `ld (StBackend),a`

### relative-jump — 18

These are size opportunities. The analyzer used conservative source-line distance; the assembler must confirm the true byte displacement.

- `src/desktop.inc:502` — `jp DskGhostAt` -> `jr DskGhostAt`
- `src/zxdesk.asm:639` — `jp PtrRestore` -> `jr PtrRestore`
- `src/zxdesk.asm:648` — `jp PtrDraw` -> `jr PtrDraw`
- `src/zxdesk.asm:1802` — `jp WeFillStrip` -> `jr WeFillStrip`
- `src/zxdesk.asm:1998` — `jp RectGrab` -> `jr RectGrab`
- `src/zxdesk.asm:3622` — `jp SsPut` -> `jr SsPut`
- `src/esxtest.inc:99` — `jp c,EtDir` -> `jr c,EtDir`
- `src/esxtest.inc:148` — `jp EtRound` -> `jr EtRound`
- `src/esxtest.inc:177` — `jp c,EtRtBad` -> `jr c,EtRtBad`
- `src/esxtest.inc:182` — `jp c,EtRtBad` -> `jr c,EtRtBad`
- `src/esxtest.inc:188` — `jp c,EtRtBad` -> `jr c,EtRtBad`
- `src/esxtest.inc:198` — `jp nz,EtRtBad` -> `jr nz,EtRtBad`
- `src/esxtest.inc:205` — `jp c,EtRtBad` -> `jr c,EtRtBad`
- `src/esxtest.inc:209` — `jp nc,EtRtBad` -> `jr nc,EtRtBad`
- `src/esxtest.inc:215` — `jp EtDone` -> `jr EtDone`
- `src/note.inc:96` — `jp NoteRowAddr` -> `jr NoteRowAddr`
- `src/bench3.asm:228` — `jp BMCount` -> `jr BMCount`
- `src/sound.inc:107` — `jp SndReg` -> `jr SndReg`

### zero-a — 10

Candidate rewrite: `LD A,0` -> `XOR A`.

- `src/calendar.inc:66`
- `src/calendar.inc:249`
- `src/commander.inc:240`
- `src/dlgset.inc:138`
- `src/zxdesk.asm:1468`
- `src/filemgr.inc:320`
- `src/hittest.inc:48`
- `src/hittest.inc:67`
- `src/note.inc:1260`
- `src/scroll.inc:87`

### push-load-pop-unused — 8

The pattern is a saved HL, a temporary HL constant load, no detected use of that temporary value, then restoration of HL.

- `src/zxdesk.asm:3626`
- `src/esxtest.inc:131`
- `src/heap.inc:115`
- `src/heap.inc:254`
- `src/heap.inc:328`
- `src/heap.inc:375`
- `src/kbdtest.inc:31`
- `src/tape.inc:167`

### compare-zero — 1

- `src/kbd.inc:74` — `cp 0` -> `or a`

This replacement changes some flags even when the zero result agrees, so review the following flag consumers before changing it.

### jump-thread — 1

- `src/resize.inc:229` — jump through `RszPaint`; the chain resolves to `WndRepaintAll`.

## Suggested order of work

1. Verify the 18 relative-jump candidates with assembled addresses. These are easy size wins when in range.
2. Review the 10 zero-load candidates and the single compare-zero candidate for flag liveness.
3. Review the 8 save/load/restore candidates with register-liveness checks.
4. Treat the 22 dead-store candidates as leads, not edits. Indirect stores such as `(hl)` and `(de)` are especially unsafe to remove from this report alone.
5. Validate every accepted change with the normal build and product test flow.

The three-pass repetition found no pass-to-pass drift. The useful signal is therefore the consolidated set above, while the heuristic categories still need human or test-backed validation before code changes.
