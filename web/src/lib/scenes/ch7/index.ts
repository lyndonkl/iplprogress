import type { SceneDef } from '$lib/story/types';
import { readGapScrollLength } from '$lib/story/captionReveal.svelte';
import Title from './Title.svelte';
import Rivers from './Rivers.svelte';
import ControlGroup from './ControlGroup.svelte';
import Ruler from './Ruler.svelte';
import License from './License.svelte';
import Placebo from './Placebo.svelte';
import Playbook from './Playbook.svelte';
import Payoff from './Payoff.svelte';
import CloseCh7 from './CloseCh7.svelte';

/**
 * CHAPTER 7 — The Twelfth Man (storyboard r4b, scenes C7-1..C7-8). REGISTER: THE
 * NATURAL EXPERIMENT — the 2023 Impact Player rule as a rare experiment, with the
 * rule-free WPL as the control group. Picks up the Ch 4 cliff ("here is the
 * suspect") and plants the Ch 10 mystery ("same players, or new ones?").
 *
 * BUDGETS (blueprint §2 / §3):
 * - Exactly ONE controlling morph: free field → the twin rivers (ch7-rivers),
 *   returned in ch7-close. The flowLift divergence reveal (§23.3) and the impact-
 *   sub SPARKS (§23.4) COMPOSE with the held `flow` layout — no second morph. The
 *   licence split-screen, the placebo cursor and the playbook decoder are 2D
 *   annotation-plane scenes over the dimmed rivers.
 * - Beat budget: HERO + max 3 supporting. Hero: the twin rivers ("the control
 *   group" — orient in ch7-rivers, the divergence + sparks in ch7-control, one
 *   device across two beats). Supporting: the Licence Index, the Placebo Cursor
 *   (the chapter signature interactive), the Playbook Decoder. Title / payoff /
 *   close are structural, not beats. The sub-timing Sankey demotes to the footnote.
 *
 * Every on-screen number comes from static/data/scenes/ch7.json (see ./data.ts)
 * — never hardcoded (OWNER-LOCKED; the ARTIFACT wins over teaser copy). GLOSSARY
 * (locked): the hero leads as "the control group"; "difference-in-differences" and
 * the t-statistic live one click deep in the footnotes. HOUSE FRAMING: the WPL is
 * never "behind" — here it is the control arm, the reason the rule is readable.
 */

const clamp01 = (t: number): number => Math.min(1, Math.max(0, t));

/* the C7-3 reveal windows (progress): the climb lifts and the sparks glow during
   step 2 ("the river climbs"), both finished before the gap read lands at step 3 */
const LIFT_LO = 0.3;
const LIFT_HI = 0.5;
const SPARK_LO = 0.34;
const SPARK_HI = 0.52;

export const scenes: SceneDef[] = [
	{
		id: 'ch7-title',
		chapter: 'ch7',
		anchor: 'ch7',
		navLabel: 'Chapter 7: The Twelfth Man',
		scrollLength: 120,
		morphLength: 50,
		// ch6-close left the field at free; the title dims it a touch (a luminance
		// lerp, not a morph). Zero numbers on a title.
		fieldState: { layout: 'free', dim: 0.3 },
		annotations: Title
	},
	{
		id: 'ch7-rivers',
		chapter: 'ch7',
		scrollLength: 340,
		mobileScrollLength: readGapScrollLength(340),
		morphLength: 150,
		// C7-2: THE CONTROLLING MORPH — free field → the twin rivers (every ball flies
		// to its league-season cell; in-shader off group_ids.u16 + the WPL bit; no new
		// buffer). Rivers.svelte feeds the river table (setRiverTable) and draws the
		// centrelines / axis / fork / legend. Lands at TRUE heights (flowLift 1) — the
		// honest full picture; the divergence gets NAMED next.
		fieldState: { layout: 'flow', flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', flowLift: 1 },
		annotations: Rivers,
		footnote: 'ch7-rivers'
	},
	{
		id: 'ch7-control',
		chapter: 'ch7',
		scrollLength: 420,
		mobileScrollLength: readGapScrollLength(420),
		morphLength: 40,
		// C7-3 HERO (first half): the FORK. Enters with fromState flowLift 0, so on
		// entry ONLY the four post-2023 IPL points settle back from their climbed
		// heights (shown true in ch7-rivers) to the 2022 plateau — the rest of the
		// river (the flat fifteen-year stretch and the WPL) does NOT move, since their
		// baseHeight == trueHeight. Step 1's caption directs the eye to that stable flat
		// stretch while this happens; then in step 2 the flowLift reveal lifts the four
		// treatment points back up (the climb the reader is told to watch) and the
		// impact-sub SPARKS glow (setSparks fed in ControlGroup). The gap read lands at
		// step 3+, after the lift is complete. flowLift + sparks are POST-MORPH scalar
		// changes driven here (§23.3/§23.4). The ruler-gloss + confound are C7-4 (Ruler).
		fromState: { layout: 'flow', flowLift: 0 },
		fieldState: { layout: 'flow', flowLift: 0, sparks: { glow: 0, lift: 0.02, othersDim: 1 } },
		reducedMotionEndState: {
			layout: 'flow',
			flowLift: 1,
			sparks: { glow: 1, lift: 0.02, othersDim: 0.55 }
		},
		dynamicState: (progress, held) => {
			const lift = clamp01((progress - LIFT_LO) / (LIFT_HI - LIFT_LO));
			const glow = clamp01((progress - SPARK_LO) / (SPARK_HI - SPARK_LO));
			return {
				...held,
				flowLift: lift,
				// othersDim rides DOWN with the glow so nothing dims before the sparks light
				sparks: { glow, lift: 0.02, othersDim: 1 - 0.45 * glow }
			};
		},
		annotations: ControlGroup,
		footnote: 'ch7-rivers'
	},
	{
		id: 'ch7-ruler',
		chapter: 'ch7',
		scrollLength: 300,
		mobileScrollLength: readGapScrollLength(300),
		morphLength: 40,
		// C7-4 HERO (second half): the ruler + the honest bounds. The rivers HOLD at
		// true heights (flowLift 1) with the gap read pinned; three one-point beats
		// carry the control-group gloss, the WPL "not the laggard" reframe (should-fix
		// #6), and the confound named in main flow (should-fix #7). Declaring no
		// `sparks` lets C7-3's glow lerp back to 0 (reversible). No field morph.
		fieldState: { layout: 'flow', flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', flowLift: 1 },
		annotations: Ruler,
		footnote: 'ch7-rivers'
	},
	{
		id: 'ch7-license',
		chapter: 'ch7',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// C7-4 Supporting 1: the Licence Index split-screen (2D over the dimmed rivers).
		// Declaring no `sparks` lets the C7-3 glow lerp back to 0 (reversible). flowLift
		// stays 1 (true heights) behind the panel.
		fieldState: { layout: 'flow', dim: 0.24, flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', dim: 0.24, flowLift: 1 },
		annotations: License,
		footnote: 'ch7-license'
	},
	{
		id: 'ch7-placebo',
		chapter: 'ch7',
		scrollLength: 360,
		mobileScrollLength: readGapScrollLength(360),
		morphLength: 45,
		// C7-5 Supporting 2 + the CHAPTER SIGNATURE INTERACTIVE: the placebo cursor
		// (2D over the dimmed rivers). The reader drags the "if the rule came in…" date;
		// the jump re-reads from the precomputed grid (a lookup). Reduced motion rests
		// the cursor on the true 2023 date with the placebo cloud static (the point
		// lands with zero dragging).
		fieldState: { layout: 'flow', dim: 0.2, flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', dim: 0.2, flowLift: 1 },
		annotations: Placebo,
		footnote: 'ch7-placebo'
	},
	{
		id: 'ch7-playbook',
		chapter: 'ch7',
		scrollLength: 320,
		mobileScrollLength: readGapScrollLength(320),
		morphLength: 45,
		// C7-6 Supporting 3: the Playbook Decoder (2D per-season bars over the dimmed
		// rivers). The league learning its own rule — subs at the break 51.8% → 35.7%.
		fieldState: { layout: 'flow', dim: 0.22, flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', dim: 0.22, flowLift: 1 },
		annotations: Playbook,
		footnote: 'ch7-playbook'
	},
	{
		id: 'ch7-payoff',
		chapter: 'ch7',
		scrollLength: 240,
		morphLength: 55,
		// C7-7 payoff: your team's playbook (the rivers idle faintly behind the card).
		// All 16 variants come from ch7.json payoff.variants (card == artifact).
		fieldState: { layout: 'flow', dim: 0.3, flowLift: 1 },
		reducedMotionEndState: { layout: 'flow', dim: 0.3, flowLift: 1 },
		annotations: Payoff,
		footnote: 'ch7-payoff'
	},
	{
		id: 'ch7-close',
		chapter: 'ch7',
		scrollLength: 130,
		morphLength: 60,
		// C7-8: the rivers exhale back into the free field — the controlling morph's
		// return leg. Plants the Ch 10 mystery (same players?) and hooks Ch 8.
		fieldState: { layout: 'free' },
		annotations: CloseCh7
	}
];
