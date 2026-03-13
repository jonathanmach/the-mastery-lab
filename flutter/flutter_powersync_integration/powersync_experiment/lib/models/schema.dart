import 'package:powersync/powersync.dart';

/// Client-side PowerSync schema matching the Postgres tables.
/// Note: 'id' column is auto-created by PowerSync — do not declare it.
const schema = Schema([
  Table('lists', [
    Column.text('name'),
    Column.text('owner_id'),
    Column.text('created_at'),
  ]),
  Table('todos', [
    Column.text('list_id'),
    Column.text('description'),
    Column.integer('completed'), // SQLite has no bool; 0 = false, 1 = true
    Column.text('created_at'),
  ], indexes: [
    Index('by_list', [IndexedColumn('list_id')]),
  ]),
]);
