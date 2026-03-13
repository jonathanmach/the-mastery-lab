import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:powersync/powersync.dart';

import '../models/schema.dart';
import 'backend_connector.dart';

late PowerSyncDatabase db;

Future<void> openDatabase() async {
  final dir = await getApplicationSupportDirectory();
  final path = join(dir.path, 'powersync-todo.db');

  db = PowerSyncDatabase(schema: schema, path: path);
  await db.initialize();

  final connector = AppBackendConnector(db);
  db.connect(connector: connector);
}
