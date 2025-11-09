## Hull Torque and Sail Trim Notes

Work-in-progress summary so we can pick up the physics tuning on another machine.

### Recent Fixes
- Normalise apparent-wind direction and keep the mainsail on the leeward side inside `Manager.step()`. This prevents the “sail on wrong tack” reversal when the apparent flow crosses the bow.
- Increased `MAX_SAIL_DEG` to `70°` in the manual keyboard demo to reflect the DragonForce 65 sheet limits. The wrapper now just passes the magnitude; the physics engine chooses the sign.

### Outstanding Physics Issues
1. **Hull yaw torque**  
   - Current model only damps yaw with a simple force term derived from the hull area. Once the boat develops significant leeway, the rudder force alone overwhelms this damping, generating angular accelerations that immediately saturate at the ±720 deg/s² safety clamp.  
   - We still need a proper hull/keel contribution to yaw moment that grows with leeway.

2. **Missing Keel Foil**  
   - The DragonForce 65 carries a deep keel: ~0.30 m span, chord similar to the rudder.  
   - Action items:
     - Add a keel foil CSV (lift/drag vs AoA).
     - Extend the hull model to compute keel forces based on apparent water flow; project those into both translational slip damping and a lever-arm torque about the centre of mass.
     - Feed the keel torque into the yaw acceleration calculation alongside the rudder.

3. **Slip Model**  
   - Current empirical coefficient (`SLIP_FORCE_COEFF = 0.25`) is a placeholder. Once keel forces are modelled explicitly, revisit this term or remove it in favour of the new keel-side force.

### Suggested Next Steps
1. Create keel geometry parameters in `boats/argo_boat.json` (length, chord, distance from COM).  
2. Add keel foil data (can reuse rudder foil initially).  
3. Update `Manager.step()` to calculate keel lift/drag, apply the resulting force to translation, and compute the associated torque.  
4. Re-run the beam-reach test (`timeout 10 python3 -u manual_keyboard_control.py`) to validate forward drive and check that yaw acceleration no longer saturates.

Keep this file updated as we iterate on the physics. Once the keel model is implemented we can promote the notes into the main project documentation.

