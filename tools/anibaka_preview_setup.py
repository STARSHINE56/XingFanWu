import json
import shutil
from pathlib import Path


ROOT = Path.cwd()
ANIBAKA_SOURCE = Path("/tmp/AniBakaRule")

ASSET_ROOT = ROOT / "assets" / "anibaka"
ASSET_RULES = ASSET_ROOT / "rules"

PUBSPEC = ROOT / "pubspec.yaml"

PLUGIN_MODULE = (
    ROOT
    / "lib"
    / "pages"
    / "plugin_editor"
    / "plugin_module.dart"
)

PLUGIN_VIEW = (
    ROOT
    / "lib"
    / "pages"
    / "plugin_editor"
    / "plugin_view_page.dart"
)

ANIBAKA_PAGE = (
    ROOT
    / "lib"
    / "pages"
    / "plugin_editor"
    / "anibaka_preview_page.dart"
)


def log(message: str):
    print(f"[AniBaka] {message}")


def require_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"找不到文件：{path}"
        )


def prepare_assets():
    log("准备 AniBaka 规则资源")

    if not ANIBAKA_SOURCE.exists():
        raise FileNotFoundError(
            "找不到 /tmp/AniBakaRule，"
            "请确认工作流已经克隆 AniBakaRule"
        )

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)

    ASSET_RULES.mkdir(
        parents=True,
        exist_ok=True,
    )

    rules = []

    json_files = sorted(
        ANIBAKA_SOURCE.glob("*.json")
    )

    for source_file in json_files:
        if source_file.name == "index.json":
            continue

        try:
            data = json.loads(
                source_file.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as error:
            log(
                f"跳过无法解析的规则 "
                f"{source_file.name}: {error}"
            )
            continue

        if not isinstance(data, dict):
            continue

        if data.get("format") != "anx-rule/2":
            continue

        target_file = (
            ASSET_RULES
            / source_file.name
        )

        shutil.copy2(
            source_file,
            target_file,
        )

        rules.append(
            {
                "id": str(
                    data.get(
                        "id",
                        source_file.stem,
                    )
                ),
                "name": str(
                    data.get(
                        "name",
                        source_file.stem,
                    )
                ),
                "baseUrl": str(
                    data.get(
                        "baseUrl",
                        "",
                    )
                ),
                "description": str(
                    data.get(
                        "description",
                        "",
                    )
                ),
                "iconUrl": str(
                    data.get(
                        "iconUrl",
                        "",
                    )
                ),
                "file": source_file.name,
            }
        )

    manifest = {
        "format": "xingfanwu-anibaka-preview/1",
        "count": len(rules),
        "rules": rules,
    }

    manifest_path = (
        ASSET_ROOT
        / "manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    log(
        f"已识别 {len(rules)} 条 "
        "anx-rule/2 规则"
    )

    for rule in rules:
        log(
            f"{rule['name']} | "
            f"{rule['baseUrl']}"
        )


def patch_pubspec():
    log("修改 pubspec.yaml")

    require_file(PUBSPEC)

    text = PUBSPEC.read_text(
        encoding="utf-8"
    )

    asset_root_line = (
        "    - assets/anibaka/\n"
    )

    asset_rules_line = (
        "    - assets/anibaka/rules/\n"
    )

    if (
        asset_root_line in text
        and asset_rules_line in text
    ):
        log(
            "AniBaka assets 已存在，"
            "跳过"
        )
        return

    marker = "  assets:\n"

    if marker not in text:
        raise RuntimeError(
            "pubspec.yaml 中没有找到 "
            "flutter assets 配置"
        )

    additions = ""

    if asset_root_line not in text:
        additions += asset_root_line

    if asset_rules_line not in text:
        additions += asset_rules_line

    text = text.replace(
        marker,
        marker + additions,
        1,
    )

    PUBSPEC.write_text(
        text,
        encoding="utf-8",
    )

    log(
        "已加入 AniBaka assets"
    )


def write_anibaka_page():
    log(
        "创建 AniBaka 规则预览页面"
    )

    ANIBAKA_PAGE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = r'''
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:kazumi/bean/settings/settings_detail_scaffold.dart';

class AniBakaPreviewPage extends StatefulWidget {
  const AniBakaPreviewPage({
    super.key,
  });

  @override
  State<AniBakaPreviewPage> createState() =>
      _AniBakaPreviewPageState();
}

class _AniBakaPreviewPageState extends State<AniBakaPreviewPage> {
  final TextEditingController _searchController =
      TextEditingController();

  List<_AniBakaRule> _rules = const [];

  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRules();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadRules() async {
    try {
      final raw = await rootBundle.loadString(
        'assets/anibaka/manifest.json',
      );

      final decoded = jsonDecode(raw);

      if (decoded is! Map) {
        throw const FormatException(
          'AniBaka manifest 格式错误',
        );
      }

      final rawRules = decoded['rules'];

      if (rawRules is! List) {
        throw const FormatException(
          'AniBaka manifest 缺少 rules',
        );
      }

      final rules = <_AniBakaRule>[];

      for (final item in rawRules) {
        if (item is! Map) {
          continue;
        }

        rules.add(
          _AniBakaRule(
            id: item['id']?.toString() ?? '',
            name: item['name']?.toString() ?? '',
            baseUrl: item['baseUrl']?.toString() ?? '',
            description:
                item['description']?.toString() ?? '',
            iconUrl: item['iconUrl']?.toString() ?? '',
            file: item['file']?.toString() ?? '',
          ),
        );
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _rules = rules;
        _loading = false;
        _error = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  List<_AniBakaRule> get _visibleRules {
    final query = _searchController.text
        .trim()
        .toLowerCase();

    if (query.isEmpty) {
      return _rules;
    }

    return _rules.where((rule) {
      return rule.name
              .toLowerCase()
              .contains(query) ||
          rule.id
              .toLowerCase()
              .contains(query) ||
          rule.baseUrl
              .toLowerCase()
              .contains(query);
    }).toList();
  }

  Future<void> _showRuleJson(
    _AniBakaRule rule,
  ) async {
    try {
      final raw = await rootBundle.loadString(
        'assets/anibaka/rules/${rule.file}',
      );

      final decoded = jsonDecode(raw);

      final formatted =
          const JsonEncoder.withIndent(
        '  ',
      ).convert(decoded);

      if (!mounted) {
        return;
      }

      await showDialog<void>(
        context: context,
        builder: (dialogContext) {
          return AlertDialog(
            title: Text(rule.name),
            content: SizedBox(
              width: 720,
              child: SingleChildScrollView(
                child: SelectableText(
                  formatted,
                ),
              ),
            ),
            actions: [
              TextButton.icon(
                onPressed: () async {
                  await Clipboard.setData(
                    ClipboardData(
                      text: formatted,
                    ),
                  );

                  if (!dialogContext.mounted) {
                    return;
                  }

                  ScaffoldMessenger.of(
                    dialogContext,
                  ).showSnackBar(
                    const SnackBar(
                      content: Text(
                        '规则 JSON 已复制',
                      ),
                    ),
                  );
                },
                icon: const Icon(
                  Icons.content_copy_rounded,
                ),
                label: const Text(
                  '复制',
                ),
              ),
              FilledButton(
                onPressed: () {
                  Navigator.of(
                    dialogContext,
                  ).pop();
                },
                child: const Text(
                  '关闭',
                ),
              ),
            ],
          );
        },
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(
        SnackBar(
          content: Text(
            '读取规则失败：$error',
          ),
        ),
      );
    }
  }

  @override
  Widget build(
    BuildContext context,
  ) {
    return SettingsDetailScaffold(
      title: const Text(
        'AniBaka 规则',
      ),
      body: SafeArea(
        top: false,
        child: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints:
                const BoxConstraints(
              maxWidth: 1000,
            ),
            child: _buildBody(),
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
        child:
            CircularProgressIndicator(),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding:
              const EdgeInsets.all(24),
          child: Column(
            mainAxisSize:
                MainAxisSize.min,
            children: [
              const Icon(
                Icons.error_outline_rounded,
                size: 52,
              ),
              const SizedBox(
                height: 16,
              ),
              Text(
                'AniBaka 规则加载失败',
                style: Theme.of(context)
                    .textTheme
                    .titleLarge,
              ),
              const SizedBox(
                height: 8,
              ),
              SelectableText(
                _error!,
              ),
              const SizedBox(
                height: 16,
              ),
              FilledButton.icon(
                onPressed: () {
                  setState(() {
                    _loading = true;
                    _error = null;
                  });

                  _loadRules();
                },
                icon: const Icon(
                  Icons.refresh_rounded,
                ),
                label: const Text(
                  '重新加载',
                ),
              ),
            ],
          ),
        ),
      );
    }

    final visibleRules =
        _visibleRules;

    return ListView(
      padding:
          const EdgeInsets.fromLTRB(
        16,
        16,
        16,
        32,
      ),
      children: [
        Card(
          child: Padding(
            padding:
                const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons
                          .extension_rounded,
                      size: 30,
                    ),
                    const SizedBox(
                      width: 12,
                    ),
                    Expanded(
                      child: Text(
                        'AniBaka 规则库',
                        style:
                            Theme.of(context)
                                .textTheme
                                .titleLarge,
                      ),
                    ),
                  ],
                ),
                const SizedBox(
                  height: 12,
                ),
                Text(
                  '已加载 ${_rules.length} 条 '
                  'anx-rule/2 规则',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium,
                ),
                const SizedBox(
                  height: 8,
                ),
                Text(
                  '当前为兼容性测试页面。'
                  '这一阶段用于确认星番屋能够读取、'
                  '展示和检查 AniBaka 规则。'
                  '搜索、剧集解析和播放将在后续版本接入。',
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(
          height: 16,
        ),
        TextField(
          controller:
              _searchController,
          onChanged: (_) {
            setState(() {});
          },
          decoration:
              InputDecoration(
            hintText:
                '搜索规则名称或站点',
            prefixIcon:
                const Icon(
              Icons.search_rounded,
            ),
            suffixIcon:
                _searchController
                        .text
                        .isEmpty
                    ? null
                    : IconButton(
                        tooltip:
                            '清除',
                        onPressed:
                            () {
                          _searchController
                              .clear();
                          setState(
                            () {},
                          );
                        },
                        icon:
                            const Icon(
                          Icons
                              .close_rounded,
                        ),
                      ),
            border:
                const OutlineInputBorder(),
          ),
        ),
        const SizedBox(
          height: 16,
        ),
        Row(
          children: [
            Text(
              '规则列表',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium,
            ),
            const Spacer(),
            Text(
              '${visibleRules.length} / '
              '${_rules.length}',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium,
            ),
          ],
        ),
        const SizedBox(
          height: 10,
        ),
        if (visibleRules.isEmpty)
          const Card(
            child: Padding(
              padding:
                  EdgeInsets.all(32),
              child: Center(
                child: Text(
                  '没有找到符合条件的规则',
                ),
              ),
            ),
          ),
        for (final rule
            in visibleRules) ...[
          Card(
            clipBehavior:
                Clip.antiAlias,
            child: ListTile(
              contentPadding:
                  const EdgeInsets
                      .symmetric(
                horizontal: 16,
                vertical: 10,
              ),
              leading: const CircleAvatar(
                child: Icon(
                  Icons
                      .movie_filter_rounded,
                ),
              ),
              title: Text(
                rule.name,
              ),
              subtitle: Column(
                crossAxisAlignment:
                    CrossAxisAlignment
                        .start,
                children: [
                  if (rule.baseUrl
                      .isNotEmpty) ...[
                    const SizedBox(
                      height: 4,
                    ),
                    Text(
                      rule.baseUrl,
                      maxLines: 1,
                      overflow:
                          TextOverflow
                              .ellipsis,
                    ),
                  ],
                  const SizedBox(
                    height: 3,
                  ),
                  Text(
                    rule.file,
                    style:
                        Theme.of(context)
                            .textTheme
                            .bodySmall,
                  ),
                  if (rule.description
                      .isNotEmpty) ...[
                    const SizedBox(
                      height: 4,
                    ),
                    Text(
                      rule.description,
                      maxLines: 2,
                      overflow:
                          TextOverflow
                              .ellipsis,
                    ),
                  ],
                ],
              ),
              trailing:
                  const Icon(
                Icons.code_rounded,
              ),
              onTap: () {
                _showRuleJson(
                  rule,
                );
              },
            ),
          ),
          const SizedBox(
            height: 8,
          ),
        ],
      ],
    );
  }
}

class _AniBakaRule {
  const _AniBakaRule({
    required this.id,
    required this.name,
    required this.baseUrl,
    required this.description,
    required this.iconUrl,
    required this.file,
  });

  final String id;
  final String name;
  final String baseUrl;
  final String description;
  final String iconUrl;
  final String file;
}
'''.lstrip()

    ANIBAKA_PAGE.write_text(
        content,
        encoding="utf-8",
    )

    log(
        "AniBaka 页面创建完成"
    )


def patch_plugin_module():
    log(
        "修改 plugin_module.dart"
    )

    require_file(PLUGIN_MODULE)

    text = PLUGIN_MODULE.read_text(
        encoding="utf-8"
    )

    import_line = (
        "import "
        "'package:kazumi/pages/plugin_editor/"
        "anibaka_preview_page.dart';\n"
    )

    if import_line not in text:
        import_marker = (
            "import "
            "'package:flutter_modular/"
            "flutter_modular.dart';\n"
        )

        if import_marker not in text:
            raise RuntimeError(
                "plugin_module.dart 中"
                "找不到 flutter_modular import"
            )

        text = text.replace(
            import_marker,
            import_marker + import_line,
            1,
        )

    route_path = (
        "'/anibaka-preview'"
    )

    if route_path not in text:
        shop_marker = """      ..route(
        '/shop',
"""

        route_code = """      ..route(
        '/anibaka-preview',
        child: (context, state) =>
            const AniBakaPreviewPage(),
      )
      ..route(
        '/shop',
"""

        if shop_marker not in text:
            raise RuntimeError(
                "plugin_module.dart 中"
                "找不到 /shop 路由"
            )

        text = text.replace(
            shop_marker,
            route_code,
            1,
        )

    PLUGIN_MODULE.write_text(
        text,
        encoding="utf-8",
    )

    log(
        "AniBaka 路由添加完成"
    )


def patch_plugin_view():
    log(
        "修改规则管理页面"
    )

    require_file(PLUGIN_VIEW)

    text = PLUGIN_VIEW.read_text(
        encoding="utf-8"
    )

    if (
        "AniBaka 规则"
        in text
        and "anibaka-preview"
        in text
    ):
        log(
            "AniBaka 按钮已存在，跳过"
        )
        return

    marker = """                            FilledButton.tonalIcon(
                                style: FilledButton.styleFrom(
                                    minimumSize: const Size(120, 48)),
                                onPressed: () =>
                                    context.pushNamed('/settings/plugin/shop'),
                                icon: const Icon(Icons.travel_explore_rounded),
                                label: const Text('规则仓库')),
"""

    replacement = """                            FilledButton.tonalIcon(
                                style: FilledButton.styleFrom(
                                    minimumSize: const Size(120, 48)),
                                onPressed: () =>
                                    context.pushNamed('/settings/plugin/shop'),
                                icon: const Icon(Icons.travel_explore_rounded),
                                label: const Text('规则仓库')),
                            FilledButton.tonalIcon(
                                style: FilledButton.styleFrom(
                                    minimumSize: const Size(120, 48)),
                                onPressed: () => context.pushNamed(
                                    '/settings/plugin/anibaka-preview'),
                                icon: const Icon(Icons.extension_rounded),
                                label: const Text('AniBaka 规则')),
"""

    if marker not in text:
        raise RuntimeError(
            "plugin_view_page.dart 中"
            "找不到规则仓库按钮，"
            "为避免破坏源码已停止"
        )

    text = text.replace(
        marker,
        replacement,
        1,
    )

    PLUGIN_VIEW.write_text(
        text,
        encoding="utf-8",
    )

    log(
        "规则管理页 AniBaka 按钮"
        "添加完成"
    )


def verify():
    log("执行最终检查")

    require_file(
        ASSET_ROOT
        / "manifest.json"
    )

    require_file(
        ANIBAKA_PAGE
    )

    module_text = (
        PLUGIN_MODULE.read_text(
            encoding="utf-8"
        )
    )

    view_text = (
        PLUGIN_VIEW.read_text(
            encoding="utf-8"
        )
    )

    pubspec_text = (
        PUBSPEC.read_text(
            encoding="utf-8"
        )
    )

    if (
        "anibaka-preview"
        not in module_text
    ):
        raise RuntimeError(
            "AniBaka 路由检查失败"
        )

    if (
        "AniBaka 规则"
        not in view_text
    ):
        raise RuntimeError(
            "AniBaka 按钮检查失败"
        )

    if (
        "assets/anibaka/"
        not in pubspec_text
    ):
        raise RuntimeError(
            "AniBaka assets 检查失败"
        )

    manifest = json.loads(
        (
            ASSET_ROOT
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    count = manifest.get(
        "count",
        0,
    )

    if not count:
        raise RuntimeError(
            "没有识别到 AniBaka 规则"
        )

    log(
        f"检查完成，共 {count} 条规则"
    )


def main():
    log(
        "开始生成星番屋 AniBaka "
        "可见测试版"
    )

    prepare_assets()

    patch_pubspec()

    write_anibaka_page()

    patch_plugin_module()

    patch_plugin_view()

    verify()

    log(
        "AniBaka 测试版修改全部完成"
    )


if __name__ == "__main__":
    main()
