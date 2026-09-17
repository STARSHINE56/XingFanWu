import 'dart:math';

bool needUpdate(String localVersion, String remoteVersion) {
  final normalizedLocal = _normalizeVersion(localVersion);
  final normalizedRemote = _normalizeVersion(remoteVersion);

  final localVersionList = normalizedLocal.split('.');
  final remoteVersionList = normalizedRemote.split('.');

  final maxLength = max(
    localVersionList.length,
    remoteVersionList.length,
  );

  for (var i = 0; i < maxLength; i++) {
    final localSegment = i < localVersionList.length
        ? int.tryParse(localVersionList[i]) ?? 0
        : 0;

    final remoteSegment = i < remoteVersionList.length
        ? int.tryParse(remoteVersionList[i]) ?? 0
        : 0;

    if (remoteSegment > localSegment) {
      return true;
    }

    if (remoteSegment < localSegment) {
      return false;
    }
  }

  return false;
}

String _normalizeVersion(String version) {
  var result = version.trim();

  if (result.startsWith('v') || result.startsWith('V')) {
    result = result.substring(1);
  }

  if (result.contains('+')) {
    result = result.split('+').first;
  }

  if (result.contains('-')) {
    result = result.split('-').first;
  }

  return result;
}
