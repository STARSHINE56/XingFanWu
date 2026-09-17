<div align="center">

# 星番屋

<img src="assets/images/logo/logo_rounded.png" width="180" alt="星番屋 Logo">

<br>

<img src="https://img.shields.io/badge/Flutter-03A9F4?style=flat-square&logo=flutter&logoColor=white" alt="Flutter">
<img src="https://img.shields.io/badge/Dart-0175C2?style=flat-square&logo=dart&logoColor=white" alt="Dart">
<img src="https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Android">
<img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=flat-square" alt="GPL-3.0">

<br><br>

基于自定义规则的番剧采集、在线观看与弹幕播放器。

**基于 [Kazumi](https://github.com/Predidit/Kazumi) 二次开发。**

</div>

---

## 项目介绍

**星番屋（XingFanWu）** 是基于开源项目
[Kazumi](https://github.com/Predidit/Kazumi)
进行二次开发的 Android 番剧应用。

在保留上游主要功能的基础上，对 Android 版本进行了品牌化以及部分使用体验调整。

当前项目主要信息：

- 应用名称：**星番屋**
- Android 包名：`com.starshine.xingfanwu`
- 开发框架：Flutter
- 主要平台：Android
- 开源协议：GPL-3.0
- 项目仓库：[STARSHINE56/XingFanWu](https://github.com/STARSHINE56/XingFanWu)

> 星番屋与 Kazumi 原项目独立维护。
>
> 星番屋的 APK、版本发布和应用更新均由本仓库提供。

---

## 功能

- [x] 自定义规则
- [x] 规则编辑器
- [x] 规则导入与分享
- [x] 番剧目录
- [x] 番剧搜索
- [x] 番剧时间表
- [x] 番剧字幕
- [x] 分集播放
- [x] 内置视频播放器
- [x] 多视频源支持
- [x] 番剧弹幕
- [x] 历史记录
- [x] 追番列表
- [x] 番剧下载
- [x] 倍速播放
- [x] 硬件加速
- [x] 高刷新率适配
- [x] 配色方案
- [x] 跨设备同步
- [x] 无线投屏（DLNA）
- [x] 外部播放器
- [x] Anime4K 实时超分辨率
- [x] SyncPlay 一起看
- [x] 在线更新
- [ ] 番剧更新提醒
- [ ] 更多功能持续完善中

---

## 下载

请通过本项目的 GitHub Releases 下载正式版本：

### [前往星番屋 Releases](https://github.com/STARSHINE56/XingFanWu/releases/latest)

正式版 APK 通常命名为：

`XingFanWu-v版本号-release.apk`

例如：

`XingFanWu-v1.0.0-release.apk`

建议仅从本项目 GitHub Releases 页面下载 APK。

---

## 在线更新

星番屋使用本项目自己的 GitHub Releases 作为版本更新来源。

应用会读取：

`https://api.github.com/repos/STARSHINE56/XingFanWu/releases/latest`

因此应用不会使用 Kazumi 官方 Release 作为星番屋的版本更新来源。

---

## 自定义规则

星番屋继续兼容 Kazumi 的自定义规则机制。

规则主要使用基于 `XPath` 语法的选择器实现，可用于添加不同的番剧视频来源。

当前继续兼容 Kazumi 社区规则仓库：

[KazumiRules](https://github.com/Predidit/KazumiRules)

> 视频规则可能由第三方或社区成员维护。
>
> 星番屋本身不提供、上传或托管影视资源。

---

## 常见问题

<details>
<summary><strong>为什么部分视频中会出现广告？</strong></summary>

<br>

星番屋本身不会主动向视频内容中插入广告。

部分广告可能来自第三方视频源，请不要轻信第三方页面中的广告内容。

</details>

<details>
<summary><strong>为什么开启超分辨率后播放会卡顿？</strong></summary>

<br>

Anime4K 实时超分辨率需要消耗较多 GPU 性能。

如果设备性能不足，可以尝试关闭超分辨率或使用性能消耗较低的设置。

</details>

<details>
<summary><strong>为什么播放时内存占用较高？</strong></summary>

<br>

播放器可能会缓存部分视频数据，以改善播放和缓冲体验。

如果设备内存较小，可以尝试启用低内存相关设置。

</details>

<details>
<summary><strong>为什么部分视频无法使用外部播放器？</strong></summary>

<br>

部分第三方视频源可能存在 Referer、Cookie 或其他访问限制。

内置播放器可能能够处理这些条件，而外部播放器不一定支持。

</details>

<details>
<summary><strong>为什么某些规则可以搜索，但是无法播放？</strong></summary>

<br>

不同网站的实现方式存在差异。

可以尝试切换规则中的播放器选项，或者使用 WebView 模式提高兼容性。

</details>

---

## 开发说明

本项目主要使用：

- Flutter
- Dart
- Android
- Gradle
- GitHub Actions
