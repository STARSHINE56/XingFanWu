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


def find_fetch_request(search):
    if not isinstance(search, list):
        return None

    for item in search:
        if not isinstance(item, dict):
            continue

        op = item.get("op")

        if op == "fetch":
            url = item.get("url")

            if isinstance(url, str):
                return {
                    "op": "fetch",
                    "url": url,
                    "method": str(
                        item.get(
                            "method",
                            "GET",
                        )
                    ).upper(),
                    "headers": item.get(
                        "headers",
                        {},
                    ),
                    "body": item.get(
                        "body",
                        "",
                    ),
                }

        if op == "first":
            branches = item.get(
                "branches",
                [],
            )

            if isinstance(
                branches,
                list,
            ):
                for branch in branches:
                    result = (
                        find_fetch_request(
                            branch
                        )
                    )

                    if result:
                        return result

    return None


def collect_search_ops(value):
    result = []

    if isinstance(value, dict):
        op = value.get("op")

        if isinstance(op, str):
            result.append(op)

        for child in value.values():
            result.extend(
                collect_search_ops(
                    child
                )
            )

    elif isinstance(value, list):
        for child in value:
            result.extend(
                collect_search_ops(
                    child
                )
            )

    return result


def prepare_assets():
    log(
        "准备 AniBaka 规则资源"
    )

    if not ANIBAKA_SOURCE.exists():
        raise FileNotFoundError(
            "找不到 /tmp/AniBakaRule"
        )

    if ASSET_ROOT.exists():
        shutil.rmtree(
            ASSET_ROOT
        )

    ASSET_RULES.mkdir(
        parents=True,
        exist_ok=True,
    )

    rules = []

    for source_file in sorted(
        ANIBAKA_SOURCE.glob(
            "*.json"
        )
    ):
        if (
            source_file.name
            == "index.json"
        ):
            continue

        try:
            data = json.loads(
                source_file.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as error:
            log(
                f"跳过 {source_file.name}: "
                f"{error}"
            )
            continue

        if not isinstance(
            data,
            dict,
        ):
            continue

        if (
            data.get("format")
            != "anx-rule/2"
        ):
            continue

        shutil.copy2(
            source_file,
            ASSET_RULES
            / source_file.name,
        )

        search = data.get(
            "search",
            [],
        )

        search_request = (
            find_fetch_request(
                search
            )
        )

        search_ops = list(
            dict.fromkeys(
                collect_search_ops(
                    search
                )
            )
        )

        headers = data.get(
            "headers",
            {},
        )

        if not isinstance(
            headers,
            dict,
        ):
            headers = {}

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
                "file":
                    source_file.name,
                "headers":
                    headers,
                "searchRequest":
                    search_request,
                "searchOps":
                    search_ops,
            }
        )

    manifest = {
        "format":
            "xingfanwu-anibaka-search-preview/2",
        "count":
            len(rules),
        "rules":
            rules,
    }

    (
        ASSET_ROOT
        / "manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    log(
        f"已识别 {len(rules)} 条规则"
    )

    searchable = [
        item
        for item in rules
        if item.get(
            "searchRequest"
        )
    ]

    log(
        f"其中 {len(searchable)} 条"
        "发现直接 HTTP 搜索入口"
    )


def patch_pubspec():
    require_file(
        PUBSPEC
    )

    text = PUBSPEC.read_text(
        encoding="utf-8"
    )

    lines = [
        "    - assets/anibaka/\n",
        (
            "    - "
            "assets/anibaka/rules/\n"
        ),
    ]

    missing = [
        line
        for line in lines
        if line not in text
    ]

    if not missing:
        log(
            "AniBaka assets "
            "已配置"
        )
        return

    marker = "  assets:\n"

    if marker not in text:
        raise RuntimeError(
            "pubspec.yaml 中"
            "找不到 assets"
        )

    text = text.replace(
        marker,
        marker
        + "".join(missing),
        1,
    )

    PUBSPEC.write_text(
        text,
        encoding="utf-8",
    )


def write_anibaka_page():
    log(
        "生成 AniBaka 搜索测试页面"
    )

    content = r'''
import 'dart:convert';
import 'dart:io';

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
  final TextEditingController _ruleSearchController =
      TextEditingController();

  final TextEditingController _keywordController =
      TextEditingController(
    text: '葬送的芙莉莲',
  );

  final HttpClient _client = HttpClient();

  List<_AniBakaRule> _rules = const [];
  List<_AniBakaSearchResult> _results = const [];

  _AniBakaRule? _selectedRule;

  bool _loading = true;
  bool _searching = false;

  String? _error;
  String? _searchMessage;
  String? _lastRequestUrl;

  @override
  void initState() {
    super.initState();

    _client.connectionTimeout =
        const Duration(
      seconds: 15,
    );

    _loadRules();
  }

  @override
  void dispose() {
    _ruleSearchController.dispose();
    _keywordController.dispose();
    _client.close(
      force: true,
    );
    super.dispose();
  }

  Future<void> _loadRules() async {
    try {
      final raw =
          await rootBundle.loadString(
        'assets/anibaka/manifest.json',
      );

      final decoded =
          jsonDecode(raw);

      if (decoded is! Map) {
        throw const FormatException(
          'manifest 格式错误',
        );
      }

      final rawRules =
          decoded['rules'];

      if (rawRules is! List) {
        throw const FormatException(
          'manifest 缺少 rules',
        );
      }

      final rules =
          <_AniBakaRule>[];

      for (final item
          in rawRules) {
        if (item is! Map) {
          continue;
        }

        rules.add(
          _AniBakaRule.fromMap(
            item,
          ),
        );
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _rules = rules;
        _selectedRule =
            rules.isEmpty
                ? null
                : rules.firstWhere(
                    (rule) =>
                        rule.searchRequest !=
                        null,
                    orElse:
                        () => rules.first,
                  );

        _loading = false;
        _error = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _error =
            error.toString();
      });
    }
  }

  List<_AniBakaRule>
      get _visibleRules {
    final query =
        _ruleSearchController
            .text
            .trim()
            .toLowerCase();

    if (query.isEmpty) {
      return _rules;
    }

    return _rules.where(
      (rule) {
        return rule.name
                .toLowerCase()
                .contains(query) ||
            rule.id
                .toLowerCase()
                .contains(query) ||
            rule.baseUrl
                .toLowerCase()
                .contains(query);
      },
    ).toList();
  }

  String _replaceTemplate(
    String input,
    String keyword,
  ) {
    final encoded =
        Uri.encodeComponent(
      keyword,
    );

    return input
        .replaceAll(
          '{keyword}',
          encoded,
        )
        .replaceAll(
          '{keyword:raw}',
          keyword,
        )
        .replaceAll(
          '@keyword',
          encoded,
        );
  }

  Uri? _resolveUri(
    _AniBakaRule rule,
    String value,
  ) {
    final direct =
        Uri.tryParse(value);

    if (direct != null &&
        direct.hasScheme) {
      return direct;
    }

    final base =
        Uri.tryParse(
      rule.baseUrl,
    );

    if (base == null ||
        !base.hasScheme) {
      return direct;
    }

    return base.resolve(
      value,
    );
  }

  Future<void> _search() async {
    final rule =
        _selectedRule;

    if (rule == null) {
      return;
    }

    final keyword =
        _keywordController.text
            .trim();

    if (keyword.isEmpty) {
      _showMessage(
        '请输入番剧名称',
      );
      return;
    }

    final requestInfo =
        rule.searchRequest;

    if (requestInfo == null ||
        requestInfo.url.isEmpty) {
      setState(() {
        _results = const [];
        _searchMessage =
            '这条规则没有发现可直接执行的 '
            'fetch 搜索入口。\n'
            '它可能使用了专用搜索操作，'
            '后续兼容层再补。';
      });

      return;
    }

    setState(() {
      _searching = true;
      _results = const [];
      _searchMessage = null;
      _lastRequestUrl = null;
    });

    try {
      final requestUrl =
          _replaceTemplate(
        requestInfo.url,
        keyword,
      );

      final uri =
          _resolveUri(
        rule,
        requestUrl,
      );

      if (uri == null ||
          !uri.hasScheme) {
        throw FormatException(
          '搜索地址无效：'
          '$requestUrl',
        );
      }

      _lastRequestUrl =
          uri.toString();

      final method =
          requestInfo.method
              .toUpperCase();

      HttpClientRequest request;

      if (method == 'POST') {
        request =
            await _client.postUrl(
          uri,
        );
      } else {
        request =
            await _client.getUrl(
          uri,
        );
      }

      final headers =
          <String, String>{};

      headers.addAll(
        rule.headers,
      );

      headers.addAll(
        requestInfo.headers,
      );

      headers.putIfAbsent(
        'User-Agent',
        () =>
            'Mozilla/5.0 '
            '(Linux; Android 14) '
            'AppleWebKit/537.36 '
            '(KHTML, like Gecko) '
            'Chrome/140.0.0.0 '
            'Mobile Safari/537.36',
      );

      headers.putIfAbsent(
        'Accept',
        () => '*/*',
      );

      if (rule.baseUrl.isNotEmpty) {
        headers.putIfAbsent(
          'Referer',
          () => rule.baseUrl,
        );
      }

      for (final entry
          in headers.entries) {
        request.headers.set(
          entry.key,
          _replaceTemplate(
            entry.value,
            keyword,
          ),
        );
      }

      if (method == 'POST') {
        var body =
            requestInfo.body;

        if (body.isEmpty) {
          body =
              'wd=${Uri.encodeQueryComponent(keyword)}';
        }

        request.write(
          _replaceTemplate(
            body,
            keyword,
          ),
        );
      }

      final response =
          await request.close();

      final bytes =
          await response.fold<
              List<int>>(
        <int>[],
        (
          previous,
          element,
        ) {
          previous.addAll(
            element,
          );
          return previous;
        },
      );

      final body =
          _decodeBody(
        bytes,
      );

      if (response.statusCode <
              200 ||
          response.statusCode >=
              400) {
        throw HttpException(
          'HTTP '
          '${response.statusCode}',
          uri: uri,
        );
      }

      var results =
          _parseJsonResults(
        body,
        rule,
      );

      if (results.isEmpty) {
        results =
            _parseHtmlResults(
          body,
          rule,
        );
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _results =
            _deduplicate(
          results,
        );

        _searching = false;

        if (_results.isEmpty) {
          _searchMessage =
              '请求成功，但当前兼容器'
              '没有从页面中识别到结果。\n\n'
              'HTTP ${response.statusCode}\n'
              '返回 ${bytes.length} 字节\n\n'
              '规则搜索操作：'
              '${rule.searchOps.join(' → ')}';
        } else {
          _searchMessage =
              '搜索成功：'
              '${_results.length} 条结果';
        }
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _searching = false;
        _results = const [];
        _searchMessage =
            '搜索失败：$error';
      });
    }
  }

  String _decodeBody(
    List<int> bytes,
  ) {
    try {
      return utf8.decode(
        bytes,
      );
    } catch (_) {
      return latin1.decode(
        bytes,
      );
    }
  }

  List<_AniBakaSearchResult>
      _parseJsonResults(
    String body,
    _AniBakaRule rule,
  ) {
    final trimmed =
        body.trimLeft();

    if (!trimmed.startsWith(
          '{',
        ) &&
        !trimmed.startsWith(
          '[',
        )) {
      return const [];
    }

    try {
      final decoded =
          jsonDecode(body);

      final maps =
          <Map<dynamic, dynamic>>[];

      void walk(
        dynamic value,
      ) {
        if (value is Map) {
          final hasName =
              value.containsKey(
                    'name',
                  ) ||
                  value.containsKey(
                    'title',
                  ) ||
                  value.containsKey(
                    'vod_name',
                  ) ||
                  value.containsKey(
                    'video_name',
                  );

          if (hasName) {
            maps.add(
              value,
            );
          }

          for (final child
              in value.values) {
            walk(child);
          }
        } else if (value is List) {
          for (final child
              in value) {
            walk(child);
          }
        }
      }

      walk(decoded);

      final results =
          <_AniBakaSearchResult>[];

      for (final item in maps) {
        final title =
            _firstText(
          item,
          const [
            'name',
            'title',
            'vod_name',
            'video_name',
          ],
        );

        if (title.isEmpty) {
          continue;
        }

        final image =
            _firstText(
          item,
          const [
            'pic',
            'image',
            'cover',
            'vod_pic',
            'poster',
            'thumb',
          ],
        );

        var url =
            _firstText(
          item,
          const [
            'url',
            'link',
            'href',
            'detailUrl',
            'detail_url',
          ],
        );

        final id =
            _firstText(
          item,
          const [
            'id',
            'vod_id',
            'video_id',
          ],
        );

        if (url.isEmpty &&
            id.isNotEmpty) {
          url = id;
        }

        results.add(
          _AniBakaSearchResult(
            title: title,
            image:
                _resolveTextUrl(
              rule,
              image,
            ),
            detail:
                _resolveDetail(
              rule,
              url,
            ),
            subtitle: id,
          ),
        );
      }

      return results;
    } catch (_) {
      return const [];
    }
  }

  String _firstText(
    Map<dynamic, dynamic> map,
    List<String> keys,
  ) {
    for (final key in keys) {
      final value =
          map[key];

      if (value != null) {
        final text =
            value.toString()
                .trim();

        if (text.isNotEmpty) {
          return text;
        }
      }
    }

    return '';
  }

  List<_AniBakaSearchResult>
      _parseHtmlResults(
    String html,
    _AniBakaRule rule,
  ) {
    final results =
        <_AniBakaSearchResult>[];

    final anchorPattern =
        RegExp(
      r'''<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)</a>''',
      caseSensitive: false,
    );

    for (final match
        in anchorPattern
            .allMatches(html)) {
      final href =
          match.group(1)
                  ?.trim() ??
              '';

      final inner =
          match.group(2) ?? '';

      if (href.isEmpty) {
        continue;
      }

      final lower =
          href.toLowerCase();

      final looksLikeDetail =
          lower.contains(
                '/detail',
              ) ||
              lower.contains(
                '/voddetail',
              ) ||
              lower.contains(
                '/vod/detail',
              ) ||
              lower.contains(
                '/anime/',
              ) ||
              lower.contains(
                '/bangumi/',
              ) ||
              lower.contains(
                '/show/',
              );

      if (!looksLikeDetail) {
        continue;
      }

      var title =
          _extractAttribute(
        inner,
        'title',
      );

      if (title.isEmpty) {
        title =
            _extractAttribute(
          inner,
          'alt',
        );
      }

      if (title.isEmpty) {
        title =
            _stripHtml(
          inner,
        );
      }

      title =
          title.trim();

      if (title.isEmpty ||
          title.length > 120) {
        continue;
      }

      var image =
          _extractAttribute(
        inner,
        'data-src',
      );

      if (image.isEmpty) {
        image =
            _extractAttribute(
          inner,
          'data-original',
        );
      }

      if (image.isEmpty) {
        image =
            _extractAttribute(
          inner,
          'src',
        );
      }

      results.add(
        _AniBakaSearchResult(
          title: title,
          image:
              _resolveTextUrl(
            rule,
            image,
          ),
          detail:
              _resolveTextUrl(
            rule,
            href,
          ),
          subtitle: href,
        ),
      );
    }

    if (results.isNotEmpty) {
      return results;
    }

    final loosePattern =
        RegExp(
      r'''href\s*=\s*["']([^"']*(?:detail|voddetail)[^"']*)["'][^>]*>([\s\S]{0,500}?)</a>''',
      caseSensitive: false,
    );

    for (final match
        in loosePattern
            .allMatches(html)) {
      final href =
          match.group(1) ?? '';

      final inner =
          match.group(2) ?? '';

      final title =
          _stripHtml(
        inner,
      ).trim();

      if (title.isEmpty) {
        continue;
      }

      results.add(
        _AniBakaSearchResult(
          title: title,
          image: '',
          detail:
              _resolveTextUrl(
            rule,
            href,
          ),
          subtitle: href,
        ),
      );
    }

    return results;
  }

  String _extractAttribute(
    String html,
    String attribute,
  ) {
    final pattern =
        RegExp(
      '$attribute'
      r'''\s*=\s*["']([^"']+)["']''',
      caseSensitive: false,
    );

    return pattern
            .firstMatch(html)
            ?.group(1)
            ?.trim() ??
        '';
  }

  String _stripHtml(
    String value,
  ) {
    var text =
        value.replaceAll(
      RegExp(
        r'<script[\s\S]*?</script>',
        caseSensitive: false,
      ),
      ' ',
    );

    text =
        text.replaceAll(
      RegExp(
        r'<style[\s\S]*?</style>',
        caseSensitive: false,
      ),
      ' ',
    );

    text =
        text.replaceAll(
      RegExp(
        r'<[^>]+>',
      ),
      ' ',
    );

    text =
        text.replaceAll(
      '&nbsp;',
      ' ',
    );

    text =
        text.replaceAll(
      '&amp;',
      '&',
    );

    text =
        text.replaceAll(
      '&quot;',
      '"',
    );

    text =
        text.replaceAll(
      '&#39;',
      "'",
    );

    return text.replaceAll(
      RegExp(
        r'\s+',
      ),
      ' ',
    );
  }

  String _resolveDetail(
    _AniBakaRule rule,
    String value,
  ) {
    if (value.isEmpty) {
      return '';
    }

    if (value.startsWith(
          'http://',
        ) ||
        value.startsWith(
          'https://',
        ) ||
        value.startsWith('/')) {
      return _resolveTextUrl(
        rule,
        value,
      );
    }

    final numeric =
        int.tryParse(
      value,
    );

    if (numeric != null) {
      return value;
    }

    return _resolveTextUrl(
      rule,
      value,
    );
  }

  String _resolveTextUrl(
    _AniBakaRule rule,
    String value,
  ) {
    if (value.isEmpty) {
      return '';
    }

    if (value.startsWith(
          'data:',
        )) {
      return value;
    }

    final uri =
        _resolveUri(
      rule,
      value,
    );

    return uri?.toString() ??
        value;
  }

  List<_AniBakaSearchResult>
      _deduplicate(
    List<_AniBakaSearchResult>
        input,
  ) {
    final output =
        <_AniBakaSearchResult>[];

    final seen =
        <String>{};

    for (final item in input) {
      final key =
          '${item.title}|'
          '${item.detail}';

      if (seen.add(key)) {
        output.add(item);
      }
    }

    return output
        .take(50)
        .toList();
  }

  void _showMessage(
    String message,
  ) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(
      SnackBar(
        content: Text(
          message,
        ),
      ),
    );
  }

  Future<void> _showRuleJson(
    _AniBakaRule rule,
  ) async {
    try {
      final raw =
          await rootBundle.loadString(
        'assets/anibaka/rules/${rule.file}',
      );

      final decoded =
          jsonDecode(raw);

      final formatted =
          const JsonEncoder.withIndent(
        '  ',
      ).convert(decoded);

      if (!mounted) {
        return;
      }

      await showDialog<void>(
        context: context,
        builder: (
          dialogContext,
        ) {
          return AlertDialog(
            title: Text(
              rule.name,
            ),
            content: SizedBox(
              width: 720,
              child:
                  SingleChildScrollView(
                child:
                    SelectableText(
                  formatted,
                ),
              ),
            ),
            actions: [
              TextButton.icon(
                onPressed:
                    () async {
                  await Clipboard
                      .setData(
                    ClipboardData(
                      text:
                          formatted,
                    ),
                  );
                },
                icon:
                    const Icon(
                  Icons
                      .content_copy_rounded,
                ),
                label:
                    const Text(
                  '复制 JSON',
                ),
              ),
              FilledButton(
                onPressed: () {
                  Navigator.of(
                    dialogContext,
                  ).pop();
                },
                child:
                    const Text(
                  '关闭',
                ),
              ),
            ],
          );
        },
      );
    } catch (error) {
      _showMessage(
        '读取规则失败：$error',
      );
    }
  }

  @override
  Widget build(
    BuildContext context,
  ) {
    return SettingsDetailScaffold(
      title: const Text(
        'AniBaka 搜索测试',
      ),
      body: SafeArea(
        top: false,
        child: Align(
          alignment:
              Alignment.topCenter,
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
              const EdgeInsets.all(
            24,
          ),
          child: SelectableText(
            'AniBaka 加载失败\n\n'
            '$_error',
          ),
        ),
      );
    }

    return ListView(
      padding:
          const EdgeInsets.fromLTRB(
        16,
        16,
        16,
        32,
      ),
      children: [
        _buildHeader(),
        const SizedBox(
          height: 16,
        ),
        _buildSearchPanel(),
        const SizedBox(
          height: 16,
        ),
        if (_searchMessage !=
            null)
          Card(
            child: Padding(
              padding:
                  const EdgeInsets
                      .all(16),
              child:
                  SelectableText(
                _searchMessage!,
              ),
            ),
          ),
        if (_lastRequestUrl !=
            null) ...[
          const SizedBox(
            height: 8,
          ),
          Card(
            child: ListTile(
              leading:
                  const Icon(
                Icons
                    .link_rounded,
              ),
              title:
                  const Text(
                '实际请求地址',
              ),
              subtitle:
                  SelectableText(
                _lastRequestUrl!,
              ),
            ),
          ),
        ],
        const SizedBox(
          height: 16,
        ),
        if (_results.isNotEmpty)
          _buildResults(),
        const SizedBox(
          height: 24,
        ),
        _buildRuleSection(),
      ],
    );
  }

  Widget _buildHeader() {
    final searchable =
        _rules
            .where(
              (rule) =>
                  rule.searchRequest !=
                  null,
            )
            .length;

    return Card(
      child: Padding(
        padding:
            const EdgeInsets.all(
          20,
        ),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment
                  .start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons
                      .travel_explore_rounded,
                  size: 30,
                ),
                const SizedBox(
                  width: 12,
                ),
                Expanded(
                  child: Text(
                    'AniBaka 搜索兼容测试',
                    style:
                        Theme.of(
                      context,
                    ).textTheme
                            .titleLarge,
                  ),
                ),
              ],
            ),
            const SizedBox(
              height: 12,
            ),
            Text(
              '规则总数：'
              '${_rules.length}',
            ),
            Text(
              '已发现直接搜索入口：'
              '$searchable',
            ),
            const SizedBox(
              height: 8,
            ),
            Text(
              '当前阶段支持直接 HTTP '
              '搜索、常见 JSON 搜索结果以及'
              '常见 HTML 详情链接提取。'
              '这还不是完整 anx-rule/2 '
              '解释器。',
              style: Theme.of(
                context,
              ).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchPanel() {
    final rule =
        _selectedRule;

    return Card(
      child: Padding(
        padding:
            const EdgeInsets.all(
          16,
        ),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment
                  .stretch,
          children: [
            Text(
              '搜索测试',
              style:
                  Theme.of(context)
                      .textTheme
                      .titleMedium,
            ),
            const SizedBox(
              height: 12,
            ),
            DropdownButtonFormField<
                _AniBakaRule>(
              initialValue: rule,
              isExpanded: true,
              decoration:
                  const InputDecoration(
                labelText:
                    '选择规则',
                border:
                    OutlineInputBorder(),
              ),
              items: _rules
                  .map(
                    (item) =>
                        DropdownMenuItem(
                      value: item,
                      child: Text(
                        item.searchRequest ==
                                null
                            ? '${item.name} '
                                '（暂不支持搜索）'
                            : item.name,
                        overflow:
                            TextOverflow
                                .ellipsis,
                      ),
                    ),
                  )
                  .toList(),
              onChanged:
                  (value) {
                setState(() {
                  _selectedRule =
                      value;
                  _results =
                      const [];
                  _searchMessage =
                      null;
                  _lastRequestUrl =
                      null;
                });
              },
            ),
            const SizedBox(
              height: 12,
            ),
            TextField(
              controller:
                  _keywordController,
              textInputAction:
                  TextInputAction
                      .search,
              onSubmitted: (_) {
                _search();
              },
              decoration:
                  const InputDecoration(
                labelText:
                    '番剧名称',
                hintText:
                    '例如：葬送的芙莉莲',
                prefixIcon:
                    Icon(
                  Icons
                      .search_rounded,
                ),
                border:
                    OutlineInputBorder(),
              ),
            ),
            const SizedBox(
              height: 12,
            ),
            FilledButton.icon(
              onPressed:
                  _searching
                      ? null
                      : _search,
              icon: _searching
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child:
                          CircularProgressIndicator(
                        strokeWidth:
                            2,
                      ),
                    )
                  : const Icon(
                      Icons
                          .search_rounded,
                    ),
              label: Text(
                _searching
                    ? '正在搜索...'
                    : '开始搜索',
              ),
            ),
            if (rule != null) ...[
              const SizedBox(
                height: 12,
              ),
              Text(
                '搜索操作：'
                '${rule.searchOps.join(' → ')}',
                style:
                    Theme.of(context)
                        .textTheme
                        .bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildResults() {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Text(
          '搜索结果 '
          '(${_results.length})',
          style:
              Theme.of(context)
                  .textTheme
                  .titleMedium,
        ),
        const SizedBox(
          height: 8,
        ),
        for (final item
            in _results) ...[
          Card(
            child: ListTile(
              leading: SizedBox(
                width: 48,
                height: 64,
                child:
                    item.image.isEmpty
                        ? const Icon(
                            Icons
                                .movie_rounded,
                          )
                        : Image.network(
                            item.image,
                            fit:
                                BoxFit.cover,
                            errorBuilder:
                                (
                              context,
                              error,
                              stackTrace,
                            ) {
                              return const Icon(
                                Icons
                                    .broken_image_outlined,
                              );
                            },
                          ),
              ),
              title: Text(
                item.title,
              ),
              subtitle: Column(
                crossAxisAlignment:
                    CrossAxisAlignment
                        .start,
                children: [
                  if (item.subtitle
                      .isNotEmpty)
                    Text(
                      item.subtitle,
                      maxLines: 1,
                      overflow:
                          TextOverflow
                              .ellipsis,
                    ),
                  if (item.detail
                      .isNotEmpty)
                    Text(
                      item.detail,
                      maxLines: 1,
                      overflow:
                          TextOverflow
                              .ellipsis,
                      style:
                          Theme.of(
                        context,
                      ).textTheme
                              .bodySmall,
                    ),
                ],
              ),
              trailing:
                  const Icon(
                Icons
                    .chevron_right_rounded,
              ),
              onTap: () {
                _showMessage(
                  '下一阶段会接入详情页和剧集解析',
                );
              },
            ),
          ),
          const SizedBox(
            height: 6,
          ),
        ],
      ],
    );
  }

  Widget _buildRuleSection() {
    final visible =
        _visibleRules;

    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Text(
          '规则列表',
          style:
              Theme.of(context)
                  .textTheme
                  .titleMedium,
        ),
        const SizedBox(
          height: 8,
        ),
        TextField(
          controller:
              _ruleSearchController,
          onChanged: (_) {
            setState(() {});
          },
          decoration:
              const InputDecoration(
            hintText:
                '筛选规则',
            prefixIcon:
                Icon(
              Icons.filter_alt_outlined,
            ),
            border:
                OutlineInputBorder(),
          ),
        ),
        const SizedBox(
          height: 10,
        ),
        for (final rule
            in visible) ...[
          Card(
            child: ListTile(
              leading:
                  CircleAvatar(
                child: Icon(
                  rule.searchRequest ==
                          null
                      ? Icons
                          .extension_off_outlined
                      : Icons
                          .extension_rounded,
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
                  Text(
                    rule.baseUrl,
                    maxLines: 1,
                    overflow:
                        TextOverflow
                            .ellipsis,
                  ),
                  Text(
                    rule.searchOps
                        .join(' → '),
                    maxLines: 2,
                    overflow:
                        TextOverflow
                            .ellipsis,
                  ),
                ],
              ),
              trailing:
                  IconButton(
                tooltip:
                    '查看 JSON',
                onPressed: () {
                  _showRuleJson(
                    rule,
                  );
                },
                icon:
                    const Icon(
                  Icons
                      .code_rounded,
                ),
              ),
              onTap: () {
                setState(() {
                  _selectedRule =
                      rule;
                });
              },
            ),
          ),
          const SizedBox(
            height: 6,
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
    required this.headers,
    required this.searchOps,
    required this.searchRequest,
  });

  final String id;
  final String name;
  final String baseUrl;
  final String description;
  final String iconUrl;
  final String file;

  final Map<String, String>
      headers;

  final List<String>
      searchOps;

  final _AniBakaSearchRequest?
      searchRequest;

  factory _AniBakaRule.fromMap(
    Map<dynamic, dynamic> map,
  ) {
    final headers =
        <String, String>{};

    final rawHeaders =
        map['headers'];

    if (rawHeaders is Map) {
      for (final entry
          in rawHeaders.entries) {
        headers[
            entry.key.toString()] =
            entry.value.toString();
      }
    }

    final ops =
        <String>[];

    final rawOps =
        map['searchOps'];

    if (rawOps is List) {
      for (final value
          in rawOps) {
        ops.add(
          value.toString(),
        );
      }
    }

    final rawRequest =
        map['searchRequest'];

    return _AniBakaRule(
      id:
          map['id']?.toString() ??
              '',
      name:
          map['name']
                  ?.toString() ??
              '',
      baseUrl:
          map['baseUrl']
                  ?.toString() ??
              '',
      description:
          map['description']
                  ?.toString() ??
              '',
      iconUrl:
          map['iconUrl']
                  ?.toString() ??
              '',
      file:
          map['file']
                  ?.toString() ??
              '',
      headers: headers,
      searchOps: ops,
      searchRequest:
          rawRequest is Map
              ? _AniBakaSearchRequest
                  .fromMap(
                  rawRequest,
                )
              : null,
    );
  }
}

class _AniBakaSearchRequest {
  const _AniBakaSearchRequest({
    required this.url,
    required this.method,
    required this.headers,
    required this.body,
  });

  final String url;
  final String method;
  final Map<String, String>
      headers;
  final String body;

  factory _AniBakaSearchRequest.fromMap(
    Map<dynamic, dynamic> map,
  ) {
    final headers =
        <String, String>{};

    final rawHeaders =
        map['headers'];

    if (rawHeaders is Map) {
      for (final entry
          in rawHeaders.entries) {
        headers[
            entry.key.toString()] =
            entry.value.toString();
      }
    }

    return _AniBakaSearchRequest(
      url:
          map['url']
                  ?.toString() ??
              '',
      method:
          map['method']
                  ?.toString()
                  .toUpperCase() ??
              'GET',
      headers: headers,
      body:
          map['body']
                  ?.toString() ??
              '',
    );
  }
}

class _AniBakaSearchResult {
  const _AniBakaSearchResult({
    required this.title,
    required this.image,
    required this.detail,
    required this.subtitle,
  });

  final String title;
  final String image;
  final String detail;
  final String subtitle;
}
'''.lstrip()

    ANIBAKA_PAGE.write_text(
        content,
        encoding="utf-8",
    )


def patch_plugin_module():
    require_file(
        PLUGIN_MODULE
    )

    text = PLUGIN_MODULE.read_text(
        encoding="utf-8"
    )

    import_line = (
        "import "
        "'package:kazumi/pages/"
        "plugin_editor/"
        "anibaka_preview_page.dart';\n"
    )

    if import_line not in text:
        marker = (
            "import "
            "'package:flutter_modular/"
            "flutter_modular.dart';\n"
        )

        if marker not in text:
            raise RuntimeError(
                "找不到 flutter_modular import"
            )

        text = text.replace(
            marker,
            marker + import_line,
            1,
        )

    if (
        "'/anibaka-preview'"
        not in text
    ):
        marker = """      ..route(
        '/shop',
"""

        replacement = """      ..route(
        '/anibaka-preview',
        child: (context, state) =>
            const AniBakaPreviewPage(),
      )
      ..route(
        '/shop',
"""

        if marker not in text:
            raise RuntimeError(
                "找不到 /shop 路由"
            )

        text = text.replace(
            marker,
            replacement,
            1,
        )

    PLUGIN_MODULE.write_text(
        text,
        encoding="utf-8",
    )


def patch_plugin_view():
    require_file(
        PLUGIN_VIEW
    )

    text = PLUGIN_VIEW.read_text(
        encoding="utf-8"
    )

    if (
        "anibaka-preview"
        in text
    ):
        log(
            "AniBaka 入口已存在"
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
                                icon: const Icon(Icons.travel_explore_rounded),
                                label: const Text('AniBaka 搜索')),
"""

    if marker not in text:
        raise RuntimeError(
            "找不到规则仓库按钮"
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


def verify():
    require_file(
        ASSET_ROOT
        / "manifest.json"
    )

    require_file(
        ANIBAKA_PAGE
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
            "没有识别到规则"
        )

    page_text = (
        ANIBAKA_PAGE.read_text(
            encoding="utf-8"
        )
    )

    if (
        "AniBaka 搜索兼容测试"
        not in page_text
    ):
        raise RuntimeError(
            "搜索页面生成失败"
        )

    module_text = (
        PLUGIN_MODULE.read_text(
            encoding="utf-8"
        )
    )

    if (
        "anibaka-preview"
        not in module_text
    ):
        raise RuntimeError(
            "AniBaka 路由缺失"
        )

    log(
        f"最终检查完成："
        f"{count} 条规则"
    )


def main():
    log(
        "开始生成 AniBaka "
        "搜索测试版"
    )

    prepare_assets()
    patch_pubspec()
    write_anibaka_page()
    patch_plugin_module()
    patch_plugin_view()
    verify()

    log(
        "AniBaka 搜索测试版"
        "生成完成"
    )


if __name__ == "__main__":
    main()
