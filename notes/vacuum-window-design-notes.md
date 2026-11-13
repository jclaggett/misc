# Vacuum Window Design Notes

**Date:** 2026-11-12
**Context:** Brainstorming session on prototyping a vacuum-insulated window for retrofitting old/legacy construction. Goal: maintainability over ultra-high-vacuum perfection. No exotic materials.

## Design Goals
- Target vacuum: 0.001 torr (point zero zero one torr)
- Gap: 1 mm (key advantage for retrofitting existing sashes too shallow for argon IGUs)
- Frame: wooden (legacy construction compatibility)
- Gas: argon (inert, larger atoms = slower permeation through seals)
- Philosophy: serviceable design — re-evacuate every few years rather than engineer 30-year seals

## Key Physics
- Mean free path scales inversely with pressure. At 1 torr in a 10 mm gap, MFP ≈ 52 µm — molecules still collide hundreds of times crossing the gap; gas conduction barely reduced.
- At 0.001 torr, MFP ≈ 5 cm (5x the 10 mm gap) — molecules cross without colliding. Gas conduction essentially zero.
- For a 1 mm gap, MFP only needs to reach ~1 mm, which corresponds to ~0.05 torr. Ten times easier to pump than 0.005 torr.
- Conductivity does NOT drop linearly with pressure. It stays near continuum value until MFP approaches gap size, then falls steeply (between ~0.1 and 0.001 torr).
- At 0.001 torr, insulation is radiation-dominated. Low-e coating (emissivity ~0.05) is the critical lever.
- Argon at atmospheric pressure has same density as air but ~40% lower thermal conductivity. To match argon conduction with air vacuum you'd only need ~450 torr — but 0.001 torr beats argon entirely on gas conduction.
- Bare glass (emissivity 0.84/surface): U-value ~3.7 W/m²K (worse than single pane). With low-e: ~0.26 W/m²K — matches argon.
- Argon+low-e IGU center-of-glass: U ≈ 0.2–0.25 W/m²K. Vacuum glazing with good low-e: ~0.4–0.7 W/m²K. Comparable at center of pane.
- Vacuum advantages: 1 mm gap vs 12–16 mm (weight, narrow frames), no gas depletion over decades (failure mode is seal letting air in, not gas leaking out), better edge performance (no gap for frame conduction).
- Pumping argon vs air: negligible difference at target pressure. Argon's bigger atoms permeate seals more slowly — helps long-term. Argon is inert (no oxidation of seals/getter).
- Argon availability: 3rd most abundant atmospheric gas (0.9%), fractional distillation of liquid air, welding cylinders ~$20–30 per 100 ft³. One cylinder lasts many prototype cycles.

## Spacer Concepts (all explored, none fully solved)
### Glass pillars (3 mm × 1 mm footprint, 1 mm tall)
- Borosilicate/fused silica conductivity ~1.4 W/m·K.
- 50 mm grid = 400 pillars/m², total solid area 0.12% of pane.
- ~1.7 W/K total → ~34 W for 20 K ΔT. U-value ~1.7 W/m²K. ~8x worse than argon.
- Glass-to-glass bonding: low-temp frit or UV adhesive (outgassing risk), or femtosecond laser welding.

### Femtosecond laser welding
- Focus through top pane at pillar interface; nonlinear absorption only at focus, no heat damage above.
- Raster each contact point; sub-second welds. Proven for microfluidic chips/optical assemblies at small scale.
- Challenge: gap variation shifts focus; pillar heights must be uniform. Window-scale with hundreds of pillars = engineering challenge.
- Zero filler/adhesive = zero outgassing. Major vacuum advantage.

### Stainless mesh (window-screen style)
- 50 µm wire, 5 mm pitch: 400 m of wire/m², 0.08% solid area → ~236 W for 20 K ΔT. Worse than glass pillars.
- 10 µm wire, 10 mm pitch: under 5 W total — competitive with argon, but wire too fine to source/handle.

### Aerogel
- Silica aerogel conductivity ~0.015 W/m·K (better than still air), 99% air by volume.
- Translucent (hazy/frosted), not fully clear.
- Brittle: compressive strength hundreds of kPa to low MPa. 1 atm = 100 kPa. Short squat pillars (1 mm tall, 3:1 aspect ratio) more likely to survive than tall skinny ones.
- Aerogel beads: bead-to-bead contacts create conduction network; crush risk under atmospheric load.
- Manufacturing idea: cast/extrude long aerogel rod in capillary or extrusion die, supercritical dry, slice into 1 mm cylinders with bandsaw. Supercritical drying (CO₂, 31°C, 74 atm) avoids capillary collapse but needs pressure vessel.
- Vacuum/freeze drying (ambient pressure or freeze-dry sublimation): cheaper, no high-pressure infrastructure, but some pore collapse → denser, stiffer, more crush-resistant. Gives up ~30% insulation value for mechanical integrity. For 1 mm load-bearing pillars, right trade-off. Easier to manufacture: just vacuum chamber + freeze dryer from off-the-shelf parts.
- Proposed hybrid: insert UNDRIED aerogel pillars, let vacuum pump-down serve as the drying step (outgassing as friend). Risk: capillary collapse during evaporation. Mitigation: short squat pillars limit collapse to surface skin; denser skin may still insulate adequately. Needs testing.

## Serviceability Architecture
- Wooden frame leaves room for discreet valve routing (behind trim).
- Service valve: brass needle valve with PTFE seat, survives years of cycles. Not a pinch-off port.
- Getter: one-shot by default; heating to regenerate needs hundreds of degrees (bad for wood). Design as replaceable cartridge in separate side chamber.
- Side chamber: machined aluminum/stainless, O-ring face seal, hand-torqueable. Close valve to main gap, vent chamber only, swap cartridge, reseal, pump chamber down, reopen valve. Main window vacuum never sees atmosphere.
- Kit concept: single bayonet/threaded cartridge body carrying valve + getter + pump port. One motion swap.

## Open Questions / Next Steps
- Prove glass can take atmospheric load (~100 kN/m²) without spacers at scale; pillar layout for unsupported span.
- Test vacuum-dried aerogel pillar crush resistance and insulation retention.
- Test femtosecond laser welding at multi-pillar scale with realistic gap tolerance.
- Prototype pump-down with argon; measure pressure decay over weeks to characterize seal + getter performance.
- Low-e coating selection compatible with wooden frame and service temps.

## Reference Numbers
- Sea-level MFP (air): ~68 nm
- 1 atm = 101.325 kPa ≈ 760 torr
- Atmospheric pressure load on 1 m² pane: ~100 kN
- Argon cylinder: ~$20–30 / 100 ft³
- Target: 0.001 torr; 1 mm gap; argon fill; wooden frame; serviceable valve + getter cartridge; aerogel or glass spacers; femtosecond laser welding as bonding option
