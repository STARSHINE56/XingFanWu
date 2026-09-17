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


def collect_ops(value):
    result = []

    if isinstance(value, dict):
        op = value.get("op")

        if isinstance(op, str):
            result.append(op)

        for child in value.values():
            result.extend(
                collect_ops(child)
            )

    elif isinstance(value, list):
        for child in value:
            result.extend(
                collect_ops(child)
            )

    return result


def prepare_assets():
    log("准备 AniBaka 规则")

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
        ANIBAKA_SOURCE.glob("*.json")
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

        request = (
            find_fetch_request(
                search
            )
        )

        search_ops = list(
            dict.fromkeys(
                collect_ops(search)
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
                "useWebview": bool(
                    data.get(
                        "useWebview",
                        False,
                    )
                ),
                "headers": headers,
                "file":
                    source_file.name,
                "searchRequest":
                    request,
                "searchOps":
                    search_ops,
            }
        )

    manifest = {
        "format":
            "xingfanwu-anibaka-preview/3",
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

    webview_count = sum(
        1
        for rule in rules
        if rule["useWebview"]
    )

    log(
        f"识别到 {len(rules)} 条规则"
    )

    log(
        f"其中 {webview_count} 条"
        "要求 WebView"
    )


def patch_pubspec():
    require_file(PUBSPEC)

    text = PUBSPEC.read_text(
        encoding="utf-8"
    )

    asset_lines = [
        "    - assets/anibaka/\n",
        (
            "    - "
            "assets/anibaka/rules/\n"
        ),
    ]

    missing_assets = [
        line
        for line in asset_lines
        if line not in text
    ]

    if missing_assets:
        marker = "  assets:\n"

        if marker not in text:
            raise RuntimeError(
                "pubspec.yaml 找不到 "
                "flutter assets"
            )

        text = text.replace(
            marker,
            marker
            + "".join(
                missing_assets
            ),
            1,
        )

    dependency_line = (
        "  flutter_inappwebview: "
        "^6.1.5\n"
    )

    if (
        "  flutter_inappwebview:"
        not in text
    ):
        marker = (
            "  flutter_inappwebview_"
            "platform_interface:"
        )

        index = text.find(marker)

        if index != -1:
            line_start = (
                text.rfind(
                    "\n",
                    0,
                    index,
                )
                + 1
            )

            text = (
                text[:line_start]
                + dependency_line
                + text[line_start:]
            )

            log(
                "已临时加入 "
                "flutter_inappwebview"
            )
        else:
            flutter_dep = (
                "  flutter:\n"
                "    sdk: flutter\n"
            )

            if flutter_dep not in text:
                raise RuntimeError(
                    "找不到 dependencies "
                    "中的 flutter"
                )

            text = text.replace(
                flutter_dep,
                flutter_dep
                + dependency_line,
                1,
            )

    PUBSPEC.write_text(
        text,
        encoding="utf-8",
    )


def write_anibaka_page():
    log(
        "生成 AniBaka "
        "HTTP + WebView 搜索页面"
    )

    content = r'''
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
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
  final TextEditingController _keywordController =
      TextEditingController(
    text: '葬送的芙莉莲',
  );

  final TextEditingController _ruleFilterController =
      TextEditingController();

  final HttpClient _httpClient = HttpClient();

  List<_AniBakaRule> _rules = const [];
  List<_AniBakaSearchResult> _results = const [];

  _AniBakaRule? _selectedRule;

  bool _loading = true;
  bool _searching = false;

  String? _error;
  String? _message;
  String? _requestUrl;

  @override
  void initState() {
    super.initState();

    _httpClient.connectionTimeout =
        const Duration(
      seconds: 20,
    );

    _loadRules();
  }

  @override
  void dispose() {
    _keywordController.dispose();
    _ruleFilterController.dispose();

    _httpClient.close(
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
          'manifest 没有 rules',
        );
      }

      final rules =
          <_AniBakaRule>[];

      for (final item in rawRules) {
        if (item is Map) {
          rules.add(
            _AniBakaRule.fromMap(
              item,
            ),
          );
        }
      }

      if (!mounted) {
        return;
      }

      setState(() {
        _rules = rules;

        if (rules.isNotEmpty) {
          _selectedRule =
              rules.firstWhere(
            (rule) =>
                rule.searchRequest
                    != null,
            orElse: () =>
                rules.first,
          );
        }

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
        _ruleFilterController
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
        _keywordController
            .text
            .trim();

    if (keyword.isEmpty) {
      _snack(
        '请输入番剧名称',
      );
      return;
    }

    final request =
        rule.searchRequest;

    if (request == null ||
        request.url.isEmpty) {
      setState(() {
        _results = const [];
        _message =
            '当前规则没有识别到 '
            'fetch 搜索入口';
      });

      return;
    }

    setState(() {
      _searching = true;
      _results = const [];
      _message = null;
      _requestUrl = null;
    });

    try {
      final rawUrl =
          _replaceTemplate(
        request.url,
        keyword,
      );

      final uri =
          _resolveUri(
        rule,
        rawUrl,
      );

      if (uri == null ||
          !uri.hasScheme) {
        throw FormatException(
          '无效搜索地址：$rawUrl',
        );
      }

      _requestUrl =
          uri.toString();

      String body;

      if (rule.useWebview) {
        body =
            await _fetchWithWebView(
          rule,
          request,
          uri,
          keyword,
        );
      } else {
        body =
            await _fetchWithHttp(
          rule,
          request,
          uri,
          keyword,
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

      final cleaned =
          _deduplicate(
        results,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _results = cleaned;
        _searching = false;

        if (cleaned.isEmpty) {
          _message =
              '页面读取成功，但暂时'
              '没有解析出搜索结果。\n\n'
              '执行方式：'
              '${rule.useWebview ? 'WebView' : 'HTTP'}\n'
              '搜索操作：'
              '${rule.searchOps.join(' → ')}';
        } else {
          _message =
              '搜索成功：'
              '${cleaned.length} 条结果\n'
              '执行方式：'
              '${rule.useWebview ? 'WebView' : 'HTTP'}';
        }
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _searching = false;
        _results = const [];

        _message =
            '搜索失败：$error\n\n'
            '执行方式：'
            '${rule.useWebview ? 'WebView' : 'HTTP'}';
      });
    }
  }

  Map<String, String> _makeHeaders(
    _AniBakaRule rule,
    _AniBakaSearchRequest request,
    String keyword,
  ) {
    final headers =
        <String, String>{};

    headers.addAll(
      rule.headers,
    );

    headers.addAll(
      request.headers,
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
      () =>
          'text/html,application/xhtml+xml,'
          'application/xml;q=0.9,image/avif,'
          'image/webp,*/*;q=0.8',
    );

    if (rule.baseUrl.isNotEmpty) {
      headers.putIfAbsent(
        'Referer',
        () => rule.baseUrl,
      );
    }

    return headers.map(
      (key, value) =>
          MapEntry(
        key,
        _replaceTemplate(
          value,
          keyword,
        ),
      ),
    );
  }

  Future<String> _fetchWithHttp(
    _AniBakaRule rule,
    _AniBakaSearchRequest requestInfo,
    Uri uri,
    String keyword,
  ) async {
    final method =
        requestInfo.method
            .toUpperCase();

    HttpClientRequest request;

    if (method == 'POST') {
      request =
          await _httpClient
              .postUrl(uri);
    } else {
      request =
          await _httpClient
              .getUrl(uri);
    }

    final headers =
        _makeHeaders(
      rule,
      requestInfo,
      keyword,
    );

    for (final entry
        in headers.entries) {
      request.headers.set(
        entry.key,
        entry.value,
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
        output,
        value,
      ) {
        output.addAll(value);
        return output;
      },
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

  Future<String> _fetchWithWebView(
    _AniBakaRule rule,
    _AniBakaSearchRequest requestInfo,
    Uri uri,
    String keyword,
  ) async {
    if (requestInfo.method
            .toUpperCase() !=
        'GET') {
      throw UnsupportedError(
        '当前 WebView 测试版'
        '暂只支持 GET 搜索',
      );
    }

    final completer =
        Completer<String>();

    HeadlessInAppWebView?
        headlessWebView;

    final headers =
        _makeHeaders(
      rule,
      requestInfo,
      keyword,
    );

    final userAgent =
        headers['User-Agent'];

    headlessWebView =
        HeadlessInAppWebView(
      initialUrlRequest:
          URLRequest(
        url: WebUri(
          uri.toString(),
        ),
        headers: headers,
      ),
      initialSettings:
          InAppWebViewSettings(
        javaScriptEnabled: true,
        domStorageEnabled: true,
        databaseEnabled: true,
        clearCache: false,
        cacheEnabled: true,
        useShouldOverrideUrlLoading:
            false,
        userAgent: userAgent,
        mediaPlaybackRequiresUserGesture:
            true,
      ),
      onLoadStop:
          (
        controller,
        loadedUrl,
      ) async {
        if (completer.isCompleted) {
          return;
        }

        await Future<void>.delayed(
          const Duration(
            milliseconds: 1800,
          ),
        );

        try {
          final result =
              await controller
                  .evaluateJavascript(
            source:
                'document.documentElement.outerHTML',
          );

          final html =
              result?.toString() ??
                  '';

          if (html.isNotEmpty &&
              !completer.isCompleted) {
            completer.complete(
              html,
            );
          }
        } catch (error) {
          if (!completer.isCompleted) {
            completer.completeError(
              error,
            );
          }
        }
      },
    );

    await headlessWebView.run();

    try {
      return await completer.future
          .timeout(
        const Duration(
          seconds: 35,
        ),
        onTimeout: () {
          throw TimeoutException(
            'WebView 加载超时',
          );
        },
      );
    } finally {
      await headlessWebView.dispose();
    }
  }

  List<_AniBakaSearchResult>
      _parseJsonResults(
    String body,
    _AniBakaRule rule,
  ) {
    final trimmed =
        body.trimLeft();

    if (!trimmed.startsWith('{') &&
        !trimmed.startsWith('[')) {
      return const [];
    }

    try {
      final decoded =
          jsonDecode(body);

      final maps =
          <Map<dynamic, dynamic>>[];

      void walk(dynamic value) {
        if (value is Map) {
          final hasTitle =
              value.containsKey(
                    'name',
                  ) ||
                  value.containsKey(
                    'title',
                  ) ||
                  value.containsKey(
                    'vod_name',
                  );

          if (hasTitle) {
            maps.add(value);
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
            _firstValue(
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
            _firstValue(
          item,
          const [
            'pic',
            'image',
            'cover',
            'vod_pic',
            'poster',
          ],
        );

        final detail =
            _firstValue(
          item,
          const [
            'url',
            'href',
            'link',
            'detailUrl',
          ],
        );

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
              detail,
            ),
          ),
        );
      }

      return results;
    } catch (_) {
      return const [];
    }
  }

  String _firstValue(
    Map<dynamic, dynamic> map,
    List<String> keys,
  ) {
    for (final key in keys) {
      final value =
          map[key];

      if (value != null) {
        final text =
            value
                .toString()
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
      r"""<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)</a>""",
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
          match.group(2) ??
              '';

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
          _attribute(
        inner,
        'title',
      );

      if (title.isEmpty) {
        title =
            _attribute(
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

      title = title.trim();

      if (title.isEmpty ||
          title.length > 150) {
        continue;
      }

      var image =
          _attribute(
        inner,
        'data-src',
      );

      if (image.isEmpty) {
        image =
            _attribute(
          inner,
          'data-original',
        );
      }

      if (image.isEmpty) {
        image =
            _attribute(
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
        ),
      );
    }

    return results;
  }

  String _attribute(
    String html,
    String name,
  ) {
    final pattern =
        RegExp(
      '$name'
      r"""\s*=\s*["']([^"']+)["']""",
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

    return _resolveUri(
          rule,
          value,
        )?.toString() ??
        value;
  }

  List<_AniBakaSearchResult>
      _deduplicate(
    List<_AniBakaSearchResult>
        input,
  ) {
    final seen =
        <String>{};

    final output =
        <_AniBakaSearchResult>[];

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

  void _snack(
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
    final raw =
        await rootBundle.loadString(
      'assets/anibaka/rules/${rule.file}',
    );

    final pretty =
        const JsonEncoder.withIndent(
      '  ',
    ).convert(
      jsonDecode(raw),
    );

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
              child: SelectableText(
                pretty,
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
                    text: pretty,
                  ),
                );
              },
              icon: const Icon(
                Icons
                    .content_copy_rounded,
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
        child: SelectableText(
          '加载失败\n\n$_error',
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
        _buildSearchCard(),
        if (_message != null) ...[
          const SizedBox(
            height: 12,
          ),
          Card(
            child: Padding(
              padding:
                  const EdgeInsets.all(
                16,
              ),
              child: SelectableText(
                _message!,
              ),
            ),
          ),
        ],
        if (_requestUrl !=
            null) ...[
          const SizedBox(
            height: 8,
          ),
          Card(
            child: ListTile(
              leading:
                  const Icon(
                Icons.link_rounded,
              ),
              title:
                  const Text(
                '实际请求地址',
              ),
              subtitle:
                  SelectableText(
                _requestUrl!,
              ),
            ),
          ),
        ],
        if (_results
            .isNotEmpty) ...[
          const SizedBox(
            height: 20,
          ),
          _buildResults(),
        ],
        const SizedBox(
          height: 24,
        ),
        _buildRuleList(),
      ],
    );
  }

  Widget _buildHeader() {
    final webviewCount =
        _rules
            .where(
              (rule) =>
                  rule.useWebview,
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
            Text(
              'AniBaka 双引擎搜索',
              style:
                  Theme.of(context)
                      .textTheme
                      .titleLarge,
            ),
            const SizedBox(
              height: 12,
            ),
            Text(
              '规则总数：'
              '${_rules.length}',
            ),
            Text(
              'WebView 规则：'
              '$webviewCount',
            ),
            const SizedBox(
              height: 8,
            ),
            const Text(
              '普通规则使用 HTTP，'
              'useWebview 规则自动使用 '
              'WebView 获取最终页面。',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchCard() {
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
            DropdownButtonFormField<
                _AniBakaRule>(
              value: rule,
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
                        item.useWebview
                            ? '${item.name} · WebView'
                            : '${item.name} · HTTP',
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
                  _message =
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
                border:
                    OutlineInputBorder(),
                prefixIcon:
                    Icon(
                  Icons.search_rounded,
                ),
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
                height: 10,
              ),
              Text(
                '执行方式：'
                '${rule.useWebview ? 'WebView' : 'HTTP'}',
              ),
              Text(
                '搜索操作：'
                '${rule.searchOps.join(' → ')}',
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
                            ) =>
                                    const Icon(
                              Icons
                                  .broken_image_outlined,
                            ),
                          ),
              ),
              title: Text(
                item.title,
              ),
              subtitle:
                  SelectableText(
                item.detail,
                maxLines: 2,
              ),
              trailing:
                  const Icon(
                Icons
                    .chevron_right_rounded,
              ),
              onTap: () {
                _snack(
                  '下一阶段接入详情和剧集',
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

  Widget _buildRuleList() {
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
              _ruleFilterController,
          onChanged: (_) {
            setState(() {});
          },
          decoration:
              const InputDecoration(
            hintText:
                '筛选规则',
            border:
                OutlineInputBorder(),
            prefixIcon:
                Icon(
              Icons
                  .filter_alt_outlined,
            ),
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
                  rule.useWebview
                      ? Icons
                          .language_rounded
                      : Icons
                          .http_rounded,
                ),
              ),
              title: Text(
                rule.name,
              ),
              subtitle: Text(
                '${rule.useWebview ? 'WebView' : 'HTTP'}'
                ' · '
                '${rule.searchOps.join(' → ')}',
              ),
              trailing:
                  IconButton(
                onPressed: () {
                  _showRuleJson(
                    rule,
                  );
                },
                icon:
                    const Icon(
                  Icons.code_rounded,
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
    required this.useWebview,
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

  final bool useWebview;

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
          map['id']
                  ?.toString() ??
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
      useWebview:
          map['useWebview'] ==
              true,
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
  });

  final String title;
  final String image;
  final String detail;
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
                "找不到 "
                "flutter_modular import"
            )

        text = text.replace(
            marker,
            marker
            + import_line,
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
                                icon: const Icon(Icons.language_rounded),
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
            "没有 AniBaka 规则"
        )

    page_text = (
        ANIBAKA_PAGE.read_text(
            encoding="utf-8"
        )
    )

    required = [
        "HeadlessInAppWebView",
        "useWebview",
        "AniBaka 双引擎搜索",
    ]

    for keyword in required:
        if keyword not in page_text:
            raise RuntimeError(
                f"缺少关键代码："
                f"{keyword}"
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
        f"检查完成："
        f"{count} 条规则"
    )


def main():
    log(
        "开始生成 AniBaka "
        "双引擎搜索测试版"
    )

    prepare_assets()
    patch_pubspec()
    write_anibaka_page()
    patch_plugin_module()
    patch_plugin_view()
    verify()

    log(
        "AniBaka 双引擎"
        "搜索测试版生成完成"
    )


if __name__ == "__main__":
    main()
