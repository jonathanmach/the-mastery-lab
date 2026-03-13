import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:powersync/powersync.dart';

const _backendUrl = 'http://localhost:6060';
const _userId = 'user1';

class AppBackendConnector extends PowerSyncBackendConnector {
  final PowerSyncDatabase db;

  AppBackendConnector(this.db);

  @override
  Future<PowerSyncCredentials?> fetchCredentials() async {
    final response = await http.post(
      Uri.parse('$_backendUrl/api/auth/token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': _userId}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to get token: ${response.statusCode}');
    }

    final data = jsonDecode(response.body);
    return PowerSyncCredentials(
      endpoint: data['powersync_url'],
      token: data['token'],
      expiresAt: PowerSyncCredentials.getExpiryDate(data['token']),
    );
  }

  @override
  Future<void> uploadData(PowerSyncDatabase database) async {
    CrudBatch? batch;
    while ((batch = await database.getCrudBatch()) != null) {
      for (final entry in batch!.crud) {
        final uri = Uri.parse('$_backendUrl/api/data/${entry.table}/${entry.id}');
        final headers = {'Content-Type': 'application/json'};

        http.Response response;
        switch (entry.op) {
          case UpdateType.put:
            response = await http.put(
              uri,
              headers: headers,
              body: jsonEncode(entry.opData),
            );
            break;
          case UpdateType.patch:
            response = await http.patch(
              uri,
              headers: headers,
              body: jsonEncode(entry.opData),
            );
            break;
          case UpdateType.delete:
            response = await http.delete(uri);
            break;
        }

        if (response.statusCode != 200) {
          throw Exception(
            '${entry.op} ${entry.table}/${entry.id} failed: ${response.statusCode} ${response.body}',
          );
        }
      }
      await batch.complete();
    }
  }
}
