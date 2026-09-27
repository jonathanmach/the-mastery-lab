A good way to understand Dagster as a backend engineer is:

> **Dagster is an application framework/runtime for defining, running, observing, and scheduling data-producing computations.**

The important shift is that instead of primarily thinking about **requests → services → database**, you think about **data assets → dependencies → materialization**.

Dagster itself describes the product as a data orchestrator with lineage, observability, a declarative model, and testing support. ([Dagster Docs][1])

## 1. Start with a familiar Orders / Products system

Imagine your normal application database:

```text
Postgres

products
--------
id
name
category
price

orders
------
id
customer_id
created_at

order_items
-----------
order_id
product_id
quantity
unit_price
```

Your application might serve:

```http
POST /orders
GET /orders/:id
GET /products/:id
```

This is operational software.

Your database exists primarily because your application needs to **run the business**.

Now someone asks:

> "How much revenue did each product category generate yesterday?"

You *could* run:

```sql
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price)
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.created_at >= ...
GROUP BY p.category;
```

But eventually you get 50 questions like this:

* daily revenue
* top products
* revenue by country
* customer lifetime value
* weekly active customers
* refunds
* conversion funnels
* dashboards
* ML features

Running increasingly complicated queries directly against the production database becomes undesirable.

This is where data engineering begins.

---

# 2. A very simple data pipeline

Suppose we create an analytics database.

Conceptually:

```text
            Application DB
                  │
                  │ extract
                  ▼
             raw_orders
                  │
                  │ clean
                  ▼
            clean_orders
                  │
                  ├──────────────┐
                  ▼              ▼
        daily_revenue     product_sales
                               │
                               ▼
                     category_revenue
```

Each box represents **some useful data that exists somewhere**.

For example:

```text
raw_orders
```

might be a table in your analytics database:

```sql
analytics.raw_orders
```

And:

```text
category_revenue
```

could contain:

| date       | category    | revenue |
| ---------- | ----------- | ------: |
| 2026-09-23 | Books       |   12452 |
| 2026-09-23 | Electronics |   38442 |

Dagster's key abstraction for these things is an **asset**.

---

# 3. Asset is the concept to understand first

Ignore jobs, ops, sensors and schedules for the moment.

An asset is basically:

> **A piece of persistent data that your pipeline knows how to produce.**

Examples:

```text
raw_orders
clean_orders
products
product_sales
daily_revenue
category_revenue
```

An asset can correspond to:

* a database table
* a file
* a CSV
* a Parquet dataset
* an S3 object
* a dbt model
* an ML model
* basically any persistent data artifact

A Dagster function describes **how that asset is produced**.

Very simplified:

```python
import dagster as dg


@dg.asset
def products():
    ...
```

This function means:

> Dagster knows there is an asset called `products`, and this code produces it.

Dagster's current getting-started documentation uses this asset-oriented model as the basic way of constructing pipelines. ([Dagster Docs][2])

---

# 4. Dependencies are surprisingly natural

Now:

```python
@dg.asset
def products():
    return [
        {"id": 1, "name": "Keyboard", "category": "Electronics"},
        {"id": 2, "name": "Clean Code", "category": "Books"},
    ]


@dg.asset
def orders():
    return [
        {"id": 100, "product_id": 1, "quantity": 2},
        {"id": 101, "product_id": 2, "quantity": 1},
    ]


@dg.asset
def product_sales(orders, products):
    ...
```

Notice this:

```python
def product_sales(orders, products):
```

Dagster understands:

```text
orders ──────┐
             ├──> product_sales
products ────┘
```

because `product_sales` depends on those assets.

That's your **data lineage graph**.

Dagster can display that graph in its UI and track materializations of the assets. ([Dagster Docs][3])

This is one of the most important ideas in Dagster.

---

# 5. Materialization

You'll constantly encounter the word:

> **materialize**

It's basically:

> Run the computation required to produce/update this asset.

If you click:

```text
Materialize product_sales
```

Dagster runs the code associated with that asset.

If necessary, you could materialize an entire graph:

```text
products
   \
    ── product_sales ── category_revenue
   /
orders
```

So:

```text
definition          runtime event
-----------         -------------
@asset              materialize
```

You **define** an asset.

You **materialize** its value.

Dagster also records metadata around these materializations, which is why it can give you history, lineage and observability rather than merely executing a Python script.

---

# 6. Let's make the example slightly more realistic

Instead of returning Python arrays, imagine Postgres.

We have:

```text
production Postgres
```

and:

```text
analytics Postgres
```

Our pipeline could be:

```text
production.orders
        │
        ▼
analytics.raw_orders
        │
        ▼
analytics.clean_orders
        │
        ├─────────────────────┐
        ▼                     ▼
analytics.daily_revenue   analytics.product_sales
                                   │
                                   ▼
                         analytics.category_sales
```

Your Dagster asset might effectively do:

```python
@dg.asset
def raw_orders(prod_db, analytics_db):
    rows = prod_db.execute(
        "SELECT * FROM orders"
    )

    analytics_db.write(
        "raw_orders",
        rows,
    )
```

The output isn't really:

```python
rows
```

The important output is:

```text
analytics.raw_orders
```

This distinction becomes important.

Dagster isn't merely:

```text
function orchestrator
```

It's trying to model:

```text
data lifecycle
```

---

# 7. This is where `resources` come in

You're probably already thinking:

> I don't want database connection creation scattered throughout my assets.

Correct.

Dagster has **resources** for infrastructure/external dependencies.

Think dependency injection:

```python
class ProductionDatabase:
    ...

class AnalyticsDatabase:
    ...
```

Then conceptually:

```python
@dg.asset
def raw_orders(
    prod_db: ProductionDatabase,
    warehouse: AnalyticsDatabase,
):
    ...
```

You configure those resources centrally.

As a backend engineer, a reasonable mental mapping is:

| Backend concept         | Dagster concept   |
| ----------------------- | ----------------- |
| domain/service function | asset computation |
| dependency injection    | resource          |
| database/client         | resource          |
| dependency graph        | asset graph       |
| request execution       | run               |
| cron                    | schedule          |
| event listener          | sensor            |
| admin/observability UI  | Dagster UI        |

It's not exact, but it's useful.

---

# 8. What does Dagster actually do?

This is worth separating.

Suppose you write:

```python
@dg.asset
def category_revenue():
    run_sql(...)
```

Dagster itself isn't magically transforming the database.

**Your Python/SQL/dbt/Spark/etc. performs the computation.**

Dagster provides orchestration around it:

```text
               Dagster

        ┌────────────────────┐
        │ dependency graph   │
        │ scheduling         │
        │ retries            │
        │ execution          │
        │ logging            │
        │ metadata           │
        │ lineage            │
        │ observability      │
        │ backfills          │
        │ failure handling   │
        └─────────┬──────────┘
                  │
                  ▼
       Your actual computation

       Python / SQL / dbt
       Spark / APIs / etc.
```

So if you've used:

```text
Celery
cron
GitHub Actions
Airflow
Kubernetes Jobs
```

you've encountered pieces of the problem Dagster addresses.

Dagster specifically models those executions around **data assets and their relationships**.

---

# 9. Why not just write a Python script?

You absolutely could.

Perhaps:

```python
def main():
    load_orders()
    clean_orders()
    calculate_product_sales()
    calculate_category_revenue()
```

And:

```bash
cron: 0 2 * * * python pipeline.py
```

This is basically Pipeline v0.

But now ask:

```text
Did yesterday's load succeed?

Which exact step failed?

Can I rerun only product_sales?

What depends on product_sales?

When was category_revenue last updated?

What happens if products succeeds but orders fails?

Can I retry only failed work?

Can I process January again?

Can I inspect logs from February 13?

Can I run production differently from local?

Can I tell whether downstream data is stale?
```

You gradually end up implementing an orchestration system.

Dagster gives you those primitives.

---

# 10. Assets vs jobs

This often confuses newcomers.

Start with:

```text
Asset = WHAT data exists

Job = WHICH computations should run together
```

For example, your complete asset graph could contain:

```text
raw_orders
raw_products
clean_orders
clean_products
daily_sales
monthly_sales
customer_metrics
marketing_metrics
fraud_features
```

But you might define:

```text
daily_sales_job
```

to select:

```text
raw_orders
clean_orders
daily_sales
```

A job is therefore closer to:

> **an executable selection of your computation graph.**

Dagster supports defining jobs over selections of assets, including dependency-based selections. ([Dagster Docs][4])

Initially, though, I'd recommend you mostly ignore explicit jobs.

Build assets first.

---

# 11. Schedules

Suppose we want:

```text
daily_revenue
```

updated every day at 02:00.

A **schedule** says roughly:

```text
run this job every day at 02:00
```

Conceptually:

```python
daily_schedule = dg.ScheduleDefinition(
    job=daily_sales_job,
    cron_schedule="0 2 * * *",
)
```

Nothing especially mysterious there.

Dagster's daemon is responsible for features including schedules and sensors in an OSS deployment. ([Dagster Docs][3])

---

# 12. Sensors

Sensors are more interesting.

A schedule says:

```text
WHEN clock == 02:00
    run pipeline
```

A sensor says something closer to:

```text
WHEN something happens
    run pipeline
```

Imagine orders arrive as files:

```text
s3://orders/2026-09-21.csv
s3://orders/2026-09-22.csv
s3://orders/2026-09-23.csv
```

A sensor might notice:

```text
new file arrived
```

and trigger processing.

Conceptually:

```text
S3
 │
 │ new object
 ▼
sensor
 │
 ▼
Dagster run
 │
 ▼
raw_orders
 │
 ▼
clean_orders
```

You probably won't need sensors for your first experiment.

---

# 13. Partitions — extremely important in data engineering

Now imagine:

```text
daily_orders
```

You don't really have one monolithic dataset.

Logically you have:

```text
orders / 2026-09-21
orders / 2026-09-22
orders / 2026-09-23
orders / 2026-09-24
```

These are **partitions**.

You might define:

```python
daily = dg.DailyPartitionsDefinition(
    start_date="2026-01-01"
)
```

and:

```python
@dg.asset(partitions_def=daily)
def daily_orders(context):
    date = context.partition_key

    ...
```

Now Dagster understands independently:

```text
daily_orders[2026-09-21] ✓
daily_orders[2026-09-22] ✓
daily_orders[2026-09-23] ✗
daily_orders[2026-09-24] -
```

This lets you say:

> Recompute September 1–10.

That's called a **backfill**.

For many real pipelines, partitions are one of the things that transform orchestration from "cron running Python" into something substantially more useful.

---

# 14. Your first pipeline should be much simpler

I'd build this:

```text
orders.csv       products.csv
     │                │
     ▼                ▼
   orders          products
      \              /
       \            /
        ▼          ▼
         product_sales
               │
               ▼
        category_revenue
```

Directory:

```text
orders_dagster/
├── pyproject.toml
├── data/
│   ├── orders.csv
│   └── products.csv
└── src/
    └── orders_dagster/
        ├── definitions.py
        └── defs/
            └── assets.py
```

You could scaffold the current Dagster project with:

```bash
uvx create-dagster@latest project orders-dagster
cd orders-dagster
source .venv/bin/activate
```

The current Dagster quickstart recommends Python 3.10+ and uses `uvx create-dagster@latest project ...`; local development runs with `dg dev`. ([Dagster Docs][2])

---

# 15. Our actual data

`products.csv`:

```csv
id,name,category
1,Keyboard,Electronics
2,Mouse,Electronics
3,Clean Code,Books
```

`orders.csv`:

```csv
id,product_id,quantity,unit_price
100,1,2,80
101,2,1,30
102,3,3,25
103,1,1,80
```

Now:

```python
import dagster as dg
import pandas as pd


@dg.asset
def products() -> pd.DataFrame:
    return pd.read_csv("data/products.csv")


@dg.asset
def orders() -> pd.DataFrame:
    return pd.read_csv("data/orders.csv")


@dg.asset
def product_sales(
    orders: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    sales = orders.merge(
        products,
        left_on="product_id",
        right_on="id",
    )

    sales["revenue"] = (
        sales["quantity"] * sales["unit_price"]
    )

    return sales


@dg.asset
def category_revenue(
    product_sales: pd.DataFrame,
) -> pd.DataFrame:
    return (
        product_sales
        .groupby("category")["revenue"]
        .sum()
        .reset_index()
    )
```

Conceptually, you've just declared:

```text
products ─────┐
              │
              ▼
          product_sales ────> category_revenue
              ▲
              │
orders ───────┘
```

That graph is probably the first moment where Dagster will "click."

---

# 16. Then run Dagster

Current Dagster local development uses:

```bash
dg dev
```

which starts the webserver and daemon; the UI will normally be available on port 3000. ([Dagster Docs][3])

You'll see something along the lines of:

```text
Assets

orders
products
product_sales
category_revenue
```

and Dagster can show their lineage.

Select:

```text
category_revenue
```

and materialize the graph.

Then you can inspect:

```text
Run
  ✓ products
  ✓ orders
  ✓ product_sales
  ✓ category_revenue
```

alongside logs and timings.

That is your first real Dagster pipeline.

---

# 17. One important subtlety

Our example does:

```python
return pd.DataFrame(...)
```

That's useful for learning.

But a production pipeline often looks more like:

```python
@dg.asset
def product_sales(warehouse):
    warehouse.execute("""
        CREATE OR REPLACE TABLE product_sales AS
        SELECT ...
    """)
```

The actual asset is:

```text
warehouse.product_sales
```

not necessarily the Python return value.

Dagster can also use **IO managers**, which handle storing/loading asset values so your asset code doesn't need to manually decide where every intermediate DataFrame goes.

Eventually your mental model becomes:

```text
            Asset definition

             product_sales
                   │
        ┌──────────┴───────────┐
        │                      │
     compute                 storage
        │                      │
       SQL                 IO Manager
     Python                   │
      dbt                     ▼
       ...               Postgres / S3
```

I'd intentionally postpone IO managers until your second iteration.

---

# 18. Where ETL fits

You'll see:

```text
ETL
```

constantly.

It simply means:

```text
Extract
Transform
Load
```

For example:

```text
Extract
production DB
     │
     ▼
raw_orders

Transform
raw_orders
     │
     ▼
clean_orders

Load
clean_orders
     │
     ▼
analytics.orders
```

Modern data systems also often use:

```text
ELT

Extract
Load
Transform
```

because powerful warehouses like BigQuery/Snowflake/etc. make it practical to load relatively raw data first and transform it using SQL afterward.

Dagster can orchestrate either architecture.

---

# 19. Dagster isn't your data warehouse

Another important separation:

```text
Dagster       = orchestrator
Postgres      = database
S3            = object storage
BigQuery      = warehouse
dbt           = transformation framework
Spark         = compute engine
```

They can work together:

```text
                 Dagster
                    │
       orchestrates all of this
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        Python     dbt      Spark
          │         │         │
          └─────────┼─────────┘
                    ▼
                BigQuery
```

Dagster isn't trying to replace all those systems.

---

# 20. The backend analogy I'd keep in your head

With a normal backend, you tend to reason:

```text
HTTP request
    │
    ▼
controller
    │
    ▼
service
    │
    ▼
repository
    │
    ▼
database
```

With Dagster, reason:

```text
Desired data asset
       │
       ▼
What does it depend on?
       │
       ▼
What computes it?
       │
       ▼
Where is it stored?
       │
       ▼
When should it recompute?
```

So the dependency direction becomes especially important.

Rather than:

> "Run script A, then script B, then script C."

Dagster encourages:

> "`category_revenue` depends on `product_sales`, which depends on `orders` and `products`."

```text
imperative orchestration

A()
B()
C()


        ↓


declarative data graph

A ──┐
    ├──> C
B ──┘
```

Dagster figures out the appropriate execution topology from that graph.

That's probably the single most useful conceptual distinction.

---

## The vocabulary I'd learn in this order

Don't try to digest the entire Dagster documentation. For your first pipeline, learn:

1. **Asset** — data you care about.
2. **Materialization** — producing/updating an asset.
3. **Asset dependency / lineage** — what data depends on what.
4. **Resource** — external dependency such as Postgres/S3/API.
5. **Run** — one execution.
6. **Job** — executable selection/group of computations.
7. **Schedule** — time-based execution.
8. **Partition** — divide an asset by date/key/etc.
9. **Backfill** — compute many missing/historical partitions.
10. **Sensor** — trigger runs based on external events.

You don't need most of Dagster to build something useful.

### A good learning project

Given your backend background, I would **not** start with Snowflake/dbt/Kafka/Spark. That introduces four new concepts for every one Dagster concept.

Build this progression:

```text
Iteration 1
CSV → Pandas → assets
Learn:
assets / lineage / runs / UI

        ↓

Iteration 2
Postgres → Postgres
Learn:
resources / persistence

        ↓

Iteration 3
Daily orders
Learn:
partitions / backfills

        ↓

Iteration 4
Run automatically every morning
Learn:
jobs / schedules

        ↓

Iteration 5
New order export arrives
Learn:
sensors
```

After those five steps, you'll understand the core of Dagster rather than just knowing its API.

And the first practical target is very small:

```text
orders + products
       │
       ▼
 product_sales
       │
       ▼
category_revenue
```

If you can build that, run it through `dg dev`, deliberately make `product_sales` fail, inspect the failed run, fix it and rematerialize it, you've already learned a surprisingly large part of the Dagster mental model. ([Dagster Docs][2])

[1]: https://docs.dagster.io/?utm_source=chatgpt.com "Overview | Dagster Docs"
[2]: https://docs.dagster.io/getting-started/quickstart?utm_source=chatgpt.com "Build your first Dagster pipeline | Dagster Docs"
[3]: https://docs.dagster.io/guides/operate/webserver?utm_source=chatgpt.com "Dagster webserver and UI | Dagster Docs"
[4]: https://docs.dagster.io/guides/build/assets/asset-selection-syntax/examples?utm_source=chatgpt.com "Asset selection examples | Dagster Docs"
