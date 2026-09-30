# Scorer audit log

Errors found in my own automated scoring ([scoring/04_score.py](../scoring/04_score.py)) by checking its verdicts against the call transcripts.

Both were found on the same v1 call, which was later excluded from the scored set because the caller went off-script. The false positive was fixed before the published scores were computed. The false negative is still a known limitation: it applies to every scored call, v1 and v2 alike, so paraphrased repeat questions may be undercounted on both sides.

| # | Check | Type | What happened | Evidence | Action |
|---|---|---|---|---|---|
| 1 | C02 says_rupees | False positive (wrongly marked FAIL) | The agent said "35-40 minutes" and spoke no price. The check treated any 2+ digit number as a price, so it expected the word "rupees" and marked FAIL. | v1 interrupting call, Sep 30 2026 | Fixed: a price is now a number next to Rs/rupees, or a menu price not followed by "min". Re-scored all calls; that call became N/A. The rubric text was unchanged. |
| 2 | C05 no_repeat_question | False negative (wrongly marked PASS) | The agent asked for the pizza type and size three times in different words ("Aap size poora bata sakte hain?", "Kripya pizza ka type aur size bataiye...", "Kripya pizza ka type bataiye jo aap large lena chahte hain."). The check only catches near-identical wording (similarity 0.8 or more), so it passed. | v1 interrupting call, Sep 30 2026 | Logged, not fixed: the rubric was locked before scoring, so the threshold stays. Known limitation: paraphrased repeats are missed. |
