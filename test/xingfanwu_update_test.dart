import 'package:flutter_test/flutter_test.dart';
import 'package:kazumi/services/update/auto_updater.dart';
import 'package:kazumi/utils/version.dart';

void main() {
  group('星番屋版本比较', () {
    test('GitHub v 前缀的新版本能够正常识别', () {
      expect(
        needUpdate('1.0.0', 'v1.0.1'),
        isTrue,
      );
    });

    test('相同版本不提示更新', () {
      expect(
        needUpdate('1.0.1', 'v1.0.1'),
        isFalse,
      );
    });

    test('本地版本更高不提示更新', () {
      expect(
        needUpdate('1.0.2', 'v1.0.1'),
        isFalse,
      );
    });

    test('本地 build metadata 不影响版本比较', () {
      expect(
        needUpdate('1.0.1+5', 'v1.0.2'),
        isTrue,
      );
    });

    test('预发布后缀不会造成解析异常', () {
      expect(
        needUpdate('1.0.1-beta.1', 'v1.0.2'),
        isTrue,
      );
    });
  });

  group('星番屋 Android APK 匹配', () {
    test('能够识别 XingFanWu 正式 APK', () {
      final assets = <dynamic>[
        <String, dynamic>{
          'name': 'source-code.zip',
          'browser_download_url':
              'https://example.com/source-code.zip',
        },
        <String, dynamic>{
          'name': 'XingFanWu-v1.0.2-release.apk',
          'browser_download_url':
              'https://example.com/XingFanWu-v1.0.2-release.apk',
        },
      ];

      final asset = getUpdateAssetForType(
        assets,
        InstallationType.androidApk,
      );

      expect(asset, isNotNull);
      expect(
        asset!['name'],
        'XingFanWu-v1.0.2-release.apk',
      );
    });

    test('没有 APK 时返回 null', () {
      final assets = <dynamic>[
        <String, dynamic>{
          'name': 'source-code.zip',
          'browser_download_url':
              'https://example.com/source-code.zip',
        },
      ];

      final asset = getUpdateAssetForType(
        assets,
        InstallationType.androidApk,
      );

      expect(asset, isNull);
    });

    test('APK 下载链接能够正确读取', () {
      final asset = <String, dynamic>{
        'name': 'XingFanWu-v1.0.2-release.apk',
        'browser_download_url':
            'https://example.com/XingFanWu-v1.0.2-release.apk',
      };

      expect(
        getUpdateDownloadUrlFromAsset(asset),
        'https://example.com/XingFanWu-v1.0.2-release.apk',
      );
    });

    test('SHA256 digest 能够正确解析', () {
      final asset = <String, dynamic>{
        'digest': 'sha256:1234567890abcdef',
      };

      expect(
        getUpdateFileHashFromAsset(asset),
        '1234567890abcdef',
      );
    });

    test('Android 更新规则只要求 APK 扩展名', () {
      expect(
        getUpdateFilePatterns(
          InstallationType.androidApk,
        ),
        ['.apk'],
      );
    });
  });
}
