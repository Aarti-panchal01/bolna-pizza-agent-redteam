# bolna-pizza-agent-redteam

Red-teaming a Hinglish pizza-ordering voice agent on [Bolna](https://bolna.ai) over real phone calls, then fixing it and measuring the fix.
TL;DR: Built a Hinglish pizza-ordering agent on Bolna and red-teamed it over 7 real calls. Fixes took it from 30% to 62% on a locked 11-check rubric. Best find: "haan, do do" (give it) was heard as "two" and doubled the order.

## 1. What I built
A phone agent, "Priya", that takes home-delivery orders for a Bengaluru pizza cafe in Hindi, Hinglish and English. It runs on Bolna with ElevenLabs Scribe for speech-to-text, ElevenLabs for the voice, and gpt-4.1-mini. **v1** is the baseline. **v2** is the fixed version.

## 2. How I tested it
- **7 real phone calls**: 3 on v1, 4 on v2. I was the caller and talked naturally, not from a script.
- **A locked 11-check rubric** ([rubric/rubric.json](rubric/rubric.json)). It was hash-locked before the v2 calls, and the scorer refuses to run if the rubric changes.
- **7 checks are automatic**, from the transcript and Bolna's interruption stats. **4 are manual**, and each needs a quote from the transcript as evidence.
- **I audited the scorer itself** and logged the false positive and false negative I found: [rubric/scorer-audit.md](rubric/scorer-audit.md).
- The rubric has a 12th check (per-script goals). It is excluded because the calls were free-form. See [rubric/scope.json](rubric/scope.json).

## 3. Results

| | v1 (before) | v2 (after) |
|---|---|---|
| Calls | 3 | 4 |
| **All 11 checks** | **30%** (10/33) | **62%** (24/39) |

| Check | v1 | v2 |
|---|---|---|
| C01 Never says Rs, RS, INR, /- or the rupee symbol | 0/3 | 4/4 |
| C02 Says prices with the word "rupees" | 0/3 | 2/2 |
| C03 Final read-back states subtotal, delivery and total | 0/3 | 2/2 |
| C04 Reads the phone number back digit by digit | 0/3 | 2/3 |
| C05 Never asks the same question twice | 3/3 | 2/4 |
| C06 Does not jump in while the caller is talking (at most once) | 0/3 | 0/4 |
| C07 Never talks over the caller | 3/3 | 4/4 |
| C08 Final order matches what the caller asked for | 2/3 | 4/4 |
| C09 Total correct from the menu and delivery rule | 2/3 | 1/4 |
| C10 All five address parts collected and read back | 0/3 | 2/4 |
| C11 Address and phone confirmed before the order | 0/3 | 1/4 |

Checks marked N/A on a call are left out of the counts. With 3 and 4 calls, this is a direction, not a statistic.

## 4. Best findings
- **"haan, do do" was heard as "two".** In Hindi, "do" can mean "give" or "two". The caller said "One", then "haan, do do". v1 doubled the order to 2 pizzas and 2 drinks for 1118 rupees.
- **"Farmhouse" was heard as "flat out".** Speech-to-text missed a menu name, and the agent told the caller it wasn't on the menu. *(Observed on real calls outside the scored set.)*
- **Vague addresses were accepted.** v1 took a PG name as a complete address on every scored call. It also accepted "Koramangala bus stop ke paas" *(observed on real calls outside the scored set)*.
- **Delivery-fee maths fails at edge cases.** The rule is 40 rupees under 500 and free at 500 or more. v1 once called a 409 subtotal "free delivery". v2 called a 499 subtotal free, when the total should have been 539.
- **"Rs 60" was read out as "R S 60".** The menu said "Rs", and the voice spelled it out.

## 5. What I changed (v1 to v2)
Full prompt diff: [prompts/v1-to-v2.diff](prompts/v1-to-v2.diff). Both prompts: [v1](prompts/v1-system-prompt.md), [v2](prompts/v2-system-prompt.md).
- **Prompt:** replaced the 7-step order script with CONVERSATION STYLE and ORDER FLOW sections. Ask only for what's missing, one thing at a time. Collect all five address parts. Read the phone back digit by digit. Read back subtotal, delivery and total. Confirm ambiguous quantities.
- **Prices:** the menu and every price now say "rupees".
- **Turn-taking:** endpointing 200 ms to 700 ms, linear delay 300 ms to 500 ms.
- **Recognition:** 12 menu names added as transcriber keywords.
- **Language:** Bolna multilingual mode, Hindi and English with automatic switching. Language rules were removed from the prompt, as Bolna's docs recommend.

## 6. What's still broken, and what I'd do next
- **Jumping in (C06: 0/3 to 0/4).** Longer endpointing didn't fix it. Next: tune Bolna's interruption and VAD settings on quiet calls first, because noise and the phone's call screener confounded these runs.
- **Pricing in the prompt.** The LLM still gets edge cases wrong. Next: move subtotal, delivery and total into a tool call that returns exact numbers.
- **Repeat questions (C05 got worse).** v2 re-asks for house and street when the caller gives a landmark first. Next: tell it to accept partial parts and ask only for the rest.
- **Kannada.** The current voice has no Kannada. Next: add Kannada as a third language with a Sarvam voice.

## 7. Extraction note (observed, not yet confirmed)
The v1 agent returned 7 extraction fields per call (3/3). The v2 copy with multilingual mode on returned empty `extracted_data` on 4/4 calls, still empty on re-fetch. Both agents have the same 9 dispositions, and no other config change should affect post-call extraction. The copy was also created through the API, so that isn't ruled out. Repro: the same agent, one call with multilingual off and one with it on.

## Files
- `prompts/`: v1 and v2 system prompts, and the diff
- `rubric/`: the locked rubric, its hash lock, the scoring scope, and the scorer audit log
- `scoring/04_score.py`: the scorer (needs your own Bolna runs in `runs/`; `bolna.py` reads your API key from a local `.env`)
- `showcase/best-v2-call.md`: the best v2 call, with dummy personal details

No API keys, raw call data or real personal details are in this repo.
