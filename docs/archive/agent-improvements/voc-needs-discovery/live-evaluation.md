# Live-source development corpus

Checked and frozen: 2026-09-16. This is a bounded retrieval and semantic-fixture exercise, **not** the completed release benchmark described in the implementation plan.

## Delivered

- Three source-study sets: unseeded plant-care job discovery; known-app feedback for Todoist; multilingual moving-service communities.
- Twelve semantic exercises from six inspected source pages, in English, German, French and Italian. They are not twelve independent studies. Four country/storefront discovery contexts occur (GB, DE, FR, IT), but speaker residence is often unknown and must not be inferred from language or storefront.
- Ten customer-perspective exercises and two supplier controls. Same-thread/repeated-page observations are explicitly not independent people.
- Exact short excerpts, original language, source locator/date, agent-authored paraphrase and expected distinctions in [cases.json](../../../evals/voc/live/cases.json). The quotes total at most 25 words per source page.
- Executed queries, failures, recoveries and unattempted coverage in [retrieval-log.json](../../../evals/voc/live/retrieval-log.json). Successful designated-key Firecrawl discovery retained a raw response; it returned one relevant question and one tag index, not two customer accounts.

## Research-quality challenges visible in actual sources

The plant thread begins with a failing bottle workaround and later records success with the same setup after changing soil preparation. Treating only the opening post as current unmetness is wrong. A second speaker reports a successful named product with installation constraints; feared fungus is not an observed failure. Topic discovery finds a potential entity, but official verification and entity-led feedback remain pending.

The app page mixes customer accounts, repeated renderings, developer replies, positive outcomes and a version-specific widget failure. A 2020 requested distinction between work dates and deadlines does not establish a missing feature today. A supportive developer reply neither counts as another customer nor proves resolution. Review ordering changed between retrievals; displayed reviews are not representative of the rating population. A topic-led task-management pass was not run, so this source exercise does not satisfy the complete study contract.

Moving-service forums include refusal to outsource personal packing, an effective friends/family alternative, successful coordination through a furniture retailer, and an affiliated retailer's contribution. These should not collapse into a generic wish for effortless full outsourcing. French feedback concerns overseas relocation and is too terse to explain satisfaction; four reported service uses are not four independent people. The German thread has an unread second page. Old posts are useful method fixtures, not current market or price evidence.

## Execution and limitations

The first Firecrawl request hit sandbox DNS failure. The first approved retry used an incorrectly unpacked secret-loader return tuple and received 401; after correcting the research wrapper, the designated account succeeded. This was not insufficient credits or a provider outage. A canonical URL recovered a web cache miss. Facebook discovery searches found no relevant indexed group; a discarded guessed locator could not be verified. No Facebook customer material was captured, and no conclusion about community absence follows.

Run `python3 evals/voc/live/check_fixtures.py` for local structural integrity and the exact-quote check against the retained Firecrawl response. Other source excerpts were manually checked against full-page retrieval during this run; the checker does not re-fetch them or pretend their paraphrases are original source text.

All annotations are single-agent proposals. No independently adjudicated human labels, blind baseline/candidate outputs, semantic recall/precision scores, LangExtract/Trafilatura comparison, or held-out generalization result has been established. This corpus is development material and cannot later be called untouched holdout. The planned 240–360-unit, twelve-study benchmark remains unmet. These fixtures do not clear release quality, business validation or opportunity gates.

## Sources

All accessed 2026-09-16:

- [Indoor herb-care question](https://gardening.stackexchange.com/questions/43841/vacation-care-for-indoor-plants), question 2019-03-13.
- [Balcony watering and later resolution](https://gardening.stackexchange.com/questions/4468/how-do-i-keep-my-balcony-flowers-hydrated-while-im-away), question 2012-06-08 and follow-up 2012-06-11.
- [Todoist GB review page](https://apps.apple.com/gb/app/todoist-to-do-list-calendar/id572688855?platform=ipad&see-all=reviews), mixed dates; some omit year.
- [MamaCommunity moving thread](https://www.mamacommunity.de/forum/cafe/umzug-mit-umzugsunternehmen-wer-hat-es-gewagt), posts 2012-01-06.
- [Routard AGS discussion](https://www.routard.com/forums/t/votre-avis-sur-le-demenageur-ags/265724), posts 2020-01-28.
- [Arredamento Lombardia discussion](https://www.arredamento.it/forum/viewtopic.php?t=16367), posts 2006-07-24.
