# Multi-database support via connector abstraction

The spec model (`Specification`, `User`, `Group`, `Privilege`) and the plan engine (`admin.py`) are database-agnostic. Database-specific behaviour — catalog queries, connection setup, password type handling — is isolated in a `DatabaseConnector` subclass. Adding a new database target means implementing a new connector, not forking the tool or building a SQL dialect layer.

We considered two alternatives: a separate tool per database (simpler, no abstraction needed) and a dialect-aware SQL generation layer (more flexible, but the SQL redtape emits is nearly identical across Redshift and Postgres). The connector-only approach was chosen because the SQL generation is already 95% standard Postgres SQL; the divergence is entirely in how you read the current state from system catalog views.
