# Football slang to NCAA rulebook wording

Compiled by Timothy Hays with AI assistance for the NCAA Football Referee project. These are search expansions, not automatic foul determinations. The application should retain the original question and add matching rulebook terms.

On special-teams plays, use **kicking team** and **receiving team**, including player numbers. Use offensive/defensive labels for ordinary scrimmage plays.

Machine-readable vocabulary: [`src/referee/terminology.json`](../src/referee/terminology.json). This file is ready for a retrieval loader; it does not itself implement query expansion.

| Fan/player wording | Rulebook search wording |
|---|---|
| blindside hit | blind-side block |
| block in the back | illegal block in the back |
| bobble | catch; control; possession |
| broke the plane | touchdown; goal-line plane |
| chop block | chop block; high-low combination block |
| clipping | clipping |
| clock the ball | forward pass to conserve time; illegal forward pass |
| cut block | blocking below the waist |
| down by contact | dead ball; ball declared dead |
| downed the punt | touching; recovery; ball declared dead |
| DPI | defensive pass interference; catchable forward pass |
| encroachment | encroachment; offside; neutral zone |
| endzone | end zone |
| extra point | try; field goal on a try |
| facemask | face mask; helmet opening |
| fair catch | fair catch; valid signal |
| fake punt | scrimmage-kick formation; forward pass; simulated scrimmage kick |
| flinched | false start |
| going for two | try; touchdown on a try |
| grounding | illegal forward pass; tackle box; conserve yardage |
| headshot | targeting; head or neck area; defenseless player |
| helmet-to-helmet | targeting; head or neck area; defenseless player |
| hit the punter | roughing or running into kicker or holder |
| holding | holding; illegal use of hands |
| horse collar | horse-collar tackle |
| illegal motion | player in motion; illegal motion |
| illegal shift | shift; one-second stop; false start |
| in the pocket | tackle box |
| iron cross | T signal; invalid fair catch signal; fair catch signal; no advance |
| jersey tug | holding; pass interference |
| jumped offsides | offside; false start; neutral zone |
| jumped the snap | offside; false start; neutral zone |
| kickoff | free kick |
| kickoff out of bounds | free kick out of bounds; kicking team |
| knee was down | ball declared dead |
| late hit | personal foul; dead-ball foul |
| lateral | backward pass |
| line of scrimmage | neutral zone; scrimmage line |
| LOS | scrimmage line; neutral zone |
| moved early | false start |
| moved the chains | first down; line to gain |
| muffed punt | muff; scrimmage kick; touching |
| onside | free kick; restraining line; touching and recovery |
| onside kick | free kick; restraining line; touching and recovery |
| OPI | offensive pass interference |
| OT | extra periods; extra period |
| out of bounds | boundary line; sideline; out of bounds |
| outside the pocket | tackle box; illegal forward pass |
| overtime | extra periods |
| PAT | try; field goal on a try |
| PI | pass interference |
| pick | interception; offensive pass interference |
| pick play | offensive pass interference; blocking |
| pick six | interception; touchdown; change of possession |
| picked off | interception |
| pitch | backward pass; forward and backward pass |
| punt | scrimmage kick |
| pushed off | offensive pass interference |
| quarter | period |
| roughing the QB | roughing the passer |
| rub route | offensive pass interference; blocking |
| scoop and score | fumble recovery; touchdown |
| showboating | unsportsmanlike conduct |
| spearing | crown of the helmet; targeting |
| spike | forward pass to conserve time; illegal forward pass |
| stripped | fumble; loss of possession |
| taking a knee | ball declared dead |
| targeting | crown of the helmet; defenseless player; head or neck area |
| taunting | unsportsmanlike conduct |
| throwaway | illegal forward pass; eligible receiver; neutral zone |
| toe drag | catch; inbounds; boundary line |
| toe in heel out | catch; continuous toe-heel landing; out of bounds |
| toe tap | catch; inbounds; boundary line |
| too many men | substitution; more than eleven players |
| touchback | touchback; free kick; scrimmage kick |
| turnover on downs | new series; failure to reach the line to gain |
| two point conversion | try; touchdown on a try |
| two-point conversion | try; touchdown on a try |
| waved teammates away | invalid fair catch signal; no advance |

## Ambiguities to preserve

- A lateral or pitch is not automatically a backward pass: field direction determines classification.
- Pick can mean an interception; pick play or rub route can refer to receiver contact.
- Cut block and chop block are different concepts.
- A muff does not establish possession and should not be rewritten as a fumble.
- Pick play, helmet-to-helmet, jersey tug and contact before a catch are search descriptions, not proof that a foul occurred.
- Quarter normally maps to period; OT specifically maps to extra period.
- Iron cross is Timothy’s term for a player putting both hands up to indicate he will not return the kick. Search T signal, fair-catch signal, invalid signal and no advance; preserve the actual gesture rather than assuming it is a valid fair-catch signal.
- Match abbreviations as whole tokens and phrases; do not match PI inside an unrelated word. Preserve punctuation/hyphen variants when normalizing.

Rule hints in the JSON are navigation aids and require verification before use as answer citations. The vocabulary remains open to teammate review.
