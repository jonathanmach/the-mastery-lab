import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import 'powersync/powersync.dart';

const _defaultListId = '00000000-0000-0000-0000-000000000001';
const _uuid = Uuid();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await openDatabase();
  runApp(const TodoApp());
}

class TodoApp extends StatelessWidget {
  const TodoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PowerSync Todo',
      theme: ThemeData(
        colorSchemeSeed: Colors.blue,
        useMaterial3: true,
      ),
      home: const TodoListPage(),
    );
  }
}

class TodoListPage extends StatefulWidget {
  const TodoListPage({super.key});

  @override
  State<TodoListPage> createState() => _TodoListPageState();
}

class _TodoListPageState extends State<TodoListPage> {
  final _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _ensureDefaultList();
  }

  Future<void> _ensureDefaultList() async {
    final existing = await db.getOptional(
      'SELECT id FROM lists WHERE id = ?',
      [_defaultListId],
    );
    if (existing == null) {
      await db.execute(
        'INSERT INTO lists (id, name, owner_id) VALUES (?, ?, ?)',
        [_defaultListId, 'My List', 'user1'],
      );
    }
  }

  Future<void> _addTodo() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    await db.execute(
      'INSERT INTO todos (id, list_id, description, completed) VALUES (?, ?, ?, ?)',
      [_uuid.v4(), _defaultListId, text, 0],
    );
    _controller.clear();
  }

  Future<void> _toggleTodo(String id, int currentValue) async {
    await db.execute(
      'UPDATE todos SET completed = ? WHERE id = ?',
      [currentValue == 0 ? 1 : 0, id],
    );
  }

  Future<void> _deleteTodo(String id) async {
    await db.execute('DELETE FROM todos WHERE id = ?', [id]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PowerSync Todo')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Add a todo...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _addTodo(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _addTodo,
                  icon: const Icon(Icons.add),
                ),
              ],
            ),
          ),
          Expanded(
            child: StreamBuilder(
              stream: db.watch(
                'SELECT * FROM todos WHERE list_id = ? ORDER BY created_at DESC',
                parameters: [_defaultListId],
              ),
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                }
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }

                final rows = snapshot.data!;
                if (rows.isEmpty) {
                  return const Center(
                    child: Text('No todos yet. Add one above!'),
                  );
                }

                return ListView.builder(
                  itemCount: rows.length,
                  itemBuilder: (context, index) {
                    final row = rows[index];
                    final id = row['id'] as String;
                    final description = row['description'] as String;
                    final completed = row['completed'] as int;

                    return ListTile(
                      leading: Checkbox(
                        value: completed == 1,
                        onChanged: (_) => _toggleTodo(id, completed),
                      ),
                      title: Text(
                        description,
                        style: completed == 1
                            ? const TextStyle(
                                decoration: TextDecoration.lineThrough,
                                color: Colors.grey,
                              )
                            : null,
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline),
                        onPressed: () => _deleteTodo(id),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
