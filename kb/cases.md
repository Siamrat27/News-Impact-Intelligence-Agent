# Knowledge Base — Historical Market-Impact Cases

Hand-written case studies used as the RAG corpus (SPEC §7). Each case
follows a strict format parsed by `build_embeddings.py`:

- `## <Title>` — case title (unique, used as the upsert key)
- `type: <entity_type>` — one tag per case
- `**What happened:**` — 2-4 sentence description
- `**Market impact:**` — what followed in the market

---

## Mt. Gox Exchange Collapse (2014)

type: crypto

**What happened:** Mt. Gox, then handling ~70% of global Bitcoin trading,
halted withdrawals in February 2014 citing "technical issues," then filed
for bankruptcy after revealing roughly 850,000 BTC had been stolen over
years of undetected theft. Customer funds were frozen for what became a
decade of legal proceedings.

**Market impact:** Bitcoin fell about 50% over the following weeks and the
sell-off marked the start of a multi-year bear market. Exchange-solvency
fear became a persistent, repeatable driver of crypto drawdowns.

## FTX Collapse (2022)

type: crypto

**What happened:** In November 2022 a leaked balance sheet showed Alameda
Research was heavily dependent on FTX's own FTT token. A wave of customer
withdrawals followed, FTX halted withdrawals within days, and the exchange
filed for bankruptcy revealing an ~$8B hole in customer funds.

**Market impact:** Bitcoin dropped ~25% in a week and FTT lost over 90%.
Contagion spread through lenders (BlockFi, Genesis) for months. Headlines
combining "exchange" with "halts withdrawals" now trigger immediate
solvency-panic selling across the sector.

## Terra/Luna Stablecoin Collapse (2022)

type: crypto

**What happened:** In May 2022 the algorithmic stablecoin UST lost its
dollar peg after large coordinated withdrawals from its main liquidity
pool. The mint-burn mechanism that was supposed to restore the peg instead
hyperinflated LUNA's supply, destroying ~$40B of value within a week.

**Market impact:** UST went to a few cents and LUNA to effectively zero.
The collapse dragged Bitcoin below $30k, bankrupted leveraged funds
(Three Arrows Capital), and triggered global regulatory scrutiny of
stablecoins that persists today.

## US Spot Bitcoin ETF Approval (2024)

type: crypto

**What happened:** In January 2024 the SEC approved the first US spot
Bitcoin ETFs after a decade of rejections, following a court loss to
Grayscale. Eleven funds from issuers including BlackRock and Fidelity
began trading simultaneously.

**Market impact:** The approval was largely priced in ("sell the news" dip
of ~15% in the first weeks), but sustained ETF inflows then drove Bitcoin
to new all-time highs within two months. Regulatory-approval headlines
tend to produce short-term chop but durable medium-term inflows.

## China Comprehensive Crypto Ban (2021)

type: crypto

**What happened:** In September 2021 China's central bank declared all
cryptocurrency transactions illegal and banned mining nationwide,
completing a crackdown that had escalated through the year. Mining
operations relocated en masse to the US and Central Asia.

**Market impact:** Bitcoin fell ~9% on the announcement day but recovered
within weeks — each successive China ban produced smaller reactions as
the market learned to discount repeated headlines. Hash rate fully
recovered within a year.

## Ethereum Merge (2022)

type: crypto

**What happened:** In September 2022 Ethereum completed "The Merge,"
switching consensus from proof-of-work to proof-of-stake in a live
migration executed without downtime. Energy consumption dropped ~99.9%
and new ETH issuance fell sharply.

**Market impact:** Despite flawless execution, ETH fell ~15% in the week
after — a classic "buy the rumor, sell the news" pattern for long-telegraphed
technical upgrades. The supply-reduction effect supported prices only over
subsequent quarters.

## Binance DOJ Settlement (2023)

type: crypto

**What happened:** In November 2023 Binance pleaded guilty to US anti-money-
laundering violations, paid a $4.3B fine, and CEO Changpeng Zhao stepped
down as part of the settlement. The exchange continued operating under
compliance monitoring.

**Market impact:** After brief volatility, markets rallied — resolution of
a long-overhanging legal threat was read as risk removal rather than
damage. Enforcement headlines hurt most when they open uncertainty and
often help when they close it.

## SEC Sues Ripple Over XRP (2020)

type: crypto

**What happened:** In December 2020 the SEC sued Ripple Labs alleging XRP
was an unregistered security. Major US exchanges delisted or suspended
XRP trading within weeks.

**Market impact:** XRP lost ~60% in the two weeks after filing while the
broader market was rallying. A partial court victory in 2023 recovered
much of the loss in a single day, showing lawsuit headlines dominate an
asset's price for years once securities status is in question.

## Tesla Adds Bitcoin to Balance Sheet (2021)

type: company

**What happened:** In February 2021 Tesla disclosed a $1.5B Bitcoin
purchase in an SEC filing and announced plans to accept BTC as payment.
It was the first major S&P 500 company to hold Bitcoin as a treasury
asset.

**Market impact:** Bitcoin jumped ~15% within hours to a then-record high,
and corporate-adoption speculation lifted the whole sector. Reversal
headlines later (Tesla suspending BTC payments over energy concerns in
May 2021) knocked ~10% off just as quickly — celebrity-CEO signals cut
both ways.

## COVID-19 Global Market Crash (March 2020)

type: index

**What happened:** As COVID-19 spread globally in late February and March
2020, markets priced in economic shutdowns. The S&P 500 fell ~34% in five
weeks with repeated circuit-breaker halts; liquidity evaporated across
every asset class simultaneously.

**Market impact:** Correlations went to one: equities, gold, and Bitcoin
all sold off together as investors raised cash (BTC -50% in two days).
"Everything crashes" liquidity events break normal hedging relationships;
recovery began only after unprecedented fiscal and monetary intervention.

## Lehman Brothers Bankruptcy (2008)

type: institution

**What happened:** In September 2008 Lehman Brothers filed the largest
bankruptcy in US history after the government declined a bailout, freezing
credit markets that had assumed systemically important banks would be
rescued.

**Market impact:** The S&P 500 fell ~40% over the following six months and
interbank lending seized worldwide. Bank-failure headlines carry systemic
contagion risk — the market's question is never just "is this firm dead"
but "who is exposed to it."

## Silicon Valley Bank Collapse (2023)

type: institution

**What happened:** In March 2023 SVB disclosed losses on its bond portfolio
and attempted a capital raise, triggering a deposit run of $42B in one day —
accelerated by social media. Regulators seized the bank within 48 hours of
the initial disclosure.

**Market impact:** Regional bank stocks fell 20-60% in days. The USDC
stablecoin briefly depegged to $0.87 because issuer Circle held reserves
at SVB, dragging crypto into a banking panic. Deposit-guarantee
announcements reversed most losses within a week — policy response speed
determined the damage.

## Fed 75bp Rate Hike Cycle (2022)

type: institution

**What happened:** Through 2022 the Federal Reserve raised rates at the
fastest pace in four decades, including four consecutive 75-basis-point
hikes, to fight inflation that had reached 9%. Each FOMC meeting and CPI
print became a major market event.

**Market impact:** The S&P 500 lost ~25% peak-to-trough in 2022 and
Bitcoin fell ~65% — risk assets repriced as discount rates rose. Markets
moved less on the hikes themselves than on surprises versus expectations;
hawkish-surprise headlines produced immediate 2-4% single-day drops.

## GameStop Short Squeeze (2021)

type: company

**What happened:** In January 2021 retail traders coordinating on Reddit
drove GameStop stock from ~$20 to a $483 intraday peak in two weeks,
forcing short-selling hedge funds to cover at massive losses. Brokerages
restricted buying at the peak, drawing congressional hearings.

**Market impact:** GME rose >1,500% before collapsing ~90% in the
following weeks. Short-interest and social-sentiment data became monitored
market signals; "meme stock" volatility now episodically detaches prices
from fundamentals for weeks at a time.

## Meta Q3 2022 Earnings Miss

type: company

**What happened:** In October 2022 Meta reported falling revenue, shrinking
margins, and sharply higher metaverse spending plans, missing profit
expectations while guiding capex even higher against investor objections.

**Market impact:** The stock fell ~25% in a single day, erasing ~$85B of
market value, and had lost ~75% from its 2021 peak before reversing.
Earnings misses compound when paired with spending guidance investors
dislike — the reversal came only after a public cost-discipline pivot.

## NVIDIA AI Guidance Shock (2023)

type: company

**What happened:** In May 2023 NVIDIA guided quarterly revenue ~50% above
Wall Street consensus on explosive data-center GPU demand for AI training,
one of the largest guidance beats in large-cap history.

**Market impact:** The stock jumped ~25% overnight, adding ~$200B in
market value, and pulled the entire semiconductor sector and AI-adjacent
names up with it. A single company's guidance can reprice a whole theme
when it validates a macro narrative.

## Brexit Referendum (2016)

type: currency

**What happened:** On June 23, 2016 the UK unexpectedly voted to leave the
European Union — polls and betting markets had priced Remain. The result
became clear overnight, catching positioned markets wrong-footed.

**Market impact:** GBP/USD fell ~10% within hours to a 31-year low, and
global equities lost ~$2T in a day before stabilizing. Binary political
events with mispriced probabilities produce the sharpest single-session
currency moves; gold and safe havens rallied simultaneously.

## Swiss Franc Depeg (2015)

type: currency

**What happened:** In January 2015 the Swiss National Bank abandoned its
1.20 EUR/CHF floor without warning, three days after publicly calling the
peg essential policy. The franc surged ~30% against the euro within
minutes.

**Market impact:** Several currency brokers went insolvent from client
margin losses and banks lost hundreds of millions. Central-bank surprise
reversals are the extreme tail case: when a promised backstop vanishes,
the repricing is instantaneous and gaps straight through stop-losses.

---
