<div align="center">

# 星番屋

<img src="assets/images/logo/logo_rounded.png" width="200" alt="星番屋 Logo">

<img src="https://img.shields.io/badge/Flutter-03A9F4?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter">
<img src="https://img.shields.io/badge/Dart-00B4AB?style=for-the-badge&logo=dart&logoColor=white" alt="Dart">
<img src="https://img.shields.io/badge/Platform-Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android">
<img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="GPL-3.0">

<p>
星番屋是一款使用 Flutter 开发的番剧采集与在线观看应用，
支持通过自定义规则获取番剧资源，并提供弹幕、历史记录、下载、超分辨率等功能。
</p>

<p>
本项目基于
<a href="https://github.com/Predidit/Kazumi">Kazumi</a>
进行二次开发。
</p>

</div>

---

## 项目说明

**星番屋** 基于开源项目
[Kazumi](https://github.com/Predidit/Kazumi)
进行二次开发。

在保留原项目主要功能的基础上，对 Android 版本进行了品牌化、应用标识、包名、更新渠道和发布流程等调整。

当前 Android 包名：

```text
com.starshine.xingfanwu

当前项目仓库：

https://github.com/STARSHINE56/XingFanWu


---

支持平台

当前星番屋主要维护：

Android


其他平台相关代码可能仍保留自上游 Kazumi，但目前不作为星番屋主要发布平台。


---

功能

[x] 自定义规则

[x] 规则编辑器

[x] 番剧目录

[x] 番剧搜索

[x] 番剧时间表

[x] 番剧字幕

[x] 分集播放

[x] 内置视频播放器

[x] 多视频源支持

[x] 规则导入与分享

[x] 硬件加速

[x] 高刷新率适配

[x] 追番列表

[x] 番剧弹幕

[x] 在线更新

[x] 历史记录

[x] 倍速播放

[x] 配色方案

[x] 跨设备同步

[x] 无线投屏（DLNA）

[x] 外部播放器

[x] Anime4K 实时超分辨率

[x] 一起看

[x] 番剧下载

[ ] 番剧更新提醒

[ ] 更多功能持续完善中

---

自定义规则

星番屋继续兼容 Kazumi 的自定义规则机制。

规则主要使用基于 XPath 语法的选择器实现。

上游规则仓库：

https://github.com/Predidit/KazumiRules

规则仓库属于 Kazumi 生态资源，星番屋目前继续兼容使用。


---

常见问题

<details>
<summary>为什么少数番剧中会出现广告？</summary>星番屋本身不会主动在视频内容中插入广告。

部分广告可能来自第三方视频源。

请不要相信视频源页面中的广告内容，并建议优先选择体验较好的视频源。

</details><details>
<summary>为什么开启超分辨率后播放会变卡？</summary>Anime4K 实时超分辨率会增加 GPU 负载。

设备性能不足时，建议：

关闭超分辨率

使用较低的超分辨率档位

优先对低分辨率视频源使用超分辨率


</details><details>
<summary>为什么播放视频时内存占用较高？</summary>播放器可能会将部分视频数据缓存到内存中，以改善播放和缓冲体验。

如果设备内存较少，可以尝试在播放设置中启用低内存相关选项。

</details><details>
<summary>为什么部分视频无法使用外部播放器播放？</summary>部分视频源存在 Referer、Cookie 或其他反盗链限制。

内置播放器可能能够处理这些请求条件，而第三方播放器不一定支持。

</details><details>
<summary>为什么某些自定义规则可以搜索，但是无法播放？</summary>部分网站无法直接提取标准视频地址。

可以尝试关闭规则中的“使用内置播放器”相关选项，让应用通过 WebView 兼容方式尝试播放。

如果内置播放器可以正常工作，通常建议优先使用内置播放器，以获得弹幕等完整功能。

</details>

---

开源说明

星番屋基于：

Kazumi

进行二次开发。

感谢 Kazumi 原作者及所有贡献者提供的优秀开源项目。

上游项目采用：

GNU General Public License v3.0

星番屋继续遵守 GPL-3.0 开源许可证。

项目源代码保持公开，并保留上游项目所要求的许可证及版权信息。


---

第三方项目

星番屋及上游 Kazumi 使用或参考了多个优秀的开源项目和服务，包括但不限于：

Kazumi

XpathSelector

弹弹play

Bangumi

Anime4K

SyncPlay

trace.moe

media-kit

avbuild

Hive


感谢这些项目及其开发者。


---

免责声明

本项目仅用于学习、研究以及管理用户本人有权访问的内容。

使用者应自行确保其使用行为符合所在地法律法规、第三方服务条款以及相关版权规定。

开发者不对第三方视频源提供的内容负责，也不对因使用本项目造成的直接或间接损失承担责任。

请勿使用本项目侵犯任何个人、组织或版权方的合法权益。


---

隐私

星番屋不会主动收集用户个人数据，也不包含用于广告追踪的遥测组件。

第三方视频源、Bangumi、弹弹play 以及其他外部服务拥有各自独立的隐私政策和服务条款。


---

许可证

GNU General Public License v3.0

详细内容请查看：

LICENSE


---

致谢

特别感谢：

Kazumi 原作者及所有贡献者

XpathSelector

弹弹play

Bangumi

Anime4K

SyncPlay

trace.moe

media-kit

avbuild

Hive


以及所有为相关开源项目作出贡献的开发者。
