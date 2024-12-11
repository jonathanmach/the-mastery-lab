## Objective

The goal of this experiment is to enable a smooth and incremental transition from PeeweeORM to SQLAlchemy in an existing Python test suite. Previously, all tests relied on Peewee’s approach: start a transaction before the test, run the necessary database operations, and then roll it back, ensuring that each test remains isolated and leaves the database state clean. Now, as the codebase gradually adopts SQLAlchemy, it’s crucial to maintain the same testing strategy without rewriting all of the test infrastructure at once.

By figuring out how to share a single transaction across both PeeweeORM and SQLAlchemy, we want to confirm that database operations performed by either ORM will be visible within the same transactional context.

This approach allows parts of the code still using Peewee and newer parts that rely on SQLAlchemy to coexist, all while retaining the benefits of transactional tests. The end result is a testing setup that supports a phased migration, maintains consistent isolation, and reduces the risk of introducing subtle differences between tests as the underlying ORM changes.