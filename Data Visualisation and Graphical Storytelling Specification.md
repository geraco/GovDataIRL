# Data Visualisation and Graphical Storytelling Specification

## 1. Objective

Improve the presentation layer of the analytics application so that analytical results appearing in website articles are presented using modern, editorial-quality data graphics.

The application must not default to:

- pie charts
- generic bar charts
- generic line charts
- large tables

Instead, the system should determine:

1. What question is the data answering?
2. What relationship exists in the data?
3. What is the most important finding?
4. Which visual form communicates that finding most effectively?
5. Whether the visualisation should be static, interactive or progressive.

The objective is not to make charts more decorative.

The objective is to make the analytical conclusion easier and faster to understand.

---

# 2. Core Visualisation Principle

Before producing a graphic, classify the analytical purpose into one of these categories:

- KPI / headline result
- ranking
- comparison
- change
- trend
- distribution
- relationship
- composition
- hierarchy
- flow
- geography
- sequence
- concentration
- variance
- uncertainty
- progress
- cohort behaviour
- network relationship

The visualisation engine should then select from the visualisation catalogue below.

Do not choose a graphic solely because a particular chart type is easy to generate.

---

# 3. Visualisation Catalogue

## 3.1 KPI Story Card

### Use when

There is one important number.

Examples:

- Revenue €14.2m
- Conversion 7.4%
- Risk score 82/100
- 17 exceptions identified

### Presentation

Display:

**€14.2m**

Revenue

↑ 8.3% versus previous period

Include a small sparkline showing recent movement.

### Enhancement

Add contextual language such as:

> Highest level in 18 months

This is considerably more useful than displaying a number without context.

---

## 3.2 KPI Strip

Use for 3 to 6 important metrics.

Each card contains:

- main value
- metric name
- percentage or absolute change
- mini sparkline
- optional status indicator

Example:

Revenue | Margin | Customers | Churn

Do not create 10 to 20 KPI cards.

Prioritise the metrics supporting the article's argument.

---

## 3.3 Sparkline

A tiny line chart without conventional chart furniture.

Use:

- beside KPI values
- inside tables
- inside comparison cards
- beside company names
- beside categories

Useful for showing whether an individual number is rising, falling or stable without requiring another full chart.

---

## 3.4 Bullet Chart

Use instead of gauges.

Shows:

Actual performance

versus

Target

with contextual performance ranges.

Example:

Revenue

████████████████  €8.4m  
Target             €9.0m

Ideal for:

- targets
- budgets
- SLAs
- audit metrics
- project delivery
- financial performance

---

## 3.5 Lollipop Chart

Use instead of bars when displaying relatively few ranked values.

Structure:

Category ─────────● 72

Produces a lighter editorial presentation than large rectangular bars.

Good for:

- survey results
- rankings
- scores
- percentages
- comparative metrics

---

## 3.6 Dot Plot

Use when precise comparison is more important than visual area.

Each category has a point positioned on a common scale.

Particularly useful when values are relatively close together.

Example:

Ireland       ● 73  
France      ● 69  
Germany          ● 76

---

## 3.7 Dumbbell Chart

Use when comparing exactly two values for each category.

Examples:

- 2025 versus 2026
- budget versus actual
- before versus after
- male versus female
- expected versus observed

Structure:

2025 ●────────────● 2026

The connecting line visually communicates the size of the difference.

---

## 3.8 Range Plot

Similar to a dumbbell chart but intended to communicate ranges.

Examples:

- minimum and maximum
- forecast range
- acceptable threshold
- low and high estimate
- analyst price targets

Useful when uncertainty or variation matters.

---

## 3.9 Arrow Chart

Use when direction of movement matters.

Example:

Product A

48% ───────────────→ 71%

Particularly effective for showing changes across a relatively small number of categories.

---

## 3.10 Slopegraph

Use to compare two points in time across several categories.

Example:

2024                        2026

Product A  42% ─────────── 61%  
Product B  55% ───── 49%  
Product C  31% ─────────────── 67%

Useful for highlighting:

- winners
- losers
- reversals
- convergence
- divergence

---

## 3.11 Bump Chart

Use when the ranking itself changes over time.

Examples:

- company market positions
- sports rankings
- product popularity
- investment rankings
- departmental performance

Lines move vertically as rank changes.

Focus should be placed on changes in position rather than absolute values.

---

## 3.12 Small Multiples

One of the default techniques for complex articles.

Instead of putting ten lines on a single chart, create ten small charts using the same axes.

Example:

Revenue trend by:

- Europe
- North America
- Asia
- Middle East

Each receives its own mini-chart.

This makes patterns significantly easier to compare.

Observable Plot supports this concept through faceting, where the same visualisation is repeated for different partitions of the dataset.

---

## 3.13 Highlighted Line Chart

Do not simply draw six equally prominent lines.

Instead:

- highlight the important series
- mute contextual series
- directly label important lines
- annotate significant events

Example:

AVGO highlighted

NVDA, AMD and SOXX displayed as muted contextual lines.

The chart should visually communicate what the reader should examine.

---

## 3.14 Indexed Performance Chart

Use when values have very different absolute scales but relative performance matters.

Set every series to:

Starting value = 100

Then show subsequent percentage movement.

Ideal for:

- investment performance
- sales growth comparisons
- inflation comparisons
- benchmark comparisons

---

## 3.15 Area Difference Chart

Show the difference between two time series as a filled region.

Examples:

Revenue versus target

Demand versus capacity

Bull versus bear forecast

The gap becomes the focus rather than the individual lines.

---

## 3.16 Waterfall Chart

Use to explain how a starting number became an ending number.

Example:

Starting profit  
+ Revenue increase  
- Labour costs  
- Tax  
+ FX movement  
= Final profit

Very useful for financial and operational analysis.

---

## 3.17 Diverging Bar Chart

Use when values move around a meaningful centre point.

Examples:

- positive versus negative sentiment
- gain versus loss
- over budget versus under budget
- strongly disagree through strongly agree

Zero or neutral becomes the central reference line.

---

## 3.18 Likert Chart

Specialised diverging stacked bars for surveys.

Example:

Strongly disagree | Disagree | Neutral | Agree | Strongly agree

Use for questionnaires and opinion data instead of separate pie charts for every question.

---

## 3.19 Heatmap

Encode magnitude through a two-dimensional grid.

Example:

             Mon Tue Wed Thu Fri

08:00        ░   ░   █   ░   ░
09:00        ▓   █   █   ▓   ░
10:00        █   █   ▓   █   ▓

Useful for:

- activity
- correlations
- risk
- incidents
- usage
- performance matrices

---

## 3.20 Calendar Heatmap

Display activity across individual days.

Common visual structure:

Jan Feb Mar ... Dec

with each day represented as a small coloured square.

Ideal for:

- system incidents
- website traffic
- trading activity
- workouts
- commits
- transactions
- alerts

Immediately reveals streaks, clusters and periods of inactivity.

---

## 3.21 Cohort Heatmap

Use for retention or behaviour over time.

Example:

| Cohort | Month 0 | Month 1 | Month 2 | Month 3 |

Represent percentages through colour intensity.

Excellent for:

- customers
- subscriptions
- product usage
- employee retention
- recurring purchases

---

## 3.22 Histogram

Use to show how a variable is distributed.

Examples:

- transaction size
- customer age
- response time
- investment return
- audit finding age

Do not replace distributions with averages.

An average can hide the structure of the underlying data.

---

## 3.23 Density Plot

A smoother alternative to a histogram.

Useful when comparing the shape of several distributions.

Example:

2025 response times versus 2026 response times.

---

## 3.24 Ridgeline Plot

Stack multiple density distributions vertically.

Example:

Response-time distribution by month.

Jan  ╭────╮  
Feb    ╭─────╮  
Mar       ╭────╮  
Apr   ╭────────╮

Useful for showing how an entire distribution changes over time.

Use selectively because it is visually sophisticated.

---

## 3.25 Box Plot

Show:

- median
- quartiles
- spread
- outliers

Use where statistical distribution matters.

Particularly useful for analytical rather than general consumer articles.

---

## 3.26 Violin Plot

Use when the shape of the distribution is important in addition to median and quartiles.

Use sparingly.

Prefer histogram, box plot or beeswarm when the audience is unlikely to understand violin plots.

---

## 3.27 Beeswarm Plot

Represent every observation as an individual dot while preventing overlap.

Excellent for showing:

- salary distribution
- company valuation
- transactions
- test results
- investment returns
- risk scores

Provides a sense of the actual population rather than an aggregated summary.

---

## 3.28 Scatter Plot with Quadrants

For two-variable analysis.

Example:

X = Revenue growth  
Y = Profit margin

Create meaningful quadrants such as:

HIGH GROWTH / HIGH MARGIN

HIGH GROWTH / LOW MARGIN

LOW GROWTH / HIGH MARGIN

LOW GROWTH / LOW MARGIN

Label important observations directly.

This transforms a generic scatter plot into a decision graphic.

---

## 3.29 Bubble Plot

Add a third variable using circle size.

Example:

X = growth  
Y = margin  
Bubble size = revenue

Avoid excessive numbers of bubbles.

The important observations should be labelled.

---

## 3.30 Hexbin Plot

Use instead of a scatter plot when thousands of observations overlap.

Divide the plot into hexagonal regions.

Colour intensity represents observation density.

Good for large datasets.

---

## 3.31 Treemap

Represent hierarchical quantities as nested rectangles.

Example:

Company

├── Cloud  
├── Networking  
├── Software  
└── Services

Rectangle size represents value.

Useful for:

- portfolio allocation
- budgets
- market composition
- organisational metrics
- product revenue

Interactive treemaps can support drill-down into hierarchical categories.

---

## 3.32 Sunburst Chart

Use for hierarchical relationships where levels matter.

Example:

Organisation

→ Division

→ Department

→ Product

Use when hierarchy itself is part of the analytical story.

Do not use merely because it looks impressive.

---

## 3.33 Waffle Chart

A 10 × 10 grid representing 100%.

Example:

73 highlighted squares = 73%.

Useful for simple percentages when a large editorial graphic is desired.

Particularly suitable for article call-outs.

Do not create multiple waffle charts where a dot plot would allow easier comparison.

Observable Plot includes a dedicated waffle visualisation mark.

---

## 3.34 Sankey Diagram

Use to explain flows between categories.

Example:

Revenue

→ Products  
→ Geography  
→ Costs  
→ Profit

Or:

Website visitors

→ Product page  
→ Basket  
→ Checkout  
→ Purchase

Line width represents volume.

Excellent for showing where something came from and where it went.

---

## 3.35 Alluvial Diagram

Similar to Sankey but particularly useful for movement between categories over several stages.

Example:

Customer segment 2024  
→ Customer segment 2025  
→ Customer segment 2026

Useful for changing states.

---

## 3.36 Funnel Visualisation

Use for sequential conversion processes.

Example:

10,000 visitors  
3,200 product views  
850 baskets  
410 checkouts  
370 purchases

Prefer proportional bars or stepped blocks rather than decorative funnel shapes if precise comparison matters.

Show conversion percentages between stages.

---

## 3.37 Network Graph

Use where relationships between entities are the important finding.

Nodes = entities

Edges = relationships

Examples:

- suppliers
- companies
- people
- systems
- APIs
- transactions

Node size may represent importance.

Edge thickness may represent relationship strength.

Use only when the network structure itself is analytically meaningful.

---

## 3.38 Choropleth Map

Colour geographic regions by a metric.

Examples:

- sales per capita
- unemployment rate
- incident rate
- voting percentage

Use normalised values such as percentages or rates where region sizes/populations differ.

Datawrapper identifies choropleth, symbol and locator maps as distinct geographical visualisation types.

---

## 3.39 Proportional Symbol Map

Display circles or other symbols on geographic locations.

Symbol size represents magnitude.

Useful for:

- airports
- stores
- cities
- incidents
- investments
- transactions

Prefer this to choropleths where the underlying observations occur at specific locations.

---

## 3.40 Geographic Flow Map

Use arrows or curved paths between places.

Examples:

Dublin → Dubai

Supplier → Airport

Origin → Destination

The thickness of the path can represent traffic or volume.

Useful for logistics, travel, migration and transaction analysis.

---

## 3.41 Timeline

Use for events rather than continuous numerical measurements.

Examples:

2019 Product launch  
2020 Acquisition  
2021 Regulation  
2022 Major incident  
2023 Platform migration

Include icons, annotation and significant values where useful.

---

## 3.42 Event-Annotated Time Series

Combine quantitative data with a timeline.

Example:

Stock price

with annotations showing:

- earnings
- acquisition
- regulatory announcement
- product launch

The reader should be able to connect events with changes in the metric.

---

## 3.43 Interactive Data Table

Tables should not be eliminated.

They should be improved.

Support:

- sorting
- filtering
- search
- sticky headers
- conditional formatting
- bars inside cells
- sparklines
- status indicators
- expandable detail
- highlighted maximum/minimum
- CSV download where appropriate

Datawrapper specifically supports tables containing embedded visual elements, and contemporary visualisation systems increasingly allow text, marks and data to be combined.

---

# 4. Editorial Presentation Modes

The same data can be presented differently depending upon where it appears in the article.

## 4.1 Hero Statistic

Large number occupying substantial page width.

Example:

# 73%

### of all incidents originated from just three systems.

Follow with a small supporting visual.

---

## 4.2 Annotated Graphic

Important charts should contain explanatory annotations directly on the graphic.

Instead of requiring the reader to interpret:

"Revenue increased sharply here."

Place an annotation at that point:

"Enterprise contract signed"

Annotations should explain significant:

- peaks
- drops
- crossings
- outliers
- threshold breaches
- inflection points

---

## 4.3 Insight Callout

Automatically identify an interesting result and combine the graphic with an editorial statement.

Example:

### One region accounts for almost half of the increase.

[graphic]

North America contributed 47% of the total year-on-year growth.

---

## 4.4 Comparison Card

Place two entities side-by-side.

Example:

### Broadcom vs NVIDIA

Revenue growth  
AVGO 23%  
NVDA 18%

Margins  
AVGO 61%  
NVDA 58%

Valuation  
AVGO 32x  
NVDA 37x

Include tiny comparison graphics rather than plain text where appropriate.

---

## 4.5 Visual Ranking

Use ranked cards containing:

1. Entity
2. Metric
3. mini-chart
4. rank movement
5. key contextual statistic

Useful for Top 5 / Bottom 5 analysis.

---

# 5. Scrollytelling

For long analytical articles, support scroll-driven storytelling.

Instead of displaying a complex chart immediately, reveal the analytical argument progressively.

Example:

### Scroll stage 1

Show total revenue.

### Stage 2

Split revenue into business segments.

### Stage 3

Highlight the segment creating most growth.

### Stage 4

Reveal geographic performance.

### Stage 5

Highlight the major anomaly.

The chart remains fixed while its visual state changes as the user scrolls.

Modern data-storytelling platforms use this technique to allow charts, timelines and maps to progressively change as an article advances.

Use scrollytelling only where there is genuinely a sequence to explain.

---

# 6. Interaction Requirements

Where appropriate, graphics should support:

### Hover

Display exact values and supporting context.

### Highlight

Hovering one entity should mute unrelated entities.

### Crosshair

Useful for detailed time-series analysis.

### Filtering

Allow:

- date
- region
- product
- category
- scenario

### Toggle

Examples:

Absolute | Percentage

Monthly | Quarterly | Annual

Revenue | Growth

Bull | Base | Bear

### Zoom

Use for dense time-series or geographic information.

### Drill-down

Click a treemap, map or hierarchical graphic to reveal lower levels.

### Linked graphics

Selecting a region on one graphic may update another graphic.

Observable Plot currently provides pointer, tooltip and crosshair interactions, while Vega-Lite provides declarative selections and interactive multi-view visualisations.

---

# 7. Automatic Visualisation Selection Engine

Implement a `visualisationSelector()` layer.

It should inspect metadata about the analytical result before rendering.

Suggested input:

```json
{
  "question": "How has market share changed?",
  "dataType": "time_series",
  "dimensions": ["company", "year"],
  "measures": ["market_share"],
  "primaryMessage": "ranking_change",
  "observationCount": 48
}
```

The selector could return:

```json
{
  "visualisation": "bump_chart",
  "reason": "The primary insight concerns changes in ranking over time.",
  "interaction": ["tooltip", "highlight"],
  "annotation": true
}
```

---

# 8. Selection Rules

Use approximately the following hierarchy.

### One important value

Use:

KPI card  
Hero statistic  
KPI + sparkline

### Compare categories

Use:

Dot plot  
Lollipop  
Bar  
Small multiples

### Compare two states

Use:

Dumbbell  
Arrow chart  
Slopegraph

### Change over time

Use:

Line chart  
Area difference  
Small multiples  
Bump chart  
Event-annotated timeline

### Distribution

Use:

Histogram  
Density  
Box plot  
Beeswarm  
Ridgeline

### Relationship

Use:

Scatter  
Quadrant scatter  
Bubble  
Hexbin

### Part of whole

Use:

Treemap  
Waffle  
Stacked bar  
100% stacked bar

Pie/donut should be a secondary option.

### Flow

Use:

Sankey  
Alluvial  
Funnel  
Geographic flow map

### Hierarchy

Use:

Treemap  
Sunburst  
Tree/network

### Geography

Use:

Choropleth  
Symbol map  
Flow map

### Progress against target

Use:

Bullet chart  
Progress bar

### Sequential explanation

Use:

Scrollytelling  
Timeline  
Annotated graphic

---

# 9. Visualisation Composition

Do not assume that one chart equals one insight.

Modern graphics can consist of multiple visual layers.

For example:

Stock price line  
+ earnings markers  
+ analyst target band  
+ moving average  
+ recession/background region  
+ key annotations

Observable Plot constructs visualisations by layering marks rather than requiring every graphic to belong to one rigid chart type. Vega-Lite similarly supports layering, faceting and multi-view composition.

The system should therefore support a visualisation composed of:

`base mark + context + emphasis + annotation + interaction`

rather than simply:

`chart type = line`

---

# 10. Design Rules

Every graphic must have:

### Insight-led title

BAD:

"Revenue 2021-2026"

GOOD:

"Revenue growth accelerated sharply after 2024"

### Optional subtitle

Explain the measurement or comparison.

### Direct labels

Prefer labels beside important data rather than requiring repeated movement between chart and legend.

### Source

Where applicable.

### Units

Never leave units ambiguous.

### Context

Where useful include:

- average
- target
- previous period
- benchmark
- historical range

### Annotation

Highlight important points.

---

# 11. Colour Rules

Colour must communicate meaning.

Use one strong accent colour to identify the main analytical subject.

Use muted colours for context.

Reserve semantic colours for established meanings:

- positive
- negative
- warning
- neutral

Do not create rainbow charts merely to distinguish categories.

Do not rely on colour alone to convey important information.

---

# 12. Animation Rules

Animation should explain change.

Good:

- bars smoothly reorder after filtering
- lines reveal chronologically
- Sankey flow appears progressively
- map transitions to selected region
- scrollytelling advances through analytical stages

Bad:

- charts bouncing
- decorative spinning
- numbers constantly counting
- animation every time the user scrolls past a graphic

Respect `prefers-reduced-motion`.

---

# 13. Mobile Behaviour

Every graphic must have a mobile-specific layout.

Do not merely shrink desktop charts.

Possible transformations:

Desktop grouped chart → mobile small multiples

Desktop horizontal comparison → mobile vertical comparison

Large legend → direct labels

Dense scatter → simplified highlighted scatter

Complex table → horizontally scrollable or card view

All text must remain readable without pinch zoom.

---

# 14. Accessibility

Every visualisation must provide:

- textual title
- explanatory subtitle
- accessible description
- keyboard-accessible interaction where applicable
- sufficient contrast
- non-colour indicators
- reduced-motion support
- underlying values or alternative data representation where practical

---

# 15. Recommended Rendering Architecture

Use a layered approach rather than attempting to build every visualisation manually.

### Primary

**Observable Plot**

Use for the majority of article graphics.

It supports layered marks, facets, geographic projections, transforms, tooltips, crosshairs and many statistical/data marks.

### Declarative/complex charts

**Vega-Lite**

Use where a JSON-based visualisation grammar is beneficial.

Vega-Lite supports filtering, aggregation, faceting, layering, repeated views and interactive selections. As of 2026, the current documentation identifies Vega-Lite 6.4.3.

### Bespoke graphics

**D3**

Use when a genuinely custom graphical treatment, layout or interaction is required.

Do not use raw D3 for simple charts that can be produced more maintainably using the higher-level visualisation layer.

---

# 16. Visualisation Registry

Create a reusable internal registry.

Example:

```javascript
visualisations = {
    kpi: {},
    sparkline: {},
    bullet: {},
    lollipop: {},
    dotPlot: {},
    dumbbell: {},
    rangePlot: {},
    arrowPlot: {},
    slopegraph: {},
    bumpChart: {},
    smallMultiples: {},
    line: {},
    indexedLine: {},
    areaDifference: {},
    waterfall: {},
    divergingBar: {},
    likert: {},
    heatmap: {},
    calendarHeatmap: {},
    cohortHeatmap: {},
    histogram: {},
    density: {},
    ridgeline: {},
    boxPlot: {},
    violin: {},
    beeswarm: {},
    scatter: {},
    quadrantScatter: {},
    bubble: {},
    hexbin: {},
    waffle: {},
    treemap: {},
    sunburst: {},
    sankey: {},
    alluvial: {},
    funnel: {},
    network: {},
    choropleth: {},
    symbolMap: {},
    flowMap: {},
    timeline: {}
}
```

Each registry entry should define:

```javascript
{
    id,
    analyticalPurpose,
    supportedDataShapes,
    minimumObservations,
    maximumRecommendedObservations,
    renderer,
    responsiveBehaviour,
    interactionOptions,
    annotationSupport,
    accessibilityFallback
}
```

---

# 17. Analytical Insight Engine

Before rendering, calculate potentially interesting characteristics of the data.

Look for:

- largest value
- smallest value
- biggest increase
- biggest decrease
- fastest growth
- trend reversal
- outlier
- threshold crossing
- rank movement
- concentration
- correlation
- unusual distribution
- variance
- acceleration/deceleration
- historical high
- historical low
- convergence
- divergence

Pass these findings into the visualisation renderer.

The graphic should then visually emphasise the analytical finding.

---

# 18. Example

Input:

```text
Company revenue by segment, 2022-2026.
Cloud revenue increased 77%.
Hardware declined 18%.
Services remained approximately flat.
```

Do NOT automatically create:

three equally coloured lines.

Consider instead:

### Main graphic

Small multiples showing each segment.

### Highlight

Cloud displayed prominently.

### Annotation

"+77% since 2022"

### Secondary annotation

"Hardware is the only segment to contract."

### Supporting KPI

Cloud now represents 42% of revenue.

The result should resemble an editorial analytical story, rather than the default output of a spreadsheet application.

---

# 19. Anti-Patterns

Avoid unless specifically justified:

- 3D charts
- exploded pie charts
- excessive donuts
- speedometer gauges
- decorative infographics without analytical value
- rainbow palettes
- more than approximately five competing line colours
- huge legends
- unexplained dual axes
- unnecessary animation
- truncated axes designed to exaggerate differences
- visual effects that obscure values
- excessive dashboard-style card grids inside articles

An article is not a dashboard.

The graphic should support the narrative surrounding it.

---

# 20. Final Requirement

The visualisation system should behave like an **editorial data designer**, not a chart generator.

The workflow must be:

```text
DATA
  ↓
ANALYTICAL QUESTION
  ↓
INSIGHT DETECTION
  ↓
VISUAL RELATIONSHIP
  ↓
VISUALISATION SELECTION
  ↓
ANNOTATION
  ↓
INTERACTION
  ↓
RESPONSIVE ARTICLE GRAPHIC
```

The primary success criterion is:

> A reader should understand the important analytical finding before they have finished reading the accompanying paragraph.

Novelty is secondary to clarity.

However, where several visualisations communicate the information equally well, favour the more engaging editorial treatment rather than repeatedly using conventional bar, pie and line charts.